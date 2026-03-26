"""
통계 계산 스냅샷 테스트

사용법:
  1) 스냅샷 저장 (리팩토링 전에 실행):
     python tests/snapshot_stats.py save

  2) 스냅샷 검증 (리팩토링 후에 실행):
     python tests/snapshot_stats.py verify

  3) 특정 플레이어만:
     python tests/snapshot_stats.py save --player "Kns2"
     python tests/snapshot_stats.py verify --player "Kns2"

동작 원리:
  - save: 현재 DB 데이터로 모든 플레이어의 통계를 계산하여 JSON 파일로 저장
  - verify: 같은 데이터로 다시 계산한 결과를 스냅샷과 비교
  - 숫자 비교는 소수점 6자리까지 허용 (부동소수점 오차 대응)
  - 불일치 항목이 있으면 상세 diff 출력
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_config
from config.users import USERS
from services.database import DatabaseService
from src import tenhouLog, tenhouStatistics

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
TOLERANCE = 1e-6  # 부동소수점 비교 허용 오차


def compute_stats_for_player(data, user, count=100):
    """단일 플레이어의 통계를 계산하여 dict로 반환."""
    total_games = [tenhouLog.game(log) for log in data]
    ps = tenhouStatistics.PlayerStatistic(games=total_games, playerName=user)
    stats = json.loads(ps.json())

    if hasattr(ps, "rank") and hasattr(ps.rank, "datas"):
        stats["rankData"] = ps.rank.datas[-count:]
    else:
        stats["rankData"] = []

    return stats


def save_snapshot(data, players=None, season="all"):
    """현재 계산 결과를 스냅샷으로 저장."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    if players is None:
        players = USERS

    results = {}
    for user in players:
        name = user["name"]
        print(f"  Computing stats for {name}...", end=" ")
        try:
            stats = compute_stats_for_player(data, user)
            results[name] = stats
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")
            results[name] = {"error": str(e)}

    filename = SNAPSHOT_DIR / f"snapshot_season_{season}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nSnapshot saved: {filename}")
    print(f"Players: {len(results)}")
    return filename


def verify_snapshot(data, players=None, season="all"):
    """현재 계산 결과를 스냅샷과 비교."""
    filename = SNAPSHOT_DIR / f"snapshot_season_{season}.json"
    if not filename.exists():
        print(f"ERROR: Snapshot not found: {filename}")
        print("Run 'python tests/snapshot_stats.py save' first.")
        return False

    with open(filename, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    if players is None:
        players = USERS

    all_passed = True
    total_checks = 0
    total_diffs = 0

    for user in players:
        name = user["name"]
        if name not in snapshot:
            print(f"  SKIP {name} — not in snapshot")
            continue

        print(f"  Verifying {name}...", end=" ")
        try:
            current = compute_stats_for_player(data, user)
        except Exception as e:
            print(f"COMPUTE FAILED: {e}")
            all_passed = False
            continue

        saved = snapshot[name]
        if "error" in saved:
            print(f"SKIP (snapshot had error)")
            continue

        diffs = compare_dicts(saved, current, path=name)
        total_checks += 1

        if diffs:
            total_diffs += len(diffs)
            all_passed = False
            print(f"MISMATCH ({len(diffs)} differences)")
            for d in diffs[:10]:  # 최대 10개만 출력
                print(f"    {d}")
            if len(diffs) > 10:
                print(f"    ... and {len(diffs) - 10} more")
        else:
            print("PASS")

    print(f"\nResult: {'ALL PASSED' if all_passed else 'FAILED'}")
    print(f"Checked: {total_checks} players, {total_diffs} differences found")
    return all_passed


def compare_dicts(expected, actual, path=""):
    """두 dict를 재귀적으로 비교하여 차이 목록 반환."""
    diffs = []

    if isinstance(expected, dict) and isinstance(actual, dict):
        all_keys = set(expected.keys()) | set(actual.keys())
        for key in sorted(all_keys):
            subpath = f"{path}.{key}" if path else key
            if key not in expected:
                diffs.append(f"{subpath}: NEW KEY (value={actual[key]})")
            elif key not in actual:
                diffs.append(f"{subpath}: MISSING KEY (expected={expected[key]})")
            else:
                diffs.extend(compare_dicts(expected[key], actual[key], subpath))

    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            diffs.append(f"{path}: list length {len(expected)} → {len(actual)}")
        for i, (e, a) in enumerate(zip(expected, actual)):
            diffs.extend(compare_dicts(e, a, f"{path}[{i}]"))

    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if not (math.isnan(expected) and math.isnan(actual)):
            if abs(expected - actual) > TOLERANCE:
                diffs.append(f"{path}: {expected} → {actual}")

    elif expected != actual:
        diffs.append(f"{path}: {repr(expected)} → {repr(actual)}")

    return diffs


def main():
    parser = argparse.ArgumentParser(description="Statistics snapshot tester")
    parser.add_argument("action", choices=["save", "verify"])
    parser.add_argument("--player", help="Test specific player only")
    parser.add_argument("--season", default="all", help="Season to test (default: all)")
    args = parser.parse_args()

    # DB 연결
    config = get_config()
    db = DatabaseService(config)
    db.connect()

    # 데이터 조회
    print(f"Fetching game logs (season={args.season})...")
    data = list(db.collection.find())
    print(f"Found {len(data)} game logs.\n")

    # 플레이어 필터
    players = USERS
    if args.player:
        players = [u for u in USERS if u["name"] == args.player]
        if not players:
            print(f"Player not found: {args.player}")
            sys.exit(1)

    if args.action == "save":
        save_snapshot(data, players, args.season)
    elif args.action == "verify":
        passed = verify_snapshot(data, players, args.season)
        sys.exit(0 if passed else 1)

    db.close()


if __name__ == "__main__":
    main()
