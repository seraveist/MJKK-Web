# 마자까까 내전 집계 — 최종 업그레이드 가이드

## 전체 변경 사항 (16개 항목)

### 기능
| # | 항목 | 위치 | 설명 |
|---|------|------|------|
| 1 | 대시보드 요약 카드 | 대시보드 상단 | 총 대국 수, 참가 인원, 최근 대국일, 최다 대국자 |
| 2 | 페이지 간 연동 | 개인 통계 | "비교하기", "상성 보기" 바로가기 버튼 |
| 3 | 시즌 자동 선택 | 전체 페이지 | 데이터 있는 가장 최근 시즌을 기본값으로 |
| 4 | 대국별 상세 분석 | /games/<ref> | 국별 점수 흐름 차트, 결과 배지 |
| 5 | 상성 분석 | /matchup | 동탁 전적, 승률, 순위 비교, 대국 이력 |
| 6 | 프론트엔드 공통 모듈 | static/js/common.js | API 래퍼, 포맷팅, 시즌 탭 유틸 |
| 7 | 캐시 무효화 정밀화 | services/precompute.py | 해당 시즌+all 키만 선별 삭제 |
| 8 | 다크 모드 | base.html | 네비바 우측 토글, localStorage 유지 |
| 9 | ELO 레이팅 | 추이 페이지 "ELO 레이팅" 탭 | 국수지 기반 제로섬 ELO, 추이 차트 |
| 10 | 시즌 어워드 | 대시보드 | 9개 항목 자동 계산 (최다대국, 최고우마 등) |
| 11 | 메타 분석 | 대시보드 | 리그 평균 화료율/방총률, TOP 10 역 |
| 12 | 역만 히스토리 | 대시보드 + 대국 기록 | 삼배만/역만 타임라인, 배만급 배지 표기 |
| 13 | 연승/연패 추적 | 개인 통계 | 최장 연속 1위/연대/4위, 현재 진행 중 |
| 14 | 대국 기록 페이지네이션 | 대국 기록 | 30건 단위 페이지 분할 |

### 인프라/코드 품질
| # | 항목 | 파일 | 설명 |
|---|------|------|------|
| 15 | API 응답 압축 | main.py | flask-compress (gzip) |
| 16 | DB 인덱스 추가 | services/database.py | name 멀티키 + title.1+name 복합 |
| 17 | 헬스체크 강화 | routes/api_routes.py | MongoDB 연결 + 캐시 상태 반환 |
| 18 | DB 백업 | 관리 페이지 | JSON export 다운로드 |
| 19 | 테스트 | tests/ | ELO 유닛 테스트 + API 통합 테스트 |
| 20 | 구조화 로깅 | main.py | 프로덕션 JSON 로깅 |

### 기존 메뉴에 통합 (신규 메뉴 최소화)
- **대시보드(/)**: 요약 카드 + 메타 분석 + 시즌 어워드 + 역만 타임라인
- **개인 통계(/stats)**: 연승/연패 카드 + 비교/상성 바로가기
- **추이(/trend)**: ELO 레이팅 탭 추가
- **대국 기록(/games)**: 페이지네이션 + 배만/삼배만/역만 배지 + 상세 링크
- **관리(/admin/users)**: DB 백업 + 사전계산 트리거
- **신규 메뉴 2개만**: 상성(/matchup), 대국 상세(/games/<ref>)

---

## 파일 목록 (총 28개)

### 신규 파일 (10개)
```
services/elo.py              ← ELO 계산 서비스
services/awards.py           ← 시즌 어워드 계산
static/js/common.js          ← 공통 유틸리티 모듈
static/js/matchup.js         ← 상성 분석 JS
static/js/gameDetail.js      ← 대국 상세 JS
templates/matchup.html       ← 상성 분석 페이지
templates/gameDetail.html    ← 대국 상세 페이지
tests/test_elo.py            ← ELO 유닛 테스트
tests/test_api.py            ← API 통합 테스트
UPGRADE_GUIDE.md             ← 이 파일
```

