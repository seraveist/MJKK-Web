"""
랭킹 계산 서비스
- 라우트 핸들러에서 비즈니스 로직 분리
- 랭킹 집계 및 일별 점수 계산
"""
import logging
from typing import Optional

from config.users import USERS, find_user_by_alias

logger = logging.getLogger(__name__)


def calculate_ranking(game_logs: list, users=None):
    """
    게임 로그로부터 랭킹과 일별 점수를 계산.
    
    Args:
        game_logs: DB에서 가져온 게임 로그 리스트
        users: 유저 목록 (기본값: config.users.USERS)
        
    Returns:
        dict with keys: ranking, players, daily
        None if no data
    """
    if users is None:
        users = USERS

    if not game_logs:
        return None

    player_scores = {
        user["name"]: {"point_sum": 0, "games": 0, "point_avg": 0}
        for user in users
    }
    daily_scores = {}

    for log in game_logs:
        ref = log.get("ref", "unknown")
        if ref not in daily_scores:
            daily_scores[ref] = {}

        names = log.get("name", [])
        sc = log.get("sc", [])

        for i in range(min(4, len(names))):
            try:
                name = names[i]
                point = sc[i * 2 + 1]
            except (IndexError, KeyError):
                continue

            matched = find_user_by_alias(users, name)
            if matched:
                matched_name = matched["name"]
                player_scores[matched_name]["point_sum"] += point
                player_scores[matched_name]["games"] += 1
                daily_scores[ref][matched_name] = point

    # 평균 계산
    for stats in player_scores.values():
        if stats["games"] > 0:
            stats["point_avg"] = round(stats["point_sum"] / stats["games"], 2)

    # 정렬: 대국 수 내림차순 → 우마 평균 내림차순
    ranking_list = [
        {"name": name, **stats}
        for name, stats in player_scores.items()
    ]
    ranking_list.sort(key=lambda x: (-x["games"], -x["point_avg"]))

    # 일별 점수 (최신순) — ref 포함
    daily_list = [
        {
            "date": k.split("-")[0] if "-" in k else k,
            "ref": k,
            "points": v,
        }
        for k, v in sorted(daily_scores.items(), reverse=True)
    ]

    return {
        "ranking": ranking_list,
        "players": [user["name"] for user in users],
        "daily": daily_list,
    }
