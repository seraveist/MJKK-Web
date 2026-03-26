"""
애플리케이션 설정 모듈
"""
import os
import logging

logger = logging.getLogger(__name__)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())
    DEBUG = False

    # MongoDB
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_CLUSTER = os.getenv("DB_CLUSTER", "cluster0.6nqoq8u.mongodb.net")
    DB_NAME = os.getenv("DB_NAME", "totalLogDB")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "gameLog")

    @property
    def DB_URL(self):
        if not self.DB_USER or not self.DB_PASSWORD:
            raise ValueError("DB_USER and DB_PASSWORD 환경변수 필요")
        return (
            f"mongodb+srv://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_CLUSTER}/?retryWrites=true&w=majority&appName=Cluster0"
        )

    # 작혼 API
    MS_USERNAME = os.getenv("MS_USERNAME")
    MS_PASSWORD = os.getenv("MS_PASSWORD")
    MS_HOST = os.getenv("MS_HOST", "https://game.maj-soul.com")

    # 시즌
    SEASON_BASE_YEAR = int(os.getenv("SEASON_BASE_YEAR", "2023"))

    # 패보 업로드 비밀번호 (데이터 오염 방지)
    UPLOAD_PASSWORD = os.getenv("UPLOAD_PASSWORD", "")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


def get_config():
    env = os.getenv("FLASK_ENV", "production").lower()
    if env == "development":
        return DevelopmentConfig()
    return ProductionConfig()
