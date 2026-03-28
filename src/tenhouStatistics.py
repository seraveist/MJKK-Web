"""
tenhouStatistics.py — 리팩토링 v3

변경사항:
  1. Statistic → RunningStatistic (메모리 O(N) → O(1))
  2. PlayerStatistic.__init__ 루프 → process_game() 메서드 추출
  3. rank → 전용 필드 (rank_counts, rank_sum, rank_history)
  4. 기존 __init__(games, playerName) 호출 100% 호환 유지

[중요] dict() 출력은 리팩토링 전과 완전히 동일해야 합니다.
       tests/verify_refactor.py로 검증하세요.
"""
import json


class RunningStatistic(object):
    """
    경량 통계 클래스 — raw 리스트 대신 집계값만 유지.
    
    기존 Statistic의 메서드를 전부 지원하되,
    group()/groupPercent()/per2over()는 제거 (미사용).
    """
    __slots__ = ['count', '_sum', '_min', '_max', 
                 'nz_count', 'nz_sum', 'bool_count', 'valid_count']
    
    def __init__(self):
        self.count = 0
        self._sum = 0
        self._min = float('inf')
        self._max = float('-inf')
        self.nz_count = 0
        self.nz_sum = 0
        self.bool_count = 0
        self.valid_count = 0

    def add(self, data):
        if data is None:
            return
        
        self.valid_count += 1
        
        if data is not False and data != 0:
            self.bool_count += 1
            self.nz_count += 1
            self.nz_sum += data
        
        numeric = data if isinstance(data, (int, float)) else (1 if data else 0)
        self.count += 1
        self._sum += numeric
        if numeric < self._min:
            self._min = numeric
        if numeric > self._max:
            self._max = numeric

    def avg(self):
        return float(self._sum) / self.valid_count if self.valid_count else 0

    def min(self):
        return self._min if self.valid_count and self._min != float('inf') else 0

    def max(self):
        return self._max if self.valid_count and self._max != float('-inf') else 0

    def sum(self):
        return self._sum

    def len(self):
        return self.valid_count

    def sum_not_zero(self):
        return self.nz_sum

    def len_not_zero(self):
        return self.nz_count

    def avg_not_zero(self):
        return float(self.nz_sum) / self.nz_count if self.nz_count else 0

    def avg_bool(self):
        return float(self.bool_count) / self.valid_count if self.valid_count else 0


# 기존 코드 호환
Statistic = RunningStatistic


