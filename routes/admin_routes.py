"""
관리자 라우트
- 유저 관리 CRUD (MongoDB에 저장)
- 비밀번호 인증 (UPLOAD_PASSWORD 재사용)
"""
import logging
from functools import wraps

from flask import Blueprint, jsonify, request, render_template, current_app

import config.users as users_module

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _get_db():
    return current_app.config["DB_SERVICE"]


def _get_password():
    return current_app.config["APP_CONFIG"].UPLOAD_PASSWORD


def require_admin(f):
    """관리자 비밀번호 검증 데코레이터"""
    @wraps(f)
    def decorated(*args, **kwargs):
        pw = _get_password()
        if pw:  # 비밀번호가 설정된 경우만 검증
            submitted = request.headers.get("X-Admin-Password", "")
            if submitted != pw:
                return jsonify({"error": "비밀번호가 틀렸습니다."}), 403
        return f(*args, **kwargs)
    return decorated


# ── 페이지 렌더링 ──

@admin_bp.route("/users", methods=["GET"])
def user_management_page():
    return render_template("userManagement.html")


# ── 유저 CRUD API ──

@admin_bp.route("/api/users", methods=["GET"])
@require_admin
def get_users():
    """유저 목록 조회"""
    try:
        users = _load_users_from_db()
        return jsonify({"users": users})
    except Exception as e:
        logger.error("Error loading users", exc_info=e)
        return jsonify({"error": "유저 목록 조회 실패"}), 500


@admin_bp.route("/api/users", methods=["POST"])
@require_admin
def manage_user():
    """유저 추가/수정/삭제"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "요청 데이터가 없습니다."}), 400

    action = data.get("action")

    try:
        if action == "add":
            return _add_user(data)
        elif action == "update":
            return _update_user(data)
        elif action == "delete":
            return _delete_user(data)
        else:
            return jsonify({"error": f"알 수 없는 action: {action}"}), 400
    except Exception as e:
        logger.error("User management error", exc_info=e)
        return jsonify({"error": "처리 중 오류가 발생했습니다."}), 500


def _add_user(data):
    name = data.get("name", "").strip()
    aliases = data.get("aliases", [])

    if not name:
        return jsonify({"error": "이름을 입력해주세요."}), 400

    if not aliases:
        aliases = [name]

    db = _get_db()
    users_col = db._db["usersConfig"]

    # 중복 체크
    if users_col.find_one({"name": name}):
        return jsonify({"error": f"'{name}' 유저가 이미 존재합니다."}), 400

    users_col.insert_one({"name": name, "aliases": aliases})
    _refresh_users_cache()

    return jsonify({"message": f"'{name}' 유저가 추가되었습니다."})


def _update_user(data):
    original_name = data.get("originalName", "").strip()
    new_name = data.get("name", "").strip()
    aliases = data.get("aliases", [])

    if not original_name or not new_name:
        return jsonify({"error": "이름을 입력해주세요."}), 400

    if not aliases:
        aliases = [new_name]

    db = _get_db()
    users_col = db._db["usersConfig"]

    result = users_col.update_one(
        {"name": original_name},
        {"$set": {"name": new_name, "aliases": aliases}},
    )

    if result.matched_count == 0:
        return jsonify({"error": f"'{original_name}' 유저를 찾을 수 없습니다."}), 404

    _refresh_users_cache()
    return jsonify({"message": f"'{new_name}' 유저가 수정되었습니다."})


def _delete_user(data):
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "이름을 입력해주세요."}), 400

    db = _get_db()
    users_col = db._db["usersConfig"]

    result = users_col.delete_one({"name": name})
    if result.deleted_count == 0:
        return jsonify({"error": f"'{name}' 유저를 찾을 수 없습니다."}), 404

    _refresh_users_cache()
    return jsonify({"message": f"'{name}' 유저가 삭제되었습니다."})


def _load_users_from_db():
    """MongoDB에서 유저 목록 로드. 없으면 기본값으로 초기화."""
    db = _get_db()
    users_col = db._db["usersConfig"]

    users = list(users_col.find({}, {"_id": 0, "name": 1, "aliases": 1}))

    if not users:
        # DB에 유저가 없으면 기본값으로 초기화
        default_users = users_module._DEFAULT_USERS
        for u in default_users:
            users_col.update_one(
                {"name": u["name"]},
                {"$setOnInsert": u},
                upsert=True,
            )
        users = list(users_col.find({}, {"_id": 0, "name": 1, "aliases": 1}))
        logger.info("Initialized usersConfig collection with %d default users", len(users))

    return users


def _refresh_users_cache():
    """DB에서 유저 목록을 다시 로드하여 인메모리 캐시 갱신"""
    users = _load_users_from_db()
    users_module.USERS = users
    logger.info("Users cache refreshed: %d users", len(users))
