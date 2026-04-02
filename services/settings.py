"""
설정 외부화 서비스
- MongoDB settings 컬렉션에 저장
- 기본값 fallback
"""
import logging

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS = {
    "elo_params": {"K": 6, "NORM": 8000, "initial": 1500, "sensitivity": 400},
    "awards_config": {"min_games_ratio": 0.3, "min_games_floor": 3},
    "cache_ttl": {"stats": 3600, "elo": 86400},
}


def get_setting(db_service, key, default=None):
    """설정 값 조회. DB에 없으면 기본값 반환."""
    try:
        col = db_service._db["settings"]
        doc = col.find_one({"key": key}, {"_id": 0})
        if doc and "value" in doc:
            return doc["value"]
    except Exception as e:
        logger.warning("Failed to get setting '%s': %s", key, e)
    return default if default is not None else DEFAULT_SETTINGS.get(key)


def set_setting(db_service, key, value):
    """설정 값 저장."""
    try:
        col = db_service._db["settings"]
        col.update_one(
            {"key": key},
            {"$set": {"key": key, "value": value}},
            upsert=True,
        )
        return True
    except Exception as e:
        logger.error("Failed to set setting '%s': %s", key, e)
        return False


def get_all_settings(db_service):
    """전체 설정 조회."""
    result = dict(DEFAULT_SETTINGS)
    try:
        col = db_service._db["settings"]
        for doc in col.find({}, {"_id": 0}):
            if "key" in doc and "value" in doc:
                result[doc["key"]] = doc["value"]
    except Exception as e:
        logger.warning("Failed to get all settings: %s", e)
    return result


def init_default_settings(db_service):
    """기본 설정 초기화 (없는 키만)."""
    try:
        col = db_service._db["settings"]
        for key, value in DEFAULT_SETTINGS.items():
            if not col.find_one({"key": key}):
                col.insert_one({"key": key, "value": value})
                logger.info("Initialized default setting: %s", key)
    except Exception as e:
        logger.warning("Failed to init default settings: %s", e)
