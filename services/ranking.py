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
    """
    if users is None:
        users = USERS

    if not game_logs:
        return None

    player_scores = {
        user["name"]: {"point_sum": 0, "games": 0, "point_avg": 0}
        for user in users
    }
    daily_entries = []

    for log in game_logs:
        ref = log.get("ref", "unknown")
        title = log.get("title", ["", ""])
        date = title[1] if len(title) > 1 else ""

        names = log.get("name", [])
        sc = log.get("sc", [])

        points = {}
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
                points[matched_name] = point

        if points:
            daily_entries.append({
                "date": date,
                "ref": ref,
                "points": points,
            })

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

    # 일별 점수 (최신순) — title[1] 날짜 기준 정렬
    daily_entries.sort(key=lambda x: x["date"], reverse=True)

    return {
        "ranking": ranking_list,
        "players": [user["name"] for user in users],
        "daily": daily_entries,
    }
