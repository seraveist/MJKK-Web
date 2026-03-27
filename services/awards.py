"""
시즌 어워드 계산 서비스
- 9개 확정 항목
- 랭킹 API + 통계 API 데이터 결합
"""
import logging

from config.users import USERS
from services.ranking import calculate_ranking
from services.precompute import get_precomputed_stats

logger = logging.getLogger(__name__)


def calculate_awards(db_service, season_param):
    """
    시즌 어워드 계산.
    Returns: list of { "title": str, "winner": str, "value": str, "detail": str }
    """
    # 랭킹 데이터 (우마평균, 대국수)
    ranking_data = None
    try:
        data = db_service.fetch_game_logs(season_param, lightweight=True)
        ranking_data = calculate_ranking(data)
    except Exception as e:
        logger.warning("Awards: ranking calc failed: %s", e)

    # 통계 데이터
    precomputed = get_precomputed_stats(db_service, season_param)
    stats = precomputed.get("stats", {}) if precomputed else {}

    awards = []

    # 1. 최다 대국상
    if ranking_data:
        ranked = sorted(ranking_data["ranking"], key=lambda x: -x["games"])
        if ranked and ranked[0]["games"] > 0:
            awards.append({
                "title": "최다 대국상",
                "icon": "games",
                "winner": ranked[0]["name"],
                "value": f'{ranked[0]["games"]}국',
            })

    # 2. 최고 우마평균
    if ranking_data:
        with_games = [p for p in ranking_data["ranking"] if p["games"] >= 5]
        if with_games:
            best = max(with_games, key=lambda x: x["point_avg"])
            sign = "+" if best["point_avg"] >= 0 else ""
            awards.append({
                "title": "최고 우마평균",
                "icon": "uma",
                "winner": best["name"],
                "value": f'{sign}{best["point_avg"]:.1f}',
            })

    # 3~9: 통계 기반
    stat_awards = [
        ("최고 승률", "first_rate", True, "percent", 5),
        ("최고 국수지", "kuksuji", True, "int", 5),
        ("최대 타점", "winGame_score.max", True, "int", 1),
        ("최고 화료수지", "winGame_score.avg", True, "int", 5),
        ("최소 방총수지", "chong_score.avg", False, "int", 5),
        ("최고 일발율", "richi_yifa.per", True, "percent_raw", 5),
        ("최고 평균도라", "dora.avg", True, "float", 5),
    ]

    for title, key, higher_is_better, fmt, min_games in stat_awards:
        best_name = None
        best_val = None

        for name, player_stats in stats.items():
            games = player_stats.get("games", 0)
            if games < min_games:
                continue

            val = _get_nested(player_stats, key)
            if val is None or not isinstance(val, (int, float)):
                continue

            if best_val is None:
                best_name, best_val = name, val
            elif higher_is_better and val > best_val:
                best_name, best_val = name, val
            elif not higher_is_better and val < best_val:
                best_name, best_val = name, val

        if best_name is not None:
            awards.append({
                "title": title,
                "icon": key.split(".")[0],
                "winner": best_name,
                "value": _format_award_value(best_val, fmt),
            })

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
        if val < 1:
            return f"{val * 100:.1f}%"
        return f"{val:.1f}%"
    elif fmt == "int":
        return f"{int(val):,}"
    elif fmt == "float":
        return f"{val:.2f}"
    return str(val)