class PlayerStatistic(object):
    """
    플레이어 통계.
    
    사용법 1 (기존 호환):
        ps = PlayerStatistic(games=total_games, playerName=user)
        
    사용법 2 (single-pass):
        ps = PlayerStatistic(games=None, playerName=user)
        ps.process_game(game)
    """
    def __init__(self, games, playerName):
        super(PlayerStatistic, self).__init__()
        
        if isinstance(playerName, dict):
            self.playerName = playerName['name']
            self._aliases = playerName.get('aliases', [playerName['name']])
        else:
            self.playerName = playerName
            self._aliases = [playerName]

        # ── rank 전용 필드 ──
        self.rank_counts = [0, 0, 0, 0, 0]  # [unused, 1위, 2위, 3위, 4위]
        self.rank_sum = 0
        self.rank_history = []
        
        self.wind_rank_sum = [0, 0, 0, 0]
        self.wind_rank_count = [0, 0, 0, 0]

        # ── 일반 통계 ──
        self.endScore = RunningStatistic()
        self.minusScore = RunningStatistic()
        self.minusOther = RunningStatistic()
        self.minusOther_sum = RunningStatistic()
        
        self.dora = RunningStatistic()
        self.dora_outer = RunningStatistic()
        self.dora_inner = RunningStatistic()
        self.dora_inner_eff = RunningStatistic()
        self.dora_akai = RunningStatistic()
        
        self.winGame = RunningStatistic()
        self.winGame_host = RunningStatistic()
        self.winGame_zimo = RunningStatistic()
        self.winGame_rong = RunningStatistic()
        self.winGame_fulu = RunningStatistic()
        self.winGame_richi = RunningStatistic()
        self.winGame_score = RunningStatistic()
        self.winGame_round = RunningStatistic()
        self.winGame_dama = RunningStatistic()
        
        self.fulu = RunningStatistic()
        self.fulu_winGame = RunningStatistic()
        self.fulu_zimo = RunningStatistic()
        self.fulu_rong = RunningStatistic()
        self.fulu_chong = RunningStatistic()
        self.fulu_score = RunningStatistic()
        
        self.chong = RunningStatistic()
        self.chong_fulu = RunningStatistic()
        self.chong_richi = RunningStatistic()
        self.chong_host = RunningStatistic()
        self.chong_score = RunningStatistic()
        
        self.dehost = RunningStatistic()
        self.dehost_score = RunningStatistic()
        
        self.otherZimo = RunningStatistic()
        self.otherZimo_score = RunningStatistic()
        
        self.richi = RunningStatistic()
        self.richi_score = RunningStatistic()
        self.richi_winGame = RunningStatistic()
        self.richi_zimo = RunningStatistic()
        self.richi_rong = RunningStatistic()
        self.richi_yifa = RunningStatistic()
        self.richi_chong = RunningStatistic()
        self.richi_otherZimo = RunningStatistic()
        self.richi_draw = RunningStatistic()
        self.richi_inner_dora = RunningStatistic()
        
        self.richi_count_total = 0
        self.richi_first_sum = 0
        self.richi_multi_sum = 0
        self.richi_remain_sum = 0
        self.richi_fan_sum = 0
        
        self.kuksu = 0
        self.yakus = dict()

        # 기존 호환: games가 주어지면 바로 계산
        if games is not None:
            for game in games:
                self.process_game(game)

    def process_game(self, game):
        """단일 게임의 통계를 누적."""
        playerIndex = game.getPlayerIndex_ByName(self._aliases)
        if playerIndex == -1:
            return

        rank = game.players[playerIndex].rank
        self.rank_counts[rank] += 1
        self.rank_sum += rank
        self.rank_history.append(rank)
        
        if 0 <= playerIndex <= 3:
            self.wind_rank_sum[playerIndex] += rank
            self.wind_rank_count[playerIndex] += 1
        
        self.endScore.add(game.players[playerIndex].score)
        self.minusScore.add(game.players[playerIndex].score < 0)
        
        if game.logs:
            if playerIndex in game.logs[-1].winnerIndex:
                mo_sum = sum([pl.score < 0 for pl in game.players if pl.index != playerIndex])
            else:
                mo_sum = 0
            self.minusOther.add(mo_sum > 0)
            self.minusOther_sum.add(mo_sum)

            for log in game.logs:
                self._process_round(log, playerIndex)

    def _process_round(self, log, playerIndex):
        """단일 국(round) 처리"""
        isDraw = log.isDraw
        isWin = log.isWin(playerIndex)
        isYifa = log.isYifa(playerIndex)
        isZimo = log.isZimo(playerIndex)
        isRong = log.isRong(playerIndex)
        isChong = log.isChong(playerIndex)
        isFulu = log.isFulu(playerIndex)
        isRichi = log.isRichi(playerIndex)
        isHost = log.isHost(playerIndex)
        isOtherZimo = log.isOtherZimo(playerIndex)
        isDama = log.isDama(playerIndex)
        endRound = log.endRound(playerIndex)
        scoreChange = sum([sc[playerIndex] for sc in log.changeScore])
        self.kuksu += len(log.changeScore)
        
        if isWin:
            if log.dora:
                try:
                    win_order_idx = log.winnerIndex.index(playerIndex)
                    self.dora.add(log.dora[win_order_idx])
                    self.dora_outer.add(log.dora_outer[win_order_idx])
                    self.dora_inner.add(log.dora_inner[win_order_idx])
                    self.dora_akai.add(log.dora_akai[win_order_idx])
                except ValueError:
                    pass

        self.winGame.add(isWin)
        if isWin:
            self.winGame_host.add(isHost and scoreChange)
            self.winGame_zimo.add(isZimo and scoreChange)
            self.winGame_rong.add(isRong and scoreChange)
            self.winGame_fulu.add(isFulu and scoreChange)
            self.winGame_richi.add(isRichi and scoreChange)
            self.winGame_score.add(scoreChange)
            self.winGame_round.add(endRound)
            self.winGame_dama.add(isDama and scoreChange)
            
            for i in range(len(log.changeScore)):
                if log.changeScore[i][playerIndex] > 0:
                    for yaku_str in log.yakus[i]:
                        if "Dora" in yaku_str or "ドラ" in yaku_str or "Red" in yaku_str or "赤" in yaku_str:
                            continue
                        clean_name = yaku_str.split('(')[0]
                        self.yakus[clean_name] = self.yakus.get(clean_name, 0) + 1
            
            result_data = log.logObj[4 + 3 * log.playerSum]
            for entry in result_data[2::2]:
                if isinstance(entry, list) and len(entry) > 3 and entry[0] == playerIndex:
                    if '数え役満' in str(entry[3]):
                        self.yakus['数え役満'] = self.yakus.get('数え役満', 0) + 1
                    break

        self.fulu.add(isFulu)
        if isFulu:
            self.fulu_zimo.add(isZimo and scoreChange)
            self.fulu_rong.add(isRong and scoreChange)
            self.fulu_chong.add(isChong and scoreChange)
            self.fulu_score.add(scoreChange)
            self.fulu_winGame.add(isWin and scoreChange)
        
        self.chong.add(isChong)
        if isChong:
            self.chong_fulu.add(isFulu and scoreChange)
            self.chong_richi.add(isRichi and scoreChange)
            self.chong_host.add(isHost and scoreChange)
            self.chong_score.add(scoreChange)
        
        self.otherZimo.add(isOtherZimo)
        if isOtherZimo:
            self.otherZimo_score.add(scoreChange)
            self.dehost.add(isHost)
            if isHost:
                self.dehost_score.add(scoreChange)
        
        self.richi.add(isRichi)
        if isRichi:
            self.richi_score.add(scoreChange)
            self.richi_winGame.add(isWin and scoreChange)
            self.richi_zimo.add(isZimo and scoreChange)
            self.richi_rong.add(isRong and scoreChange)
            self.richi_yifa.add(isYifa and scoreChange)
            self.richi_chong.add(isChong and scoreChange)
            self.richi_otherZimo.add(isOtherZimo and scoreChange)
            self.richi_draw.add(isDraw and scoreChange)
            
            if isWin:
                ura_count = 0
                if log.dora:
                    try:
                        win_order_idx = log.winnerIndex.index(playerIndex)
                        ura_count = log.dora_inner[win_order_idx]
                    except (ValueError, IndexError):
                        ura_count = 0
                self.richi_inner_dora.add(ura_count)
                impact_score = log.get_dora_impact_score(playerIndex)
                self.dora_inner_eff.add(impact_score)
            
            r_data = log.get_richi_data(playerIndex)
            if r_data and r_data['is_richi']:
                self.richi_count_total += 1
                if r_data['is_first']:
                    self.richi_first_sum += 1
                if r_data['is_multi_wait']:
                    self.richi_multi_sum += 1
                self.richi_remain_sum += r_data['remaining_count']
                self.richi_fan_sum += r_data['expected_fan']

    def _games_count(self):
        return sum(self.rank_counts)

    def dict(self):
        games = self._games_count()
        r_cnt = self.richi_count_total if self.richi_count_total > 0 else 1
        
        def _wind_avg(idx):
            return self.wind_rank_sum[idx] / self.wind_rank_count[idx] if self.wind_rank_count[idx] else 0
        
        total_avg = self.rank_sum / games if games else 0
        
        return dict(
            name = self.playerName,
            games = games,
            kuksu = self.kuksu,
            kuksuji = (self.endScore.avg() - 25000) / self.kuksu * games if self.kuksu > 0 else 0,
            
            total = dict(avg = total_avg),
            east = dict(avg = _wind_avg(0)),
            south = dict(avg = _wind_avg(1)),
            west = dict(avg = _wind_avg(2)),
            north = dict(avg = _wind_avg(3)),
            endScore = dict(avg = self.endScore.avg(), max = self.endScore.max(), min = self.endScore.min()),
            minusScore = dict(avg = self.minusScore.avg(), sum = self.minusScore.sum()),
            minusOther = dict(avg = self.minusOther.avg(), sum = self.minusOther.sum(), plr = self.minusOther_sum.sum()),
            
            dora = dict(avg = self.dora.avg(), per = self.dora.avg_bool(), max = self.dora.max()),
            dora_outer = dict(avg = self.dora_outer.avg(), per = self.dora_outer.avg_bool(), max = self.dora_outer.max()),
            dora_inner = dict(avg = self.richi_inner_dora.avg(), per = self.richi_inner_dora.avg_bool(), max = self.richi_inner_dora.max()),
            dora_inner_eff = dict(avg = self.dora_inner_eff.avg_not_zero(), per = self.dora_inner_eff.avg_bool(), max = self.dora_inner_eff.max()),
            dora_akai = dict(avg = self.dora_akai.avg(), per = self.dora_akai.avg_bool(), max = self.dora_akai.max()),
            
            winGame = dict(avg = self.winGame.avg(), len = self.winGame.sum()),
            winGame_score = dict(avg = self.winGame_score.avg(), max = self.winGame_score.max()),
            winGame_host = dict(avg = self.winGame_host.avg_not_zero(), max = self.winGame_host.max(), per = self.winGame_host.avg_bool()),
            winGame_zimo = dict(avg = self.winGame_zimo.avg_not_zero(), max = self.winGame_zimo.max(), per = self.winGame_zimo.avg_bool()),
            winGame_rong = dict(avg = self.winGame_rong.avg_not_zero(), max = self.winGame_rong.max(), per = self.winGame_rong.avg_bool()),
            winGame_fulu = dict(avg = self.winGame_fulu.avg_not_zero(), max = self.winGame_fulu.max(), per = self.winGame_fulu.avg_bool()),
            winGame_richi = dict(avg = self.winGame_richi.avg_not_zero(), max = self.winGame_richi.max(), per = self.winGame_richi.avg_bool()),
            winGame_dama = dict(avg = self.winGame_dama.avg_not_zero(), max = self.winGame_dama.max(), per = self.winGame_dama.avg_bool()),
            winGame_round = dict(avg = self.winGame_round.avg_not_zero(), min = self.winGame_round.min()),
            
            fulu = dict(avg = self.fulu.avg(), len = self.fulu.sum()),
            fulu_winGame = dict(per = self.fulu_winGame.avg_bool()),
            fulu_score = dict(avg = self.fulu_score.avg(), max = self.fulu_score.max(), min = self.fulu_score.min()),
            fulu_zimo = dict(avg = self.fulu_zimo.avg_not_zero(), max = self.fulu_zimo.max(), per = self.fulu_zimo.avg_bool()),
            fulu_rong = dict(avg = self.fulu_rong.avg_not_zero(), max = self.fulu_rong.max(), per = self.fulu_rong.avg_bool()),
            fulu_chong = dict(avg = self.fulu_chong.avg_not_zero(), min = self.fulu_chong.min(), per = self.fulu_chong.avg_bool()),
            
            chong = dict(avg = self.chong.avg(), len = self.chong.sum()),
            chong_score = dict(avg = self.chong_score.avg(), min = self.chong_score.min()),
            chong_host = dict(avg = self.chong_host.avg_not_zero(), min = self.chong_host.min(), per = self.chong_host.avg_bool()),
            chong_fulu = dict(avg = self.chong_fulu.avg_not_zero(), min = self.chong_fulu.min(), per = self.chong_fulu.avg_bool()),
            chong_richi = dict(avg = self.chong_richi.avg_not_zero(), min = self.chong_richi.min(), per = self.chong_richi.avg_bool()),
            
            dehost = dict(avg = self.dehost.avg(), len = self.dehost.sum()),
            dehost_score = dict(avg = self.dehost_score.avg(), min = self.dehost_score.min()),
            
            otherZimo = dict(avg = self.otherZimo.avg(), len = self.otherZimo.sum()),
            otherZimo_score = dict(avg = self.otherZimo_score.avg(), min = self.otherZimo_score.min()),
            
            richi = dict(avg = self.richi.avg(), len = self.richi.sum()),
            richi_winGame = dict(per = self.richi_winGame.avg_bool()),
            richi_score = dict(avg = self.richi_score.avg(), min = self.richi_score.min(), max = self.richi_score.max()),
            richi_yifa = dict(avg = self.richi_yifa.avg_not_zero(), max = self.richi_yifa.max(), per = self.richi_yifa.avg_bool()),
            richi_rong = dict(avg = self.richi_rong.avg_not_zero(), max = self.richi_rong.max(), per = self.richi_rong.avg_bool()),
            richi_zimo = dict(avg = self.richi_zimo.avg_not_zero(), max = self.richi_zimo.max(), per = self.richi_zimo.avg_bool()),
            richi_chong = dict(avg = self.richi_chong.avg_not_zero(), min = self.richi_chong.min(), per = self.richi_chong.avg_bool()),
            richi_draw = dict(per = self.richi_draw.avg_bool()),
            richi_otherZimo = dict(avg = self.richi_otherZimo.avg_not_zero(), min = self.richi_otherZimo.min(), per = self.richi_otherZimo.avg_bool()),
            
            richi_first = dict(per = self.richi_first_sum / r_cnt),
            richi_machi = dict(per = self.richi_multi_sum / r_cnt),
            richi_machi_count = dict(avg = self.richi_remain_sum / r_cnt),
            richi_fan = dict(avg = self.richi_fan_sum / r_cnt),
            
            total_first_count = self.rank_counts[1],
            total_second_count = self.rank_counts[2],
            total_third_count = self.rank_counts[3],
            total_fourth_count = self.rank_counts[4],
            yakus = [[self.yakus[y], y] for y in self.yakus],
        )

    def json(self):
        return json.dumps(self.dict())
