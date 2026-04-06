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

    # 시간순 정렬 (rank_history, ELO 등 순서 의존 데이터 보장)
    game_logs_sorted = sorted(game_logs, key=lambda x: x.get("title", ["", ""])[1] if len(x.get("title", [])) > 1 else "")
    total_games = [tenhouLog.game(log) for log in game_logs_sorted]

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
    [개선#10] 해당 시즌 관련 캐시 무효화.
    make_cache_key를 직접 호출하여 키 생성 로직 동기화.
    """
    from services.cache import make_cache_key
    from config.users import USERS

    seasons_to_invalidate = [season, "all"]
    invalidated = 0

    for s in seasons_to_invalidate:
        # player_stats (모든 유저 × 모든 count 조합)
        for user in USERS:
            for count in [10, 20, 50, 100]:
                key = make_cache_key("player_stats", user['name'], s, count)
                if cache.get(key) is not None:
                    cache.delete(key)
                    invalidated += 1

        # total_stats
        key = make_cache_key("total_stats", s)
        if cache.get(key) is not None:
            cache.delete(key)
            invalidated += 1

        # game_logs (lightweight True/False)
        for lw in [True, False]:
            key = make_cache_key("game_logs", s, lw)
            if cache.get(key) is not None:
                cache.delete(key)
                invalidated += 1

        # stats_logs (전용 TTL 캐시)
        key = make_cache_key("stats_logs", s)
        if cache.get(key) is not None:
            cache.delete(key)
            invalidated += 1

        # profile_stats (다중시즌 프로파일 캐시)
        key = make_cache_key("profile_stats", s)
        if cache.get(key) is not None:
            cache.delete(key)
            invalidated += 1

        # profile (모든 유저)
        for user in USERS:
            key = make_cache_key("profile", user['name'], s)
            if cache.get(key) is not None:
                cache.delete(key)
                invalidated += 1

    if invalidated > 0:
        logger.info("Selective cache invalidation: %d keys for seasons %s", invalidated, seasons_to_invalidate)


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


def _compute_stats_from_parsed(parsed_games, users=None):
    """
    이미 파싱된 게임 객체로부터 통계 계산. (tenhouLog.game() 재호출 불필요)
    parsed_games: [(raw_log, parsed_game_obj), ...]
    """
    if users is None:
        users = USERS

    if not parsed_games:
        return {}

    alias_map = {}
    player_stats = {}
    for user in users:
        name = user["name"]
        ps = tenhouStatistics.PlayerStatistic(games=None, playerName=user)
        player_stats[name] = ps
        for alias in user.get("aliases", [name]):
            alias_map[alias] = name

    for raw_log, game in parsed_games:
        matched = set()
        for player in game.players:
            user_name = alias_map.get(player.name)
            if user_name and user_name not in matched:
                matched.add(user_name)
                player_stats[user_name].process_game(game)

    all_stats = {}
    for name, ps in player_stats.items():
        try:
            stats = json.loads(ps.json())
            stats["rankData"] = ps.rank_history
            if stats.get("games", 0) > 0:
                all_stats[name] = stats
        except Exception as e:
            logger.warning("Stats export failed for %s: %s", name, e)

    return all_stats


def _save_precomputed(db_service, season_param, stats):
    """계산 결과를 MongoDB에 저장"""
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


def precompute_all_seasons(db_service):
    """
    모든 시즌 + 전체를 한번에 계산.
    [최적화] DB 1회 조회 + 파싱 1회 → 시즌별 분배
    """
    import time
    t0 = time.time()

    from services.cache import cache
    cache.clear()
    _reload_users_from_db(db_service)

    # 1) 전체 데이터 1회 조회
    all_data = db_service.fetch_game_logs_for_stats("all")
    if not all_data:
        logger.info("No data found, skipping precompute")
        return

    # 2) 시간순 정렬 + 1회 파싱
    all_data_sorted = sorted(all_data, key=lambda x: x.get("title", ["", ""])[1] if len(x.get("title", [])) > 1 else "")
    logger.info("Parsing %d game logs...", len(all_data_sorted))
    parsed_all = []
    for log in all_data_sorted:
        try:
            parsed_all.append((log, tenhouLog.game(log)))
        except Exception as e:
            logger.warning("Parse failed for ref=%s: %s", log.get("ref", "?"), e)

    t1 = time.time()
    logger.info("Parsing done: %d games in %.1fs", len(parsed_all), t1 - t0)

    # 3) 시즌별 분배
    from collections import defaultdict
    season_groups = defaultdict(list)
    for raw_log, parsed in parsed_all:
        season = _detect_season(db_service, raw_log)
        if season:
            season_groups[str(season)].append((raw_log, parsed))

    # 4) 시즌별 계산 + 저장
    current = db_service.get_current_season()
    for s in range(1, current + 1):
        s_key = str(s)
        games = season_groups.get(s_key, [])
        if not games:
            logger.info("Season %s: no data, skipping", s_key)
            continue
        stats = _compute_stats_from_parsed(games)
        _save_precomputed(db_service, s_key, stats)
        logger.info("Season %s: %d games, %d players", s_key, len(games), len(stats))

    # 5) 전체("all") 계산 + 저장
    stats_all = _compute_stats_from_parsed(parsed_all)
    _save_precomputed(db_service, "all", stats_all)
    logger.info("All: %d games, %d players", len(parsed_all), len(stats_all))

    t2 = time.time()
    logger.info("All seasons precomputed (1~%d + all) in %.1fs (parse=%.1fs, compute=%.1fs)",
                current, t2 - t0, t1 - t0, t2 - t1)


def _reload_users_from_db(db_service):
    """DB에서 최신 유저 목록을 읽어 USERS를 in-place 업데이트"""
    try:
        db_users = list(db_service._db["usersConfig"].find({}, {"_id": 0, "name": 1, "aliases": 1}))
        if db_users:
            USERS.clear()
            USERS.extend(db_users)
            logger.info("Reloaded %d users from DB for precompute", len(db_users))
    except Exception as e:
        logger.warning("Failed to reload users from DB: %s", e)


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
        # YYYY-MM-DD hh:mm:ss 또는 YYYY-MM-DD 모두 대응
        date_part = date_str[:10]
        dt = datetime.datetime.strptime(date_part, "%Y-%m-%d")
        base_year = db_service._config.SEASON_BASE_YEAR
        if dt.month <= 6:
            return (dt.year - base_year) * 2 + 1
        else:
            return (dt.year - base_year) * 2 + 2
    except Exception as e:
        logger.warning("Could not detect season from game log: %s", e)
        return None
