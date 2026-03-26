"""
패보 URL 파싱 및 검증 서비스
- 기존 main.py의 if/split 체인을 정리
- 입력 검증 강화 (보안)
"""
import re
import logging

logger = logging.getLogger(__name__)

# 패보 UUID 패턴: 날짜-UUID 형식 (예: 250101-c3df6bf3-7444-40ce-b156-559a8bec91ac)
_PAIPU_UUID_PATTERN = re.compile(
    r"^[0-9]{6}-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)

# 허용되는 UUID 길이
_EXPECTED_UUID_LENGTH = 43


class PaipuURLError(Exception):
    """패보 URL 파싱 에러"""
    pass


def extract_paipu_id(url_or_id: str) -> str:
    """
    다양한 형태의 패보 입력에서 UUID를 추출.
    
    지원 형식:
        - 직접 UUID: "250101-c3df6bf3-7444-40ce-b156-559a8bec91ac"
        - 작혼 URL: "...paipu=UUID_..."
        - Google 공유 URL: "...paipu%3DUUID_..."
    
    Args:
        url_or_id: 사용자 입력 문자열
        
    Returns:
        정제된 패보 UUID
        
    Raises:
        PaipuURLError: 파싱 실패 또는 검증 실패
    """
    if not url_or_id or not url_or_id.strip():
        raise PaipuURLError("URL을 입력해주세요.")

    text = url_or_id.strip()

    # 1) Google 공유 URL에서 추출
    if "paipu%3D" in text:
        try:
            text = text.split("paipu%3D")[1]
        except IndexError:
            raise PaipuURLError("Google 공유 URL 형식을 확인해주세요.")

    # 2) 일반 paipu= 파라미터에서 추출
    if "paipu=" in text:
        try:
            text = text.split("paipu=")[1]
        except IndexError:
            raise PaipuURLError("패보 URL 형식을 확인해주세요.")

    # 3) 언더스코어 이후 제거 (플레이어 인덱스 등)
    if "_" in text:
        text = text.split("_")[0]

    # 4) 길이 검증
    if len(text) != _EXPECTED_UUID_LENGTH:
        raise PaipuURLError(
            f"패보 ID 길이가 올바르지 않습니다 (기대: {_EXPECTED_UUID_LENGTH}, "
            f"실제: {len(text)}). 패보 양식을 확인해주세요."
        )

    # 5) 형식 검증 (정규식)
    if not _PAIPU_UUID_PATTERN.match(text):
        raise PaipuURLError("패보 ID 형식이 올바르지 않습니다.")

    return text
