/**
 * stats.js — 개인 통계
 * - 카테고리 탭 필터링
 * - URL 상태 (season, player → 뒤로가기 지원)
 * - 에러/빈 상태 처리
 */
document.addEventListener("DOMContentLoaded", () => {
  let currentPlayer = window.config.playerName || "";
  let currentSeason = window.config.season;
  let currentCount = 10;
  let currentCategory = "전체";
  let rankChart = null;
  let cachedStats = null;

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
    });
    sel.addEventListener("change", () => {
      currentPlayer = sel.value;
      pushState();
      loadStats(currentPlayer);
    });
  }
});
