"""
API 라우트 (v3 — 전체 통합)
신규: elo, awards, meta, yakuman_history, streaks, 페이지네이션
"""
import json
import logging
import re

from flask import Blueprint, jsonify, request, current_app

from config.users import USERS, find_user_index, find_user_by_alias
from services.ranking import calculate_ranking
from services.cache import cache, make_cache_key
from services.precompute import get_precomputed_stats, precompute_for_season
from services.rate_limit import limiter
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
@limiter.limit("2 per minute")
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
    names = game_log.get("name", [])
    results = {}

    try:
        parsed = tenhouLog.game(game_log)
        for rnd in parsed.logs:
            if rnd.isDraw:
                continue
            for sc_arr in rnd.changeScore:
                for seat in range(len(names)):
                    if seat >= len(sc_arr):
                        continue
                    score = sc_arr[seat]
                    if score <= 0:
                        continue

                    matched = find_user_by_alias(USERS, names[seat])
                    display_name = matched["name"] if matched else names[seat]

                    tier = None
                    if score >= 32000:
                        tier = "역만"
                    elif score >= 24000:
                        tier = "삼배만"
                    elif score >= 16000:
                        tier = "배만"

                    if tier:
                        tier_rank = {"배만": 1, "삼배만": 2, "역만": 3}
                        existing = results.get(display_name)
                        if not existing or tier_rank.get(tier, 0) > tier_rank.get(existing, 0):
                            results[display_name] = tier
    except Exception as e:
        logger.warning("Big hand detection failed: %s", e)

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
        title = game_log.get("title", ["", ""])
        date = title[1] if len(title) > 1 else ""
        player_count = len(names)

        final_players = []
        for i in range(min(4, player_count)):
            score = sc[i * 2] if i * 2 < len(sc) else 0
            point = sc[i * 2 + 1] if i * 2 + 1 < len(sc) else 0
            final_players.append({"name": names[i], "score": score, "point": point, "seat": i})

        # tenhouLog 파서로 정확한 국별 데이터 추출
        parsed = tenhouLog.game(game_log)
        rounds = []
        cumulative_scores = [0] * player_count

        for rnd in parsed.logs:
            # 라운드 이름
            wind_idx = rnd.gameWindIndex
            wind_names = ["동", "남", "서", "북"]
            wind = wind_names[wind_idx // 4] if wind_idx // 4 < 4 else "?"
            kyoku = (wind_idx % 4) + 1
            honba = rnd.logObj[0][1] if len(rnd.logObj[0]) > 1 else 0
            round_label = f"{wind}{kyoku}국"
            if honba > 0:
                round_label += f" {honba}본장"

            # 시작 점수
            start_scores = list(rnd.startScore) if rnd.startScore else [0] * player_count

            # 점수 변동 합산 (더블론 등 복수 결과 처리)
            score_changes = [0] * player_count
            for sc_arr in rnd.changeScore:
                for i in range(min(player_count, len(sc_arr))):
                    score_changes[i] += sc_arr[i]

            # 결과 타입 판정
            result_type = "draw"
            winner = -1
            if not rnd.isDraw:
                if rnd.isSomeoneZimo():
                    result_type = "tsumo"
                    for i in range(player_count):
                        if rnd.changeScore[0][i] > 0:
                            winner = i
                            break
                else:
                    result_type = "ron"
                    # 가장 많이 얻은 사람이 winner
                    max_gain = 0
                    for i in range(player_count):
                        total_gain = sum(sc[i] for sc in rnd.changeScore if i < len(sc))
                        if total_gain > max_gain:
                            max_gain = total_gain
                            winner = i

            for i in range(player_count):
                cumulative_scores[i] += score_changes[i]

            # 역 정보 추출
            yakus_info = []
            han_fu_info = []
            if not rnd.isDraw and rnd.yakus:
                # 판수/부수 추출 (raw result block에서)
                try:
                    result_block = rnd.logObj[4 + 3 * player_count]
                    for entry in result_block[2::2]:
                        if isinstance(entry, list) and len(entry) > 3:
                            score_str = str(entry[3])
                            han_val = 0
                            fu_val = 0
                            tier = ""
                            han_m = re.findall(r'(\d+)飜', score_str)
                            if han_m:
                                han_val = int(han_m[0])
                            fu_m = re.findall(r'(\d+)符', score_str)
                            if fu_m:
                                fu_val = int(fu_m[0])
                            if '役満' in score_str:
                                tier = "역만"
                            elif '三倍満' in score_str:
                                tier = "삼배만"
                            elif '倍満' in score_str:
                                tier = "배만"
                            elif '跳満' in score_str:
                                tier = "하네만"
                            elif '満貫' in score_str:
                                tier = "만관"
                            han_fu_info.append({"han": han_val, "fu": fu_val, "tier": tier})
                except Exception:
                    pass

                for yi, yaku_list in enumerate(rnd.yakus):
                    win_seat = -1
                    for si in range(player_count):
                        if yi < len(rnd.changeScore) and si < len(rnd.changeScore[yi]) and rnd.changeScore[yi][si] > 0:
                            win_seat = si
                            break
                    cleaned = []
                    dora_counts = {}
                    for y in yaku_list:
                        if "Dora" in y or "ドラ" in y or "Red" in y or "赤" in y:
                            nums = re.findall(r"\d+", y)
                            val = int(nums[0]) if nums else 1
                            if "Ura" in y or "裏" in y:
                                dora_counts["뒷도라"] = dora_counts.get("뒷도라", 0) + val
                            elif "Red" in y or "赤" in y:
                                dora_counts["적도라"] = dora_counts.get("적도라", 0) + val
                            else:
                                dora_counts["도라"] = dora_counts.get("도라", 0) + val
                            continue
                        cleaned.append(y.split("(")[0])
                    # 0인 도라 제거
                    dora_counts = {k: v for k, v in dora_counts.items() if v > 0}
                    hf = han_fu_info[yi] if yi < len(han_fu_info) else {}
                    if cleaned or dora_counts:
                        yakus_info.append({"seat": win_seat, "yakus": cleaned, "dora": dora_counts, "han": hf.get("han", 0), "fu": hf.get("fu", 0), "tier": hf.get("tier", "")})

            rounds.append({
                "label": round_label,
                "startScores": start_scores,
                "scoreChanges": score_changes,
                "cumulativeChanges": list(cumulative_scores),
                "resultType": result_type,
                "winner": winner,
                "yakus": yakus_info,
            })

        return jsonify({
            "ref": ref, "date": date, "players": final_players,
            "names": names, "rounds": rounds,
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

        p1_user = find_user_by_alias(USERS, p1_name) or next((u for u in USERS if u["name"] == p1_name), None)
        p2_user = find_user_by_alias(USERS, p2_name) or next((u for u in USERS if u["name"] == p2_name), None)
        if not p1_user or not p2_user:
            return jsonify({"error": "플레이어를 찾을 수 없습니다."}), 404

        p1_aliases = set(p1_user.get("aliases", [p1_name]))
        p2_aliases = set(p2_user.get("aliases", [p2_name]))

        # [최적화] 집계 파이프라인으로 동탁 게임만 DB에서 필터링
        season_filter = db._season_filter(season_param)
        pipeline = [
            {"$match": {**season_filter, "$and": [
                {"name": {"$in": list(p1_aliases)}},
                {"name": {"$in": list(p2_aliases)}},
            ]}},
            {"$project": {"_id": 0, "ref": 1, "name": 1, "sc": 1, "title": 1}},
            {"$sort": {"title.1": -1}},
        ]
        data = list(db.collection.aggregate(pipeline))

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
@limiter.limit("30 per minute")
def get_elo():
    db = _get_db()
    try:
        season_param = request.args.get("season", str(db.get_current_season()))
        force = request.args.get("force", "0") == "1"
        from services.elo import get_elo_from_db, calculate_elo_for_season, save_elo_to_db

        if not force:
            cached = get_elo_from_db(db, season_param)
            if cached and cached.get("ratings"):
                return jsonify(cached)

        # 캐시 없거나 force → 재계산
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
        total_richi_rate = 0
        total_fulu_rate = 0
        yakus_merged = {}

        for name, ps in stats.items():
            g = ps.get("games", 0)
            if g == 0:
                continue
            total_players += 1
            total_games += g
            total_win_rate += (ps.get("winGame", {}).get("avg", 0) or 0)
            total_chong_rate += (ps.get("chong", {}).get("avg", 0) or 0)
            total_richi_rate += (ps.get("richi", {}).get("avg", 0) or 0)
            total_fulu_rate += (ps.get("fulu", {}).get("avg", 0) or 0)

            for yaku_entry in (ps.get("yakus") or []):
                if isinstance(yaku_entry, list) and len(yaku_entry) == 2:
                    count, yname = yaku_entry
                    yakus_merged[yname] = yakus_merged.get(yname, 0) + count

        avg_win = round(total_win_rate / total_players * 100, 1) if total_players else 0
        avg_chong = round(total_chong_rate / total_players * 100, 1) if total_players else 0
        avg_richi = round(total_richi_rate / total_players * 100, 1) if total_players else 0
        avg_fulu = round(total_fulu_rate / total_players * 100, 1) if total_players else 0

        top_yakus = sorted(yakus_merged.items(), key=lambda x: -x[1])[:20]

        return jsonify({
            "season": season_param,
            "total_games": total_games // 4 if total_players else 0,
            "total_players": total_players,
            "avg_win_rate": avg_win,
            "avg_chong_rate": avg_chong,
            "avg_richi_rate": avg_richi,
            "avg_fulu_rate": avg_fulu,
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
# [신규] 플레이 스타일 프로파일
# ==================================================================

@api_bp.route("/api/profile/<player_name>", methods=["GET"])
def get_profile(player_name):
    db = _get_db()
    try:
        season_param = request.args.get("season", str(db.get_current_season()))
        import statistics as stat_mod

        precomputed = get_precomputed_stats(db, season_param)
        stats = precomputed.get("stats", {}) if precomputed else {}

        player_stats = stats.get(player_name)
        if not player_stats or player_stats.get("games", 0) == 0:
            return jsonify({"error": "No data"}), 404

        # 리그 평균 + 표준편차 계산
        axes_keys = {
            "attack": ("winGame", "avg"),
            "defense": ("chong", "avg"),
            "richi": ("richi", "avg"),
            "fulu": ("fulu", "avg"),
            "score": ("winGame_score", "avg"),
        }
        league_vals = {k: [] for k in axes_keys}
        for name, ps in stats.items():
            if ps.get("games", 0) < 5:
                continue
            for ak, (k1, k2) in axes_keys.items():
                v = (ps.get(k1) or {}).get(k2)
                if v is not None and isinstance(v, (int, float)):
                    league_vals[ak].append(v)

        profile = {}
        for ak, (k1, k2) in axes_keys.items():
            vals = league_vals[ak]
            avg = sum(vals) / len(vals) if vals else 0
            std = stat_mod.stdev(vals) if len(vals) >= 2 else 1
            raw = (player_stats.get(k1) or {}).get(k2, 0) or 0
            z = (raw - avg) / std if std > 0 else 0
            if ak == "defense":
                z = -z  # 방총률은 낮을수록 좋음
            score = max(0, min(100, 50 + z * 20))
            profile[ak] = {"raw": round(raw, 4), "avg": round(avg, 4), "std": round(std, 4), "z": round(z, 2), "score": round(score, 1)}

        # 스타일 분류 — 가장 두드러진 축 기반 상대 분류
        a, d, r, f, sc = profile["attack"]["score"], profile["defense"]["score"], profile["richi"]["score"], profile["fulu"]["score"], profile["score"]["score"]

        # 50(리그 평균)에서 가장 많이 벗어난 축 찾기
        deviations = {
            "공격형": a - 50,
            "수비형": d - 50,
            "멘젠형": r - 50,
            "후로형": f - 50,
            "타점형": sc - 50,
        }

        # 복합 판정: 공격+타점 높으면 공격형, 수비+멘젠 높으면 수비형
        composite = {
            "공격형": (a + sc) / 2 - 50,
            "수비형": (d + (100 - a)) / 2 - 50,
            "멘젠형": (r + (100 - f)) / 2 - 50,
            "후로형": (f + (100 - r)) / 2 - 50,
        }

        best_style = max(composite, key=composite.get)
        best_deviation = composite[best_style]

        # 편차가 너무 작으면 밸런스형 (리그 평균에서 3점 이내)
        if best_deviation < 3:
            style = "밸런스형"
        else:
            style = best_style

        return jsonify({"player": player_name, "profile": profile, "style": style})
    except Exception as e:
        logger.error("Error computing profile for %s", player_name, exc_info=e)
        return jsonify({"error": "Failed to compute profile"}), 500


# ==================================================================
# [신규] 예측/시뮬레이션
# ==================================================================

@api_bp.route("/api/simulate", methods=["GET"])
@limiter.limit("20 per minute")
def simulate():
    db = _get_db()
    try:
        players_param = request.args.get("players", "")
        season_param = request.args.get("season", str(db.get_current_season()))
        n_sim = min(int(request.args.get("n", "10000")), 50000)

        player_names = [p.strip() for p in players_param.split(",") if p.strip()]
        if len(player_names) != 4:
            return jsonify({"error": "4명의 플레이어를 지정해주세요."}), 400

        from services.elo import get_elo_from_db
        elo_data = get_elo_from_db(db, season_param)
        if not elo_data or not elo_data.get("ratings"):
            return jsonify({"error": "ELO 데이터가 없습니다."}), 404

        ratings = [elo_data["ratings"].get(p, 1500) for p in player_names]

        import random
        results = [[0, 0, 0, 0] for _ in range(4)]
        for _ in range(n_sim):
            perf = [(random.gauss(r, 200), i) for i, r in enumerate(ratings)]
            perf.sort(reverse=True)
            for rank, (_, pi) in enumerate(perf):
                results[pi][rank] += 1

        pcts = [[round(r / n_sim * 100, 1) for r in res] for res in results]

        return jsonify({
            "players": [{"name": player_names[i], "rating": round(ratings[i], 1),
                         "first": pcts[i][0], "second": pcts[i][1], "third": pcts[i][2], "fourth": pcts[i][3]}
                        for i in range(4)],
            "simulations": n_sim,
        })
    except Exception as e:
        logger.error("Error in simulation", exc_info=e)
        return jsonify({"error": "Failed to simulate"}), 500


# ==================================================================
# [신규] 시즌 리포트
# ==================================================================

@api_bp.route("/api/report", methods=["GET"])
@limiter.limit("10 per minute")
def get_season_report():
    db = _get_db()
    try:
        season_param = request.args.get("season", str(db.get_current_season()))

        from services.awards import calculate_awards
        from services.elo import get_elo_from_db

        # 기존 데이터 수집
        ranking_data = None
        try:
            data = db.fetch_game_logs(season_param, lightweight=True)
            from services.ranking import calculate_ranking
            ranking_data = calculate_ranking(data)
        except Exception:
            pass

        awards = calculate_awards(db, season_param)
        elo_data = get_elo_from_db(db, season_param)

        precomputed = get_precomputed_stats(db, season_param)
        stats = precomputed.get("stats", {}) if precomputed else {}

        # 요약
        total_games = 0
        total_players = 0
        if ranking_data:
            filtered = [p for p in ranking_data["ranking"] if p["games"] > 0]
            total_games = sum(p["games"] for p in filtered) // 4
            total_players = len(filtered)

        # 역만/삼배만 하이라이트
        highlights = []
        try:
            full_data = db.fetch_game_logs(season_param, lightweight=False)
            for gl in (full_data or []):
                bh = _detect_big_hands(gl)
                for player, tier in bh.items():
                    if tier in ("삼배만", "역만"):
                        title = gl.get("title", ["", ""])
                        highlights.append({"player": player, "tier": tier, "date": title[1] if len(title) > 1 else "", "ref": gl.get("ref", "")})
        except Exception:
            pass

        # 최종 랭킹
        final_ranking = []
        if ranking_data:
            final_ranking = sorted([p for p in ranking_data["ranking"] if p["games"] > 0], key=lambda x: (-x["games"], -x["point_avg"]))[:10]

        # ELO 최종
        elo_final = {}
        if elo_data and elo_data.get("ratings"):
            elo_final = dict(sorted(elo_data["ratings"].items(), key=lambda x: -x[1]))

        return jsonify({
            "season": season_param,
            "summary": {"total_games": total_games, "total_players": total_players},
            "awards": awards,
            "ranking": final_ranking,
            "elo": elo_final,
            "highlights": sorted(highlights, key=lambda x: x["date"], reverse=True),
        })
    except Exception as e:
        logger.error("Error generating report", exc_info=e)
        return jsonify({"error": "Failed to generate report"}), 500


# ==================================================================
# [신규] 대국 코멘트
# ==================================================================

@api_bp.route("/api/comments/<path:ref>", methods=["GET"])
def get_comments(ref):
    db = _get_db()
    try:
        col = db._db["comments"]
        raw = list(col.find({"game_ref": ref}).sort("created_at", -1))
        comments = []
        for c in raw:
            c["id"] = str(c.pop("_id"))
            comments.append(c)
        return jsonify({"comments": comments})
    except Exception as e:
        logger.error("Error fetching comments", exc_info=e)
        return jsonify({"error": "Failed to fetch comments"}), 500


@api_bp.route("/api/comments/<path:ref>", methods=["POST"])
@limiter.limit("20 per minute")
def add_comment(ref):
    db = _get_db()
    try:
        import datetime
        data = request.get_json()
        if not data or not data.get("text", "").strip():
            return jsonify({"error": "내용을 입력해주세요."}), 400

        comment = {
            "game_ref": ref,
            "round_index": data.get("round_index"),
            "user_name": data.get("user_name", "익명"),
            "text": data["text"].strip()[:500],
            "is_highlight": data.get("is_highlight", False),
            "created_at": datetime.datetime.utcnow().isoformat(),
        }
        db._db["comments"].insert_one(comment)
        comment.pop("_id", None)
        return jsonify({"message": "코멘트가 등록되었습니다.", "comment": comment})
    except Exception as e:
        logger.error("Error adding comment", exc_info=e)
        return jsonify({"error": "Failed to add comment"}), 500


@api_bp.route("/api/comments/<path:ref>/<comment_id>", methods=["DELETE"])
def delete_comment(ref, comment_id):
    db = _get_db()
    try:
        from bson import ObjectId
        col = db._db["comments"]
        result = col.delete_one({"_id": ObjectId(comment_id), "game_ref": ref})
        if result.deleted_count == 0:
            return jsonify({"error": "코멘트를 찾을 수 없습니다."}), 404
        return jsonify({"message": "삭제되었습니다."})
    except Exception as e:
        logger.error("Error deleting comment", exc_info=e)
        return jsonify({"error": "Failed to delete comment"}), 500


@api_bp.route("/api/highlights", methods=["GET"])
def get_highlight_comments():
    db = _get_db()
    try:
        season_param = request.args.get("season", str(db.get_current_season()))
        col = db._db["comments"]
        highlights = list(col.find({"is_highlight": True}, {"_id": 0}).sort("created_at", -1).limit(20))
        return jsonify({"highlights": highlights})
    except Exception as e:
        return jsonify({"error": "Failed to fetch highlights"}), 500


# ==================================================================
# [신규] 설정 관리 API
# ==================================================================

@api_bp.route("/api/settings", methods=["GET"])
def get_settings():
    db = _get_db()
    from services.settings import get_all_settings
    return jsonify(get_all_settings(db))


@api_bp.route("/api/settings", methods=["POST"])
@limiter.limit("5 per minute")
def update_settings():
    db = _get_db()
    pw = current_app.config["APP_CONFIG"].UPLOAD_PASSWORD
    if pw:
        submitted = request.headers.get("X-Admin-Password", "")
        if submitted != pw:
            return jsonify({"error": "Unauthorized"}), 403
    try:
        data = request.get_json()
        from services.settings import set_setting
        for key, value in data.items():
            set_setting(db, key, value)

        # ELO 파라미터 변경 시 전체 재계산 트리거
        if "elo_params" in data:
            from services.elo import calculate_elo_for_season, save_elo_to_db
            db._db["elo_ratings"].delete_many({})
            import threading
            def _recompute():
                for s in [str(db.get_current_season()), "all"]:
                    elo = calculate_elo_for_season(db, s)
                    if elo:
                        save_elo_to_db(db, s, elo)
            threading.Thread(target=_recompute, daemon=True).start()

        return jsonify({"message": "설정이 저장되었습니다."})
    except Exception as e:
        logger.error("Error updating settings", exc_info=e)
        return jsonify({"error": "Failed to update settings"}), 500


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
