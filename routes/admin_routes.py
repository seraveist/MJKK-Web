"""
관리자 라우트
- 유저 관리 CRUD
- [신규] DB 백업 (JSON export)
"""
import json
import logging
import datetime
from functools import wraps
from flask import Blueprint, jsonify, request, render_template, current_app, Response
import config.users as users_module
from services.rate_limit import limiter

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _get_db():
    return current_app.config["DB_SERVICE"]


def _get_password():
    return current_app.config["APP_CONFIG"].UPLOAD_PASSWORD


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        pw = _get_password()
        if pw:
            submitted = request.headers.get("X-Admin-Password", "")
            if submitted != pw:
                return jsonify({"error": "비밀번호가 틀렸습니다."}), 403
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/users", methods=["GET"])
def user_management_page():
    return render_template("userManagement.html")


@admin_bp.route("/api/users", methods=["GET"])
@require_admin
def get_users():
    try:
        users = _load_users_from_db()
        return jsonify({"users": users})
    except Exception as e:
        logger.error("Error loading users", exc_info=e)
        return jsonify({"error": "유저 목록 조회 실패"}), 500


@admin_bp.route("/api/users", methods=["POST"])
@require_admin
def manage_user():
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


# ==================================================================
# [신규] DB 백업
# ==================================================================

@admin_bp.route("/api/backup", methods=["POST"])
@require_admin
@limiter.limit("3 per minute")
def backup_database():
    """게임 로그 + 유저 설정을 JSON으로 export"""
    db = _get_db()
    try:
        game_logs = list(db.collection.find({}, {"_id": 0}))
        users = list(db._db["usersConfig"].find({}, {"_id": 0}))

        backup_data = {
            "exported_at": datetime.datetime.utcnow().isoformat(),
            "game_logs_count": len(game_logs),
            "users_count": len(users),
            "game_logs": game_logs,
            "users": users,
        }

        json_str = json.dumps(backup_data, ensure_ascii=False, default=str, indent=2)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        return Response(
            json_str,
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment; filename=mjkk_backup_{timestamp}.json"},
        )
    except Exception as e:
        logger.error("Backup failed", exc_info=e)
        return jsonify({"error": "백업 실패"}), 500


@admin_bp.route("/api/backup/info", methods=["GET"])
@require_admin
def backup_info():
    """백업 가능한 데이터 정보"""
    db = _get_db()
    try:
        game_count = db.collection.count_documents({})
        user_count = db._db["usersConfig"].count_documents({})
        return jsonify({"game_logs": game_count, "users": user_count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================================================================
# 유저 CRUD 헬퍼
# ==================================================================

def _load_users_from_db():
    db = _get_db()
    users_col = db._db["usersConfig"]
    users = list(users_col.find({}, {"_id": 0, "name": 1, "aliases": 1}))
    if not users:
        for u in users_module._DEFAULT_USERS:
            users_col.insert_one({"name": u["name"], "aliases": u["aliases"]})
        users = list(users_col.find({}, {"_id": 0, "name": 1, "aliases": 1}))
    return users


def _refresh_users_cache():
    db = _get_db()
    users_col = db._db["usersConfig"]
    users = list(users_col.find({}, {"_id": 0, "name": 1, "aliases": 1}))
    if users:
        # in-place 변경: 다른 모듈이 from config.users import USERS로 
        # 가져간 참조도 함께 업데이트됨
        users_module.USERS.clear()
        users_module.USERS.extend(users)
    # 유저 변경 시 모든 통계/ELO 캐시 무효화
    try:
        from services.cache import cache
        cache.clear()
        db._db["precomputed_stats"].delete_many({})
        db._db["elo_ratings"].delete_many({})
        logger.info("All caches invalidated due to user change")
    except Exception as e:
        logger.warning("Cache invalidation on user change failed: %s", e)


def _add_user(data):
    name = data.get("name", "").strip()
    aliases = data.get("aliases", [])
    if not name:
        return jsonify({"error": "이름을 입력해주세요."}), 400
    if not aliases:
        aliases = [name]
    db = _get_db()
    users_col = db._db["usersConfig"]
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
    result = users_col.update_one({"name": original_name}, {"$set": {"name": new_name, "aliases": aliases}})
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
