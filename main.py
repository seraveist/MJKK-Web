import os
import logging
import json
import datetime
from flask import Flask, jsonify, render_template, request
from pymongo import MongoClient
from config import Config
from src import tenhouStatistics, tenhouLog

# 환경 변수 및 설정 로드 (config.py 활용)
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(Config)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DB 연결
try:
    client = MongoClient(app.config["DB_URL"])
    db = client["totalLogDB"]
    collection = db["gameLog"]
    logger.info("Connected to MongoDB successfully.")
except Exception as e:
    logger.error("Failed to connect to MongoDB", exc_info=e)
    raise e

# 사용자 데이터 (하드코딩, 나중에 DB 또는 외부 설정으로 관리 가능)
USERS = [
    {'name': 'Kns2', 'aliases': ['Kns2', 'ganado']},
    {'name': 'HorTeNsiA', 'aliases': ['HorTeNsiA', '筒美絹香']},
    {'name': 'jongja', 'aliases': ['jongja']},
    {'name': 'ARKANA', 'aliases': ['ARKANA', 'BingHayu']},
    {'name': 'N@Gi', 'aliases': ['N@Gi', 'cloudsin']},
    {'name': 'セラビー', 'aliases': ['セラビー', 'ラビビビ']},
    {'name': 'SinYoA', 'aliases': ['SinYoA', 'RyuYoA']},
    {'name': '한벼리', 'aliases': ['한벼리']},
    {'name': '맬렁호랭이', 'aliases': ['맬렁호랭이']},
    {'name': '적극적인소극성', 'aliases': ['적극적인소극성']},
    {'name': '黑荏子', 'aliases': ['黑荏子']},
    {'name': '숭악', 'aliases': ['숭악']},
    {'name': '무흐루', 'aliases': ['무흐루']},
    {'name': '태어닝', 'aliases': ['태어닝']},
    {'name': 'nyabru', 'aliases': ['nyabru']}
]

# -------------------------------
# 시즌 관련 헬퍼 함수들
def get_season_range(season_number):
    if season_number < 1:
        raise ValueError("Season number must be >= 1")
    # 기본년도 2023년부터 시작한다고 가정
    year = 2023 + (season_number - 1) // 2
    if season_number % 2 == 1:  # 홀수 시즌: 1월 ~ 6월
        start = datetime.datetime(year, 1, 1)
        end = datetime.datetime(year, 6, 30, 23, 59, 59)
    else:  # 짝수 시즌: 7월 ~ 12월
        start = datetime.datetime(year, 7, 1)
        end = datetime.datetime(year, 12, 31, 23, 59, 59)
    return start, end

def get_current_season():
    today = datetime.datetime.today()
    base_year = 2023
    if today.month <= 6:
        season = (today.year - base_year) * 2 + 1
    else:
        season = (today.year - base_year) * 2 + 2
    return season

def parse_title_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except Exception as e:
        logger.error("Date parse error: %s", e, exc_info=True)
        return None
    
def filter_data_by_season(data, season_param):
    if season_param.lower() == "all":
        return data
    try:
        season_number = int(season_param)
        season_start, season_end = get_season_range(season_number)
    except Exception as e:
        raise ValueError("Invalid season parameter")
    
    filtered_data = []
    for log in data:
        title_arr = log.get("title", [])
        if len(title_arr) >= 2:
            log_date = parse_title_date(title_arr[1])
            if log_date and season_start <= log_date <= season_end:
                filtered_data.append(log)
    return filtered_data


# 헬스 체크 엔드포인트 (Cloud Run 용)
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

@app.route("/players", methods=["GET"])
def get_players():
    try:
        players = [user["name"] for user in USERS]
        return jsonify({"players": players})
    except Exception as e:
        logger.error("Error fetching players", exc_info=e)
        return jsonify({"error": "Failed to fetch players"}), 500

@app.route("/", methods=["GET"])
def index():
    current_season = get_current_season()
    available_seasons = list(range(1, current_season + 1))
    available_seasons.reverse()
    return render_template("index.html", season=current_season, available_seasons=available_seasons)

@app.route("/stats", methods=["GET"])
def stats_page():
    current_season = get_current_season()
    available_seasons = list(range(1, current_season + 1))
    available_seasons.reverse()  # 최신 시즌부터 나열
    # 플레이어 이름을 선택할 수 있는 stats.html 템플릿을 렌더링
    return render_template("stats.html", season=current_season, available_seasons=available_seasons)

@app.route("/stats/all", methods=["GET"])
def get_all_players():
    try:
        return jsonify({"allPlayers": [user["name"] for user in USERS]})
    except Exception as e:
        logger.error("Error fetching all players", exc_info=e)
        return jsonify({"error": "Failed to fetch all players"}), 500

