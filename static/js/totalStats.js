/**
 * totalStats.js — 전체 유저 통계 (v4)
 * - 행=유저, 열=스탯 (전치)
 * - 카테고리 탭 필터
 * - 열 헤더 클릭 정렬
 * - ELO 열 포함
 * - 최고/최저 하이라이팅
 */
let currentSeason = window.config ? window.config.season : "all";
let allPlayers = [];
let userStats = {};
let eloRatings = {};
let currentCategory = "전체";
let sortKey = null;
let sortDesc = true;

const urlSeason = new URLSearchParams(location.search).get("season");
if (urlSeason) { currentSeason = urlSeason; syncTabUI(currentSeason); }

function syncTabUI(season) {
  document.querySelectorAll(".season-tabs .tab").forEach(t => {
    t.classList.toggle("active", t.dataset.season === String(season));
  });
}

function pushState(season) {
  const p = new URLSearchParams(location.search);
  p.set("season", season);
  history.pushState({ season }, "", `?${p}`);
}

window.addEventListener("popstate", (e) => {
  if (e.state && e.state.season) {
    currentSeason = e.state.season;
    syncTabUI(currentSeason);
    loadTotalStats();
  }
});

document.querySelectorAll(".season-tabs .tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".season-tabs .tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    currentSeason = tab.dataset.season;
    pushState(currentSeason);
    loadTotalStats();
  });
});

document.addEventListener("DOMContentLoaded", () => {
  buildCatTabs();
  loadTotalStats();
});

// ── 카테고리 탭 ──
function buildCatTabs() {
  const container = document.getElementById("catTabs");
  if (!container) return;
  container.innerHTML = "";
  ["전체", ...CATEGORIES].forEach(cat => {
    const btn = document.createElement("button");
    btn.className = "cat-tab" + (cat === currentCategory ? " active" : "");
    btn.textContent = cat;
    btn.addEventListener("click", () => {
      currentCategory = cat;
      document.querySelectorAll("#catTabs .cat-tab").forEach(t => t.classList.remove("active"));
      btn.classList.add("active");
      sortKey = null;
      buildTable();
    });
    container.appendChild(btn);
  });
}

// ── 데이터 로드 ──
async function loadTotalStats() {
  showLoading();
  try {
    const [statsRes, eloRes] = await Promise.all([
      fetch(`/totalstats_api?season=${currentSeason}`),
      fetch(`/api/elo?season=${currentSeason}`).catch(() => null),
    ]);

    if (!statsRes.ok) throw new Error(`HTTP ${statsRes.status}`);
    const data = await statsRes.json();

    eloRatings = {};
    try {
      if (eloRes && eloRes.ok) {
        const eloData = await eloRes.json();
        eloRatings = eloData.ratings || {};
      }
    } catch (e) { /* */ }

    if (data.error) {
      document.getElementById("totalStatsBody").innerHTML = `<tr><td class="empty-state">${
        data.error === "No game data found" ? "이 시즌의 대국 데이터가 없습니다." : data.error
      }</td></tr>`;
      document.getElementById("colHeader").innerHTML = "";
      return;
    }

    allPlayers = data.allPlayers || [];
    userStats = {};
    for (const p of allPlayers) {
      if (data.stats[p]) userStats[p] = enrichStats(data.stats[p]);
    }

    sortKey = null;
    buildTable();
  } catch (e) {
    console.error("Error:", e);
    document.getElementById("totalStatsBody").innerHTML = `<tr><td class="error-state">데이터를 불러오는 중 오류가 발생했습니다.</td></tr>`;
  } finally {
    hideLoading();
  }
}

