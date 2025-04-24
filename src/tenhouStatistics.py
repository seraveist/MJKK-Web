import json, math, datetime

class Statistic(object):
    """docstring for Statistic"""
    def __init__(self):
        super(Statistic, self).__init__()
        self.datas = list()

    def add(self, data):
        self.datas.append(data)

    def max(self):
        if not self.datas:
            return 0
        return max(self.datas)

    def min(self):
        if not self.datas:
            return 0
        return min(self.datas)

    def sum(self):
        if not self.datas:
            return 0
        return sum(self.datas)

    def sum_not_zero(self):
        s = 0
        for data in self.datas:
            if data != False:
                s += data
        return s

    def len(self):
        return len(self.datas)

    def len_not_zero(self):
        c = 0
        for data in self.datas:
            if data != False:
                c += 1
        return c

    def avg(self):
        if not self.datas:
            return 0
        return float(sum(self.datas)) / len(self.datas)

    def avg_not_zero(self):
        s, c = 0, 0
        for data in self.datas:
            if data != False:
                s += data
                c += 1
        if c:
            return float(s) / c
        else:
            return 0

    def avg_bool(self):
        if not self.datas:
            return 0
        s = 0
        for data in self.datas:
            if data != False:
                s += bool(data)
        return float(s) / len(self.datas)

    def group(self):
        temp = dict()
        for d in self.datas:
            temp[d] = temp.get(d, 0) + 1
        return temp

    def groupPercent(self):
        temp = self.group()
        for key in temp:
            temp[key] /= float(len(self.datas))
        return temp
    
    def per2over(self):
        filter = [ x for x in self.datas if x >= 2]
        if len(filter) == 0:
            return 0
        return len(filter) / len(self.datas)

