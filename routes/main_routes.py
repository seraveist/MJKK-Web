"""
페이지 렌더링 라우트
- 시즌 자동 선택: 데이터 있는 가장 최근 시즌을 기본값으로
"""
import logging
from flask import Blueprint, render_template, request, current_app
from config.users import USERS

logger = logging.getLogger(__name__)
main_bp = Blueprint("main", __name__)


def _get_db():
    return current_app.config["DB_SERVICE"]


def _season_context():
    db = _get_db()
    current_season = db.get_current_season()
    available_seasons = list(range(1, current_season + 1))
    available_seasons.reverse()

    # [개선] 데이터 있는 가장 최근 시즌 찾기
    best_season = current_season
    for s in available_seasons:
        try:
            data = db.fetch_game_logs(str(s), lightweight=True)
            if data and len(data) > 0:
                best_season = s
                break
        except Exception:
            continue

    return best_season, available_seasons


@main_bp.route("/", methods=["GET"])
def index():
    current_season, available_seasons = _season_context()
    return render_template("index.html", season=current_season, available_seasons=available_seasons)


@main_bp.route("/stats", methods=["GET"])
def stats_page():
    current_season, available_seasons = _season_context()
    return render_template("stats.html", season=current_season, available_seasons=available_seasons)


@main_bp.route("/stats_page/<player_name>", methods=["GET"])
def stats_page_player(player_name: str):
    db = _get_db()
    best_season, available_seasons = _season_context()
    season_param = request.args.get("season")
    if season_param and season_param.lower() != "all":
        try:
            best_season = int(season_param)
        except (ValueError, TypeError):
            pass
    return render_template("stats.html", season=best_season, available_seasons=available_seasons, player_name=player_name)


@main_bp.route("/totalstats", methods=["GET"])
def totalstats_page():
    s, a = _season_context()
    return render_template("totalStats.html", season=s, available_seasons=a)


@main_bp.route("/compare", methods=["GET"])
def compare_page():
    s, a = _season_context()
    return render_template("compare.html", season=s, available_seasons=a)


@main_bp.route("/trend", methods=["GET"])
def trend_page():
    s, a = _season_context()
    return render_template("trend.html", season=s, available_seasons=a)


@main_bp.route("/games", methods=["GET"])
def games_page():
    s, a = _season_context()
    return render_template("gameLogViewer.html", season=s, available_seasons=a)


@main_bp.route("/matchup", methods=["GET"])
def matchup_page():
    s, a = _season_context()
    return render_template("matchup.html", season=s, available_seasons=a)


@main_bp.route("/games/<path:ref>", methods=["GET"])
def game_detail_page(ref):
    s, a = _season_context()
    return render_template("gameDetail.html", ref=ref, season=s, available_seasons=a)


@main_bp.route("/report", methods=["GET"])
def report_page():
    s, a = _season_context()
    return render_template("report.html", season=s, available_seasons=a)
