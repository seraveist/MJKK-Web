"""
API 라우트 (사전 계산 적용)
- stats_api, totalstats_api: precomputed_stats 우선 → fallback to live
- ranking: 기존 경량 쿼리 유지 (충분히 빠름)
"""
import json
import logging

from flask import Blueprint, jsonify, request, current_app

from config.users import USERS, find_user_index
from services.ranking import calculate_ranking
from services.cache import cache, make_cache_key
from services.precompute import get_precomputed_stats, precompute_for_season
from src import tenhouLog, tenhouStatistics

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)


def _get_db():
    return current_app.config["DB_SERVICE"]


# ------------------------------------------------------------------
# 플레이어 목록
# ------------------------------------------------------------------

@api_bp.route("/players", methods=["GET"])
def get_players():
    try:
        return jsonify({"players": [u["name"] for u in USERS]})
    except Exception as e:
        logger.error("Error fetching players", exc_info=e)
        return jsonify({"error": "Failed to fetch players"}), 500


@api_bp.route("/stats/all", methods=["GET"])
def get_all_players():
    try:
        return jsonify({"allPlayers": [u["name"] for u in USERS]})
    except Exception as e:
        logger.error("Error fetching all players", exc_info=e)
        return jsonify({"error": "Failed to fetch all players"}), 500


# ------------------------------------------------------------------
# 랭킹 (기존 유지 — 경량 쿼리로 충분)
# ------------------------------------------------------------------