class PlayerStatistic(object):
    """docstring for Statistic"""
    def __init__(self, games, playerName):
        super(PlayerStatistic, self).__init__()
        self.games = games
        self.playerName = playerName['name']

        self.rank                    = Statistic()          #평균순위,1234위율
        self.east_rank               = Statistic()          #동가_시작_평균순위,1234위율
        self.south_rank              = Statistic()          #남가_시작_평균순위,1234위율
        self.west_rank               = Statistic()          #서가_시작_평균순위,1234위율
        self.north_rank              = Statistic()          #북가_시작_평균순위,1234위율
        self.endScore                = Statistic()          #최종점수
        self.minusScore              = Statistic()          #토비점수
        self.minusOther              = Statistic()          #상대토비
        self.minusOther_sum          = Statistic()          #상대토비_횟수
        self.dora                    = Statistic()          #도라
        self.dora_outer              = Statistic()          #표시도라
        self.dora_inner              = Statistic()          #뒷도라
        self.dora_inner_eff          = Statistic()          #뒷도라 점수변화
        self.dora_akai               = Statistic()          #적도라
        self.winGame                 = Statistic()          #화료
        self.winGame_host            = Statistic()          #화료_오야
        self.winGame_zimo            = Statistic()          #화료_쯔모
        self.winGame_rong            = Statistic()          #화료_론
        self.winGame_fulu            = Statistic()          #화료_후로
        self.winGame_richi           = Statistic()          #화료_리치
        self.winGame_score           = Statistic()          #화료_점수
        self.winGame_round           = Statistic()          #화료_순
        self.winGame_dama            = Statistic()          #화료_다마
        self.fulu                    = Statistic()          #후로
        self.fulu_winGame            = Statistic()          #후로_화료
        self.fulu_zimo               = Statistic()          #후로_쯔모
        self.fulu_rong               = Statistic()          #후로_론
        self.fulu_chong              = Statistic()          #후로_방총
        self.fulu_score              = Statistic()          #후로_점수
        self.chong                   = Statistic()          #방총
        self.chong_fulu              = Statistic()          #방총_후로
        self.chong_richi             = Statistic()          #방총_리치
        self.chong_host              = Statistic()          #방총_自亲
        self.chong_score             = Statistic()          #방총_점수
        self.dehost                  = Statistic()          #오야카부리
        self.dehost_score            = Statistic()          #오야카부리_점수
        self.otherZimo               = Statistic()          #피쯔모
        self.otherZimo_score         = Statistic()          #피쯔모_점수
        self.richi                   = Statistic()          #리치
        self.richi_score             = Statistic()          #리치_점수
        self.richi_winGame           = Statistic()          #리치_화료
        self.richi_zimo              = Statistic()          #리치_쯔모
        self.richi_rong              = Statistic()          #리치_론
        self.richi_yifa              = Statistic()          #리치_일발
        self.richi_chong             = Statistic()          #리치_방총
        self.richi_otherZimo         = Statistic()          #리치_피쯔모
        self.richi_draw              = Statistic()          #리치_유국
        self.richi_inner_dora        = Statistic()          #리치_뒷도라
        self.richi_machi             = Statistic()          #리치_대기
        self.richi_first             = Statistic()          #리치_선제율

        self.yakus = dict()
        kazoe = 0
        
        for game in self.games:
            playerIndex = game.getPlayerIndex_ByName(playerName.get('aliases'))
            if playerIndex == -1:
                continue

            #with game
            self.rank.add(game.players[playerIndex].rank)
            if playerIndex == 0:
                self.east_rank.add(game.players[playerIndex].rank)
            elif playerIndex == 1:
                self.south_rank.add(game.players[playerIndex].rank)
            elif playerIndex == 2:
                self.west_rank.add(game.players[playerIndex].rank)
            elif playerIndex == 3:
                self.north_rank.add(game.players[playerIndex].rank)
            self.endScore.add(game.players[playerIndex].score)
            self.minusScore.add(game.players[playerIndex].score < 0)

            if playerIndex in game.logs[-1].winnerIndex:
                minusOther_sum = sum([pl.score < 0 for pl in game.players if pl.index != playerIndex])
            else:
                minusOther_sum = 0
            self.minusOther.add(minusOther_sum > 0)
            self.minusOther_sum.add(minusOther_sum)

            #with log
            for log in game.logs:
                isDraw        = log.isDraw
                isWin         = log.isWin(playerIndex)
                isYifa        = log.isYifa(playerIndex)
                isZimo        = log.isZimo(playerIndex)
                isRong        = log.isRong(playerIndex)
                isChong       = log.isChong(playerIndex)
                isFulu        = log.isFulu(playerIndex)
                isRichi       = log.isRichi(playerIndex)
                isHost        = log.isHost(playerIndex)
                isOtherZimo   = log.isOtherZimo(playerIndex)
                isDama        = log.isDama(playerIndex)
                endRound      = log.endRound(playerIndex)
                score         = log.endScore[playerIndex]
                scoreChange   = sum([sc[playerIndex] for sc in log.changeScore])
                index = 0
                for sc in log.changeScore:
                    if sc[playerIndex] > 0:
                        index = 0

                if isWin:
                    self.dora.add(log.dora[index])
                    self.dora_outer.add(log.dora_outer[index])
                    self.dora_akai.add(log.dora_akai[index])
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
                            for yaku in log.yakuNames[i]:
                                self.yakus[yaku] = self.yakus.get(yaku, 0) + 1
                            if log.isKazoe() == True:
                                kazoe += 1

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
                    self.richi_machi.add(log.richiMachi(playerIndex))
                    self.richi_first.add(log.richiFirst(playerIndex))
                    self.dora_inner.add(isWin and log.dora_inner[index])
                    if isWin and log.dora_inner[index]:
                        self.dora_inner_eff.add(log.doraInnerScore(playerIndex, log.dora_inner[index]))
        if kazoe > 0:
            self.yakus['数え役満'] = kazoe
            
    def dict(self):
        return dict(
            name                   = self.playerName,
            games                  = self.rank.len(),
            total                  = dict(avg = self.rank.avg()),
            east                   = dict(avg = self.east_rank.avg()),
            south                  = dict(avg = self.south_rank.avg()),
            west                   = dict(avg = self.west_rank.avg()),
            north                  = dict(avg = self.north_rank.avg()),
            endScore               = dict(avg = self.endScore.avg(),
                                          max = self.endScore.max(),
                                          min = self.endScore.min()),
            minusScore             = dict(avg = self.minusScore.avg(),
                                          sum = self.minusScore.sum()),
            minusOther             = dict(avg = self.minusOther.avg(),
                                          sum = self.minusOther.sum(),
                                          plr = self.minusOther_sum.sum()),
            dora                   = dict(avg = self.dora.avg(),
                                          per = self.dora.avg_bool(),
                                          max = self.dora.max()),
            dora_outer             = dict(avg = self.dora_outer.avg(),
                                          per = self.dora_outer.avg_bool(),
                                          max = self.dora_outer.max()),
            dora_inner             = dict(avg = self.dora_inner.avg(),
                                          per = self.dora_inner.avg_bool(),
                                          max = self.dora_inner.max()),
            dora_inner_eff         = dict(avg = self.dora_inner_eff.avg(),
                                          per = self.dora_inner_eff.avg_bool(),
                                          max = self.dora_inner_eff.max()),
            dora_akai             = dict(avg = self.dora_akai.avg(),
                                          per = self.dora_akai.avg_bool(),
                                          max = self.dora_akai.max()),
            winGame                = dict(avg = self.winGame.avg(),
                                          len = self.winGame.sum()),
            winGame_score          = dict(avg = self.winGame_score.avg(),
                                          max = self.winGame_score.max()),
            winGame_host           = dict(avg = self.winGame_host.avg_not_zero(),
                                          max = self.winGame_host.max(),
                                          per = self.winGame_host.avg_bool()),
            winGame_zimo           = dict(avg = self.winGame_zimo.avg_not_zero(),
                                          max = self.winGame_zimo.max(),
                                          per = self.winGame_zimo.avg_bool()),
            winGame_rong           = dict(avg = self.winGame_rong.avg_not_zero(),
                                          max = self.winGame_rong.max(),
                                          per = self.winGame_rong.avg_bool()),
            winGame_fulu           = dict(avg = self.winGame_fulu.avg_not_zero(),
                                          max = self.winGame_fulu.max(),
                                          per = self.winGame_fulu.avg_bool()),
            winGame_richi          = dict(avg = self.winGame_richi.avg_not_zero(),
                                          max = self.winGame_richi.max(),
                                          per = self.winGame_richi.avg_bool()),
            winGame_dama           = dict(avg = self.winGame_dama.avg_not_zero(),
                                          max = self.winGame_dama.max(),
                                          per = self.winGame_dama.avg_bool()),            
            winGame_round          = dict(avg = self.winGame_round.avg_not_zero(),
                                          min = self.winGame_round.min()),
            fulu                   = dict(avg = self.fulu.avg(),
                                          len = self.fulu.sum()),
            fulu_winGame           = dict(per = self.fulu_winGame.avg_bool()),
            fulu_score             = dict(avg = self.fulu_score.avg(),
                                          max = self.fulu_score.max(),
                                          min = self.fulu_score.min()),
            fulu_zimo              = dict(avg = self.fulu_zimo.avg_not_zero(),
                                          max = self.fulu_zimo.max(),
                                          per = self.fulu_zimo.avg_bool()),
            fulu_rong              = dict(avg = self.fulu_rong.avg_not_zero(),
                                          max = self.fulu_rong.max(),
                                          per = self.fulu_rong.avg_bool()),
            fulu_chong             = dict(avg = self.fulu_chong.avg_not_zero(),
                                          min = self.fulu_chong.min(),
                                          per = self.fulu_chong.avg_bool()),
            chong                  = dict(avg = self.chong.avg(),
                                          len = self.chong.sum()),
            chong_score            = dict(avg = self.chong_score.avg(),
                                          min = self.chong_score.min()),
            chong_host             = dict(avg = self.chong_host.avg_not_zero(),
                                          min = self.chong_host.min(),
                                          per = self.chong_host.avg_bool()),
            chong_fulu             = dict(avg = self.chong_fulu.avg_not_zero(),
                                          min = self.chong_fulu.min(),
                                          per = self.chong_fulu.avg_bool()),
            chong_richi            = dict(avg = self.chong_richi.avg_not_zero(),
                                          min = self.chong_richi.min(),
                                          per = self.chong_richi.avg_bool()),
            dehost                 = dict(avg = self.dehost.avg(),
                                          len = self.dehost.sum()),
            dehost_score           = dict(avg = self.dehost_score.avg(),
                                          min = self.dehost_score.min()),
            otherZimo              = dict(avg = self.otherZimo.avg(),
                                          len = self.otherZimo.sum()),
            otherZimo_score        = dict(avg = self.otherZimo_score.avg(),
                                          min = self.otherZimo_score.min()),
            richi                  = dict(avg = self.richi.avg(),
                                          len = self.richi.sum()),
            richi_winGame          = dict(per = self.richi_winGame.avg_bool()),
            richi_score            = dict(avg = self.richi_score.avg(),
                                          min = self.richi_score.min(),
                                          max = self.richi_score.max()),
            richi_yifa             = dict(avg = self.richi_yifa.avg_not_zero(),
                                          max = self.richi_yifa.max(),
                                          per = self.richi_yifa.avg_bool()),
            richi_rong             = dict(avg = self.richi_rong.avg_not_zero(),
                                          max = self.richi_rong.max(),
                                          per = self.richi_rong.avg_bool()),
            richi_zimo             = dict(avg = self.richi_zimo.avg_not_zero(),
                                          max = self.richi_zimo.max(),
                                          per = self.richi_zimo.avg_bool()),
            richi_chong            = dict(avg = self.richi_chong.avg_not_zero(),
                                          min = self.richi_chong.min(),
                                          per = self.richi_chong.avg_bool()),
            richi_draw             = dict(per = self.richi_draw.avg_bool()),
            richi_otherZimo        = dict(avg = self.richi_otherZimo.avg_not_zero(),
                                          min = self.richi_otherZimo.min(),
                                          per = self.richi_otherZimo.avg_bool()),
            richi_machi            = dict(avg = self.richi_machi.avg(),
                                          per = self.richi_machi.per2over()),
            richi_first            = dict(per = self.richi_first.avg_bool()),
            total_first_count       = self.rank.datas.count(1),
            total_second_count       = self.rank.datas.count(2),
            total_third_count       = self.rank.datas.count(3),
            total_fourth_count       = self.rank.datas.count(4),
            yakus                  = [[self.yakus[yaku], yaku] for yaku in self.yakus],
        )
        
    def json(self):
        return json.dumps(self.dict())
