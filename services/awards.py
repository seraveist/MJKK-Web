"""
시즌 어워드 계산 서비스
- 11개 항목 (최고 레이팅 + 최다 연승 추가)
- 최소 대국수 = int(최다대국자 대국수 * 0.3)
- 방총수지 = 방총률 × 평균 방총점
"""
import logging

from config.users import USERS, find_user_by_alias
from services.ranking import calculate_ranking
from services.precompute import get_precomputed_stats

logger = logging.getLogger(__name__)


def calculate_awards(db_service, season_param):
    ranking_data = None
    data = None
    try:
        data = db_service.fetch_game_logs(season_param, lightweight=True)
        ranking_data = calculate_ranking(data)
    except Exception as e:
        logger.warning("Awards: ranking calc failed: %s", e)

    precomputed = get_precomputed_stats(db_service, season_param)
    stats = precomputed.get("stats", {}) if precomputed else {}

    max_games = 0
    if ranking_data:
        for p in ranking_data["ranking"]:
            if p["games"] > max_games:
                max_games = p["games"]
    dynamic_min = max(3, int(max_games * 0.3))

    awards = []

    # 1. 최고 레이팅
    try:
        from services.elo import get_elo_from_db, calculate_elo_for_season, save_elo_to_db
        elo_data = get_elo_from_db(db_service, season_param)
        if not elo_data:
            elo_data = calculate_elo_for_season(db_service, season_param)
            if elo_data:
                save_elo_to_db(db_service, season_param, elo_data)
        if elo_data and elo_data.get("ratings"):
            best_elo = max(elo_data["ratings"].items(), key=lambda x: x[1])
            awards.append({"title": "최고 레이팅", "icon": "elo", "winner": best_elo[0], "value": f"{round(best_elo[1])}"})
    except Exception as e:
        logger.warning("Awards: ELO failed: %s", e)

    # 2. 최다 연승
    try:
        if data:
            sorted_data = sorted(data, key=lambda x: x.get("title", ["", ""])[1] if len(x.get("title", [])) > 1 else "")
            best_streak_name, best_streak_val = None, 0
            for user in USERS:
                name = user["name"]
                aliases = set(user.get("aliases", [name]))
                ranks = []
                for gl in sorted_data:
                    gn = gl.get("name", [])
                    sc = gl.get("sc", [])
                    idx = next((i for i, n in enumerate(gn) if n in aliases), -1)
                    if idx < 0:
                        continue
                    scores = [(j, sc[j*2] if j*2 < len(sc) else 0) for j in range(min(4, len(gn)))]
                    scores.sort(key=lambda x: -x[1])
                    rank = next((r+1 for r, (j, _) in enumerate(scores) if j == idx), 0)
                    ranks.append(rank)
                cur, best = 0, 0
                for r in ranks:
                    if r == 1:
                        cur += 1
                        best = max(best, cur)
                    else:
                        cur = 0
                if best > best_streak_val:
                    best_streak_val = best
                    best_streak_name = name
            if best_streak_name and best_streak_val >= 2:
                awards.append({"title": "최다 연승", "icon": "streak", "winner": best_streak_name, "value": f"{best_streak_val}연승"})
    except Exception as e:
        logger.warning("Awards: streak failed: %s", e)

    # 3. 최다 대국상
    if ranking_data:
        ranked = sorted(ranking_data["ranking"], key=lambda x: -x["games"])
        if ranked and ranked[0]["games"] > 0:
            awards.append({"title": "최다 대국상", "icon": "games", "winner": ranked[0]["name"], "value": f'{ranked[0]["games"]}국'})

    # 4. 최고 우마평균
    if ranking_data:
        with_games = [p for p in ranking_data["ranking"] if p["games"] >= dynamic_min]
        if with_games:
            best = max(with_games, key=lambda x: x["point_avg"])
            sign = "+" if best["point_avg"] >= 0 else ""
            awards.append({"title": "최고 우마평균", "icon": "uma", "winner": best["name"], "value": f'{sign}{best["point_avg"]:.1f}'})

    # 5~11: 통계 기반
    stat_awards = [
        ("최고 승률", "first_rate", True, "percent"),
        ("최고 국수지", "kuksuji", True, "int"),
        ("최대 타점", "winGame_score.max", True, "int"),
        ("최고 화료수지", "winGame_score.avg", True, "int"),
        ("최소 방총수지", "_chong_combined", False, "int"),
        ("최고 일발율", "richi_yifa.per", True, "percent_raw"),
        ("최고 평균도라", "dora.avg", True, "float"),
    ]

    for title, key, higher_is_better, fmt in stat_awards:
        best_name, best_val = None, None
        for name, ps in stats.items():
            games = ps.get("games", 0)
            if games < dynamic_min:
                continue
            if key == "_chong_combined":
                cr = _get_nested(ps, "chong.avg")
                cs = _get_nested(ps, "chong_score.avg")
                val = cr * abs(cs) if cr is not None and cs is not None else None
            else:
                val = _get_nested(ps, key)
            if val is None or not isinstance(val, (int, float)):
                continue
            if best_val is None or (higher_is_better and val > best_val) or (not higher_is_better and val < best_val):
                best_name, best_val = name, val
        if best_name is not None:
            awards.append({"title": title, "icon": key.split(".")[0], "winner": best_name, "value": _format_award_value(best_val, fmt)})

    return awards


def _get_nested(obj, path):
    for key in path.split("."):
        if isinstance(obj, dict):
            obj = obj.get(key)
        else:
            return None
    return obj


def _format_award_value(val, fmt):
    if fmt == "percent":
        return f"{val * 100:.1f}%"
    elif fmt == "percent_raw":
        return f"{val * 100:.1f}%" if val < 1 else f"{val:.1f}%"
    elif fmt == "int":
        return f"{int(val):,}"
    elif fmt == "float":
        return f"{val:.2f}"
    return str(val)
