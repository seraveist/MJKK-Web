"""
유저 데이터 관리
- 현재: JSON 파일 기반
- 향후: DB로 이전 가능 (관리자 페이지에서 CRUD)

USERS 리스트의 각 항목:
  - name: 표시 이름 (고유)
  - aliases: 작혼 계정에서 사용하는 닉네임 목록
"""
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 기본 유저 데이터 (users.json이 없을 때 사용)
_DEFAULT_USERS = [
    {"name": "Kns2", "aliases": ["Kns2", "ganado"]},
    {"name": "HorTeNsiA", "aliases": ["HorTeNsiA", "筒美絹香"]},
    {"name": "jongja", "aliases": ["jongja"]},
    {"name": "ARKANA", "aliases": ["ARKANA", "BingHayu"]},
    {"name": "N@Gi", "aliases": ["N@Gi", "cloudsin"]},
    {"name": "セラビー", "aliases": ["セラビー", "ラビビビ", "MeikyouShisui"]},
    {"name": "SinYoA", "aliases": ["SinYoA", "RyuYoA"]},
    {"name": "한벼리", "aliases": ["한벼리"]},
    {"name": "맬렁호랭이", "aliases": ["맬렁호랭이"]},
    {"name": "黑荏子", "aliases": ["黑荏子"]},
    {"name": "숭악", "aliases": ["숭악"]},
    {"name": "적극적인소극성", "aliases": ["적극적인소극성"]},
    {"name": "최하노", "aliases": ["최하노"]},
    {"name": "쵸로기", "aliases": ["쵸로기"]},
    {"name": "무흐루", "aliases": ["무흐루"]},
    {"name": "태어닝", "aliases": ["태어닝"]},
    {"name": "nyabru", "aliases": ["nyabru"]},
]

_USERS_FILE = Path(__file__).parent / "users.json"


def load_users():
    """유저 데이터 로드 (JSON 파일 → 기본값 fallback)"""
    if _USERS_FILE.exists():
        try:
            with open(_USERS_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
            logger.info("Loaded %d users from %s", len(users), _USERS_FILE)
            return users
        except Exception as e:
            logger.warning("Failed to load users.json, using defaults: %s", e)

    return _DEFAULT_USERS


def get_user_names(users):
    """유저 이름 목록 반환"""
    return [u["name"] for u in users]


def find_user_by_alias(users, alias):
    """alias로 유저 검색, 없으면 None"""
    for user in users:
        if alias in user.get("aliases", []):
            return user
    return None


def find_user_index(users, alias):
    """alias로 유저 인덱스 검색, 없으면 -1"""
    for i, user in enumerate(users):
        if alias in user.get("aliases", []):
            return i
    return -1


# 모듈 로드 시 유저 데이터 초기화
USERS = load_users()
