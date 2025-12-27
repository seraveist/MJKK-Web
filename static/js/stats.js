const display_keys = {
    "games": { label: "대국 수", format: "int", category: "기본" },
    "kuksu": { label: "총합 국 수", format: "int", category: "기본" },
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

    const yaku_name_map = {
        "立直" : "리치",
        "両立直" : "더블리치",
        "門前清自摸和" : "멘젠쯔모",
        "嶺上開花" : "영상개화",
        "海底摸月" : "해저로월",
        "河底撈魚" : "하저로어",
        "一発" : "일발",
        "ドラ" : "도라",
        "赤ドラ" : "적도라",
        "裏ドラ" : "뒷도라",
        "平和" : "핑후",
        "断幺九" : "탕야오",
        "一気通貫" : "일기통관",
        "一盃口" : "이페코",
        "二盃口	" : "량페코",
        "三色同順" : "삼색동순",
        "三色同刻" : "삼색동각",
        "混全帯幺九" : "찬타",
        "純全帯幺九	" : "준찬타",
        "混老頭	" : "혼노두",
        "混一色" : "혼일색",
        "清一色" : "청일색",
        "七対子" : "치또이츠",
        "対々和" : "또이또이",
        "三暗刻" : "산안커",
        "自風 東" : "자풍 동",
        "自風 南" : "자풍 남",
        "自風 西" : "자풍 서",
        "自風 北" : "자풍 북",
        "場風 東" : "장풍 동",
        "場風 南" : "장풍 남",
        "役牌 白" : "역패 백",
        "役牌 發" : "역패 발",
        "役牌 中" : "역패 중",
        "小三元" : "소삼원",
        "槍槓" : "창깡",
        "三杠子" : "산깡즈",
        "流し満貫" : "유국 만관",
        "数え役満" : "헤아림 역만",
        "天和" : "천화",
        "地和" : "지화",
        "国士無双" : "국사무쌍",
        "四暗刻" : "스안커",
        "大三元" : "대삼원",
        "小四喜" : "소사희",
        "字一色" : "자일색",
        "緑一色" : "녹일색",
        "清老頭	" : "청노두",
        "九蓮宝燈" : "구련보등",
        "国士無双十三面待ち" : "국사무쌍 13면 대기",
        "四暗刻単騎" : "스안커 단기",
        "大四喜" : "대사희",
        "純正九蓮宝燈" : "순정구련보등"
    };
    document.addEventListener("DOMContentLoaded", () => {
      // HTML에서 window.config를 통해 전달한 초기 값 사용
      let currentPlayer = window.config.playerName || "";
      let currentSeason = window.config.season;
      let currentCount = 10;
      let rankChart = null;
  
      // 기존에 전역 변수(display_keys, yaku_name_map)가 정의되어 있다고 가정
      // 만약 ES6 모듈로 분리했다면 위처럼 import 구문 사용
  
      function drawChart(rankData) {
        const ctx = document.getElementById('rankChart').getContext('2d');
        const labels = rankData.map((_, index) => index + 1);
        if (rankChart) {
          rankChart.data.labels = labels;
          rankChart.data.datasets[0].data = rankData;
          rankChart.update();
        } else {
          rankChart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: labels,
              datasets: [{
                data: rankData,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.2)',
                fill: false,
                tension: 0,
                pointStyle: 'circle',
                pointRadius: 4,
                pointBackgroundColor: '#3498db'
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                x: { display: false },
                y: { reverse: true, ticks: { stepSize: 1 }, suggestedMin: 1, suggestedMax: 4 }
              },
              plugins: { legend: { display: false } },
              layout: { padding: { top: 0, bottom: 0, left: 0, right: 0 } }
            }
          });
        }
      }
    
      const graphBtns = document.querySelectorAll(".graph-btn");
      graphBtns.forEach(btn => {
        btn.addEventListener("click", function(){
          currentCount = parseInt(this.getAttribute("data-count"));
          loadStats(currentPlayer);
        });
      });
    
      const tabs = document.querySelectorAll(".season-tabs .tab");
      tabs.forEach(tab => {
        tab.addEventListener("click", function(){
          tabs.forEach(t => t.classList.remove("active"));
          this.classList.add("active");
          currentSeason = this.getAttribute("data-season");
          loadStats(currentPlayer);
        });
      });
    
      function showLoading() {
        const loadingElem = document.getElementById("loading");
        if (loadingElem) loadingElem.style.display = "flex";
      }
      function hideLoading() {
        const loadingElem = document.getElementById("loading");
        if (loadingElem) loadingElem.style.display = "none";
      }
    
      function renderTable(stats) {
        const tbody = document.querySelector("#statsTable tbody");
        tbody.innerHTML = "";
        const totalGames = stats.games || 0;
        if (totalGames > 0) {
          stats.first_rate = stats.total_first_count / totalGames;
          stats.second_rate = stats.total_second_count / totalGames;
          stats.third_rate = stats.total_third_count / totalGames;
          stats.fourth_rate = stats.total_fourth_count / totalGames;
        }
        let currentCategory = "";
        // display_keys는 config.js 등에서 정의되어 있어야 함.
        for (const [key, { label, format, category }] of Object.entries(display_keys)) {
          const value = key.split('.').reduce((o, i) => (o ? o[i] : undefined), stats);
          if (value !== undefined) {
            if (category && category !== currentCategory) {
              const headerRow = document.createElement("tr");
              const headerCell = document.createElement("td");
              headerCell.colSpan = 2;
              headerCell.className = "category-header";
              headerCell.textContent = category;
              headerRow.appendChild(headerCell);
              tbody.appendChild(headerRow);
              currentCategory = category;
            }
            const row = document.createElement("tr");
            let formattedValue = "";
            if (typeof value === "number") {
              switch (format) {
                case "int": formattedValue = Math.floor(value).toLocaleString(); break;
                case "float": formattedValue = value.toFixed(2); break;
                case "percent": formattedValue = (value * 100).toFixed(2) + "%"; break;
                default: formattedValue = value;
              }
            } else {
              formattedValue = value;
            }
            row.innerHTML = `<td>${label}</td><td>${formattedValue}</td>`;
            tbody.appendChild(row);
          }
        }
      }
    
      function renderYakus(yakusArray) {
        const yakuTableBody = document.querySelector("#yakuTable tbody");
        yakuTableBody.innerHTML = "";
        if (!yakusArray || !Array.isArray(yakusArray)) {
          yakuTableBody.innerHTML = "<tr><td colspan='2'>데이터 없음</td></tr>";
          return;
        }
        const yakusMap = Object.fromEntries(yakusArray.map(([count, name]) => [name.trim(), count]));
        // yaku_name_map는 config.js 등에서 전역 혹은 import된 변수여야 함.
        const sortedYakus = Object.keys(yaku_name_map).map(name => [yakusMap[name] || 0, name]);
        sortedYakus.forEach(([count, yaku]) => {
          const row = document.createElement("tr");
          const nameCell = document.createElement("td");
          const countCell = document.createElement("td");
          nameCell.textContent = yaku_name_map[yaku] || yaku;
          countCell.textContent = count.toLocaleString();
          row.appendChild(nameCell);
          row.appendChild(countCell);
          yakuTableBody.appendChild(row);
        });
      }
    
      function loadStats(player) {
        showLoading();
        currentPlayer = player;
        // 요청 URL은 window.config로 전달된 값(currentSeason)을 사용
        fetch(`/stats_api/${currentPlayer}?season=${currentSeason}&count=${currentCount}`)
          .then((res) => res.json())
          .then((data) => {
            const stats = data.stats || data.data;
            if (!stats) return;
            renderTable(stats);
            renderYakus(stats.yakus);
            if (stats.rankData && stats.rankData.length > 0) {
              drawChart(stats.rankData);
            } else {
              console.warn("rankData is empty or undefined.");
            }
          })
          .catch(error => console.error("Error loading stats:", error))
          .finally(() => hideLoading());
      }
    
      const playerSelect = document.getElementById("playerSelect");
      if (playerSelect) {
        playerSelect.innerHTML = "";
        fetch("/stats/all")
          .then((res) => res.json())
          .then((data) => {
            data.allPlayers.forEach((player) => {
              const option = document.createElement("option");
              option.value = player;
              option.textContent = player;
              playerSelect.appendChild(option);
            });
            // 초기 선택된 플레이어가 있으면 currentPlayer에 반영
            if (data.allPlayers.length > 0) {
              if (currentPlayer && data.allPlayers.includes(currentPlayer)) {
                playerSelect.value = currentPlayer;
              } else {
                playerSelect.value = data.allPlayers[0];
                currentPlayer = data.allPlayers[0];
              }
              loadStats(currentPlayer);
            }
          });
        playerSelect.addEventListener("change", () => {
          currentPlayer = playerSelect.value;
          loadStats(currentPlayer);
        });
      } else {
        console.error("playerSelect 요소를 찾을 수 없습니다.");
      }
  });
