from .mahjong_core import calculate_waiting_tiles, calculate_expected_values
import re, math

# ---------------------------------------------------------------
# [Helper Functions] 로그 파싱 및 핸드 복원 (Type-Safe Fix)
# ---------------------------------------------------------------

def safe_int(val):
    """안전한 정수 변환 헬퍼: 문자열, 숫자 모두 처리"""
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        # "r60" -> 60, "33" -> 33
        if "r" in val:
            return int(val.replace("r", ""))
        try:
            return int(val)
        except:
            pass
    return val

def generate_hand(baihais: list, tsumohais: list, sutehais: list) -> list:
    """로그 재생을 통한 손패 복원"""
    current_hand = list(baihais)
    for i, sutehai in enumerate(sutehais):
        if i >= len(tsumohais): break
        drawn_tile = tsumohais[i]
        current_hand.append(drawn_tile)

        # [수정] 타입 안전 변환 적용
        discard_val = safe_int(sutehai)
        
        # 리치 여부 판단 (원본 문자열 기준)
        is_riichi = False
        if isinstance(sutehai, str) and "r" in sutehai:
            is_riichi = True

        # 정수로 변환된 discard_val 사용
        tile_to_remove = drawn_tile if discard_val == 60 else discard_val
        
        if tile_to_remove in current_hand:
            current_hand.remove(tile_to_remove)
        
        if is_riichi: break

    normalized_hand = []
    for tile in current_hand:
        if tile > 50: normalized_hand.append((tile - 51) * 10 + 5)
        else: normalized_hand.append(tile - 10)
    normalized_hand.sort()
    return normalized_hand

def generate_hand_at_turn(baihais, tsumohais, sutehais, turn_limit):
    """특정 턴까지만 진행하여 손패 복원"""
    return generate_hand(baihais, tsumohais[:turn_limit+1], sutehais[:turn_limit+1])

def calculate_score_points(han, fu, is_host, is_tsumo=False):
    """판수/부수 기반 점수 계산"""
    if han <= 0: return 0
    base = 0
    if han >= 13: base = 8000
    elif han >= 11: base = 6000
    elif han >= 8: base = 4000
    elif han >= 6: base = 3000
    elif han >= 5: base = 2000
    else:
        base = fu * (2 ** (2 + han))
        if base > 2000: base = 2000

    total_score = 0
    if is_tsumo:
        if is_host:
            unit = math.ceil((base * 2) / 100) * 100
            total_score = unit * 3
        else:
            child_pay = math.ceil(base / 100) * 100
            parent_pay = math.ceil((base * 2) / 100) * 100
            total_score = child_pay * 2 + parent_pay
    else:
        mult = 6 if is_host else 4
        total_score = math.ceil((base * mult) / 100) * 100

    return int(total_score)

# ---------------------------------------------------------------
# [Classes] 게임 및 로그 객체
# ---------------------------------------------------------------

class game(object):
    __slots__ = ['jsonObj', 'players', 'logs'] 
    
    def __init__(self, jsonObj, name_map=None):
        self.jsonObj = jsonObj
        
        raw_names = self.jsonObj.get("name", [])
        sx_list = self.jsonObj.get("sx", [])
        dan_list = self.jsonObj.get("dan", [])
        rate_list = self.jsonObj.get("rate", [])
        sc_list = self.jsonObj.get("sc", [])

        self.players = []
        for i in range(len(raw_names)):
            original_name = raw_names[i]
            display_name = name_map.get(original_name, original_name) if name_map else original_name
            
            p_sex = sx_list[i] if i < len(sx_list) else 'N/A'
            p_dan = dan_list[i] if i < len(dan_list) else 0
            p_rate = rate_list[i] if i < len(rate_list) else 0.0
            p_score = sc_list[i*2] if (i*2) < len(sc_list) else 0
            p_point = sc_list[i*2+1] if (i*2+1) < len(sc_list) else 0.0

            self.players.append(player(display_name, p_sex, p_dan, p_rate, p_score, p_point, i))
        
        orders = [(self.players[i].score + i * 0.1, self.players[i]) for i in range(len(self.players))]
        orders.sort(reverse=True)
        for i in range(len(self.players)): orders[i][1].rank = i + 1

        if "log" in self.jsonObj and self.jsonObj["log"]:
            self.logs = [log(logObj, len(self.jsonObj["name"])) for logObj in self.jsonObj["log"]]
        else:
            self.logs = []

    def getPlayerIndex_ByName(self, aliases):
        search_list = aliases if isinstance(aliases, list) else [aliases]
        for pl in self.players:
            if pl.name in search_list: return pl.index
        return -1

