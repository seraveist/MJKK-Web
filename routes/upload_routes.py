"""
패보 업로드 라우트
- 비밀번호 검증
- 성공 시 사전 계산 트리거 (해당 시즌 즉시 + 전체 백그라운드)
"""
import asyncio
import logging

from flask import Blueprint, render_template, request, current_app

from services.paipu_parser import extract_paipu_id, PaipuURLError
from services.precompute import precompute_after_upload
from src import paipu

logger = logging.getLogger(__name__)

upload_bp = Blueprint("upload", __name__)


def _get_db():
    return current_app.config["DB_SERVICE"]


def _get_upload_password():
    return current_app.config["APP_CONFIG"].UPLOAD_PASSWORD


@upload_bp.route("/upload_log", methods=["GET", "POST"])
def upload_log():
    message = ""
    game_log = None

    if request.method != "POST":
        return render_template("upload_log.html", message=message)

    # 1) 비밀번호 검증
    upload_pw = _get_upload_password()
    if upload_pw:
        submitted_pw = request.form.get("password", "").strip()
        if submitted_pw != upload_pw:
            return render_template(
                "upload_log.html",
                message="비밀번호가 틀렸습니다.",
            )

    # 2) URL 파싱 및 검증
    url_input = request.form.get("url", "").strip()
    try:
        paipu_id = extract_paipu_id(url_input)
    except PaipuURLError as e:
        return render_template("upload_log.html", message=str(e))

    # 3) 작혼 API에서 게임 로그 가져오기
    try:
        game_log = asyncio.run(paipu.get_game_log(paipu_id))
    except Exception as e:
        logger.error("패보 API 호출 실패: %s", paipu_id, exc_info=e)
        return render_template(
            "upload_log.html",
            message="패보 저장 실패: API 호출 오류.",
        )

    if game_log is None:
        return render_template(
            "upload_log.html",
            message="패보 저장 실패: 로그 데이터가 없습니다.",
        )

    # 4) DB 저장
    db = _get_db()
    try:
        inserted = db.insert_game_log(game_log)
        if inserted:
            message = "패보 저장 성공!"

            # 5) 사전 계산 트리거 (해당 시즌 즉시 + 전체 백그라운드)
            try:
                precompute_after_upload(db, game_log)
            except Exception as e:
                logger.warning("Precompute trigger failed (non-fatal): %s", e)
        else:
            message = "이미 저장된 패보입니다."
    except ValueError as e:
        message = f"패보 저장 실패: {e}"
    except Exception as e:
        logger.error("패보 DB 저장 실패", exc_info=e)
        message = "패보 저장 실패: 데이터베이스 오류."

    return render_template(
        "upload_log.html",
        message=message,
        game_log=game_log,
    )