@api_bp.route("/ranking", methods=["GET"])
def get_ranking():
    db = _get_db()
    try:
        season_param = request.args.get("season", "all")
        data = db.fetch_game_logs(season_param, lightweight=True)

        result = calculate_ranking(data)
        if result:
            return jsonify(result)
        else:
            return jsonify({"error": "No game data found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error generating ranking", exc_info=e)
        return jsonify({"error": "Failed to generate ranking"}), 500


# ------------------------------------------------------------------
# 개인 통계 (precomputed 우선)
# ------------------------------------------------------------------

def _compute_player_stats_live(data, player_name, count=10):
    """라이브 계산 (fallback용)"""
    total_games = [tenhouLog.game(log) for log in data]

    user_index = find_user_index(USERS, player_name)
    if user_index == -1:
        user_index = next(
            (i for i, u in enumerate(USERS) if u["name"] == player_name), 0
        )

    ps = tenhouStatistics.PlayerStatistic(
        games=total_games, playerName=USERS[user_index]
    )
    stats_data = json.loads(ps.json())

    if hasattr(ps, "rank") and hasattr(ps.rank, "datas"):
        stats_data["rankData"] = ps.rank.datas[-count:]
    else:
        stats_data["rankData"] = []

    return stats_data


@api_bp.route("/stats_api/<player_name>", methods=["GET"])
def get_player_stats_api(player_name: str):
    db = _get_db()
    try:
        season_param = request.args.get("season", str(db.get_current_season()))
        count = int(request.args.get("count", "10"))

        # 1) 사전 계산된 통계에서 조회
        precomputed = get_precomputed_stats(db, season_param)
        if precomputed and player_name in (precomputed.get("stats") or {}):
            stats_data = precomputed["stats"][player_name]
            # rankData를 count에 맞게 잘라줌
            if "rankData" in stats_data:
                stats_data = {**stats_data, "rankData": stats_data["rankData"][-count:]}
            logger.debug("Serving precomputed stats for %s (season=%s)", player_name, season_param)
            return jsonify({
                "stats": stats_data,
                "allPlayers": [u["name"] for u in USERS],
            })

        # 2) Fallback: 라이브 계산 (캐시 적용)
        logger.info("Precomputed miss, live computing for %s (season=%s)", player_name, season_param)
        cache_key = make_cache_key("player_stats", player_name, season_param, count)
        cached = cache.get(cache_key)
        if cached is not None:
            return jsonify(cached)

        data = db.fetch_game_logs_for_stats(season_param)
        if not data:
            return jsonify({"error": "No game data found"}), 404

        stats_data = _compute_player_stats_live(data, player_name, count)
        result = {
            "stats": stats_data,
            "allPlayers": [u["name"] for u in USERS],
        }

        cache.set(cache_key, result)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error fetching stats for %s", player_name, exc_info=e)
        return jsonify({"error": "Failed to fetch player stats"}), 500


# ------------------------------------------------------------------
# 전체 유저 통계 배치 API (precomputed 우선)
# ------------------------------------------------------------------

@api_bp.route("/totalstats_api", methods=["GET"])
def get_total_stats_api():
    db = _get_db()
    try:
        season_param = request.args.get("season", str(db.get_current_season()))

        # 1) 사전 계산된 통계에서 조회
        precomputed = get_precomputed_stats(db, season_param)
        if precomputed and precomputed.get("stats"):
            logger.debug("Serving precomputed total stats (season=%s)", season_param)
            return jsonify({
                "allPlayers": precomputed.get("players", []),
                "stats": precomputed["stats"],
            })

        # 2) Fallback: 라이브 계산
        logger.info("Precomputed miss, live computing total stats (season=%s)", season_param)
        cache_key = make_cache_key("total_stats", season_param)
        cached = cache.get(cache_key)
        if cached is not None:
            return jsonify(cached)

        data = db.fetch_game_logs_for_stats(season_param)
        if not data:
            return jsonify({"error": "No game data found"}), 404

        all_stats = {}
        players_with_data = []

        for user in USERS:
            name = user["name"]
            try:
                stats = _compute_player_stats_live(data, name)
                if stats.get("games", 0) > 0:
                    all_stats[name] = stats
                    players_with_data.append(name)
            except Exception as e:
                logger.warning("Stats computation failed for %s: %s", name, e)

        result = {"allPlayers": players_with_data, "stats": all_stats}

        # 라이브 계산 결과를 precomputed에도 저장 (다음 요청부터 즉시)
        precompute_for_season(db, season_param)

        cache.set(cache_key, result)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error fetching total stats", exc_info=e)
        return jsonify({"error": "Failed to fetch total stats"}), 500


# ------------------------------------------------------------------
# 수동 사전 계산 트리거 (관리용)
# ------------------------------------------------------------------

@api_bp.route("/admin/precompute", methods=["POST"])
def trigger_precompute():
    """모든 시즌 통계를 수동으로 재계산"""
    from services.precompute import precompute_all_seasons
    db = _get_db()

    pw = current_app.config["APP_CONFIG"].UPLOAD_PASSWORD
    if pw:
        submitted = request.headers.get("X-Admin-Password", "")
        if submitted != pw:
            return jsonify({"error": "Unauthorized"}), 403

    import threading
    thread = threading.Thread(
        target=precompute_all_seasons,
        args=(db,),
        daemon=True,
    )
    thread.start()
    return jsonify({"message": "Precompute started in background."})


# ------------------------------------------------------------------
# 캐시/사전계산 상태
# ------------------------------------------------------------------

@api_bp.route("/cache/stats", methods=["GET"])
def cache_stats():
    db = _get_db()
    precomputed_seasons = []
    try:
        col = db._db["precomputed_stats"]
        docs = col.find({}, {"_id": 0, "season": 1, "updated_at": 1, "players": 1})
        for d in docs:
            precomputed_seasons.append({
                "season": d["season"],
                "players": len(d.get("players", [])),
                "updated_at": str(d.get("updated_at", "")),
            })
    except Exception:
        pass

    return jsonify({
        "cache": cache.stats,
        "precomputed": precomputed_seasons,
    })


# ------------------------------------------------------------------
# 대국 기록 열람 API (game log viewer)
# ------------------------------------------------------------------

@api_bp.route("/api/gamelogs", methods=["GET"])
def get_game_logs():
    """
    시즌별 대국 기록 목록 + tenhou viewer URL 반환.
    순위별 정렬된 플레이어 정보 포함.
    """
    db = _get_db()
    try:
        season_param = request.args.get("season", "all")
        data = db.fetch_game_logs(season_param, lightweight=False)

        if not data:
            return jsonify({"error": "No game data found"}), 404

        logs = []
        for game_log in sorted(data, key=lambda x: x.get("title", ["", ""])[1], reverse=True):
            # 날짜
            title = game_log.get("title", ["", ""])
            date = title[1] if len(title) > 1 else ""

            # 플레이어를 순위(우마)별로 정렬
            names = game_log.get("name", [])
            sc = game_log.get("sc", [])
            players = []
            for i in range(min(4, len(names))):
                score = sc[i * 2] if i * 2 < len(sc) else 0
                point = sc[i * 2 + 1] if i * 2 + 1 < len(sc) else 0
                players.append({
                    "name": names[i],
                    "score": score,
                    "point": point,
                })
            players.sort(key=lambda p: -p["score"])

            # tenhou + majsoul(일본) + majsoul(글로벌) URL 생성
            viewer_url = _build_tenhou_url(game_log)
            majsoul_url = _build_majsoul_url(game_log)
            majsoul_global_url = _build_majsoul_global_url(game_log)

            logs.append({
                "ref": game_log.get("ref", ""),
                "date": date,
                "players": players,
                "viewer_url": viewer_url,
                "majsoul_url": majsoul_url,
                "majsoul_global_url": majsoul_global_url,
            })

        return jsonify({"logs": logs})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error fetching game logs", exc_info=e)
        return jsonify({"error": "Failed to fetch game logs"}), 500


def _build_tenhou_url(game_log):
    """MongoDB 게임 로그 → tenhou.net/5 viewer URL"""
    import urllib.parse

    rule = game_log.get("rule", {})
    aka = 1 if (rule.get("aka51", 0) or rule.get("aka52", 0) or rule.get("aka53", 0)) else 0

    tenhou_data = {
        "title": game_log.get("title", ["", ""]),
        "name": game_log.get("name", ["", "", "", ""]),
        "rule": {"aka": aka},
        "log": game_log.get("log", []),
    }

    json_str = json.dumps(tenhou_data, ensure_ascii=False, separators=(",", ":"))
    encoded = urllib.parse.quote(json_str)
    return f"https://tenhou.net/5/#json={encoded}"


def _build_majsoul_url(game_log):
    """MongoDB 게임 로그 → 작혼 일본 패보 URL"""
    ref = game_log.get("ref", "")
    if not ref:
        return None
    return f"https://game.mahjongsoul.com/?paipu={ref}"


def _build_majsoul_global_url(game_log):
    """MongoDB 게임 로그 → 작혼 글로벌 패보 URL"""
    ref = game_log.get("ref", "")
    if not ref:
        return None
    return f"https://mahjongsoul.yo-star.com/?paipu={ref}"


# ------------------------------------------------------------------
# 단일 게임 패보 뷰어 URL (대시보드 날짜 클릭용)
# ------------------------------------------------------------------

@api_bp.route("/api/viewer/<path:ref>", methods=["GET"])
def get_viewer_urls(ref):
    """ref로 게임 로그를 찾아 tenhou/majsoul URL 반환"""
    db = _get_db()
    try:
        game_log = db.find_log_by_ref(ref)
        if not game_log:
            return jsonify({"error": "Game not found"}), 404

        return jsonify({
            "tenhou": _build_tenhou_url(game_log),
            "majsoul": _build_majsoul_url(game_log),
            "majsoul_global": _build_majsoul_global_url(game_log),
        })
    except Exception as e:
        logger.error("Error building viewer URL for %s", ref, exc_info=e)
        return jsonify({"error": "Failed to build viewer URL"}), 500
