import json
import pandas as pd

from statics import tenhouStatistics
from statics import tenhouLog

import variables

import gspread
import gspread_dataframe as gd
from google.oauth2.service_account import Credentials

scopes = ['https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive']

credentials = Credentials.from_service_account_file(variables.credential_path,scopes=scopes)

def update_statics(logDatas, userData):

    try:
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open_by_url(variables.sheetUrl)

        recordDf = pd.DataFrame(columns=['ref', 'title', 'player', 'score', 'point'])
        newRef = pd.DataFrame(columns=['id'])

        list_datas = list(logDatas)

        totalgames = []
        staticList = []
        playerList = []
        totalPlayer = []
        totalStatic = []
        
        for idx, log in enumerate(list_datas):
            ref = log['ref']
            title = log['title'][0]
            newRef.loc[idx] = ref
            for i, player in enumerate(log['name']):
                for i1, dict in enumerate(userData):
                    if i1 not in totalPlayer:
                        totalPlayer.append(i1)
                    if player in dict.get('list'):
                        if i1 not in playerList:
                            playerList.append(i1)

                        playerName = dict.get('name')
                        score = log['sc'][i * 2]
                        point = log['sc'][i * 2 + 1]
                        recordDf.loc[idx * len(log['name']) + i] = [ref, title, playerName, score, point]

            totalgames.append(tenhouLog.game(log))

        wks = spreadsheet.worksheet('recordData')
        wks.clear()
        gd.set_with_dataframe(wks, recordDf, row=1, col=1, include_index=False, include_column_header=True,
            resize=False, allow_formulas=True)

        wks = spreadsheet.worksheet('refList')
        wks.clear()
        gd.set_with_dataframe(wks, newRef,row=1, col=1, include_index=False, include_column_header=True,
            resize=False, allow_formulas=True)
        
        for idx in playerList:
            ps  = tenhouStatistics.PlayerStatistic(games = totalgames, playerName = userData[idx])
            staticList.append(ps)
        
        wks = spreadsheet.worksheet('staticRawData')
        wks.clear()
        dataList = []

        for ps in staticList:
            infoDf = json.loads(ps.json())
            infoDf = pd.json_normalize(infoDf)
            infoList = infoDf.loc[:, infoDf.columns != 'yakus']
            dataList.append(infoList)

        nDf = pd.concat(dataList, ignore_index=True)
        gd.set_with_dataframe(wks, nDf)

        wks = spreadsheet.worksheet('rankData')
        wks.clear()
        maxGame = len(list(list_datas))

        for idx in totalPlayer:
            ps  = tenhouStatistics.PlayerStatistic(games = totalgames, playerName = userData[idx])
            totalStatic.append(ps)

        if maxGame != 0:
            if int(maxGame * variables.regularGame) == 0:
                filteredList = [ x for x in totalStatic if x.rank.len() >= 1]
            else:
                filteredList = [ x for x in totalStatic if x.rank.len() >= int(maxGame * variables.regularGame)]
            rankList = GetRankData(filteredList)
            rankDf = pd.DataFrame(rankList, index = ['Top Score', 'Top First', 'Top Win', 'Top Lichi', 'Top Furo', 'Top Eva', 'Top Luck', 'Top Yifa'],columns = ['Point', 'Player'])
            gd.set_with_dataframe(wks, rankDf, include_index=True)

        return {'status' : 'ok', 'desc' : staticList }
    
    except:
        return {'status' : 'ok', 'desc' : "시트 업데이트에 실패했다냥..." }

