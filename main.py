"""
마자까까 내전 집계 — 메인 애플리케이션
"""
import logging
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[DEV] .env 파일 로드 완료")
except ImportError:
    pass

from flask import Flask

from config import get_config
import config.users as users_module
from services.database import DatabaseService
from routes import register_blueprints

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(config=None):
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    if config is None:
        config = get_config()
    app.config["APP_CONFIG"] = config

    # DB 서비스 초기화
    db_service = DatabaseService(config)
    db_service.connect()
    app.config["DB_SERVICE"] = db_service

    # MongoDB에서 유저 목록 로드 (있으면)
    _init_users_from_db(db_service)

    # Blueprint 등록
    register_blueprints(app)

    # 에러 핸들러
    _register_error_handlers(app)

    logger.info("Application initialized. Users: %d", len(users_module.USERS))
    return app


def _init_users_from_db(db_service):
    """MongoDB usersConfig 컬렉션에서 유저 로드 (비어있으면 기본값 유지)"""
    try:
        users_col = db_service._db["usersConfig"]
        db_users = list(users_col.find({}, {"_id": 0, "name": 1, "aliases": 1}))
        if db_users:
            users_module.USERS = db_users
            logger.info("Loaded %d users from MongoDB", len(db_users))
        else:
            logger.info("No users in MongoDB, using %d defaults", len(users_module.USERS))
    except Exception as e:
        logger.warning("Failed to load users from MongoDB: %s", e)


def _register_error_handlers(app):
    from flask import jsonify

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error("Internal server error", exc_info=e)
        return jsonify({"error": "Internal server error"}), 500


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
