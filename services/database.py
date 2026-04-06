"""
데이터베이스 서비스 모듈
- [개선] name 멀티키 인덱스
- [개선] title.1 + name 복합 인덱스
"""
import datetime
import logging
from typing import Optional
from pymongo import MongoClient, ASCENDING
from services.cache import cache, make_cache_key

logger = logging.getLogger(__name__)

RANKING_PROJECTION = {"_id": 0, "ref": 1, "name": 1, "sc": 1, "title": 1}
STATS_PROJECTION = {"_id": 0, "ref": 1, "name": 1, "sc": 1, "title": 1, "log": 1, "dan": 1, "rate": 1, "sx": 1, "rule": 1, "ratingc": 1, "ver": 1}


class DatabaseService:
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

            # 기존 인덱스
            self._collection.create_index([("ref", ASCENDING)], unique=True, background=True)
            self._collection.create_index([("title.1", ASCENDING)], background=True)

            # [신규] name 멀티키 인덱스 — 특정 플레이어가 포함된 게임 검색
            self._collection.create_index([("name", ASCENDING)], background=True)

            # [신규] 코멘트 인덱스
            self._db["comments"].create_index([("game_ref", ASCENDING)], background=True)

            # [신규] 설정 초기화
            try:
                from services.settings import init_default_settings
                init_default_settings(self)
            except Exception as e:
                logger.warning("Settings init skipped: %s", e)

            logger.info("Connected to MongoDB. DB=%s, indexes created.", self._config.DB_NAME)
        except Exception as e:
            logger.error("Failed to connect to MongoDB", exc_info=e)
            raise

    @property
    def collection(self):
        if self._collection is None:
            raise RuntimeError("Database not connected.")
        return self._collection

    def _season_to_date_range(self, season):
        """단일 시즌 번호 → (start_date, end_date) 변환"""
        base_year = self._config.SEASON_BASE_YEAR
        if season % 2 == 1:
            year = base_year + season // 2
            return f"{year}-01-01", f"{year}-06-30 23:59:59"
        else:
            year = base_year + (season - 1) // 2
            return f"{year}-07-01", f"{year}-12-31 23:59:59"

    def _season_filter(self, season_param):
        if season_param == "all":
            return {}

        # 멀티 시즌 지원: "5,6,7" 형태
        if isinstance(season_param, str) and "," in season_param:
            parts = [p.strip() for p in season_param.split(",") if p.strip()]
            or_conditions = []
            for p in parts:
                try:
                    s = int(p)
                    start, end = self._season_to_date_range(s)
                    or_conditions.append({"title.1": {"$gte": start, "$lte": end}})
                except (ValueError, TypeError):
                    continue
            if not or_conditions:
                raise ValueError(f"Invalid seasons: {season_param}")
            return {"$or": or_conditions} if len(or_conditions) > 1 else or_conditions[0]

        # 단일 시즌
        try:
            season = int(season_param)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid season: {season_param}")

        start, end = self._season_to_date_range(season)
        return {"title.1": {"$gte": start, "$lte": end}}

    def fetch_game_logs(self, season_param, lightweight=False):
        cache_key = make_cache_key("game_logs", season_param, lightweight)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        query = self._season_filter(season_param)
        projection = RANKING_PROJECTION if lightweight else None
        data = list(self._collection.find(query, projection))

        cache.set(cache_key, data)
        return data

    def fetch_game_logs_for_stats(self, season_param):
        """통계 계산용 전체 로그 조회 — 전용 TTL(600초)"""
        cache_key = make_cache_key("stats_logs", season_param)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        query = self._season_filter(season_param)
        data = list(self._collection.find(query, STATS_PROJECTION))
        cache.set(cache_key, data, ttl=600)
        return data

    def fetch_game_logs_paged(self, season_param, page=1, per_page=30, filters=None):
        """
        시즌 필터와 추가 필터(날짜, 유저)를 결합하여
        DB 레벨에서 정렬 및 페이징된 데이터를 가져옵니다.
        """
        query = self._season_filter(season_param)

        if filters:
            # [버그#1 수정] 날짜 필터를 시즌 필터와 병합 (덮어쓰기 방지)
            if filters.get('date_from') or filters.get('date_to'):
                existing = query.get("title.1", {})
                if not isinstance(existing, dict):
                    existing = {}
                if filters.get('date_from'):
                    existing["$gte"] = max(existing.get("$gte", ""), filters['date_from'])
                if filters.get('date_to'):
                    existing["$lte"] = min(existing.get("$lte", "\uffff"), filters['date_to'])
                query["title.1"] = existing

            if filters.get('aliases'):
                query["name"] = {"$in": list(filters['aliases'])}

        # [패치#7] $facet으로 count + data 단일 쿼리
        skip = (page - 1) * per_page
        pipeline = [
            {"$match": query},
            {"$sort": {"title.1": -1}},
            {"$facet": {
                "data": [
                    {"$skip": skip},
                    {"$limit": per_page},
                    {"$project": {"_id": 0, "ref": 1, "name": 1, "sc": 1, "title": 1, "log": 1}},
                ],
                "count": [{"$count": "total"}],
            }},
        ]
        result = list(self._collection.aggregate(pipeline))
        if result:
            data = result[0].get("data", [])
            count_arr = result[0].get("count", [])
            total = count_arr[0]["total"] if count_arr else 0
        else:
            data, total = [], 0

        return data, total

    def insert_game_log(self, game_log):
        try:
            # 2차 중복 검사: 동일 날짜 + 동일 참가자 조합
            names = game_log.get("name", [])
            title = game_log.get("title", [])
            date = title[1] if len(title) > 1 else None
            if date and names:
                sorted_names = sorted(names)
                existing = self._collection.find_one({
                    "title.1": date,
                    "name": {"$all": sorted_names, "$size": len(sorted_names)},
                })
                if existing:
                    return False

            self._collection.insert_one(game_log)
            return True
        except Exception as e:
            if "duplicate key" in str(e).lower() or "E11000" in str(e):
                return False
            raise

    def find_log_by_ref(self, ref):
        return self._collection.find_one({"ref": ref}, {"_id": 0})

    def fetch_shared_games(self, season_param, alias1, alias2):
        """집계 파이프라인으로 두 플레이어가 동탁인 게임만 조회 (name 인덱스 활용)"""
        season_filter = self._season_filter(season_param)
        pipeline = [
            {"$match": {**season_filter, "name": {"$all": [alias1, alias2]}}},
            {"$project": {"_id": 0, "ref": 1, "name": 1, "sc": 1, "title": 1}},
            {"$sort": {"title.1": -1}},
        ]
        return list(self._collection.aggregate(pipeline))

    def get_current_season(self):
        now = datetime.datetime.now()
        base_year = self._config.SEASON_BASE_YEAR
        if now.month <= 6:
            return (now.year - base_year) * 2 + 1
        else:
            return (now.year - base_year) * 2 + 2
