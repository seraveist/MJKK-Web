"""
ELO 계산 유닛 테스트
- 제로섬 검증
- 강자/약자 변동폭 검증
- 엣지 케이스
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_pairwise_zero_sum():
    """단일 쌍의 ELO 변동이 제로섬인지 확인"""
    K = 6
    NORM = 8000
    rw, rl = 1500, 1500
    loss_abs = 8000
    weight = min(loss_abs / NORM, 2.5)
    ew = 1 / (1 + 10 ** ((rl - rw) / 400))

    delta_w = K * weight * (1 - ew)
    delta_l = K * weight * (0 - (1 - ew))

    assert abs(delta_w + delta_l) < 1e-10, f"Zero-sum violated: {delta_w} + {delta_l} = {delta_w + delta_l}"
    print(f"PASS: pairwise zero-sum ({delta_w:.4f} + {delta_l:.4f} = {delta_w + delta_l:.10f})")


def test_strong_vs_weak():
    """강자가 약자에게 지면 더 많이 떨어지는지 확인"""
    K = 6
    NORM = 8000
    loss_abs = 8000
    weight = min(loss_abs / NORM, 2.5)

    # 강자(1800)가 약자(1200)에게 짐
    rw_strong, rl_weak = 1200, 1800  # weak wins
    ew = 1 / (1 + 10 ** ((rl_weak - rw_strong) / 400))
    delta_weak_wins = K * weight * (1 - ew)  # weak의 상승폭

    # 약자(1200)가 강자(1800)에게 짐 (정상)
    rw_strong2, rl_weak2 = 1800, 1200  # strong wins
    ew2 = 1 / (1 + 10 ** ((rl_weak2 - rw_strong2) / 400))
    delta_strong_wins = K * weight * (1 - ew2)  # strong의 상승폭

    # 약자가 이겼을 때 더 많이 상승해야 함
    assert delta_weak_wins > delta_strong_wins, \
        f"Upset should give more points: {delta_weak_wins:.4f} vs {delta_strong_wins:.4f}"
    print(f"PASS: upset gives more ({delta_weak_wins:.4f} > {delta_strong_wins:.4f})")


def test_weight_scaling():
    """점수에 따른 weight 스케일링 확인"""
    NORM = 8000

    w1000 = min(1000 / NORM, 2.5)
    w8000 = min(8000 / NORM, 2.5)
    w16000 = min(16000 / NORM, 2.5)

    assert w1000 < w8000 < w16000, "Weight should scale with score"
    assert w16000 <= 2.5, "Weight should be capped at 2.5"
    print(f"PASS: weight scaling (1000={w1000:.3f}, 8000={w8000:.3f}, 16000={w16000:.3f})")


def test_no_change_for_equal_scores():
    """동점인 쌍은 ELO 변동 없어야 함"""
    scores = [45000, 25000, 25000, 5000]
    involved = []
    for i in range(4):
        for j in range(i + 1, 4):
            diff = scores[i] - scores[j]
            if diff == 0:
                continue
            involved.append((i, j))

    # 2,3은 동점이라 제외 → 5쌍만 관여
    assert len(involved) == 5, f"5 pairs should be involved (excluding tie), got {len(involved)}"
    assert (1, 2) not in involved, "Tied players should not be paired"
    print(f"PASS: equal-score players not involved (pairs={len(involved)})")


def test_full_game_zero_sum():
    """4인 최종 스코어 기반 전체 ELO 변동 합이 0인지 확인"""
    K = 6
    NORM = 8000
    ratings = [1500, 1500, 1400, 1600]
    scores = [45000, 30000, 15000, 10000]

    elo_deltas = [0.0, 0.0, 0.0, 0.0]

    for i in range(4):
        for j in range(i + 1, 4):
            diff = scores[i] - scores[j]
            if diff == 0:
                continue

            wi = i if diff > 0 else j
            li = i if diff < 0 else j
            weight = min(abs(diff) / NORM, 2.5)

            rw, rl = ratings[wi], ratings[li]
            ew = 1 / (1 + 10 ** ((rl - rw) / 400))

            dw = K * weight * (1 - ew)
            dl = K * weight * (0 - (1 - ew))

            elo_deltas[wi] += dw
            elo_deltas[li] += dl

    total = sum(elo_deltas)
    assert abs(total) < 1e-8, f"Full game not zero-sum: {total}"
    print(f"PASS: full game zero-sum (total={total:.10f})")
    print(f"  Deltas: {[f'{d:.4f}' for d in elo_deltas]}")


if __name__ == "__main__":
    test_pairwise_zero_sum()
    test_strong_vs_weak()
    test_weight_scaling()
    test_no_change_for_equal_scores()
    test_full_game_zero_sum()
    print("\nAll ELO tests passed!")