@app.route("/stats_api/<player_name>", methods=["GET"])
def get_player_stats_api(player_name: str):
    try:
        # season 파라미터 (없으면 현재 시즌)
        season_param = request.args.get("season", str(get_current_season()))
        # count 파라미터 (최근 몇 개의 게임 순위를 반환할지; 기본값 10)
        count_param = request.args.get("count", "10")
        try:
            count = int(count_param)
        except Exception:
            count = 10

        # 시즌이 "all"이면 일반적으로 find()로 모든 데이터를 받아옴
        if season_param.lower() == "all":
            data = list(collection.find())
        else:
            try:
                season_number = int(season_param)
                season_start, season_end = get_season_range(season_number)
            except Exception as e:
                return jsonify({"error": "Invalid season parameter"}), 400

            # MongoDB aggregation pipeline을 사용하여, title[1]을 날짜로 변환 후 필터링
            pipeline = [
                {
                    "$addFields": {
                        "logDate": {
                            "$dateFromString": {
                                "dateString": { "$arrayElemAt": ["$title", 1] },
                                "format": "%Y-%m-%d"
                            }
                        }
                    }
                },
                {
                    "$match": {
                        "logDate": {
                            "$gte": season_start,
                            "$lte": season_end
                        }
                    }
                }
            ]
            data = list(collection.aggregate(pipeline))
        
        if data:
            total_games = [tenhouLog.game(log) for log in data]
            # 사용자 이름은 문자열이어야 하므로, USERS에서 'name' 값을 찾음 (alias 기반)
            user_index = next((index for index, user in enumerate(USERS) if player_name in user.get('aliases', [])), 0)
            ps = tenhouStatistics.PlayerStatistic(games=total_games, playerName=USERS[user_index])
            stats_data = json.loads(ps.json())
            if hasattr(ps, "rank") and hasattr(ps.rank, "datas"):
                stats_data["rankData"] = ps.rank.datas[-count:]
            else:
                stats_data["rankData"] = []
            return jsonify({
                "stats": stats_data,
                "allPlayers": [user["name"] for user in USERS]
            })
        else:
            return jsonify({"error": "No game data found"}), 404
    except Exception as e:
        logger.error("Error fetching player stats", exc_info=e)
        return jsonify({"error": "Failed to fetch player stats"}), 500

@app.route("/stats_page/<player_name>", methods=["GET"])
def stats_page_player(player_name: str):
    # 시스템에서 현재 시즌 계산 (예: 5)
    system_season = get_current_season()
    
    # URL에서 season 파라미터가 있으면 사용하지만, available_seasons는 항상 시스템 현재 시즌까지.
    season_param = request.args.get("season")
    if season_param and season_param.lower() != "all":
        try:
            selected_season = int(season_param)
        except Exception as e:
            selected_season = system_season
    else:
        selected_season = system_season

    # available_seasons는 항상 1부터 시스템 시즌까지 생성
    available_seasons = list(range(1, system_season + 1))
    available_seasons.reverse()

    return render_template("stats.html", season=selected_season, available_seasons=available_seasons, player_name=player_name)

@app.route("/ranking", methods=["GET"])
def get_ranking():

    pipeline = [
        {"$unwind": "$name"},
        {"$group": {"_id": "$name"}},
        {"$sort": {"_id": 1}}
    ]
    results = list(collection.aggregate(pipeline))
    print(results)
    try:
        season_param = request.args.get("season", "all")
        # 시즌이 "all"이면 그냥 전체 문서를 가져옵니다.
        if season_param.lower() == "all":
            data = list(collection.find())
        else:
            try:
                season_number = int(season_param)
                season_start, season_end = get_season_range(season_number)
            except Exception as e:
                return jsonify({"error": "Invalid season parameter"}), 400

            # aggregation pipeline을 사용해 title[1]을 날짜로 변환 후 필터링합니다.
            pipeline = [
                {
                    "$addFields": {
                        "logDate": {
                            "$dateFromString": {
                                "dateString": { "$arrayElemAt": ["$title", 1] },
                                "format": "%Y-%m-%d"
                            }
                        }
                    }
                },
                {
                    "$match": {
                        "logDate": {
                            "$gte": season_start,
                            "$lte": season_end
                        }
                    }
                }
            ]
            data = list(collection.aggregate(pipeline))
        
        # 데이터가 존재하는 경우 랭킹 및 일별 점수 계산
        if data:
            player_scores = {user["name"]: {"point_sum": 0, "games": 0, "point_avg": 0} for user in USERS}
            daily_scores = {}

            for log in data:
                date = log.get("ref", "unknown")
                if date not in daily_scores:
                    daily_scores[date] = {}
                for i in range(4):
                    try:
                        name = log["name"][i]
                        point = log["sc"][i * 2 + 1]
                    except (IndexError, KeyError):
                        continue
                    matched_name = next((user["name"] for user in USERS if name in user.get("aliases", [])), None)
                    if matched_name:
                        player_scores[matched_name]["point_sum"] += point
                        player_scores[matched_name]["games"] += 1
                        daily_scores[date][matched_name] = point

            for player, stats in player_scores.items():
                games = stats["games"]
                if games > 0:
                    stats["point_avg"] = round(stats["point_sum"] / games, 2)

            ranking_list = [{"name": name, **stats} for name, stats in player_scores.items()]
            ranking_list.sort(key=lambda x: (-x["games"], -x["point_avg"]))
            daily_list = [{"date": k.split("-")[0] if "-" in k else k, "points": v} 
                          for k, v in sorted(daily_scores.items(), reverse=True)]
            
            total_points_all_users = sum(stats["point_sum"] for stats in player_scores.values())
            logger.info("Total POINT for all users: %s", total_points_all_users)

            return jsonify({
                "ranking": ranking_list,
                "players": [user["name"] for user in USERS],
                "daily": daily_list
            })
        else:
            return jsonify({"error": "No game data found"}), 404
    except Exception as e:
        logger.error("Error generating ranking", exc_info=e)
        return jsonify({"error": "Failed to generate ranking"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)