class player(object):
    __slots__ = ['name', 'sex', 'dan', 'rate', 'score', 'point', 'rank', 'index']
    def __init__(self, name, sex, dan, rate, score, point, index):
        self.name = name
        self.sex = sex
        self.dan = dan
        self.rate = rate
        self.score = score
        self.point = point
        self.index = index
        self.rank = -1

class log(object):
    __slots__ = ['logObj', '_playerSum', '_winnerIndex', '_loserIndex', 
                 '_endScore', '_fan', '_dora', '_dora_outer', '_dora_inner', '_dora_akai']

    def __init__(self, logObj, playerSum):
        self.logObj = logObj
        while self.logObj and not self.logObj[-1]: self.logObj.pop()
        self._playerSum = playerSum
        
        self._winnerIndex = []
        self._loserIndex = []
        if not self.isDraw:
            for row in self.changeScore:
                for i in range(self.playerSum):
                    if row[i] > 0: self._winnerIndex.append(i)
                    elif row[i] < 0: self._loserIndex.append(i)

        self._endScore = []
        for i in range(self.playerSum):
            temp = self.startScore[i]
            for sc in self.changeScore:
                temp += sc[i]
            self._endScore.append(temp)

        self._fan = []
        for lst in self.yakus:
            temp = 0
            for yaku in lst:
                m = re.findall(r"\d{1,2}", yaku)
                if m: temp += int(m[0])
            self._fan.append(temp)

        self._dora = []
        self._dora_outer = []
        self._dora_inner = []
        self._dora_akai = []

        if not self.isDraw:
            for lst in self.yakus:
                d_outer, d_inner, d_akai = 0, 0, 0
                for yaku in lst:
                    nums = re.findall(r"\d+", yaku)
                    val = int(nums[0]) if nums else 0

                    if "Dora" in yaku or "ドラ" in yaku:
                        if not ("Ura" in yaku or "裏" in yaku or "Red" in yaku or "赤" in yaku):
                            d_outer += val
                    if "Ura Dora" in yaku or "裏ドラ" in yaku:
                        d_inner += val
                    if "Red Five" in yaku or "赤ドラ" in yaku:
                        d_akai += val
                
                self._dora_outer.append(d_outer)
                self._dora_inner.append(d_inner)
                self._dora_akai.append(d_akai)
                self._dora.append(d_outer + d_inner + d_akai)

        if self.isSomeoneZimo():
            self._loserIndex = []

    # -------------------------------------------------------------
    # [Core Logic] 리치 분석 (Type-Safe Fix)
    # -------------------------------------------------------------
    def count_visible_tiles(self, turn_limit):
        visible = {}
        for p in range(self._playerSum):
            discards = self.logObj[6 + p * 3]
            for idx, d in enumerate(discards):
                if idx > turn_limit: break
                
                # [수정] safe_int 사용하여 문자열/숫자 모두 정수로 변환
                val = safe_int(d)
                if not isinstance(val, int): continue # 변환 실패 시 스킵

                if val == 60: continue
                
                # 이제 val은 무조건 int이므로 안전하게 연산 가능
                norm = (val - 51) * 10 + 5 if val > 50 else val - 10
                visible[norm] = visible.get(norm, 0) + 1
        return visible

    def get_richi_data(self, player_index):
        discards = self.logObj[6 + player_index * 3]
        is_richi = False
        richi_turn = -1
        for idx, d in enumerate(discards):
            if isinstance(d, str) and "r" in d:
                is_richi = True; richi_turn = idx; break
        if not is_richi: return None

        is_first = True
        for p in range(self._playerSum):
            if p == player_index: continue
            other_discards = self.logObj[6 + p * 3]
            for idx, d in enumerate(other_discards):
                if isinstance(d, str) and "r" in d:
                    if idx < richi_turn: is_first = False
                    break
        
        player_hand = generate_hand_at_turn(self.logObj[4 + player_index * 3],
                                            self.logObj[5 + player_index * 3],
                                            self.logObj[6 + player_index * 3], richi_turn)
        
        waiting_list = calculate_waiting_tiles(player_hand)
        expected_vals = calculate_expected_values(player_hand, waiting_list, {'dora_count': 0})
        
        visible_tiles = self.count_visible_tiles(richi_turn)
        remaining_count = 0
        for w in waiting_list:
            tile = w['tile']
            used = player_hand.count(tile) + visible_tiles.get(tile, 0)
            left = 4 - used
            if left < 0: left = 0
            remaining_count += left

        return {
            "is_richi": True,
            "is_first": is_first,
            "is_multi_wait": expected_vals['wait_types'] >= 2,
            "remaining_count": remaining_count,
            "expected_fan": expected_vals['avg_han']
        }
    
    def get_dora_impact_score(self, player_index):
        """뒷도라로 인한 점수 변화량을 계산"""
        if self.isDraw or player_index not in self._winnerIndex: return 0
        
        result_data = self.logObj[4 + 3 * self._playerSum]
        if result_data[0] != "和了": return 0

        # 화료자의 win_info 찾기
        win_info = None
        win_order_idx = -1
        order = 0
        for i in range(2, len(result_data), 2):
            if i >= len(result_data): break
            info = result_data[i]
            if isinstance(info, list) and len(info) > 0 and info[0] == player_index:
                win_info = info
                win_order_idx = order
                break
            order += 1
        
        if not win_info or len(win_info) < 4: return 0
        
        # 뒷도라 개수 확인
        if win_order_idx < 0 or win_order_idx >= len(self._dora_inner): return 0
        dora_inner = self._dora_inner[win_order_idx]
        if dora_inner <= 0: return 0
        
        # 점수 문자열에서 판수/부수 추출 (예: "30符3飜3900点")
        score_str = win_info[3]
        
        fan = 0
        fu = 30  # 기본값
        is_tsumo = '-' in score_str or '∀' in score_str
        is_host = self.isHost(player_index)
        
        # 판수 추출
        fan_match = re.findall(r'(\d+)飜', score_str)
        if fan_match:
            fan = int(fan_match[0])
        
        # 부수 추출
        fu_match = re.findall(r'(\d+)符', score_str)
        if fu_match:
            fu = int(fu_match[0])
        
        # 만관 이상 처리 (飜 없이 "満貫", "跳満" 등으로 표기)
        if fan == 0:
            if '満貫' in score_str: fan = 5
            elif '跳満' in score_str: fan = 6
            elif '倍満' in score_str: fan = 8
            elif '三倍満' in score_str: fan = 11
            elif '役満' in score_str: fan = 13
            else: return 0
        
        if fan <= 0: return 0
        
        # 원래 점수 vs 뒷도라 제외 점수
        ori_score = calculate_score_points(fan, fu, is_host, is_tsumo)
        reduced_score = calculate_score_points(fan - dora_inner, fu, is_host, is_tsumo)
        
        return ori_score - reduced_score

    # -------------------------------------------------------------
    # [Properties]
    # -------------------------------------------------------------
    @property
    def playerSum(self): return self._playerSum
    @property
    def result(self): return self.logObj[4 + 3 * self._playerSum][0]
    @property
    def isDraw(self): return self.result != u'和了'
    
    @property
    def winnerIndex(self): return self._winnerIndex
    @property
    def loserIndex(self): return self._loserIndex

    @property
    def changeScore(self):
        resultObj = self.logObj[4 + 3 * self._playerSum]
        if self.isDraw:
            return [resultObj[1]] if len(resultObj) > 1 else [[0]*self._playerSum]
        return resultObj[1::2]
    @property
    def yakus(self):
        if self.isDraw: return []
        resultObj = self.logObj[4 + 3 * self._playerSum]
        return [lst[4:] for lst in resultObj[2::2]]
    @property
    def startScore(self): return self.logObj[1]
    @property
    def endScore(self): return self._endScore
    @property
    def fan(self): return self._fan
    
    @property
    def dora(self): return self._dora
    @property
    def dora_outer(self): return self._dora_outer
    @property
    def dora_inner(self): return self._dora_inner
    @property
    def dora_akai(self): return self._dora_akai

    @property
    def gameWindIndex(self): return self.logObj[0][0]
    @property
    def gameRoundIndex(self): return self.logObj[0][1]

    def isSomeoneZimo(self):
        if self.isDraw or len(self.changeScore) != 1: return False
        pls, mus = 0, 0
        for sc in self.changeScore[0]:
            if sc > 0: pls += 1
            elif sc < 0: mus += 1
        return pls == 1 and mus > 1 

    def isHost(self, playerIndex): return (self.gameWindIndex) % 4 == playerIndex
    
    def isFulu(self, playerIndex):
        for cID in self.logObj[5 + playerIndex * 3]:
            if isinstance(cID, str) and any(x in cID for x in ['c', 'p', 'k']): return True
        return False

    def isRichi(self, playerIndex):
        for cID in self.logObj[6 + playerIndex * 3]:
            if isinstance(cID, str) and "r" in cID: return True
        return False
        
    def isWin(self, playerIndex):
        if self.isDraw: return False
        for sc in self.changeScore:
            if sc[playerIndex] > 0: return True
        return False

    def isChong(self, playerIndex):
        if self.isDraw or self.isSomeoneZimo(): return False
        for sc in self.changeScore:
            if sc[playerIndex] < 0: return True
        return False

    def isZimo(self, playerIndex):
        if not self.isSomeoneZimo(): return False
        return self.changeScore[0][playerIndex] > 0

        if '飜' in score[0]:
            fu = int(score[0].split('符')[0])
        if '-' in score[0] or '∀' in score[0]:
            isTsumo = True
        oriScore = CalcScore(fan, fu, isHost, isTsumo)
        lastScore = CalcScore(fan - dora_inner, fu, isHost, isTsumo)
        return oriScore-lastScore
        
    def isKazoe(self):
        score = self.logObj[16][2][3]
        if '数え役満' in score:
            return True
        return False
            
    @property
    def doraPtr(self):
        return self._doraPtr

    def isDoubleChong(self, playerIndex):
        return len(self.changeScore) if self.isChong(playerIndex) else 0

    def isOtherZimo(self, playerIndex):
        return self.isSomeoneZimo() and not self.isZimo(playerIndex)

    def isDama(self, playerIndex):
        return self.isWin(playerIndex) and not self.isFulu(playerIndex) and not self.isRichi(playerIndex)

    def endRound(self, playerIndex):
        return len(self.logObj[6 + playerIndex * 3])

    @property
    def dora_akai(self):
        return self._dora_akai      

    @property
    def playerSum(self):
        return self._playerSum
    
    @property
    def name(self):
        return log.gameIndexDes(self.logObj[0])

    @property
    def isDraw(self):
        return self.result != u'和了'
    
    @property
    def _resultObj(self):
        return self.logObj[4 + 3 * self._playerSum]

    @property
    def result(self):
        return self._resultObj[0]

    @property
    def changeScoreDes(self):
        if self.isDraw:
            return [self.result]
        else:
            return [lst[3] for lst in self._resultObj[2::2]]
    
    @property
    def fan(self):
        return self._fan   

    @property
    def yakus(self):
        if self.isDraw:
            return []
        else:
            return [lst[4:] for lst in self._resultObj[2::2]]

    @property
    def yakuNames(self):
        return [[n[:-4] for n in yakus if not "Dora" in n or not "ドラ" in n]
                for yakus in self.yakus]
    
    @property
    def gameWindIndex(self):
        return self.logObj[0][0]

    @property
    def gameRoundIndex(self):
        return self.logObj[0][1]

    @property
    def winnerIndex(self):
        return self._winnerIndex

    @property
    def loserIndex(self):
        return self._loserIndex
    
    @property
    def startScore(self):
        return self.logObj[1]
        
    @property
    def changeScore(self):
        if self.isDraw:
            if len(self._resultObj) > 1:
                return [self._resultObj[1]]
            else:
                return [[0] * self.playerSum]
        else:
            return self._resultObj[1::2]

    @property
    def endScore(self):
        return self._endScore  

    @staticmethod
    def gameIndexDes(indexTuple):
        changfeng = MJCard.dxnb[indexTuple[0] / 4 + 1]
        changshu  = MJCard.chnum(indexTuple[0] % 4 + 1)
        changju   = indexTuple[1]
        return u"%s%s局%s本场" % (changfeng, changshu, changju)       
    
