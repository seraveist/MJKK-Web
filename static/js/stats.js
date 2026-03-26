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

  // URL에서 복원
  const params = new URLSearchParams(location.search);
  if (params.get("season")) currentSeason = params.get("season");
  if (params.get("player")) currentPlayer = params.get("player");
  syncTabUI(currentSeason);

  // ── URL 상태 관리 ──
  function pushState() {
    const p = new URLSearchParams();
    p.set("season", currentSeason);
    if (currentPlayer) p.set("player", currentPlayer);
    history.pushState({ season: currentSeason, player: currentPlayer }, "", `?${p}`);
  }

  window.addEventListener("popstate", (e) => {
    if (e.state) {
      currentSeason = e.state.season || currentSeason;
      currentPlayer = e.state.player || currentPlayer;
      syncTabUI(currentSeason);
      const sel = document.getElementById("playerSelect");
      if (sel && currentPlayer) sel.value = currentPlayer;
      loadStats(currentPlayer);
    }
  });

  function syncTabUI(season) {
    document.querySelectorAll(".season-tabs .tab").forEach(t => {
      t.classList.toggle("active", t.dataset.season === String(season));
    });
  }

  // ── 카테고리 탭 ──
  function buildCategoryTabs() {
    const container = document.getElementById("categoryTabs");
    if (!container) return;
    container.innerHTML = "";

    ["전체", ...CATEGORIES].forEach(cat => {
      const btn = document.createElement("button");
      btn.className = "cat-tab" + (cat === currentCategory ? " active" : "");
      btn.textContent = cat;
      btn.addEventListener("click", () => {
        currentCategory = cat;
        document.querySelectorAll(".cat-tab").forEach(t => t.classList.remove("active"));
        btn.classList.add("active");
        if (cachedStats) renderTable(cachedStats);
      });
      container.appendChild(btn);
    });
  }

  // ── 차트 ──
  function drawChart(rankData) {
    const ctx = document.getElementById("rankChart").getContext("2d");
    const labels = rankData.map((_, i) => i + 1);
    if (rankChart) {
      rankChart.data.labels = labels;
      rankChart.data.datasets[0].data = rankData;
      rankChart.update();
    } else {
      rankChart = new Chart(ctx, {
        type: "line",
        data: {
          labels,
          datasets: [{
            data: rankData,
            borderColor: "#5b8def",
            backgroundColor: "rgba(91,141,239,0.08)",
            fill: true, tension: 0.3,
            pointRadius: 3, pointBackgroundColor: "#5b8def",
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          scales: {
            x: { display: false },
            y: { reverse: true, ticks: { stepSize: 1 }, suggestedMin: 1, suggestedMax: 4 },
          },
          plugins: { legend: { display: false } },
        },
      });
    }
  }

  // ── 통계 테이블 (탭 필터) ──
  function renderTable(stats) {
    const tbody = document.querySelector("#statsTable tbody");
    tbody.innerHTML = "";
    enrichStats(stats);

    let hasData = false;
    for (const [key, { label, format, category }] of Object.entries(display_keys)) {
      if (currentCategory !== "전체" && category !== currentCategory) continue;
      const value = getNestedValue(stats, key);
      if (value === undefined) continue;
      hasData = true;
      const row = document.createElement("tr");
      row.innerHTML = `<td>${label}</td><td>${formatValue(value, format)}</td>`;
      tbody.appendChild(row);
    }
    if (!hasData) {
      tbody.innerHTML = `<tr><td colspan="2" class="empty-state">표시할 통계가 없습니다.</td></tr>`;
    }
  }

  // ── 역 달성 ──
  function renderYakus(yakusArray) {
    const tbody = document.querySelector("#yakuTable tbody");
    tbody.innerHTML = "";
    if (!yakusArray || !Array.isArray(yakusArray)) {
      tbody.innerHTML = `<tr><td colspan="2" class="empty-state">역 데이터가 없습니다.</td></tr>`;
      return;
    }
    const yakusMap = Object.fromEntries(yakusArray.map(([c, n]) => [n.trim(), c]));
    Object.keys(yaku_name_map).forEach(name => {
      const count = yakusMap[name] || 0;
      const row = document.createElement("tr");
      row.innerHTML = `<td>${yaku_name_map[name]}</td><td>${count.toLocaleString()}</td>`;
      tbody.appendChild(row);
    });
  }

  // ── 데이터 로드 ──
  function loadStats(player) {
    showLoading();
    currentPlayer = player;
    fetch(`/stats_api/${encodeURIComponent(currentPlayer)}?season=${currentSeason}&count=${currentCount}`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(data => {
        if (data.error) {
          showPageEmpty("이 시즌의 대국 데이터가 없습니다.");
          return;
        }
        const stats = data.stats || data.data;
        if (!stats) { showPageEmpty("통계를 계산할 수 없습니다."); return; }
        cachedStats = stats;
        renderTable(stats);
        renderYakus(stats.yakus);
        if (stats.rankData && stats.rankData.length > 0) drawChart(stats.rankData);
      })
      .catch(e => {
        console.error("Error:", e);
        showPageError("데이터를 불러오는 중 오류가 발생했습니다.");
      })
      .finally(() => hideLoading());
  }

  function showPageEmpty(msg) {
    const tbody = document.querySelector("#statsTable tbody");
    if (tbody) tbody.innerHTML = `<tr><td colspan="2" class="empty-state">${msg}</td></tr>`;
    const yakuTbody = document.querySelector("#yakuTable tbody");
    if (yakuTbody) yakuTbody.innerHTML = "";
  }

  function showPageError(msg) {
    const tbody = document.querySelector("#statsTable tbody");
    if (tbody) tbody.innerHTML = `<tr><td colspan="2" class="error-state">${msg}</td></tr>`;
  }

  // ── 이벤트 ──
  document.querySelectorAll(".graph-btn").forEach(btn => {
    btn.addEventListener("click", function () {
      currentCount = parseInt(this.dataset.count);
      loadStats(currentPlayer);
    });
  });

  document.querySelectorAll(".season-tabs .tab").forEach(tab => {
    tab.addEventListener("click", function () {
      document.querySelectorAll(".season-tabs .tab").forEach(t => t.classList.remove("active"));
      this.classList.add("active");
      currentSeason = this.dataset.season;
      pushState();
      loadStats(currentPlayer);
    });
  });

  function showLoading() { const e = document.getElementById("loading"); if (e) e.style.display = "flex"; }
  function hideLoading() { const e = document.getElementById("loading"); if (e) e.style.display = "none"; }

  // ── 초기화 ──
  buildCategoryTabs();

  const sel = document.getElementById("playerSelect");
  if (sel) {
    fetch("/stats/all").then(r => r.json()).then(data => {
      data.allPlayers.forEach(p => {
        const o = document.createElement("option");
        o.value = p; o.textContent = p;
        sel.appendChild(o);
      });
      if (data.allPlayers.length > 0) {
        if (currentPlayer && data.allPlayers.includes(currentPlayer)) sel.value = currentPlayer;
        else { sel.value = data.allPlayers[0]; currentPlayer = data.allPlayers[0]; }
        pushState();
        loadStats(currentPlayer);
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
