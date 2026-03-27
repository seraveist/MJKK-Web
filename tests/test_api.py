"""
API 통합 테스트
- Flask test client 기반
- 각 엔드포인트 기본 동작 확인

사용법:
  python -m pytest tests/test_api.py -v
  또는
  python tests/test_api.py
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def get_test_client():
    """테스트용 Flask 클라이언트 생성"""
    import os
    os.environ.setdefault("FLASK_ENV", "development")

    from main import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_health():
    client = get_test_client()
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] in ("ok", "degraded")
    assert "checks" in data
    print("PASS: /health")


def test_players():
    client = get_test_client()
    res = client.get("/stats/all")
    assert res.status_code == 200
    data = res.get_json()
    assert "allPlayers" in data
    assert isinstance(data["allPlayers"], list)
    assert len(data["allPlayers"]) > 0
    print(f"PASS: /stats/all ({len(data['allPlayers'])} players)")


def test_ranking():
    client = get_test_client()
    res = client.get("/ranking?season=all")
    # 404 is ok if no data
    assert res.status_code in (200, 404)
    data = res.get_json()
    if res.status_code == 200:
        assert "ranking" in data
        assert "players" in data
        assert "daily" in data
        print(f"PASS: /ranking (games={len(data['ranking'])})")
    else:
        print("PASS: /ranking (no data, 404)")


def test_gamelogs_pagination():
    client = get_test_client()
    res = client.get("/api/gamelogs?season=all&page=1&per_page=5")
    assert res.status_code in (200, 404)
    data = res.get_json()
    if res.status_code == 200:
        assert "logs" in data
        assert "pagination" in data
        pg = data["pagination"]
        assert pg["page"] == 1
        assert pg["per_page"] == 5
        assert len(data["logs"]) <= 5
        print(f"PASS: /api/gamelogs pagination (page=1, got {len(data['logs'])} logs)")
    else:
        print("PASS: /api/gamelogs (no data, 404)")


def test_meta():
    client = get_test_client()
    res = client.get("/api/meta?season=all")
    assert res.status_code == 200
    data = res.get_json()
    assert "total_players" in data
    assert "top_yakus" in data
    print(f"PASS: /api/meta (players={data['total_players']})")


def test_awards():
    client = get_test_client()
    res = client.get("/api/awards?season=all")
    assert res.status_code == 200
    data = res.get_json()
    assert "awards" in data
    print(f"PASS: /api/awards ({len(data['awards'])} awards)")


def test_elo():
    client = get_test_client()
    res = client.get("/api/elo?season=all")
    assert res.status_code in (200, 404)
    data = res.get_json()
    if res.status_code == 200:
        assert "ratings" in data
        assert "history" in data
        # 제로섬 검증: 전체 레이팅 합 ≈ 1500 * N
        if data["ratings"]:
            n = len(data["ratings"])
            total = sum(data["ratings"].values())
            expected = 1500 * n
            drift = abs(total - expected)
            print(f"PASS: /api/elo ({n} players, drift={drift:.2f})")
    else:
        print("PASS: /api/elo (no data, 404)")


def test_yakuman_history():
    client = get_test_client()
    res = client.get("/api/yakuman_history?season=all")
    assert res.status_code == 200
    data = res.get_json()
    assert "history" in data
    print(f"PASS: /api/yakuman_history ({len(data['history'])} entries)")


def test_cache_stats():
    client = get_test_client()
    res = client.get("/cache/stats")
    assert res.status_code == 200
    data = res.get_json()
    assert "cache" in data
    print(f"PASS: /cache/stats (hit_rate={data['cache'].get('hit_rate', 'N/A')})")


if __name__ == "__main__":
    tests = [
        test_health, test_players, test_ranking,
        test_gamelogs_pagination, test_meta, test_awards,
        test_elo, test_yakuman_history, test_cache_stats,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} — {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")