class MJCard(object):
    """docstring for MJCard"""
    PostfixNames = [
        u"", u"萬", u"筒", u"索", u""
    ]
    WordPerfixNames = [
    
        u"", u"東", u"南", u"西", u"北", u"白", u"發", u"中"
    ]
    dxnb = [
        u"", u"東", u"南", u"西", u"北"
    ]
    numb = [
        u"零", u"一", u"二", u"三", u"四", u"五", u"六", u"七", u"八", u"九"
    ]
    numx = [
        u"", u"十", u"百", u"千", u"万", u"十万", u"百万", u"千万", u"亿"
    ]

    def __init__(self, ID, akai = False, zmgr = False):
        super(MJCard, self).__init__()
        self.ID = int(ID)
        self.akai = akai
        self.zmgr = zmgr
        self.dora_outer = 0
        self.dora_inner = 0

        text = u"赤" if self.akai else u""
        if self.ID > 40:
            text += MJCard.WordPerfixNames[self.ID % 10]
        else:
            text += MJCard.chnum(self.ID % 10) + MJCard.PostfixNames[int(self.ID / 10)]
        self._name = text

    def __str__(self):
        return self._name.encode("utf-8")
    
    def __lt__(self, target):
        return self.ID < target.ID

    def PointTo(self, target):
        if not target:
            return False
        if self.ID / 10 != target.ID / 10:
            return False
        else:
            distance = target.ID - self.ID
            return distance == 1 or distance == -8

    @property
    def name(self):
        return self._name

    @property
    def dora(self):
        return self.dora_inner + self.dora_outer

    @staticmethod
    def chnum(num):
        num = abs(int(num))
        if num == 0:
            return MJCard.numb[num]
        s = u""
        upper = False
        for lvl in range(10, -1, -1):
            x = int(num / (10 ** lvl))
            if x:
                upper = True
                num -= x * (10 ** lvl)
                s += MJCard.numb[x] + MJCard.numx[lvl]
            elif upper:
                upper = False
                s += MJCard.numb[x]
        return s