// ── 테이블 빌드 (행=유저, 열=스탯) ──
function buildTable() {
  // 대국 있는 유저만
  const activePlayers = allPlayers.filter(p => userStats[p] && userStats[p].games > 0);
  if (activePlayers.length === 0) {
    document.getElementById("colHeader").innerHTML = "";
    document.getElementById("totalStatsBody").innerHTML = `<tr><td class="empty-state">통계를 표시할 플레이어가 없습니다.</td></tr>`;
    return;
  }

  // 현재 카테고리에 해당하는 키 필터
  const visibleKeys = [];
  // ELO를 첫 열로
  if (Object.keys(eloRatings).length > 0) {
    visibleKeys.push({ key: "_elo", label: "ELO", format: "int", higherIsBetter: true });
  }
  for (const [key, { label, format, category, higherIsBetter }] of Object.entries(display_keys)) {
    if (currentCategory !== "전체" && category !== currentCategory) continue;
    visibleKeys.push({ key, label, format, higherIsBetter });
  }

  // 정렬
  let sortedPlayers = [...activePlayers];
  if (sortKey) {
    sortedPlayers.sort((a, b) => {
      const va = _getStatVal(a, sortKey);
      const vb = _getStatVal(b, sortKey);
      if (va === null && vb === null) return 0;
      if (va === null) return 1;
      if (vb === null) return -1;
      return sortDesc ? vb - va : va - vb;
    });
  }

  // 열별 최고/최저 미리 계산
  const colExtremes = {};
  for (const col of visibleKeys) {
    const vals = activePlayers.map(p => _getStatVal(p, col.key)).filter(v => v !== null);
    if (vals.length >= 2) {
      colExtremes[col.key] = { max: Math.max(...vals), min: Math.min(...vals) };
    }
  }

  // 헤더
  const headerRow = document.getElementById("colHeader");
  headerRow.innerHTML = "";

  const thName = document.createElement("th");
  thName.textContent = "유저명";
  thName.className = "sortable-th";
  thName.addEventListener("click", () => {
    sortKey = "_name";
    sortDesc = !sortDesc;
    buildTable();
  });
  headerRow.appendChild(thName);

  for (const col of visibleKeys) {
    const th = document.createElement("th");
    th.className = "sortable-th";
    const arrow = sortKey === col.key ? (sortDesc ? " ▼" : " ▲") : "";
    th.innerHTML = `${col.label}<span class="sort-arrow">${arrow}</span>`;
    th.addEventListener("click", () => {
      if (sortKey === col.key) { sortDesc = !sortDesc; }
      else { sortKey = col.key; sortDesc = true; }
      buildTable();
    });
    headerRow.appendChild(th);
  }

  // 이름 정렬
  if (sortKey === "_name") {
    sortedPlayers.sort((a, b) => sortDesc ? b.localeCompare(a) : a.localeCompare(b));
  }

  // 바디
  const tbody = document.getElementById("totalStatsBody");
  tbody.innerHTML = "";

  for (const player of sortedPlayers) {
    const row = document.createElement("tr");

    const tdName = document.createElement("td");
    tdName.innerHTML = `<a href="/stats_page/${encodeURIComponent(player)}?season=${currentSeason}" style="text-decoration:none;color:var(--text-link);font-weight:600;">${player}</a>`;
    row.appendChild(tdName);

    for (const col of visibleKeys) {
      const td = document.createElement("td");
      const raw = _getStatVal(player, col.key);
      td.textContent = _formatCol(raw, col);

      // 최고/최저 하이라이팅
      const ext = colExtremes[col.key];
      if (ext && raw !== null && ext.max !== ext.min && col.higherIsBetter !== null && col.higherIsBetter !== undefined) {
        if (raw === ext.max) td.className = col.higherIsBetter ? "val-best" : "val-worst";
        else if (raw === ext.min) td.className = col.higherIsBetter ? "val-worst" : "val-best";
      }

      row.appendChild(td);
    }
    tbody.appendChild(row);
  }
}

// ── 헬퍼 ──
function _getStatVal(player, key) {
  if (key === "_elo") {
    const elo = eloRatings[player];
    return elo ? Math.round(elo) : null;
  }
  const raw = getNestedValue(userStats[player] || {}, key);
  return typeof raw === "number" && !isNaN(raw) ? raw : null;
}

function _formatCol(raw, col) {
  if (raw === null || raw === undefined) return "-";
  if (col.key === "_elo") return Math.round(raw).toLocaleString();
  return formatValue(raw, col.format);
}

function showLoading() { document.getElementById("loading").style.display = "flex"; }
function hideLoading() { document.getElementById("loading").style.display = "none"; }