def update_total_statics(logDatas, userData):

    try:
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open_by_url(variables.totalSheetUrl)

        recordDf = pd.DataFrame(columns=['ref', 'title', 'player', 'score', 'point'])
        newRef = pd.DataFrame(columns=['id'])

        list_datas = list(logDatas)

        totalgames = []
        staticList = []
        playerList = []
        
        for idx, log in enumerate(list_datas):
            ref = log['ref']
            title = log['title'][0]
            newRef.loc[idx] = ref
            for i, player in enumerate(log['name']):
                for i1, dict in enumerate(userData):
                    if player in dict.get('list'):
                        if i1 not in playerList:
                            playerList.append(i1)

                        playerName = dict.get('name')
                        score = log['sc'][i * 2]
                        point = log['sc'][i * 2 + 1]
                        recordDf.loc[idx * len(log['name']) + i] = [ref, title, playerName, score, point]

            totalgames.append(tenhouLog.game(log))

        wks = spreadsheet.worksheet('recordData')
        wks.clear()
        gd.set_with_dataframe(wks, recordDf, row=1, col=1, include_index=False, include_column_header=True,
            resize=False, allow_formulas=True)

        wks = spreadsheet.worksheet('refList')
        wks.clear()
        gd.set_with_dataframe(wks, newRef,row=1, col=1, include_index=False, include_column_header=True,
            resize=False, allow_formulas=True)
        
        for idx in playerList:
            ps  = tenhouStatistics.PlayerStatistic(games = totalgames, playerName = userData[idx])
            staticList.append(ps)
        
        wks = spreadsheet.worksheet('staticRawData')
        wks.clear()
        dataList = []

        for ps in staticList:
            infoDf = json.loads(ps.json())
            infoDf = pd.json_normalize(infoDf)
            infoList = infoDf.loc[:, infoDf.columns != 'yakus']
            dataList.append(infoList)

        nDf = pd.concat(dataList, ignore_index=True)
        gd.set_with_dataframe(wks, nDf)

        wks = spreadsheet.worksheet('rankData')
        wks.clear()
        maxGame = len(list(list_datas))

        if maxGame != 0 and int(maxGame * variables.regularGame) > 0:
            filteredList = [ x for x in staticList if x.rank.len() >= int(maxGame * variables.regularGame)]
            rankList = GetRankData(filteredList)
            rankDf = pd.DataFrame(rankList, index = ['Top Score', 'Top Win', 'Top Lichi', 'Top Furo', 'Top Eva', 'Top Luck', 'Top Yifa', 'Top First'],columns = ['Point', 'Player'])
            gd.set_with_dataframe(wks, rankDf, include_index=True)

        return {'status' : 'ok', 'desc' : staticList }
    
    except:
        return {'status' : 'ok', 'desc' : "전체 시트 업데이트에 실패했다냥..." }
    
def GetRankData(filteredList):

    topScore = [None, 0]
    topFirst = [None, 0]
    topEva = [None, 1]
    topLuck = [None, 0]
    topYifa = [None, 0]
    topWin = [None, 0]
    topLichi = [None, 0]
    topFuro = [None, 0]
    
    for static in filteredList:
        if static.endScore.max() > topScore[1]:
            topScore[1] = static.endScore.max()
            topScore[0] = static.playerName
        
        if static.rank.datas.count(1) / static.rank.len() > topFirst[1]:
            topFirst[1] = round(static.rank.datas.count(1) / static.rank.len(),4)
            topFirst[0] = static.playerName

        if static.rank.datas.count(4) / static.rank.len() < topEva[1]:
            topEva[1] = round(static.rank.datas.count(4) / static.rank.len(),4)
            topEva[0] = static.playerName

        if static.dora.avg() > topLuck[1]:
            topLuck[1] = round(static.dora.avg(), 4)
            topLuck[0] = static.playerName

        if static.winGame.avg() * static.winGame_score.avg() > topWin[1]:
            topWin[1] = int(static.winGame.avg() * static.winGame_score.avg())
            topWin[0] = static.playerName

        if static.richi_score.avg() > topLichi[1]:
            topLichi[1] = int(static.richi_score.avg())
            topLichi[0] = static.playerName

        if static.richi_yifa.avg_bool() > topYifa[1]:
            topYifa[1] = round(static.richi_yifa.avg_bool(),4)
            topYifa[0] = static.playerName

        if static.fulu_score.avg() > topFuro[1]:
            topFuro[1] = int(static.fulu_score.avg())
            topFuro[0] = static.playerName

    rankList = [topScore, topFirst, topWin, topLichi, topFuro, topEva, topLuck, topYifa]
    return rankList
