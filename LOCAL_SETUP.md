# 로컬 테스트 실행 가이드 (최종)

## 빠른 시작

```bash
# 1. 기존 저장소 준비
cd MJKK-TEST

# 2. ZIP 파일 내용을 프로젝트 루트에 덮어쓰기
#    기존 src/ms, src/rp, src/tenhouLog.py 등은 유지

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 실행
python main.py

# 5. 브라우저에서 확인
#    http://localhost:8080
```

---

## 전체 페이지 구조

| URL | 페이지 | 설명 |
|-----|--------|------|
| `/` | 대시보드 | 랭킹 + 날짜별 점수 (양수 파란색, 음수 빨간색) |
| `/stats` | 개인 통계 | 카테고리 탭 필터 + 순위 차트 + 역 달성 |
| `/totalstats` | 전체 통계 | 배치 API, 행별 최고/최저 하이라이팅 |
| `/compare` | 플레이어 비교 | 🆕 head-to-head 비교, 더 좋은 쪽 하이라이팅 |
| `/trend` | 추이/분석 | 🆕 누적 우마 차트 + 시즌 간 비교 |
| `/upload_log` | 패보 등록 | 비밀번호 보호 (UPLOAD_PASSWORD 환경변수) |
| `/admin/users` | 유저 관리 | 🆕 비밀번호 인증 후 유저 CRUD |
| `/cache/stats` | 캐시 상태 | hit rate, size 확인 |

---

## 신규 기능 테스트 가이드

### 1. 플레이어 비교 (/compare)

- 두 플레이어를 선택하고 "비교" 클릭
- 통계 항목별로 더 좋은 쪽이 파란색, 나쁜 쪽이 빨간색
- 카테고리 탭으로 필터링 가능
- 시즌 변경 가능
- URL이 `?season=7&p1=Kns2&p2=HorTeNsiA` 형태로 공유 가능

### 2. 추이/분석 (/trend)

#### 우마 추이 탭
- 플레이어를 체크박스로 복수 선택 (기본 4명)
- 시즌 선택 → 해당 시즌의 대국별 누적 우마 그래프
- X축: 대국 순서, Y축: 누적 우마

#### 시즌 비교 탭
- 플레이어 1명 선택 → 비교할 시즌 복수 체크 → "비교" 클릭
- 같은 플레이어의 시즌별 통계를 나란히 비교
- 최고/최저 시즌이 파란색/빨간색으로 하이라이팅

### 3. 유저 관리 (/admin/users)

- 비밀번호 입력 후 "인증" 클릭
  - `.env`의 `UPLOAD_PASSWORD`가 비어있으면 아무 값이나 입력해도 통과
  - 테스트하려면 `.env`에 `UPLOAD_PASSWORD=test1234` 설정
- 등록된 유저 목록 확인
- "수정" 클릭 → 이름/별명 수정 → "저장"
- "유저 추가" 영역에서 새 유저 등록
- "삭제" → 확인 팝업 후 삭제
- 유저 데이터는 MongoDB `usersConfig` 컬렉션에 저장
- 첫 접근 시 기존 하드코딩 유저가 자동으로 DB에 초기화됨

### 4. URL 상태 관리 (모든 페이지)

- 시즌/플레이어 변경 시 URL 쿼리 파라미터 업데이트
- 브라우저 뒤로가기/앞으로가기 정상 작동
- URL을 직접 공유하면 같은 상태로 열림

### 5. 에러/빈 상태 (모든 페이지)

- 데이터 없는 시즌 선택 → "이 시즌의 대국 데이터가 없습니다."
- API 실패 → "데이터를 불러오는 중 오류가 발생했습니다."
- 빈 테이블 대신 안내 메시지 표시

---

## 기존 src/ 폴더 필요

리팩토링 ZIP에 포함되지 않은 기존 파일들 (그대로 유지):
- `src/__init__.py`
- `src/tenhouLog.py`
- `src/tenhouStatistics.py`
- `src/mahjong301.py`
- `src/ms/` (전체)
- `src/rp/` (전체)
- `static/favicon-16x16.png`

---

## 문제 해결

### ModuleNotFoundError: No module named 'src'
→ `main.py`가 있는 디렉토리에서 실행하세요

### MongoDB 연결 실패
→ `.env`의 DB_USER, DB_PASSWORD 확인
→ MongoDB Atlas → Network Access에서 현재 IP 허용 필요할 수 있음

### 유저 관리 인증 실패
→ `.env`의 `UPLOAD_PASSWORD` 값과 동일한 비밀번호 입력
→ 빈 값이면 아무 값으로도 통과

### 추이 차트가 안 그려짐
→ 대시보드(/ranking API)가 정상 작동하는지 먼저 확인
→ 해당 시즌에 데이터가 있는지 확인
