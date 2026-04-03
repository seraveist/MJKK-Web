# src/mahjong_core.py
from collections import Counter
import functools

# 상수 정의
TILE_EAST, TILE_SOUTH, TILE_WEST, TILE_NORTH = 31, 32, 33, 34
TILE_HAKU, TILE_HATSU, TILE_CHUN = 35, 36, 37
ALL_TILES = [i for i in range(1, 38) if i % 10 != 0]

def calculate_waiting_tiles(hand_tiles: list, is_number_only: bool = False) -> list:
    if len(hand_tiles) != 13:
        return []

    tile_counts = [0] * 38
    for t in hand_tiles: tile_counts[t] += 1

    waiting_list = []
    search_range = range(1, 10) if is_number_only else ALL_TILES
    
    for potential_tile in search_range:
        if tile_counts[potential_tile] >= 4: continue
            
        tile_counts[potential_tile] += 1
        
        # [변경점] 매번 check_agari를 부르지 않고 캐시된 함수를 부름
        if _cached_check_agari(tuple(tile_counts)):
            waiting_list.append({'tile': potential_tile, 'han': 1})
            
        tile_counts[potential_tile] -= 1

    return waiting_list

def calculate_expected_values(hand_tiles: list, win_group_candidates: list, config: dict) -> dict:
    """리치 시점의 기대 판수와 대기패 종류 수 계산"""
    total_han_sum = 0
    valid_wait_count = 0
    
    if not win_group_candidates:
        return {'wait_types': 0, 'avg_han': 0}

    for candidate in win_group_candidates:
        # 약식 기대값 계산: 리치(1) + 멘젠쯔모(1) + 기본판수 + 도라(config에서 받음)
        # 정확한 계산을 위해서는 여기서 calculate_yaku_and_han 호출 필요
        dora = config.get('dora_count', 0)
        expected_han = candidate.get('han', 1) + 2 + dora
        
        total_han_sum += expected_han
        valid_wait_count += 1
        
    avg_han = total_han_sum / valid_wait_count if valid_wait_count > 0 else 0
    return {'wait_types': valid_wait_count, 'avg_han': avg_han}

# --- Agari Check Logic (Backtracking) ---
def check_agari(tile_counts: list) -> bool:
    if check_chiitoitsu(tile_counts): return True
    if check_kokushi(tile_counts): return True
    if check_standard_agari(tile_counts): return True
    return False

def check_chiitoitsu(tile_counts: list) -> bool:
    pairs = 0
    for count in tile_counts:
        if count == 2: pairs += 1
        elif count != 0: return False
    return pairs == 7

def check_kokushi(tile_counts: list) -> bool:
    yao_indices = [1, 9, 11, 19, 21, 29, 31, 32, 33, 34, 35, 36, 37]
    found_yao = 0
    pair_found = False
    for idx in yao_indices:
        if tile_counts[idx] == 1: found_yao += 1
        elif tile_counts[idx] == 2:
            found_yao += 1
            pair_found = True
        else: return False
    return found_yao == 13 and pair_found

def check_standard_agari(tile_counts: list) -> bool:
    # 머리 찾기 후 몸통 분해
    for i in range(1, 38):
        if tile_counts[i] >= 2:
            tile_counts[i] -= 2
            if decompose_body(tile_counts, 0):
                tile_counts[i] += 2
                return True
            tile_counts[i] += 2
    return False

def decompose_body(tile_counts: list, depth: int) -> bool:
    if depth == 4: return True
    first_tile = -1
    for i in range(1, 38):
        if tile_counts[i] > 0:
            first_tile = i
            break
    if first_tile == -1: return True

    # Koutsu (Triple)
    if tile_counts[first_tile] >= 3:
        tile_counts[first_tile] -= 3
        if decompose_body(tile_counts, depth + 1):
            tile_counts[first_tile] += 3
            return True
        tile_counts[first_tile] += 3

    # Shuntsu (Sequence)
    if first_tile < 30 and first_tile % 10 <= 7:
        if tile_counts[first_tile+1] > 0 and tile_counts[first_tile+2] > 0:
            tile_counts[first_tile] -= 1; tile_counts[first_tile+1] -= 1; tile_counts[first_tile+2] -= 1
            if decompose_body(tile_counts, depth + 1):
                tile_counts[first_tile] += 1; tile_counts[first_tile+1] += 1; tile_counts[first_tile+2] += 1
                return True
            tile_counts[first_tile] += 1; tile_counts[first_tile+1] += 1; tile_counts[first_tile+2] += 1
            
    return False

@functools.lru_cache(maxsize=131072)
def _cached_check_agari(tile_counts_tuple: tuple) -> bool:
    """리스트는 캐싱이 안 되므로 튜플로 변환해서 캐싱하는 안전한 래퍼"""
    return check_agari(list(tile_counts_tuple))