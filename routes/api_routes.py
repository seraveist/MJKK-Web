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
    
    # [수정] 직렬화 과정 제거
    stats_data = ps.dict() 
    stats_data["rankData"] = ps.rank_history[-count:] if hasattr(ps, "rank_history") else []
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

        # [핵심 수정] 유저별 루프를 삭제하고 precompute의 single-pass 함수를 호출합니다.
        from services.precompute import _compute_all_player_stats
        all_stats = _compute_all_player_stats(data)
        players_with_data = list(all_stats.keys())

        result = {"allPlayers": players_with_data, "stats": all_stats}
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
        date_from = request.args.get("date_from", "")
        date_to = request.args.get("date_to", "")
        player_filter = request.args.get("player", "")

        data = db.fetch_game_logs(season_param, lightweight=False)
        if not data:
            return jsonify({"error": "No game data found"}), 404

        sorted_data = sorted(data, key=lambda x: x.get("title", ["", ""])[1], reverse=True)

        # 날짜 필터
        if date_from:
            sorted_data = [d for d in sorted_data if (d.get("title", ["", ""])[1] if len(d.get("title", [])) > 1 else "") >= date_from]
        if date_to:
            # date picker는 YYYY-MM-DD를 보내므로 시간 보정
            date_to_cmp = date_to + " 23:59:59" if len(date_to) == 10 else date_to
            sorted_data = [d for d in sorted_data if (d.get("title", ["", ""])[1] if len(d.get("title", [])) > 1 else "") <= date_to_cmp]

        # 유저 필터
        if player_filter:
            user = find_user_by_alias(USERS, player_filter) or next((u for u in USERS if u["name"] == player_filter), None)
            if user:
                aliases = set(user.get("aliases", [player_filter]))
                sorted_data = [d for d in sorted_data if any(n in aliases for n in d.get("name", []))]

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
                matched = find_user_by_alias(USERS, names[i])
                display_name = matched["name"] if matched else names[i]
                players.append({"name": display_name, "score": score, "point": point})
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

        # 시즌 날짜 범위 계산
        season_dates = _get_season_dates(db, season_param)

        return jsonify({
            "logs": logs,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
            "season_dates": season_dates,
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Error fetching game logs", exc_info=e)
        return jsonify({"error": "Failed to fetch game logs"}), 500


# routes/api_routes.py 수정안

def _detect_big_hands(game_log):
    """
    무거운 파서를 사용하지 않고 원본 JSON 로그의 결과 문자열만 검사하여 
    배만/삼배만/역만을 감지합니다. (리치봉/본장 점수 오차 없음)
    """
    names = game_log.get("name", [])
    results = {}
    logs = game_log.get("log", [])
    player_count = len(names)

    # 역만 이름 한글 매핑 (기존 유지)
    YAKU_KR = {"国士無双":"국사무쌍", "四暗刻":"스안커", "대삼원":"대삼원", ...} # 생략

    for rnd in logs:
        if not rnd or len(rnd) < 4: continue
        
        # 결과 블록(보통 16번 인덱스 부근, player_count에 따라 다름) 찾기
        # tenhouLog.py 로직에 따라 결과 블록 위치 산출
        res_idx = 4 + 3 * player_count
        if len(rnd) <= res_idx: continue
        
        result_block = rnd[res_idx]
        if not result_block or result_block[0] != "和了":
            continue

        # result_block 예: ["和了", [점수변동], [승리정보1], [승리정보2]...]
        # 승리정보 예: [0, 1, 0, "40符3飜5200点", "立直(1飜)", ...]
        for i in range(2, len(result_block), 2):
            win_info = result_block[i]
            if not isinstance(win_info, list) or len(win_info) < 4: continue
            
            winner_seat = win_info[0]
            score_str = str(win_info[3]) # "배만", "삼배만", "역만" 등이 포함된 문자열
            
            tier = None
            if "役満" in score_str: tier = "역만"
            elif "三倍満" in score_str: tier = "삼배만"
            elif "倍満" in score_str: tier = "배만"
            # ※ 하네만(跳満)은 무시하거나 필요시 추가
            
            if tier:
                matched = find_user_by_alias(USERS, names[winner_seat])
                display_name = matched["name"] if matched else names[winner_seat]
                
                # 역만급인 경우에만 구체적인 역 이름 추출 (win_info[4:] 에 들어있음)
                yaku_names = []
                if tier == "역만":
                    for y in win_info[4:]:
                        clean = str(y).split("(")[0]
                        if any(k in clean for k in ["Dora", "ドラ", "Red", "赤"]): continue
                        yaku_names.append(YAKU_KR.get(clean, clean))
                
                results[display_name] = {"tier": tier, "yakus": yaku_names}
                
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
                            # 더블역만 이상을 먼저 체크 (役満 포함 문자열이므로 순서 중요)
                            ym_multi = re.findall(r'(\d+)倍役満', score_str)
                            if ym_multi:
                                n = int(ym_multi[0])
                                if n == 2: tier = "더블역만"
                                elif n == 3: tier = "트리플역만"
                                else: tier = f"{n}배역만"
                            elif 'ダブル役満' in score_str:
                                tier = "더블역만"
                            elif 'トリプル役満' in score_str:
                                tier = "트리플역만"
                            elif '役満' in score_str:
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
            for player, info in big.items():
                tier = info["tier"]
                if tier != "배만":
                    entry = {"date": date, "player": player, "tier": tier, "ref": game_log.get("ref", "")}
                    if info.get("yakus"):
                        entry["yakus"] = info["yakus"]
                    history.append(entry)

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

        # ── 6축 정의 ──
        axes_keys = {
            "attack": ("winGame", "avg"),
            "defense": ("chong", "avg"),
            "speed": ("winGame_round", "avg"),
            "score": ("winGame_score", "avg"),
            "richi": ("richi", "avg"),
            "fulu": ("fulu", "avg"),
        }

        # 리그 평균 + 표준편차 계산 (최소 5국 이상)
        league_vals = {k: [] for k in axes_keys}
        # 보너스용 리그 데이터
        bonus_keys = {
            "dama": lambda ps: (ps.get("winGame_dama") or {}).get("per", 0),
            "ippatsu": lambda ps: (ps.get("richi_yifa") or {}).get("per", 0),
            "tsumo": lambda ps: (ps.get("winGame_zimo") or {}).get("per", 0),
            "oya": lambda ps: (ps.get("winGame_host") or {}).get("per", 0),
            "dora_avg": lambda ps: (ps.get("dora") or {}).get("avg", 0),
            "rentai": lambda ps: _calc_rentai(ps),
            "fourth": lambda ps: _calc_fourth(ps),
            "ron": lambda ps: (ps.get("winGame_rong") or {}).get("per", 0),
            "tobi_maker": lambda ps: (ps.get("minusOther") or {}).get("avg", 0),
            "kuksuji": lambda ps: ps.get("kuksuji", 0),
            "tamen": lambda ps: (ps.get("richi_machi") or {}).get("per", 0),
        }
        league_bonus = {k: [] for k in bonus_keys}

        for name, ps in stats.items():
            if ps.get("games", 0) < 5:
                continue
            for ak, (k1, k2) in axes_keys.items():
                v = (ps.get(k1) or {}).get(k2)
                if v is not None and isinstance(v, (int, float)):
                    league_vals[ak].append(v)
            for bk, fn in bonus_keys.items():
                try:
                    v = fn(ps)
                    if v is not None and isinstance(v, (int, float)):
                        league_bonus[bk].append(v)
                except Exception:
                    pass

        # ── 6축 Z-score + 레이더 점수 ──
        profile = {}
        for ak, (k1, k2) in axes_keys.items():
            vals = league_vals[ak]
            avg = sum(vals) / len(vals) if vals else 0
            std = stat_mod.stdev(vals) if len(vals) >= 2 else 1
            raw = (player_stats.get(k1) or {}).get(k2, 0) or 0
            z = (raw - avg) / std if std > 0 else 0
            # 방총률/화료순목: 낮을수록 좋음 → 반전
            if ak in ("defense", "speed"):
                z = -z
            chart_score = max(0, min(100, 50 + z * 20))
            profile[ak] = {"raw": round(raw, 4), "z": round(z, 2), "score": round(chart_score, 1)}

        # ── 6축 태그 판정 ──
        TAG_DEFS = {
            "attack": [
                (-999, -1.2, "소극", "red", "화료율 매우 낮음"),
                (-1.2, -0.5, "신중", "green", "화료율 낮음"),
                (0.5, 1.2, "공격", "blue", "화료율 높음"),
                (1.2, 999, "돌격", "gold", "화료율 매우 높음"),
            ],
            "defense": [
                (-999, -1.2, "노가드", "red", "방총률 매우 높음"),
                (-1.2, -0.5, "과감", "green", "방총률 높음"),
                (0.5, 1.2, "방어", "blue", "방총률 낮음"),
                (1.2, 999, "철벽", "gold", "방총률 매우 낮음"),
            ],
            "speed": [
                (-999, -1.2, "집념", "green", "화료순 매우 늦음"),
                (-1.2, -0.5, "끈기", "green", "화료순 늦음"),
                (0.5, 1.2, "속공", "blue", "화료순 빠름"),
                (1.2, 999, "전광석화", "gold", "화료순 매우 빠름"),
            ],
            "score": [
                (-999, -1.2, "잽", "red", "타점 매우 낮음"),
                (-1.2, -0.5, "훅", "green", "타점 낮음"),
                (0.5, 1.2, "스트레이트", "blue", "타점 높음"),
                (1.2, 999, "K.O", "gold", "타점 매우 높음"),
            ],
            "richi": [
                (0.5, 1.2, "리치", "green", "리치율 높음"),
                (1.2, 999, "리치광", "blue", "리치율 매우 높음"),
            ],
            "fulu": [
                (0.5, 1.2, "후로", "green", "후로율 높음"),
                (1.2, 999, "후로광", "blue", "후로율 매우 높음"),
            ],
        }

        tags = []
        for ak, defs in TAG_DEFS.items():
            z = profile[ak]["z"]
            for lo, hi, name, color, tooltip in defs:
                if lo <= z < hi or (hi == 999 and z >= lo):
                    tags.append({"name": name, "color": color, "tooltip": tooltip, "axis": ak})
                    break

        # ── 보너스 태그 판정 ──
        BONUS_DEFS = [
            ("dama", 0.8, True, "다마", "green", "다마 화료율 상위"),
            ("ippatsu", 0.8, True, "일발", "blue", "일발율 상위"),
            ("tsumo", 0.8, True, "쯔모", "blue", "쯔모율 상위"),
            ("oya", 0.8, True, "오야", "blue", "오야 화료율 상위"),
            ("dora_avg", 0.8, True, "도라 수집가", "blue", "평균 도라 수 상위"),
            ("rentai", 0.8, True, "연대", "gold", "1위율+2위율 상위"),
            ("fourth", -0.8, False, "4위회피", "gold", "4위율 하위"),
            ("ron", 0.8, True, "론 사냥꾼", "green", "론 화료율 상위"),
            ("tobi_maker", 0.8, True, "토비 메이커", "green", "상대 토비율 상위"),
            ("kuksuji", 0.8, True, "국수지", "gold", "국수지 상위"),
            ("tamen", 0.8, True, "다면 설계사", "blue", "리치 다면율 상위"),
            ("tamen", -0.8, False, "우형 매니아", "green", "리치 다면율 하위"),
        ]

        for bk, threshold, is_upper, name, color, tooltip in BONUS_DEFS:
            vals = league_bonus.get(bk, [])
            if len(vals) < 2:
                continue
            avg = sum(vals) / len(vals)
            std = stat_mod.stdev(vals)
            if std == 0:
                continue
            try:
                fn = bonus_keys[bk]
                raw = fn(player_stats)
            except Exception:
                continue
            if raw is None:
                continue
            z = (raw - avg) / std
            if is_upper and z > threshold:
                tags.append({"name": name, "color": color, "tooltip": tooltip, "axis": "bonus"})
            elif not is_upper and z < threshold:
                tags.append({"name": name, "color": color, "tooltip": tooltip, "axis": "bonus"})

        return jsonify({"player": player_name, "profile": profile, "tags": tags})
    except Exception as e:
        logger.error("Error computing profile for %s", player_name, exc_info=e)
        return jsonify({"error": "Failed to compute profile"}), 500


def _calc_rentai(ps):
    """1위+2위 비율"""
    total = ps.get("games", 0)
    if total == 0:
        return 0
    return (ps.get("total_first_count", 0) + ps.get("total_second_count", 0)) / total


def _calc_fourth(ps):
    """4위 비율"""
    total = ps.get("games", 0)
    if total == 0:
        return 0
    return ps.get("total_fourth_count", 0) / total


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
                for player, info in bh.items():
                    tier = info["tier"]
                    if tier != "배만":
                        title = gl.get("title", ["", ""])
                        entry = {"player": player, "tier": tier, "date": title[1] if len(title) > 1 else "", "ref": gl.get("ref", "")}
                        if info.get("yakus"):
                            entry["yakus"] = info["yakus"]
                        highlights.append(entry)
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

def _get_season_dates(db, season_param):
    """시즌 시작/종료일 계산"""
    if season_param == "all":
        return {"start": "", "end": ""}
    try:
        season = int(season_param)
        base_year = db._config.SEASON_BASE_YEAR
        # 시즌 번호 → 연도/반기 역산
        # season 1 = base_year 상반기, season 2 = base_year 하반기
        half = (season - 1) % 2  # 0=상반기, 1=하반기
        year = base_year + (season - 1) // 2
        if half == 0:
            return {"start": f"{year}-01-01", "end": f"{year}-06-30"}
        else:
            return {"start": f"{year}-07-01", "end": f"{year}-12-31"}
    except Exception:
        return {"start": "", "end": ""}


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
