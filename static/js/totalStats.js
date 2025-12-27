const display_keys = {
    "games": { label: "대국 수", format: "int", category: "기본" },
    "kuksu": { label: "총합 국 수", format: "int", category: "기본" },
    "kuksuji" : { label: "국 수지", format: "int", category: "기본" },
    "total.avg": { label: "평균순위", format: "float", category: "기본" },
    "total_first_count": { label: "1위 횟수", format: "int", category: "기본" },
    "total_second_count": { label: "2위 횟수", format: "int", category: "기본" },
    "total_third_count": { label: "3위 횟수", format: "int", category: "기본" },
    "total_fourth_count": { label: "4위 횟수", format: "int", category: "기본" },
    "first_rate": { label: "1위율", format: "percent", category: "기본" },
    "second_rate": { label: "2위율", format: "percent", category: "기본" },
    "third_rate": { label: "3위율", format: "percent", category: "기본" },
    "fourth_rate": { label: "4위율", format: "percent", category: "기본" },
    "endScore.avg": { label: "최종 점수 평균", format: "int", category: "기본" },
    "endScore.max": { label: "최종 점수 최고", format: "int", category: "기본" },
    "endScore.min": { label: "최종 점수 최저", format: "int", category: "기본" },
    "minusScore.avg": { label: "토비율", format: "percent", category: "기본" },
    "minusOther.avg": { label: "타가 들통률", format: "percent", category: "기본" },
    "east.avg": { label: "동 시작 평균 순위", format: "float", category: "기본" },
    "south.avg": { label: "남 시작 평균 순위", format: "float", category: "기본" },
    "west.avg": { label: "서 시작 평균 순위", format: "float", category: "기본" },
    "north.avg": { label: "북 시작 평균 순위", format: "float", category: "기본" },
    "winGame.avg": { label: "화료율", format: "percent", category: "화료 및 방총" },
    "winGame_score.avg": { label: "평균 타점", format: "int", category: "화료 및 방총" },
    "winGame_host.per": { label: "오야 화료율", format: "percent", category: "화료 및 방총" },
    "winGame_zimo.per": { label: "쯔모율", format: "percent", category: "화료 및 방총" },
    "winGame_dama.per": { label: "다마율", format: "percent", category: "화료 및 방총" },
    "winGame_round.avg": { label: "평균 화료 순수", format: "float", category: "화료 및 방총" },
    "chong.avg": { label: "방총률", format: "percent", category: "화료 및 방총" },
    "chong_score.avg": { label: "평균 방총", format: "int", category: "화료 및 방총" },
    "chong_host.per": { label: "방총시 오야율", format: "percent", category: "화료 및 방총" },
    "chong_fulu.per": { label: "방총시 후로율", format: "percent", category: "화료 및 방총" },
    "chong_richi.per": { label: "방총시 리치율", format: "percent", category: "화료 및 방총" },
    "dehost.avg": { label: "오야카부리율", format: "percent", category: "화료 및 방총" },
    "dehost_score.avg": { label: "오야카부리 평균", format: "int", category: "화료 및 방총" },
    "otherZimo.avg": { label: "피쯔모율", format: "percent", category: "화료 및 방총" },
    "richi.avg": { label: "리치율", format: "percent", category: "리치 및 후로" },
    "richi_winGame.per": { label: "리치 성공률", format: "percent", category: "리치 및 후로" },
    "richi_score.avg": { label: "리치 수지", format: "int", category: "리치 및 후로" },
    "richi_yifa.per": { label: "일발률", format: "percent", category: "리치 및 후로" },
    "richi_rong.per": { label: "리치시 론률", format: "percent", category: "리치 및 후로" },
    "richi_zimo.per": { label: "리치시 쯔모율", format: "percent", category: "리치 및 후로" },
    "richi_chong.per": { label: "리치시 방총률", format: "percent", category: "리치 및 후로" },
    "richi_draw.per": { label: "리치시 유국률", format: "percent", category: "리치 및 후로" },
    "richi_otherZimo.per": { label: "리치시 타가 쯔모율", format: "percent", category: "리치 및 후로" },
    "richi_machi.per": { label: "리치 다면율", format: "percent", category: "리치 및 후로" },
    "richi_first.per": { label: "리치 선제율", format: "percent", category: "리치 및 후로"  },
    "fulu.avg": { label: "후로율", format: "percent", category: "리치 및 후로" },
    "fulu_score.avg": { label: "후로 수지", format: "int", category: "리치 및 후로" },
    "fulu_zimo.per": { label: "후로시 쯔모율", format: "percent", category: "리치 및 후로" },
    "fulu_rong.per": { label: "후로시 론율", format: "percent", category: "리치 및 후로" },
    "fulu_chong.per": { label: "후로시 방총률", format: "percent", category: "리치 및 후로" },
    "dora.avg": { label: "평균 전체 도라갯수", format: "float", category: "도라" },
    "dora_outer.avg": { label: "평균 도라갯수", format: "float", category: "도라" },
    "dora_akai.avg": { label: "평균 적도라갯수", format: "float", category: "도라" },
    "dora_inner.avg": { label: "평균 뒷도라갯수", format: "float", category: "도라" },
    "dora.per": { label: "전체 도라율", format: "percent", category: "도라" },
    "dora_outer.per": { label: "일반 도라율", format: "percent", category: "도라" },
    "dora_akai.per": { label: "적도라율", format: "percent", category: "도라" },
    "dora_inner.per": { label: "뒷도라율", format: "percent", category: "도라" },
    "dora.max": { label: "최대 전체 도라갯수", format: "int", category: "도라" },
    "dora_outer.max": { label: "최대 도라갯수", format: "int", category: "도라" },
    "dora_akai.max": { label: "최대 적도라갯수", format: "int", category: "도라" },
    "dora_inner.max": { label: "최대 뒷도라갯수", format: "int", category: "도라" },
    "dora_inner_eff.avg": { label: "뒷도라 평균 변화점", format: "int", category: "도라" },
    "dora_inner_eff.per": { label: "뒷도라 유효율", format: "percent", category: "도라" },
    "dora_inner_eff.max": { label: "뒷도라 최대 변화점", format: "int", category: "도라" }
    };

    let currentSeason = window.config ? window.config.season : "all";

    // 기타 전역 변수
    let allPlayers = [];
    let userStats = {};
    
    // 시즌 탭 클릭 이벤트 처리
    document.querySelectorAll(".season-tabs .tab").forEach(tab => {
      tab.addEventListener("click", () => {
        document.querySelectorAll(".season-tabs .tab").forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        currentSeason = tab.getAttribute("data-season");
        // 테이블 재빌드
        document.getElementById("colHeader").innerHTML = "<th style='position: sticky; left: 0; background-color: #fff; z-index: 11;'>항목</th>";
        document.getElementById("totalStatsBody").innerHTML = "";
        loadTotalStats();
      });
    });
    
    // 페이지 로드 시 동작
    document.addEventListener("DOMContentLoaded", () => {
      loadTotalStats();
    });
    
    // 전체 통계 로딩 함수
    function loadTotalStats() {
      showLoading();
      // 1) allPlayers 목록 가져오기
      fetch("/stats/all")
        .then(res => res.json())
        .then(data => {
          allPlayers = data.allPlayers || [];
          return fetchAllPlayersStats();
        })
        .then(() => {
          buildTable();
        })
        .catch(err => console.error("Error in loadTotalStats:", err))
        .finally(() => hideLoading());
    }
    
    // 모든 플레이어 통계 불러오기
    async function fetchAllPlayersStats() {
      userStats = {}; // 초기화
      const promises = allPlayers.map(player => {
        return fetch(`/stats_api/${player}?season=${currentSeason}`)
          .then(res => res.json())
          .then(data => {
            if (data && data.stats) {
              const totalGames = data.stats.games || 0;
              if (totalGames > 0) {
                data.stats.first_rate = data.stats.total_first_count / totalGames;
                data.stats.second_rate = data.stats.total_second_count / totalGames;
                data.stats.third_rate = data.stats.total_third_count / totalGames;
                data.stats.fourth_rate = data.stats.total_fourth_count / totalGames;
                userStats[player] = data.stats;
              } else {
                userStats[player] = null;
              }
            } else {
              userStats[player] = null;
            }
          })
          .catch(error => {
            console.error(`Error fetching stats for player ${player}:`, error);
            userStats[player] = null;
          });
      });
      await Promise.all(promises);
      // 필터링: userStats가 null이 아닌 플레이어만 남김
      allPlayers = allPlayers.filter(player => userStats[player] !== null);
    }
    
    // 테이블 구성 함수
    function buildTable() {
      // 1) 테이블 헤더 구성
      const headerRow = document.getElementById("colHeader");
      allPlayers.forEach(player => {
        const th = document.createElement("th");
        th.textContent = player;
        th.style.position = "sticky";
        th.style.top = "0";
        th.style.backgroundColor = "#fff";
        th.style.zIndex = "10";
        headerRow.appendChild(th);
      });
    
      // 2) 테이블 바디 구성
      const tableBody = document.getElementById("totalStatsBody");
      tableBody.innerHTML = "";
      for (const key in display_keys) {
        const { label, format } = display_keys[key];
        const row = document.createElement("tr");
    
        // 행 헤더 생성
        const th = document.createElement("th");
        th.textContent = label;
        th.style.position = "sticky";
        th.style.left = "0";
        th.style.backgroundColor = "#fff";
        th.style.zIndex = "5";
        row.appendChild(th);
    
        // 각 플레이어 통계 값 추가
        allPlayers.forEach(player => {
          const td = document.createElement("td");
          let rawValue = key.split('.').reduce((o, i) => (o ? o[i] : undefined), userStats[player] || {});
          if (typeof rawValue === "number") {
            rawValue = formatValue(rawValue, format);
          } else if (rawValue === undefined || rawValue === null) {
            rawValue = "-";
          }
          td.textContent = rawValue;
          row.appendChild(td);
        });
    
        tableBody.appendChild(row);
      }
    }
    
    // 값 포맷팅 함수
    function formatValue(value, format) {
      if (isNaN(value)) return "-";
      switch (format) {
        case "int":
          return Math.floor(value).toLocaleString();
        case "float":
          return value.toFixed(1);
        case "percent":
          return (value * 100).toFixed(1) + "%";
        default:
          return value.toString();
      }
    }
    
    // 로딩 표시/숨김 함수
    function showLoading() {
      document.getElementById("loading").style.display = "flex";
    }
    function hideLoading() {
      document.getElementById("loading").style.display = "none";
    }
