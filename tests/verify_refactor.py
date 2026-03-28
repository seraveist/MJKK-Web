"""
통계 리팩토링 검증 스크립트

사용법:
  1) 리팩토링 전에 스냅샷 저장:
     python tests/verify_refactor.py save

  2) 리팩토링 후에 검증:
     python tests/verify_refactor.py verify

  결과가 100% 일치하면 리팩토링 성공.
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SNAPSHOT_FILE = Path(__file__).parent / "snapshots" / "refactor_snapshot.json"
TOLERANCE = 1e-4


def get_db_data():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    from config import get_config
    from services.database import DatabaseService
    config = get_config()
    db = DatabaseService(config)
    db.connect()
    return db.fetch_game_logs_for_stats("all")


def compute_all_stats(data):
    from config.users import USERS
    from src import tenhouLog, tenhouStatistics
    total_games = [tenhouLog.game(log) for log in data]
    results = {}
    for user in USERS:
        name = user["name"]
        try:
            ps = tenhouStatistics.PlayerStatistic(games=total_games, playerName=user)
            stats = json.loads(ps.json())
            if hasattr(ps, "rank_history"):
                stats["rankData"] = ps.rank_history
            elif hasattr(ps, "rank") and hasattr(ps.rank, "datas"):
                stats["rankData"] = ps.rank.datas
            else:
                stats["rankData"] = []
            if stats.get("games", 0) > 0:
                results[name] = stats
                print(f"  {name}: {stats['games']}국 OK")
        except Exception as e:
            print(f"  {name}: FAILED — {e}")
    return results


def save_snapshot():
    print("Loading data from DB...")
    data = get_db_data()
    print(f"Loaded {len(data)} game logs.\n")
    print("Computing stats...")
    results = compute_all_stats(data)
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSnapshot saved: {SNAPSHOT_FILE}")
    print(f"Players: {len(results)}")


def verify_snapshot():
    if not SNAPSHOT_FILE.exists():
        print(f"ERROR: {SNAPSHOT_FILE} not found. Run 'save' first.")
        return False
    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        snapshot = json.load(f)
    print("Loading data from DB...")
    data = get_db_data()
    print(f"Loaded {len(data)} game logs.\n")
    print("Computing stats (refactored)...")
    current = compute_all_stats(data)

    print("\n" + "=" * 60)
    all_match = True
    for name in sorted(set(list(snapshot.keys()) + list(current.keys()))):
        if name not in snapshot:
            print(f"  [NEW] {name}"); continue
        if name not in current:
            print(f"  [MISSING] {name}"); all_match = False; continue
        diffs = []
        _compare(snapshot[name], current[name], "", diffs)
        if diffs:
            all_match = False
            print(f"\n  [MISMATCH] {name}:")
            for d in diffs[:20]:
                print(f"    {d}")
            if len(diffs) > 20:
                print(f"    ... +{len(diffs)-20} more")
        else:
            print(f"  [OK] {name}")

    print("\n" + "=" * 60)
    print("RESULT: ALL MATCH!" if all_match else "RESULT: MISMATCHES FOUND")
    return all_match


def _compare(old, new, prefix, diffs):
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(set(list(old.keys()) + list(new.keys()))):
            path = f"{prefix}.{key}" if prefix else key
            if key == "rankData":
                if old.get(key, []) != new.get(key, []):
                    diffs.append(f"{path}: differs")
                continue
            if key not in old:
                diffs.append(f"{path}: NEW")
            elif key not in new:
                diffs.append(f"{path}: MISSING")
            else:
                _compare(old[key], new[key], path, diffs)
    elif isinstance(old, list) and isinstance(new, list):
        if len(old) != len(new):
            diffs.append(f"{prefix}: len {len(old)}→{len(new)}")
        else:
            for i in range(len(old)):
                _compare(old[i], new[i], f"{prefix}[{i}]", diffs)
    elif isinstance(old, (int, float)) and isinstance(new, (int, float)):
        if abs(old) > 0:
            if abs(old - new) / max(abs(old), 1) > TOLERANCE:
                diffs.append(f"{prefix}: {old}→{new}")
        elif abs(new) > TOLERANCE:
            diffs.append(f"{prefix}: {old}→{new}")
    elif old != new:
        diffs.append(f"{prefix}: {repr(old)}→{repr(new)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["save", "verify"])
    args = parser.parse_args()
    if args.action == "save":
        save_snapshot()
    else:
        sys.exit(0 if verify_snapshot() else 1)
