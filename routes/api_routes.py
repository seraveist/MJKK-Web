"""
API 라우트 (v3 — 전체 통합)
신규: elo, awards, meta, yakuman_history, streaks, 페이지네이션
"""
import json
import logging

from flask import Blueprint, jsonify, request, current_app

from config.users import USERS, find_user_index, find_user_by_alias
from services.ranking import calculate_ranking
from services.cache import cache, make_cache_key
from services.precompute import get_precomputed_stats, precompute_for_season
from src import tenhouLog, tenhouStatistics

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)


def _get_db():
    return current_app.config["DB_SERVICE"]


# ==================================================================
# 플레이어 목록
# ==================================================================

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


# ==================================================================
# 랭킹
# ==================================================================

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


# ==================================================================
# 개인 통계 (precomputed 우선)
# ==================================================================

def _compute_player_stats_live(data, player_name, count=10):
    total_games = [tenhouLog.game(log) for log in data]
    user_index = find_user_index(USERS, player_name)
    if user_index == -1:
        user_index = next((i for i, u in enumerate(USERS) if u["name"] == player_name), 0)
    ps = tenhouStatistics.PlayerStatistic(games=total_games, playerName=USERS[user_index])
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

        precomputed = get_precomputed_stats(db, season_param)
        if precomputed and player_name in (precomputed.get("stats") or {}):
            stats_data = precomputed["stats"][player_name]
            if "rankData" in stats_data:
                stats_data = {**stats_data, "rankData": stats_data["rankData"][-count:]}
            return jsonify({"stats": stats_data, "allPlayers": [u["name"] for u in USERS]})

        cache_key = make_cache_key("player_stats", player_name, season_param, count)
        cached = cache.get(cache_key)
        if cached is not None:
            return jsonify(cached)

        data = db.fetch_game_logs_for_stats(season_param)
        if not data:
            return jsonify({"error": "No game data found"}), 404

        stats_data = _compute_player_stats_live(data, player_name, count)
        result = {"stats": stats_data, "allPlayers": [u["name"] for u in USERS]}
        cache.set(cache_key, result)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error fetching stats for %s", player_name, exc_info=e)
        return jsonify({"error": "Failed to fetch player stats"}), 500


# ==================================================================
# 전체 유저 통계 배치 (precomputed 우선)
# ==================================================================

@api_bp.route("/totalstats_api", methods=["GET"])
def get_total_stats_api():
    db = _get_db()
    try:
        season_param = request.args.get("season", str(db.get_current_season()))

        precomputed = get_precomputed_stats(db, season_param)
        if precomputed and precomputed.get("stats"):
            return jsonify({"allPlayers": precomputed.get("players", []), "stats": precomputed["stats"]})

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
        precompute_for_season(db, season_param)
        cache.set(cache_key, result)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error fetching total stats", exc_info=e)
        return jsonify({"error": "Failed to fetch total stats"}), 500


# ==================================================================
# 수동 사전 계산 트리거
# ==================================================================

@api_bp.route("/admin/precompute", methods=["POST"])
def trigger_precompute():
    from services.precompute import precompute_all_seasons
    db = _get_db()
    pw = current_app.config["APP_CONFIG"].UPLOAD_PASSWORD
    if pw:
        submitted = request.headers.get("X-Admin-Password", "")
        if submitted != pw:
            return jsonify({"error": "Unauthorized"}), 403
    import threading
    threading.Thread(target=precompute_all_seasons, args=(db,), daemon=True).start()
    return jsonify({"message": "Precompute started in background."})


# ==================================================================
# 캐시/사전계산 상태
# ==================================================================

@api_bp.route("/cache/stats", methods=["GET"])
def cache_stats():
    db = _get_db()
    precomputed_seasons = []
    try:
        col = db._db["precomputed_stats"]
        for d in col.find({}, {"_id": 0, "season": 1, "updated_at": 1, "players": 1}):
            precomputed_seasons.append({
                "season": d["season"],
                "players": len(d.get("players", [])),
                "updated_at": str(d.get("updated_at", "")),
            })
    except Exception:
        pass
    return jsonify({"cache": cache.stats, "precomputed": precomputed_seasons})


