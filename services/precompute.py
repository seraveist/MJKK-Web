"""
사전 계산 서비스 (Pre-compute)
- 패보 업로드 시 호출
- 해당 시즌: 즉시 계산 → precomputed_stats 저장
- 전체(all): 백그라운드 스레드로 계산
- 조회 시: precomputed_stats에서 즉시 반환
- [개선] 캐시 무효화 정밀화: 해당 시즌 키만 선별 삭제
"""
import json
import logging
import threading
import datetime

from src import tenhouLog, tenhouStatistics
from config.users import USERS, find_user_index

logger = logging.getLogger(__name__)

COLLECTION_NAME = "precomputed_stats"


def _compute_all_player_stats(game_logs, users=None):
    """
    게임 로그로부터 모든 플레이어의 통계를 계산.
    Returns: { "Kns2": {stats dict}, "HorTeNsiA": {stats dict}, ... }
    """
    if users is None:
        users = USERS

    if not game_logs:
        return {}

    total_games = [tenhouLog.game(log) for log in game_logs]

    # [v3] single-pass: 1번 순회로 N명 동시 처리
    # alias → user name 매핑 빌드
    alias_map = {}
    player_stats = {}
    for user in users:
        name = user["name"]
        ps = tenhouStatistics.PlayerStatistic(games=None, playerName=user)
        player_stats[name] = ps
        for alias in user.get("aliases", [name]):
            alias_map[alias] = name

    for game in total_games:
        # 이 게임에 참여한 유저 찾기
        matched = set()
        for player in game.players:
            user_name = alias_map.get(player.name)
            if user_name and user_name not in matched:
                matched.add(user_name)
                player_stats[user_name].process_game(game)

    # 결과 수집
    all_stats = {}
    for name, ps in player_stats.items():
        try:
            stats = json.loads(ps.json())
            stats["rankData"] = ps.rank_history
            games = stats.get("games", 0)
            if games > 0:
                all_stats[name] = stats
        except Exception as e:
            logger.warning("Stats export failed for %s: %s", name, e)

    return all_stats


def precompute_for_season(db_service, season_param):
    """
    특정 시즌의 통계를 계산하여 MongoDB에 저장.
    """
    try:
        data = db_service.fetch_game_logs_for_stats(season_param)
        if not data:
            logger.info("No data for season %s, skipping precompute", season_param)
            return

        stats = _compute_all_player_stats(data)

        col = db_service._db[COLLECTION_NAME]
        col.update_one(
            {"season": str(season_param)},
            {
                "$set": {
                    "season": str(season_param),
                    "stats": stats,
                    "players": list(stats.keys()),
                    "updated_at": datetime.datetime.utcnow(),
                }
            },
            upsert=True,
        )

        logger.info("Precomputed stats saved: season=%s, players=%d", season_param, len(stats))
    except Exception as e:
        logger.error("Precompute failed for season %s: %s", season_param, e, exc_info=True)


def precompute_after_upload(db_service, game_log):
    """
    패보 업로드 후 호출.
    1) 해당 시즌 → 즉시 계산 (동기)
    2) 전체(all) → 백그라운드 스레드

    [개선] 캐시 무효화를 전체 clear → 해당 시즌 관련 키만 선별 삭제
    """
    from services.cache import cache

    # 게임 날짜에서 시즌 번호 결정
    season = _detect_season(db_service, game_log)

    if season:
        logger.info("Precomputing stats for season %s (sync)...", season)

        # [개선] 해당 시즌 + 전체 관련 캐시만 선별 무효화
        _invalidate_season_cache(cache, str(season))

        # ELO 캐시 무효화 (MongoDB)
        _invalidate_elo_cache(db_service, str(season))

        precompute_for_season(db_service, str(season))

        # 해당 시즌 ELO 즉시 재계산 (대시보드에 바로 반영)
        try:
            from services.elo import calculate_elo_for_season, save_elo_to_db
            elo_data = calculate_elo_for_season(db_service, str(season))
            if elo_data:
                save_elo_to_db(db_service, str(season), elo_data)
        except Exception as e:
            logger.warning("Sync ELO recompute failed (non-fatal): %s", e)

    # 전체(all)는 백그라운드
    logger.info("Scheduling background precompute for 'all'...")
    thread = threading.Thread(
        target=_background_precompute_all,
        args=(db_service,),
        daemon=True,
    )
    thread.start()


