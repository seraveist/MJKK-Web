from flask import Flask, jsonify, request, render_template
from pymongo import MongoClient
from statics import tenhouStatistics
from statics import tenhouLog

import json

app = Flask(__name__)


dbUser = "logUpdater"
dbPassword = "kCij9L7lZRAeDPiV"
dbURL = "mongodb+srv://"+ dbUser +":" + dbPassword + "@cluster0.6nqoq8u.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# MongoDB 연결
client = MongoClient(dbURL)  # 여기에 실제 MongoDB URI 입력
db = client["logDB"]  # 사용할 데이터베이스 이름
collection = db["gameLog"]  # 컬렉션 이름

# 전체 통계 데이터 반환
@app.route("/stats", methods=["GET"])
def get_stats():
    # MongoDB에서 모든 데이터 가져오기
    data = list(collection.find({}, {"_id": 0}))  # _id 필드는 제외하고 가져옴
    return jsonify(data)

# 특정 플레이어의 통계 데이터 반환
@app.route("/stats/<player_name>", methods=["GET"])
def get_player_stats(player_name):
    data = collection.find()
    if data:
        totalgames = []
        for log in data:
            totalgames.append(tenhouLog.game(log))
            ps  = tenhouStatistics.PlayerStatistic(games = totalgames, playerName = player_name)
        return ps.json()
    else:
        return jsonify({"error": "Player not found"}), 404
    
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)