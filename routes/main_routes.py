"""
페이지 렌더링 라우트
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
    return current_season, available_seasons


@main_bp.route("/health", methods=["GET"])
def health():
    return "OK", 200


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
    system_season = db.get_current_season()
    available_seasons = list(range(1, system_season + 1))
    available_seasons.reverse()

    season_param = request.args.get("season")
    if season_param and season_param.lower() != "all":
        try:
            selected_season = int(season_param)
        except (ValueError, TypeError):
            selected_season = system_season
    else:
        selected_season = system_season

    return render_template(
        "stats.html", season=selected_season,
        available_seasons=available_seasons, player_name=player_name,
    )


@main_bp.route("/totalstats", methods=["GET"])
def totalstats_page():
    current_season, available_seasons = _season_context()
    return render_template("totalStats.html", season=current_season, available_seasons=available_seasons)


@main_bp.route("/compare", methods=["GET"])
def compare_page():
    current_season, available_seasons = _season_context()
    return render_template("compare.html", season=current_season, available_seasons=available_seasons)


@main_bp.route("/trend", methods=["GET"])
def trend_page():
    current_season, available_seasons = _season_context()
    return render_template("trend.html", season=current_season, available_seasons=available_seasons)


@main_bp.route("/games", methods=["GET"])
def games_page():
    current_season, available_seasons = _season_context()
    return render_template("gameLogViewer.html", season=current_season, available_seasons=available_seasons)
