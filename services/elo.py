"""
ELO 레이팅 서비스 — 최종 스코어 기반 제로섬
- 게임 최종 점수로 쌍별 비교
- 점수 차이에 비례한 weight
- 완전한 제로섬 보장
"""
import logging
import datetime
from typing import Optional

from config.users import USERS, find_user_by_alias

logger = logging.getLogger(__name__)

DEFAULT_RATING = 1500
DEFAULT_K = 6
DEFAULT_NORM = 8000
DEFAULT_SENSITIVITY = 400
ELO_COLLECTION = "elo_ratings"


def _get_elo_params(db_service):
    """설정에서 ELO 파라미터 조회"""
    try:
        from services.settings import get_setting
        params = get_setting(db_service, "elo_params")
        if params:
            return (params.get("K", DEFAULT_K), params.get("NORM", DEFAULT_NORM),
                    params.get("initial", DEFAULT_RATING), params.get("sensitivity", DEFAULT_SENSITIVITY))
    except Exception:
        pass
    return DEFAULT_K, DEFAULT_NORM, DEFAULT_RATING, DEFAULT_SENSITIVITY


def calculate_elo_for_season(db_service, season_param, K=None, NORM=None):
    """
    시즌 전체 대국을 시간순으로 처리하여 ELO 레이팅 계산.
    """
    cfg_K, cfg_NORM, cfg_initial, cfg_sens = _get_elo_params(db_service)
    if K is None: K = cfg_K
    if NORM is None: NORM = cfg_NORM

    data = db_service.fetch_game_logs_for_stats(season_param)
    if not data:
        return None

    data.sort(key=lambda x: x.get("title", ["", ""])[1] if len(x.get("title", [])) > 1 else "")

    ratings = {}
    history = {}

    for user in USERS:
        ratings[user["name"]] = cfg_initial
        history[user["name"]] = []

    for game_log in data:
        title = game_log.get("title", ["", ""])
        date = title[1] if len(title) > 1 else ""
        names_raw = game_log.get("name", [])
        sc = game_log.get("sc", [])

        # 게임 내 플레이어를 유저에 매핑
        seat_to_user = {}
        final_scores = {}
        for i, raw_name in enumerate(names_raw):
            matched = find_user_by_alias(USERS, raw_name)
            if matched:
                seat_to_user[i] = matched["name"]
                final_scores[i] = sc[i * 2] if i * 2 < len(sc) else 0

        if len(seat_to_user) < 2:
            continue

        # 최종 스코어 기반 쌍별 ELO 업데이트
        seats = list(seat_to_user.keys())
        for a in range(len(seats)):
            for b in range(a + 1, len(seats)):
                si, sj = seats[a], seats[b]
                score_diff = final_scores[si] - final_scores[sj]
                if score_diff == 0:
                    continue

                wi = si if score_diff > 0 else sj
                li = si if score_diff < 0 else sj

                w_user = seat_to_user[wi]
                l_user = seat_to_user[li]

                weight = min(abs(score_diff) / NORM, 2.5)

                rw = ratings[w_user]
                rl = ratings[l_user]
                ew = 1 / (1 + 10 ** ((rl - rw) / cfg_sens))

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
        "params": {"K": K, "NORM": NORM, "initial": cfg_initial, "sensitivity": cfg_sens},
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
