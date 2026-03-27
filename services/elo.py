"""
ELO 레이팅 서비스 — 국수지 기반 제로섬
- 매 국의 점수 변동에서 득점/실점 쌍 추출
- 쌍별 ELO 변동 계산 (선형 weight)
- 완전한 제로섬 보장
"""
import logging
import datetime
from typing import Optional

from config.users import USERS, find_user_by_alias
from src import tenhouLog

logger = logging.getLogger(__name__)

DEFAULT_RATING = 1500
DEFAULT_K = 6
DEFAULT_NORM = 8000
ELO_COLLECTION = "elo_ratings"
ELO_HISTORY_COLLECTION = "elo_history"


def calculate_elo_for_season(db_service, season_param, K=DEFAULT_K, NORM=DEFAULT_NORM):
    """
    시즌 전체 대국을 시간순으로 처리하여 ELO 레이팅 계산.
    Returns: { "ratings": {name: rating, ...}, "history": {name: [(date, rating), ...], ...} }
    """
    data = db_service.fetch_game_logs_for_stats(season_param)
    if not data:
        return None

    # 날짜순 정렬
    data.sort(key=lambda x: x.get("title", ["", ""])[1] if len(x.get("title", [])) > 1 else "")

    ratings = {}
    history = {}

    for user in USERS:
        ratings[user["name"]] = DEFAULT_RATING
        history[user["name"]] = []

    for game_log in data:
        title = game_log.get("title", ["", ""])
        date = title[1] if len(title) > 1 else ""
        log_data = game_log.get("log", [])
        names_raw = game_log.get("name", [])

        # 게임 내 플레이어를 유저에 매핑
        seat_to_user = {}
        for i, raw_name in enumerate(names_raw):
            matched = find_user_by_alias(USERS, raw_name)
            if matched:
                seat_to_user[i] = matched["name"]

        if len(seat_to_user) < 2:
            continue

        # 각 국별로 ELO 업데이트
        for round_data in (log_data or []):
            if not round_data or len(round_data) < 16:
                continue

            round_info = round_data[0] if round_data[0] else []
            player_count = min(4, len(names_raw))

            # 점수 변동 추출
            result_block = round_data[16] if len(round_data) > 16 else None
            if not result_block:
                continue

            deltas = [0] * player_count

            if isinstance(result_block, list) and len(result_block) >= 1:
                score_arr = result_block[0] if isinstance(result_block[0], list) else result_block
                if isinstance(score_arr, list):
                    for i in range(min(player_count, len(score_arr))):
                        if isinstance(score_arr[i], (int, float)):
                            deltas[i] = score_arr[i]

            # 제로섬 검증
            if sum(deltas) != 0 or all(d == 0 for d in deltas):
                continue

            # 득점/실점 쌍 추출 후 ELO 업데이트
            for i in range(player_count):
                for j in range(i + 1, player_count):
                    if deltas[i] == 0 or deltas[j] == 0:
                        continue
                    if (deltas[i] > 0 and deltas[j] > 0) or (deltas[i] < 0 and deltas[j] < 0):
                        continue

                    wi = i if deltas[i] > 0 else j
                    li = i if deltas[i] < 0 else j

                    w_user = seat_to_user.get(wi)
                    l_user = seat_to_user.get(li)
                    if not w_user or not l_user:
                        continue

                    loss_abs = abs(deltas[li])
                    weight = min(loss_abs / NORM, 2.5)

                    rw = ratings[w_user]
                    rl = ratings[l_user]
                    ew = 1 / (1 + 10 ** ((rl - rw) / 400))

                    delta_w = K * weight * (1 - ew)
                    delta_l = K * weight * (0 - (1 - ew))

                    ratings[w_user] += delta_w
                    ratings[l_user] += delta_l

        # 게임 종료 후 히스토리 기록
        for user_name in seat_to_user.values():
            history[user_name].append({
                "date": date,
                "rating": round(ratings[user_name], 1),
            })

    # 대국 없는 유저 제거
    active_ratings = {k: round(v, 1) for k, v in ratings.items()
                      if history.get(k) and len(history[k]) > 0}
    active_history = {k: v for k, v in history.items() if len(v) > 0}

    return {
        "ratings": active_ratings,
        "history": active_history,
        "params": {"K": K, "NORM": NORM, "initial": DEFAULT_RATING},
    }


def save_elo_to_db(db_service, season_param, elo_data):
    """ELO 결과를 MongoDB에 저장"""
    try:
        col = db_service._db[ELO_COLLECTION]
        col.update_one(
            {"season": str(season_param)},
            {"$set": {
                "season": str(season_param),
                "ratings": elo_data["ratings"],
                "history": elo_data["history"],
                "params": elo_data["params"],
                "updated_at": datetime.datetime.utcnow(),
            }},
            upsert=True,
        )
    except Exception as e:
        logger.error("Failed to save ELO: %s", e)


def get_elo_from_db(db_service, season_param):
    """저장된 ELO 조회"""
    try:
        col = db_service._db[ELO_COLLECTION]
        return col.find_one(
            {"season": str(season_param)},
            {"_id": 0},
        )
    except Exception as e:
        logger.error("Failed to fetch ELO: %s", e)
        return None
