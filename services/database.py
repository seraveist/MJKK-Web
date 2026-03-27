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

            # [신규] title.1 + name 복합 인덱스 — 시즌+플레이어 필터링
            #self._collection.create_index([("title.1", ASCENDING), ("name", ASCENDING)], background=True)

            logger.info("Connected to MongoDB. DB=%s, indexes created.", self._config.DB_NAME)
        except Exception as e:
            logger.error("Failed to connect to MongoDB", exc_info=e)
            raise

    @property
    def collection(self):
        if self._collection is None:
            raise RuntimeError("Database not connected.")
        return self._collection

    def _season_filter(self, season_param):
        if season_param == "all":
            return {}
        try:
            season = int(season_param)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid season: {season_param}")

        base_year = self._config.SEASON_BASE_YEAR
        if season % 2 == 1:
            year = base_year + season // 2
            start = f"{year}-01-01"
            end = f"{year}-06-30"
        else:
            year = base_year + (season - 1) // 2
            start = f"{year}-07-01"
            end = f"{year}-12-31"

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
        cache_key = make_cache_key("stats_logs", season_param)
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        query = self._season_filter(season_param)
        data = list(self._collection.find(query, STATS_PROJECTION))

        cache.set(cache_key, data, ttl=600)
        return data

    def insert_game_log(self, game_log):
        try:
            self._collection.insert_one(game_log)
            return True
        except Exception as e:
            if "duplicate key" in str(e).lower() or "E11000" in str(e):
                return False
            raise

    def find_log_by_ref(self, ref):
        return self._collection.find_one({"ref": ref}, {"_id": 0})

    def get_current_season(self):
        now = datetime.datetime.now()
        base_year = self._config.SEASON_BASE_YEAR
        if now.month <= 6:
            return (now.year - base_year) * 2 + 1
        else:
            return (now.year - base_year) * 2 + 2