# ==================================================================
# 대국 기록 (페이지네이션 추가)
# ==================================================================

@api_bp.route("/api/gamelogs", methods=["GET"])
def get_game_logs():
    db = _get_db()
    try:
        season_param = request.args.get("season", "all")
        page = int(request.args.get("page", "1"))
        per_page = int(request.args.get("per_page", "30"))

        data = db.fetch_game_logs(season_param, lightweight=False)
        if not data:
            return jsonify({"error": "No game data found"}), 404

        sorted_data = sorted(data, key=lambda x: x.get("title", ["", ""])[1], reverse=True)
        total = len(sorted_data)
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        page_data = sorted_data[start:start + per_page]

        logs = []
        for game_log in page_data:
            title = game_log.get("title", ["", ""])
            date = title[1] if len(title) > 1 else ""
            names = game_log.get("name", [])
            sc = game_log.get("sc", [])

            players = []
            for i in range(min(4, len(names))):
                score = sc[i * 2] if i * 2 < len(sc) else 0
                point = sc[i * 2 + 1] if i * 2 + 1 < len(sc) else 0
                players.append({"name": names[i], "score": score, "point": point})
            players.sort(key=lambda p: -p["score"])

            # 배만/삼배만/역만 감지
            big_hands = _detect_big_hands(game_log)

            logs.append({
                "ref": game_log.get("ref", ""),
                "date": date,
                "players": players,
                "viewer_url": _build_tenhou_url(game_log),
                "majsoul_url": _build_majsoul_url(game_log),
                "majsoul_global_url": _build_majsoul_global_url(game_log),
                "big_hands": big_hands,
            })

        return jsonify({
            "logs": logs,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error fetching game logs", exc_info=e)
        return jsonify({"error": "Failed to fetch game logs"}), 500


def _detect_big_hands(game_log):
    """대국에서 배만/삼배만/역만 감지. { playerName: "역만"|"삼배만"|"배만" }"""
    log_data = game_log.get("log", [])
    names = game_log.get("name", [])
    results = {}

    for round_data in (log_data or []):
        if not round_data or len(round_data) < 16:
            continue
        result_block = round_data[16] if len(round_data) > 16 else None
        if not result_block:
            continue

        if isinstance(result_block, list):
            for entry in result_block[2::2] if len(result_block) > 2 else []:
                if not isinstance(entry, list) or len(entry) < 3:
                    continue
                seat = entry[0] if isinstance(entry[0], int) else -1
                score = entry[2] if len(entry) > 2 and isinstance(entry[2], (int, float)) else 0

                if seat < 0 or seat >= len(names):
                    continue

                name = names[seat]
                matched = find_user_by_alias(USERS, name)
                display_name = matched["name"] if matched else name

                tier = None
                abs_score = abs(score)
                if abs_score >= 32000:
                    tier = "역만"
                elif abs_score >= 24000:
                    tier = "삼배만"
                elif abs_score >= 16000:
                    tier = "배만"

                if tier:
                    existing = results.get(display_name)
                    tier_rank = {"배만": 1, "삼배만": 2, "역만": 3}
                    if not existing or tier_rank.get(tier, 0) > tier_rank.get(existing, 0):
                        results[display_name] = tier

    return results


# ==================================================================
# 대국 상세
# ==================================================================

@api_bp.route("/api/gamedetail/<path:ref>", methods=["GET"])
def get_game_detail(ref):
    db = _get_db()
    try:
        game_log = db.find_log_by_ref(ref)
        if not game_log:
            return jsonify({"error": "Game not found"}), 404

        names = game_log.get("name", [])
        sc = game_log.get("sc", [])
        log_data = game_log.get("log", [])
        title = game_log.get("title", ["", ""])
        date = title[1] if len(title) > 1 else ""

        final_players = []
        for i in range(min(4, len(names))):
            score = sc[i * 2] if i * 2 < len(sc) else 0
            point = sc[i * 2 + 1] if i * 2 + 1 < len(sc) else 0
            final_players.append({"name": names[i], "score": score, "point": point, "seat": i})

        rounds = []
        cumulative_scores = [0, 0, 0, 0]
        for round_data in (log_data or []):
            if not round_data or len(round_data) < 16:
                continue
            round_info = round_data[0] if round_data[0] else []
            round_num = round_info[0] if len(round_info) > 0 else 0
            honba = round_info[1] if len(round_info) > 1 else 0
            wind_names = ["동", "남", "서", "북"]
            wind = wind_names[round_num // 4] if round_num // 4 < 4 else "?"
            kyoku = (round_num % 4) + 1
            round_label = f"{wind}{kyoku}국"
            if honba > 0:
                round_label += f" {honba}본장"

            start_scores = [round_info[4 + i] if 4 + i < len(round_info) else 0 for i in range(4)]

            result_type = "unknown"
            score_changes = [0, 0, 0, 0]
            winner = -1
            hule_result = round_data[16] if len(round_data) > 16 else None
            if hule_result and isinstance(hule_result, list) and len(hule_result) >= 2:
                result_arr = hule_result[0] if isinstance(hule_result[0], list) else hule_result
                if isinstance(result_arr, list):
                    for i in range(min(4, len(result_arr))):
                        if isinstance(result_arr[i], (int, float)):
                            score_changes[i] = result_arr[i]

                if any(s > 0 for s in score_changes):
                    winner_idx = score_changes.index(max(score_changes))
                    negative_count = sum(1 for s in score_changes if s < 0)
                    result_type = "tsumo" if negative_count == 3 else "ron" if negative_count == 1 else "win"
                    winner = winner_idx
                else:
                    result_type = "draw"

            for i in range(4):
                cumulative_scores[i] += score_changes[i]

            rounds.append({
                "label": round_label, "startScores": start_scores,
                "scoreChanges": score_changes, "cumulativeChanges": list(cumulative_scores),
                "resultType": result_type, "winner": winner,
            })

        return jsonify({
            "ref": ref, "date": date, "players": final_players, "names": names, "rounds": rounds,
            "viewer_url": _build_tenhou_url(game_log),
            "majsoul_url": _build_majsoul_url(game_log),
            "majsoul_global_url": _build_majsoul_global_url(game_log),
        })
    except Exception as e:
        logger.error("Error fetching game detail for %s", ref, exc_info=e)
        return jsonify({"error": "Failed to fetch game detail"}), 500


# ==================================================================
# 상성 분석
# ==================================================================

@api_bp.route("/api/matchup", methods=["GET"])
def get_matchup():
    db = _get_db()
    try:
        p1_name = request.args.get("p1", "")
        p2_name = request.args.get("p2", "")
        season_param = request.args.get("season", "all")

        if not p1_name or not p2_name:
            return jsonify({"error": "p1, p2 파라미터 필요"}), 400
        if p1_name == p2_name:
            return jsonify({"error": "같은 플레이어입니다."}), 400

        data = db.fetch_game_logs(season_param, lightweight=True)
        if not data:
            return jsonify({"error": "No game data found"}), 404

        p1_user = find_user_by_alias(USERS, p1_name) or next((u for u in USERS if u["name"] == p1_name), None)
        p2_user = find_user_by_alias(USERS, p2_name) or next((u for u in USERS if u["name"] == p2_name), None)
        if not p1_user or not p2_user:
            return jsonify({"error": "플레이어를 찾을 수 없습니다."}), 404

        p1_aliases = set(p1_user.get("aliases", [p1_name]))
        p2_aliases = set(p2_user.get("aliases", [p2_name]))

        shared_games = []
        for gl in data:
            game_names = gl.get("name", [])
            sc = gl.get("sc", [])
            p1_idx = next((i for i, n in enumerate(game_names) if n in p1_aliases), -1)
            p2_idx = next((i for i, n in enumerate(game_names) if n in p2_aliases), -1)
            if p1_idx < 0 or p2_idx < 0:
                continue

            all_scores = [(j, sc[j*2] if j*2 < len(sc) else 0) for j in range(min(4, len(game_names)))]
            all_scores.sort(key=lambda x: -x[1])
            rank_map = {idx: r+1 for r, (idx, _) in enumerate(all_scores)}

            shared_games.append({
                "ref": gl.get("ref", ""),
                "date": gl.get("title", ["", ""])[1] if len(gl.get("title", [])) > 1 else "",
                "p1_rank": rank_map.get(p1_idx, 0),
                "p1_score": sc[p1_idx*2] if p1_idx*2 < len(sc) else 0,
                "p1_point": sc[p1_idx*2+1] if p1_idx*2+1 < len(sc) else 0,
                "p2_rank": rank_map.get(p2_idx, 0),
                "p2_score": sc[p2_idx*2] if p2_idx*2 < len(sc) else 0,
                "p2_point": sc[p2_idx*2+1] if p2_idx*2+1 < len(sc) else 0,
            })

        if not shared_games:
            return jsonify({"p1": p1_name, "p2": p2_name, "totalGames": 0, "message": "같은 탁에서 대국한 기록이 없습니다."})

        total = len(shared_games)
        p1_ranks = [g["p1_rank"] for g in shared_games]
        p2_ranks = [g["p2_rank"] for g in shared_games]
        p1_points = [g["p1_point"] for g in shared_games]
        p2_points = [g["p2_point"] for g in shared_games]
        p1_wins = sum(1 for g in shared_games if g["p1_rank"] < g["p2_rank"])
        p2_wins = sum(1 for g in shared_games if g["p2_rank"] < g["p1_rank"])

        return jsonify({
            "p1": p1_name, "p2": p2_name, "totalGames": total,
            "stats": {
                "p1_avg_rank": round(sum(p1_ranks)/total, 2), "p2_avg_rank": round(sum(p2_ranks)/total, 2),
                "p1_avg_point": round(sum(p1_points)/total, 2), "p2_avg_point": round(sum(p2_points)/total, 2),
                "p1_total_point": round(sum(p1_points), 1), "p2_total_point": round(sum(p2_points), 1),
                "p1_wins": p1_wins, "p2_wins": p2_wins, "draws": total - p1_wins - p2_wins,
                "p1_win_rate": round(p1_wins/total*100, 1), "p2_win_rate": round(p2_wins/total*100, 1),
                "p1_first_count": sum(1 for r in p1_ranks if r==1), "p2_first_count": sum(1 for r in p2_ranks if r==1),
                "p1_first_rate": round(sum(1 for r in p1_ranks if r==1)/total*100, 1),
                "p2_first_rate": round(sum(1 for r in p2_ranks if r==1)/total*100, 1),
                "p1_last_count": sum(1 for r in p1_ranks if r==4), "p2_last_count": sum(1 for r in p2_ranks if r==4),
                "p1_last_rate": round(sum(1 for r in p1_ranks if r==4)/total*100, 1),
                "p2_last_rate": round(sum(1 for r in p2_ranks if r==4)/total*100, 1),
            },
            "games": sorted(shared_games, key=lambda x: x["date"], reverse=True),
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error computing matchup", exc_info=e)
        return jsonify({"error": "Failed to compute matchup"}), 500


# ==================================================================
# [신규] ELO 레이팅
# ==================================================================

@api_bp.route("/api/elo", methods=["GET"])
def get_elo():
    db = _get_db()
    try:
        season_param = request.args.get("season", str(db.get_current_season()))
        from services.elo import get_elo_from_db, calculate_elo_for_season, save_elo_to_db

        cached = get_elo_from_db(db, season_param)
        if cached:
            return jsonify(cached)

        elo_data = calculate_elo_for_season(db, season_param)
        if not elo_data:
            return jsonify({"error": "No game data found"}), 404

        save_elo_to_db(db, season_param, elo_data)
        return jsonify(elo_data)
    except Exception as e:
        logger.error("Error computing ELO", exc_info=e)
        return jsonify({"error": "Failed to compute ELO"}), 500


# ==================================================================
# [신규] 시즌 어워드
# ==================================================================

@api_bp.route("/api/awards", methods=["GET"])
def get_awards():
    db = _get_db()
    try:
        season_param = request.args.get("season", str(db.get_current_season()))
        from services.awards import calculate_awards
        awards = calculate_awards(db, season_param)
        return jsonify({"awards": awards, "season": season_param})
    except Exception as e:
        logger.error("Error computing awards", exc_info=e)
        return jsonify({"error": "Failed to compute awards"}), 500


# ==================================================================
# [신규] 메타 분석 (리그 전체 통계)
# ==================================================================

@api_bp.route("/api/meta", methods=["GET"])
def get_meta():
    db = _get_db()
    try:
        season_param = request.args.get("season", str(db.get_current_season()))

        precomputed = get_precomputed_stats(db, season_param)
        stats = precomputed.get("stats", {}) if precomputed else {}

        total_games = 0
        total_players = 0
        total_win_rate = 0
        total_chong_rate = 0
        yakus_merged = {}

        for name, ps in stats.items():
            g = ps.get("games", 0)
            if g == 0:
                continue
            total_players += 1
            total_games += g
            total_win_rate += (ps.get("winGame", {}).get("avg", 0) or 0)
            total_chong_rate += (ps.get("chong", {}).get("avg", 0) or 0)

            for yaku_entry in (ps.get("yakus") or []):
                if isinstance(yaku_entry, list) and len(yaku_entry) == 2:
                    count, yname = yaku_entry
                    yakus_merged[yname] = yakus_merged.get(yname, 0) + count

        avg_win = round(total_win_rate / total_players * 100, 1) if total_players else 0
        avg_chong = round(total_chong_rate / total_players * 100, 1) if total_players else 0

        top_yakus = sorted(yakus_merged.items(), key=lambda x: -x[1])[:10]

        return jsonify({
            "season": season_param,
            "total_games": total_games // 4 if total_players else 0,
            "total_players": total_players,
            "avg_win_rate": avg_win,
            "avg_chong_rate": avg_chong,
            "top_yakus": [{"name": y, "count": c} for y, c in top_yakus],
        })
    except Exception as e:
        logger.error("Error computing meta", exc_info=e)
        return jsonify({"error": "Failed to compute meta"}), 500


# ==================================================================
# [신규] 역만/삼배만 히스토리
# ==================================================================

@api_bp.route("/api/yakuman_history", methods=["GET"])
def get_yakuman_history():
    db = _get_db()
    try:
        season_param = request.args.get("season", str(db.get_current_season()))
        data = db.fetch_game_logs(season_param, lightweight=False)
        if not data:
            return jsonify({"history": []})

        history = []
        for game_log in data:
            title = game_log.get("title", ["", ""])
            date = title[1] if len(title) > 1 else ""
            big = _detect_big_hands(game_log)
            for player, tier in big.items():
                if tier in ("삼배만", "역만"):
                    history.append({"date": date, "player": player, "tier": tier, "ref": game_log.get("ref", "")})

        history.sort(key=lambda x: x["date"], reverse=True)
        return jsonify({"history": history})
    except Exception as e:
        logger.error("Error fetching yakuman history", exc_info=e)
        return jsonify({"error": "Failed to fetch yakuman history"}), 500


# ==================================================================
# [신규] 연승/연패 기록
# ==================================================================

@api_bp.route("/api/streaks/<player_name>", methods=["GET"])
def get_streaks(player_name):
    db = _get_db()
    try:
        season_param = request.args.get("season", str(db.get_current_season()))
        data = db.fetch_game_logs(season_param, lightweight=True)
        if not data:
            return jsonify({"error": "No data"}), 404

        user = next((u for u in USERS if u["name"] == player_name), None)
        if not user:
            return jsonify({"error": "Player not found"}), 404

        aliases = set(user.get("aliases", [player_name]))
        sorted_data = sorted(data, key=lambda x: x.get("title", ["", ""])[1] if len(x.get("title", [])) > 1 else "")

        ranks = []
        for gl in sorted_data:
            game_names = gl.get("name", [])
            sc = gl.get("sc", [])
            idx = next((i for i, n in enumerate(game_names) if n in aliases), -1)
            if idx < 0:
                continue
            all_scores = [(j, sc[j*2] if j*2 < len(sc) else 0) for j in range(min(4, len(game_names)))]
            all_scores.sort(key=lambda x: -x[1])
            rank = next((r+1 for r, (j, _) in enumerate(all_scores) if j == idx), 0)
            ranks.append(rank)

        # 연승(1위 연속), 연패(4위 연속), 연대(1~2위 연속)
        def max_streak(arr, condition):
            best, cur = 0, 0
            for v in arr:
                if condition(v):
                    cur += 1
                    best = max(best, cur)
                else:
                    cur = 0
            return best

        def current_streak(arr, condition):
            cur = 0
            for v in reversed(arr):
                if condition(v):
                    cur += 1
                else:
                    break
            return cur

        return jsonify({
            "player": player_name,
            "total_games": len(ranks),
            "max_first_streak": max_streak(ranks, lambda r: r == 1),
            "max_top2_streak": max_streak(ranks, lambda r: r <= 2),
            "max_last_streak": max_streak(ranks, lambda r: r == 4),
            "current_first_streak": current_streak(ranks, lambda r: r == 1),
            "current_top2_streak": current_streak(ranks, lambda r: r <= 2),
            "current_last_streak": current_streak(ranks, lambda r: r == 4),
        })
    except Exception as e:
        logger.error("Error computing streaks for %s", player_name, exc_info=e)
        return jsonify({"error": "Failed to compute streaks"}), 500


# ==================================================================
# 패보 뷰어 URL
# ==================================================================

@api_bp.route("/api/viewer/<path:ref>", methods=["GET"])
def get_viewer_urls(ref):
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


# ==================================================================
# [강화] 헬스체크
# ==================================================================

@api_bp.route("/health", methods=["GET"])
def health_check():
    db = _get_db()
    status = {"status": "ok", "checks": {}}
    try:
        db._client.admin.command("ping")
        status["checks"]["mongodb"] = "connected"
    except Exception:
        status["checks"]["mongodb"] = "disconnected"
        status["status"] = "degraded"

    status["checks"]["cache"] = cache.stats
    return jsonify(status), 200 if status["status"] == "ok" else 503


# ==================================================================
# 헬퍼
# ==================================================================

def _build_tenhou_url(game_log):
    import urllib.parse
    rule = game_log.get("rule", {})
    aka = 1 if (rule.get("aka51", 0) or rule.get("aka52", 0) or rule.get("aka53", 0)) else 0
    tenhou_data = {"title": game_log.get("title", ["", ""]), "name": game_log.get("name", [""]*4),
                   "rule": {"aka": aka}, "log": game_log.get("log", [])}
    return f"https://tenhou.net/5/#json={urllib.parse.quote(json.dumps(tenhou_data, ensure_ascii=False, separators=(',', ':')))}"


def _build_majsoul_url(game_log):
    ref = game_log.get("ref", "")
    return f"https://game.mahjongsoul.com/?paipu={ref}" if ref else None


def _build_majsoul_global_url(game_log):
    ref = game_log.get("ref", "")
    return f"https://mahjongsoul.yo-star.com/?paipu={ref}" if ref else None
