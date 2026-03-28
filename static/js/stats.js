/**
 * stats.js — 개인 통계 (v3)
 * - 연승/연패 기록
 * - 비교/상성 바로가기
 */
document.addEventListener("DOMContentLoaded", () => {
  let currentPlayer = window.config.playerName || "";
  let currentSeason = window.config.season;
  let currentCount = 10;
  let currentCategory = "전체";
  let rankChart = null;
  let cachedStats = null;

  const params = new URLSearchParams(location.search);
  if (params.get("season")) currentSeason = params.get("season");
  if (params.get("player")) currentPlayer = params.get("player");
  syncTabUI(currentSeason);

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
    const parts = season === "all" ? [] : String(season).split(",");
    const allBtn = document.getElementById("btnAllSeason");
    document.querySelectorAll(".season-btn").forEach(btn => {
      if (btn.id === "btnAllSeason") {
        btn.classList.toggle("active", season === "all");
      } else {
        btn.classList.toggle("active", season === "all" || parts.includes(btn.dataset.season));
      }
    });
  }

  // 카테고리 탭
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

  // 차트
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
        data: { labels, datasets: [{ data: rankData, borderColor: "#5b8def", backgroundColor: "rgba(91,141,239,0.08)", fill: true, tension: 0.3, pointRadius: 3, pointBackgroundColor: "#5b8def" }] },
        options: { responsive: true, maintainAspectRatio: false, scales: { x: { display: false }, y: { reverse: true, ticks: { stepSize: 1 }, suggestedMin: 1, suggestedMax: 4 } }, plugins: { legend: { display: false } } },
      });
    }
  }

  // 테이블
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
      tbody.innerHTML = '<tr><td colspan="2" class="empty-state">표시할 통계가 없습니다.</td></tr>';
    }
  }

  // 역 달성
  function renderYakus(yakusArray) {
    const tbody = document.querySelector("#yakuTable tbody");
    tbody.innerHTML = "";
    if (!yakusArray || !Array.isArray(yakusArray)) {
      tbody.innerHTML = '<tr><td colspan="2" class="empty-state">역 데이터가 없습니다.</td></tr>';
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

  // [신규] 연승/연패 로드
  async function loadStreaks(player) {
    try {
      const res = await fetch(`/api/streaks/${encodeURIComponent(player)}?season=${currentSeason}`);
      const data = await res.json();
      if (data.error || !data.total_games) {
        document.getElementById("streakSection").style.display = "none";
        return;
      }
      document.getElementById("streakSection").style.display = "";
      document.getElementById("streakCards").innerHTML = `
        <div class="streak-card"><div class="sk-label">최장 연속 1위</div><div class="sk-value">${data.max_first_streak}</div><div class="sk-sub">현재 ${data.current_first_streak}연속</div></div>
        <div class="streak-card"><div class="sk-label">최장 연대 (1~2위)</div><div class="sk-value">${data.max_top2_streak}</div><div class="sk-sub">현재 ${data.current_top2_streak}연속</div></div>
        <div class="streak-card"><div class="sk-label">최장 연속 4위</div><div class="sk-value">${data.max_last_streak}</div><div class="sk-sub">현재 ${data.current_last_streak}연속</div></div>
      `;
    } catch (e) { console.error(e); document.getElementById("streakSection").style.display = "none"; }
  }

  // [신규] 바로가기 링크 업데이트
  function updateNavLinks(player) {
    const nav = document.getElementById("navBtns");
    if (!player) { nav.style.display = "none"; return; }
    nav.style.display = "";
    document.getElementById("linkCompare").href = `/compare?p1=${encodeURIComponent(player)}&season=${currentSeason}`;
    document.getElementById("linkMatchup").href = `/matchup?p1=${encodeURIComponent(player)}&season=${currentSeason}`;
    document.getElementById("linkSeasonCmp").href = `/trend?view=seasonCmp&player=${encodeURIComponent(player)}`;
  }

  // 로딩/에러
  function showLoading() { document.getElementById("loading").style.display = "flex"; }
  function hideLoading() { document.getElementById("loading").style.display = "none"; }
  function showPageEmpty(msg) {
    document.querySelector("#statsTable tbody").innerHTML = `<tr><td colspan="2" class="empty-state">${msg}</td></tr>`;
    document.getElementById("streakSection").style.display = "none";
  }
  function showPageError(msg) {
    document.querySelector("#statsTable tbody").innerHTML = `<tr><td colspan="2" class="error-state">${msg}</td></tr>`;
  }

  // 데이터 로드
  function loadStats(player) {
    showLoading();
    currentPlayer = player;
    updateNavLinks(player);

    fetch(`/stats_api/${encodeURIComponent(currentPlayer)}?season=${currentSeason}&count=${currentCount}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => {
        if (data.error) { showPageEmpty("이 시즌의 대국 데이터가 없습니다."); return; }
        const stats = data.stats || data.data;
        if (!stats) { showPageEmpty("통계를 계산할 수 없습니다."); return; }
        if (!stats.games || stats.games === 0) {
          showPageEmpty("이 시즌에 해당 플레이어의 대국 데이터가 없습니다.");
          document.getElementById("streakSection").style.display = "none";
          return;
        }
        cachedStats = stats;
        renderTable(stats);
        renderYakus(stats.yakus);
        if (stats.rankData && stats.rankData.length > 0) drawChart(stats.rankData);
        loadStreaks(player);
      })
      .catch(e => { console.error("Error:", e); showPageError("데이터를 불러오는 중 오류가 발생했습니다."); })
      .finally(() => hideLoading());
  }

  // 초기화
  buildCategoryTabs();

  fetch("/stats/all")
    .then(r => r.json())
    .then(data => {
      const sel = document.getElementById("playerSelect");
      const players = data.allPlayers || [];
      players.forEach(p => { const o = document.createElement("option"); o.value = p; o.textContent = p; sel.appendChild(o); });
      if (currentPlayer) sel.value = currentPlayer;
      else if (players.length > 0) currentPlayer = players[0];

      sel.addEventListener("change", () => {
        currentPlayer = sel.value;
        pushState();
        loadStats(currentPlayer);
      });

      if (currentPlayer) loadStats(currentPlayer);
    });

  // ── 시즌 버튼 토글 ──
  function getSeasonParam() {
    const seasonBtns = document.querySelectorAll(".season-btn:not(#btnAllSeason)");
    const active = [...seasonBtns].filter(b => b.classList.contains("active")).map(b => b.dataset.season);
    const allBtn = document.getElementById("btnAllSeason");
    if (allBtn.classList.contains("active") || active.length === 0 || active.length === seasonBtns.length) return "all";
    if (active.length === 1) return active[0];
    return active.join(",");
  }

  function onSeasonChange() {
    currentSeason = getSeasonParam();
    pushState();
    if (currentPlayer) loadStats(currentPlayer);
  }

  // 개별 시즌 버튼 클릭: 토글
  document.querySelectorAll(".season-btn:not(#btnAllSeason)").forEach(btn => {
    btn.addEventListener("click", function () {
      this.classList.toggle("active");
      // 전체 버튼 비활성화
      const allBtn = document.getElementById("btnAllSeason");
      allBtn.classList.remove("active");
      // 모두 선택되면 자동 전체 전환
      const seasonBtns = document.querySelectorAll(".season-btn:not(#btnAllSeason)");
      const activeCount = [...seasonBtns].filter(b => b.classList.contains("active")).length;
      if (activeCount === seasonBtns.length || activeCount === 0) {
        allBtn.classList.add("active");
        if (activeCount === seasonBtns.length) {
          seasonBtns.forEach(b => b.classList.remove("active"));
        }
      }
      onSeasonChange();
    });
  });

  // 전체 버튼 클릭
  document.getElementById("btnAllSeason").addEventListener("click", function () {
    document.querySelectorAll(".season-btn").forEach(b => b.classList.remove("active"));
    this.classList.add("active");
    onSeasonChange();
  });

  // 국수 변경
  document.getElementById("countSelect").addEventListener("change", function () {
    currentCount = parseInt(this.value);
    if (currentPlayer) loadStats(currentPlayer);
  });
});