### 덮어쓰기 파일 (18개)
```
main.py                      ← flask-compress + JSON 로깅
services/database.py         ← DB 인덱스 추가
services/__init__.py         ← 신규 서비스 등록
services/precompute.py       ← 캐시 무효화 정밀화
routes/api_routes.py         ← 전체 신규 API 통합
routes/main_routes.py        ← 시즌 자동 선택 + 신규 라우트
routes/admin_routes.py       ← DB 백업 기능 추가
templates/base.html          ← 다크 모드 + 상성 메뉴 + 토글
templates/index.html         ← 대시보드 대폭 확장
templates/trend.html         ← ELO 탭 추가
templates/gameLogViewer.html ← 페이지네이션 + 배지
templates/stats.html         ← 연승/연패 + 바로가기
templates/userManagement.html← 백업 + 사전계산 UI
static/js/ranking.js         ← 대시보드 JS 전면 확장
static/js/trend.js           ← ELO 차트 추가
static/js/gameLogViewer.js   ← 페이지네이션 + 배지 JS
static/js/stats.js           ← 연승/연패 + 바로가기 JS
static/js/statsConfig.js     ← richi_yifa.per(일발율) 추가
static/js/userManagement.js  ← 백업/사전계산 JS
```

---

## 적용 방법

```bash
# 1. 프로젝트 루트로 이동
cd MJKK-TEST

# 2. ZIP 압축 해제 후 프로젝트 루트에 덮어쓰기
#    기존 src/, config/users.py, .env 등은 그대로 유지

# 3. flask-compress 설치 (선택 — 미설치 시에도 정상 동작)
pip install flask-compress --break-system-packages

# 4. ELO 테스트 실행 (DB 불필요)
python tests/test_elo.py

# 5. API 테스트 실행 (DB 연결 필요)
python tests/test_api.py

# 6. 실행
python main.py

# 7. 브라우저에서 확인
#    http://localhost:8080
```

---

## 확인 포인트

### 대시보드 (/)
- 상단: 요약 카드 4개 (총 대국 수, 참가 인원, 최근 대국일, 최다 대국자)
- 리그 메타: 평균 화료율/방총률 + "상세" 클릭 시 TOP 10 역
- 시즌 어워드: 9개 카드 (최다대국, 최고우마, 최고승률 등)
- 역만/삼배만 기록: 타임라인

### 개인 통계 (/stats)
- 플레이어 선택 후 "비교하기" / "상성 보기" 버튼
- 연속 기록 카드 (최장 연속 1위, 연대, 4위)
- 일발율 항목 추가

### 추이 (/trend)
- "ELO 레이팅" 탭: 레이팅 순위 테이블 + 추이 차트

### 대국 기록 (/games)
- 하단 페이지네이션 (30건 단위)
- 배만/삼배만/역만 발생 시 해당 유저에 배지 표시
- "상세" 링크 → /games/<ref> 상세 페이지

### 상성 (/matchup)
- 두 플레이어 선택 → 동탁 전적, 승률, 평균 순위, 대국 이력

### 관리 (/admin/users)
- 기존 유저 CRUD
- [신규] 데이터 백업: JSON 다운로드
- [신규] 사전계산: 전체 시즌 재계산 트리거

### 다크 모드
- 네비바 우측 🌙/☀️ 아이콘 클릭
- 브라우저 종료 후에도 설정 유지 (localStorage)

### 헬스체크
- `/health` → MongoDB 연결 상태 + 캐시 히트율 JSON 반환

---

## 수정하지 않는 기존 파일

아래 파일들은 이 업그레이드에 포함되지 않으며 그대로 유지해야 합니다:
- `src/` 전체 (tenhouLog.py, tenhouStatistics.py, paipu.py, ms/, rp/)
- `config/__init__.py`, `config/users.py`
- `services/cache.py`, `services/paipu_parser.py`, `services/ranking.py`
- `routes/__init__.py`, `routes/upload_routes.py`
- `templates/compare.html`, `templates/upload_log.html`, `templates/totalStats.html`
- `static/js/compare.js`, `static/js/totalStats.js`
- `static/favicon-16x16.png`
- `.env`, `.env.example`, `requirements.txt`
- `tests/snapshot_stats.py`

---

## 주의사항

1. **flask-compress**는 선택 사항. 미설치 시 로그에 "skipping compression" 출력 후 정상 동작
2. **ELO 첫 계산**은 시즌 전체 국별 데이터를 순회하므로 시간이 걸림. 계산 후 MongoDB에 캐싱되어 이후 즉시 반환
3. **역만 감지**는 점수 기준 (배만 16000+, 삼배만 24000+, 역만 32000+). 친/자 구분 없이 절대값 기준
4. **시즌 자동 선택**이 매 페이지 로드마다 DB를 한번 추가 쿼리하지만, 캐시로 인해 실질적 부하 미미
5. **다크 모드**: 기존 JS의 하드코딩 색상(ranking.js 날짜별 점수 등)은 CSS 변수로 대부분 교체됨. 일부 인라인 스타일 잔존 가능