def _invalidate_elo_cache(db_service, season):
    """ELO 캐시 무효화 (해당 시즌 + all)"""
    try:
        col = db_service._db["elo_ratings"]
        result = col.delete_many({"season": {"$in": [season, "all"]}})
        if result.deleted_count > 0:
            logger.info("ELO cache invalidated: %d entries for seasons [%s, all]", result.deleted_count, season)
    except Exception as e:
        logger.warning("ELO cache invalidation failed: %s", e)


def _invalidate_season_cache(cache, season):
    """
    [개선] 해당 시즌 관련 캐시 키만 선별 무효화.
    - 해당 시즌의 player_stats, total_stats, ranking 등
    - 'all' 시즌 캐시도 함께 무효화 (전체 통계에 영향)
    - 다른 시즌 캐시는 유지 → 캐시 히트율 보존
    """
    import hashlib

    # make_cache_key는 MD5 해시를 쓰므로, 패턴 매칭 불가
    # 대신 알려진 키 패턴들을 직접 무효화
    seasons_to_invalidate = [season, "all"]

    invalidated = 0
    for s in seasons_to_invalidate:
        # player_stats 캐시 (모든 플레이어)
        from config.users import USERS
        for user in USERS:
            for count in [10, 50, 100]:
                key = hashlib.md5(
                    f"player_stats:{user['name']}:{s}:{count}".encode()
                ).hexdigest()
                if cache.get(key) is not None:
                    cache.delete(key)
                    invalidated += 1

        # total_stats 캐시
        key = hashlib.md5(f"total_stats:{s}".encode()).hexdigest()
        if cache.get(key) is not None:
            cache.delete(key)
            invalidated += 1

    if invalidated > 0:
        logger.info(
            "Selective cache invalidation: %d keys for seasons %s",
            invalidated, seasons_to_invalidate,
        )


def _background_precompute_all(db_service):
    """백그라운드에서 전체 시즌 통계 + ELO 재계산"""
    try:
        from services.cache import cache
        _invalidate_season_cache(cache, "all")
        precompute_for_season(db_service, "all")

        # ELO 자동 재계산 (해당 시즌 + all)
        _recompute_elo(db_service)

        logger.info("Background precompute + ELO for 'all' completed.")
    except Exception as e:
        logger.error("Background precompute failed: %s", e, exc_info=True)


def _recompute_elo(db_service):
    """현재 시즌 + all의 ELO를 재계산하여 저장"""
    try:
        from services.elo import calculate_elo_for_season, save_elo_to_db
        current = db_service.get_current_season()
        for s in [str(current), "all"]:
            elo_data = calculate_elo_for_season(db_service, s)
            if elo_data:
                save_elo_to_db(db_service, s, elo_data)
                logger.info("ELO recomputed for season %s", s)
    except Exception as e:
        logger.warning("ELO recompute failed: %s", e)


def precompute_all_seasons(db_service):
    """
    모든 시즌 + 전체를 한번에 계산. 앱 시작 시 또는 수동 트리거용.
    """
    from services.cache import cache
    cache.clear()  # 전체 재계산 시에만 전체 클리어

    current = db_service.get_current_season()
    for s in range(1, current + 1):
        precompute_for_season(db_service, str(s))
    precompute_for_season(db_service, "all")
    logger.info("All seasons precomputed (1~%d + all)", current)


def get_precomputed_stats(db_service, season_param):
    """
    사전 계산된 통계를 조회.
    Returns: { "players": [...], "stats": {...} } 또는 None
    """
    try:
        col = db_service._db[COLLECTION_NAME]
        doc = col.find_one(
            {"season": str(season_param)},
            {"_id": 0, "stats": 1, "players": 1, "updated_at": 1},
        )
        return doc
    except Exception as e:
        logger.error("Failed to fetch precomputed stats: %s", e)
        return None


def _detect_season(db_service, game_log):
    """게임 로그의 날짜에서 시즌 번호를 결정."""
    try:
        date_str = game_log.get("title", [None, None])[1]
        if not date_str:
            return None
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        base_year = db_service._config.SEASON_BASE_YEAR
        if dt.month <= 6:
            return (dt.year - base_year) * 2 + 1
        else:
            return (dt.year - base_year) * 2 + 2
    except Exception as e:
        logger.warning("Could not detect season from game log: %s", e)
        return None
