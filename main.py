from flask import Flask, jsonify, request, render_template, redirect, url_for
from pymongo import MongoClient
from statics import tenhouStatistics
from statics import tenhouLog

import json

app = Flask(__name__)

dbUser = "logUpdater"
dbPassword = "kCij9L7lZRAeDPiV"
dbURL = "mongodb+srv://"+ dbUser +":" + dbPassword + "@cluster0.6nqoq8u.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

userData = [
    { 'name' : 'Kns2', 'list' : ['Kns2', 'ganado'] },
    { 'name' : 'HorTeNsiA', 'list' : ['HorTeNsiA', '筒美絹香'] },
    { 'name' : 'jongja', 'list' : ['jongja'] },
    { 'name' : 'ARKANA', 'list' : ['ARKANA', 'BingHayu'] },
    { 'name' : 'N@Gi', 'list' : ['N@Gi', 'cloudsin'] },
    { 'name' : 'セラビー', 'list' : ['セラビー', 'ラビビビ'] },
    { 'name' : 'SinYoA', 'list' : ['SinYoA', 'RyuYoA'] },
    { 'name' : '한벼리', 'list' : ['한벼리'] },
    { 'name' : '맬렁호랭이', 'list' : ['맬렁호랭이'] },
    { 'name' : '적극적인소극성', 'list' : ['적극적인소극성'] },
    { 'name' : '黑荏子', 'list' : ['黑荏子'] },
    { 'name' : '숭악', 'list' : ['숭악'] }
    ]

# MongoDB 연결
client = MongoClient(dbURL)  # 여기에 실제 MongoDB URI 입력
db = client["logDB"]  # 사용할 데이터베이스 이름
collection = db["gameLog"]  # 컬렉션 이름

@app.route("/players")
def get_players():               
    return [user["name"] for user in userData]

# 특정 플레이어의 통계 데이터 반환
@app.route("/stats/<player_name>", methods=["GET"])
def get_player_stats(player_name):
    data = list(collection.find())
    if data:
        totalgames = [tenhouLog.game(log) for log in data]
        playerList = set()
        pIndex = None
        for game in totalgames:
            for player in game.names:
                playerList.add(player)

        
        for index, dict in enumerate(userData):
            if player_name in dict.get('list'):
                pIndex = index
        
        if pIndex == None:
            pIndex = 0
        ps = tenhouStatistics.PlayerStatistic(games=totalgames, playerName = userData[pIndex])

        return jsonify({
            "stats": json.loads(ps.json()),
            "allPlayers": [user["name"] for user in userData]
        })
    else:
        return jsonify({"error": "Player not found"}), 404        

@app.route("/ranking")
def get_ranking():
    data = list(collection.find())
    player_scores = {}
    daily_scores = {}

    for user in userData:
        player_scores[user["name"]] = {
            "point_sum": 0,
            "games": 0,
            "point_avg": 0
        }

    for log in data:
        date = log["ref"]
        if date not in daily_scores:
            daily_scores[date] = {}

        for i in range(4):
            name = log["name"][i]
            point = log["sc"][i * 2 + 1]

            matched_name = None
            for user in userData:
                if name in user["list"]:
                    matched_name = user["name"]
                    break

            if matched_name:
                player_scores[matched_name]["point_sum"] += point
                player_scores[matched_name]["games"] += 1
                daily_scores[date][matched_name] = point

    # 평균 계산
    for player in player_scores:
        games = player_scores[player]["games"]
        if games > 0:
            player_scores[player]["point_avg"] = round(player_scores[player]["point_sum"] / games, 2)

    # ✅ 리스트로 변환 후 정렬
    ranking_list = [
        {
            "name": name,
            **stats
        }
        for name, stats in player_scores.items()
    ]
    ranking_list.sort(key=lambda x: (-x["games"], -x["point_avg"]))

    return jsonify({
        "ranking": ranking_list,
        "players": [user["name"] for user in userData],
        "daily": [
            {"date": k.split("-")[0], "points": v}
            for k, v in sorted(daily_scores.items())
        ]
    })

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stats")
def dashboard():
    return render_template("stats.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
