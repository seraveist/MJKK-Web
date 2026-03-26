"""
데이터베이스 서비스 모듈 (Phase 2 개선)
- 공통 시즌 필터링 파이프라인
- 프로젝션 지원 (필요한 필드만 가져오기)
- 캐싱 통합 (TTL 기반)
"""
import datetime
import logging
from typing import Optional

from pymongo import MongoClient, ASCENDING

from services.cache import cache, make_cache_key

logger = logging.getLogger(__name__)

# 랭킹 계산에 필요한 최소 필드 (log 제외 → 대폭 경량화)
RANKING_PROJECTION = {
    "_id": 0,
    "ref": 1,
    "name": 1,
    "sc": 1,
    "title": 1,
}

# 통계 계산용 필드 (log 포함, lobby 등 불필요 필드 제외)
STATS_PROJECTION = {
    "_id": 0,
    "ref": 1,
    "name": 1,
    "sc": 1,
    "title": 1,
    "log": 1,
    "dan": 1,
    "rate": 1,
    "sx": 1,
    "rule": 1,
    "ratingc": 1,
    "ver": 1,
}


class DatabaseService:
    """MongoDB 연결 및 쿼리 서비스"""

    def __init__(self, config):
        self._config = config
        self._client = None
        self._db = None
        self._collection = None

    def connect(self):
        try:
            self._client = MongoClient(self._config.DB_URL)
            self._db = self._client[self._config.DB_NAME]
            self._collection = self._db[self._config.COLLECTION_NAME]

            self._collection.create_index(
                [("ref", ASCENDING)], unique=True, background=True
            )
            self._collection.create_index(
                [("title.1", ASCENDING)], background=True
            )
            logger.info("Connected to MongoDB. DB=%s", self._config.DB_NAME)
        except Exception as e:
            logger.error("Failed to connect to MongoDB", exc_info=e)
            raise

    @property
    def collection(self):
        if self._collection is None:
            raise RuntimeError("Database not connected.")
        return self._collection

    def close(self):
        if self._client:
            self._client.close()

    # ------------------------------------------------------------------
    # 시즌 헬퍼
    # ------------------------------------------------------------------

    def get_season_range(self, season_number: int):
        if season_number < 1:
            raise ValueError("Season number must be >= 1")
        base_year = self._config.SEASON_BASE_YEAR
        year = base_year + (season_number - 1) // 2
        if season_number % 2 == 1:
            start = datetime.datetime(year, 1, 1)
            end = datetime.datetime(year, 6, 30, 23, 59, 59)
        else:
            start = datetime.datetime(year, 7, 1)
            end = datetime.datetime(year, 12, 31, 23, 59, 59)
        return start, end

    def get_current_season(self) -> int:
        today = datetime.datetime.today()
        base_year = self._config.SEASON_BASE_YEAR
        if today.month <= 6:
            return (today.year - base_year) * 2 + 1
        else:
            return (today.year - base_year) * 2 + 2

    # ------------------------------------------------------------------
    # 공통 파이프라인
    # ------------------------------------------------------------------

    def _build_season_pipeline(self, season_start, season_end, projection=None):
        pipeline = [
            {
                "$addFields": {
                    "logDate": {
                        "$dateFromString": {
                            "dateString": {"$arrayElemAt": ["$title", 1]},
                            "format": "%Y-%m-%d",
                        }
                    }
                }
            },
            {"$match": {"logDate": {"$gte": season_start, "$lte": season_end}}},
        ]
        if projection:
            pipeline.append({"$project": projection})
        return pipeline

    # ------------------------------------------------------------------
    # 데이터 조회 (캐싱 적용)
    # ------------------------------------------------------------------

    def fetch_game_logs(self, season_param: str = "all", lightweight: bool = False) -> list:
        """
        시즌별 게임 로그 조회.
        
        Args:
            season_param: "all" 또는 시즌 번호
            lightweight: True → log 필드 제외 (랭킹용, 훨씬 빠름)
        """
        mode = "light" if lightweight else "full"
        cache_key = make_cache_key("game_logs", season_param, mode)

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        projection = RANKING_PROJECTION if lightweight else None

        if season_param.lower() == "all":
            if lightweight:
                data = list(self.collection.find({}, projection))
            else:
                data = list(self.collection.find())
        else:
            try:
                season_number = int(season_param)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid season parameter: {season_param}")
            season_start, season_end = self.get_season_range(season_number)
            pipeline = self._build_season_pipeline(season_start, season_end, projection)
            data = list(self.collection.aggregate(pipeline))

        cache.set(cache_key, data)
        logger.info("DB fetch: %d logs (season=%s, %s)", len(data), season_param, mode)
        return data

    def fetch_game_logs_for_stats(self, season_param: str = "all") -> list:
        """통계 계산용 조회 (log 포함, 불필요 필드 제외)."""
        cache_key = make_cache_key("game_logs_stats", season_param)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        if season_param.lower() == "all":
            data = list(self.collection.find({}, STATS_PROJECTION))
        else:
            try:
                season_number = int(season_param)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid season parameter: {season_param}")
            season_start, season_end = self.get_season_range(season_number)
            pipeline = self._build_season_pipeline(
                season_start, season_end, STATS_PROJECTION
            )
            data = list(self.collection.aggregate(pipeline))

        cache.set(cache_key, data)
        return data

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def find_log_by_ref(self, ref: str) -> Optional[dict]:
        return self.collection.find_one({"ref": ref})

    def insert_game_log(self, game_log: dict) -> bool:
        """게임 로그 저장 + 캐시 무효화."""
        ref = game_log.get("ref")
        if not ref:
            raise ValueError("게임 로그에 'ref' 값이 없습니다.")
        if self.find_log_by_ref(ref):
            return False

        self.collection.insert_one(game_log)
        cache.clear()  # 새 데이터 → 전체 캐시 무효화
        logger.info("Game log inserted, cache cleared. ref=%s", ref)
        return True
