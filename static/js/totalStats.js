/**
 * totalStats.js — 전체 유저 통계
 * - 배치 API, 최고/최저 하이라이팅
 * - URL 상태 (season → 뒤로가기 지원)
 * - 에러/빈 상태 처리
 */

let currentSeason = window.config ? window.config.season : "all";
let allPlayers = [];
let userStats = {};

// URL에서 복원
const urlSeason = new URLSearchParams(location.search).get("season");
if (urlSeason) {
  currentSeason = urlSeason;
  syncTabUI(currentSeason);
}

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
    resetTable();
    loadTotalStats();
  }
});

// ── 시즌 탭 ──
document.querySelectorAll(".season-tabs .tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".season-tabs .tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    currentSeason = tab.dataset.season;
    pushState(currentSeason);
    resetTable();
    loadTotalStats();
  });
});

document.addEventListener("DOMContentLoaded", () => loadTotalStats());

function resetTable() {
  document.getElementById("colHeader").innerHTML = "<th>항목</th>";
  document.getElementById("totalStatsBody").innerHTML = "";
}

async function loadTotalStats() {
  showLoading();
  const tbody = document.getElementById("totalStatsBody");

  try {
    const res = await fetch(`/totalstats_api?season=${currentSeason}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();

    if (data.error) {
      tbody.innerHTML = `<tr><td class="empty-state">${
        data.error === "No game data found"
          ? "이 시즌의 대국 데이터가 없습니다."
          : data.error
      }</td></tr>`;
      return;
    }

    allPlayers = data.allPlayers || [];
    userStats = {};

    if (allPlayers.length === 0) {
      tbody.innerHTML = `<tr><td class="empty-state">통계를 표시할 플레이어가 없습니다.</td></tr>`;
      return;
    }

    for (const p of allPlayers) {
      if (data.stats[p]) userStats[p] = enrichStats(data.stats[p]);
    }
    buildTable();

  } catch (e) {
    console.error("Error:", e);
    tbody.innerHTML = `<tr><td class="error-state">데이터를 불러오는 중 오류가 발생했습니다.</td></tr>`;
  } finally {
    hideLoading();
  }
}

function buildTable() {
  // 헤더
  const headerRow = document.getElementById("colHeader");
  allPlayers.forEach(p => {
    const th = document.createElement("th");
    th.textContent = p;
    headerRow.appendChild(th);
  });

  // 바디
  const tbody = document.getElementById("totalStatsBody");
  tbody.innerHTML = "";

  for (const [key, { label, format, higherIsBetter }] of Object.entries(display_keys)) {
    const row = document.createElement("tr");

    const th = document.createElement("th");
    th.textContent = label;
    row.appendChild(th);

    const cells = [];
    const rawValues = [];

    allPlayers.forEach(player => {
      const td = document.createElement("td");
      const raw = getNestedValue(userStats[player] || {}, key);
      td.textContent = formatValue(raw, format);
      cells.push(td);
      rawValues.push(typeof raw === "number" && !isNaN(raw) ? raw : null);
      row.appendChild(td);
    });

    // 최고/최저 하이라이팅
    if (higherIsBetter !== null && higherIsBetter !== undefined) {
      const valid = rawValues.filter(v => v !== null);
      if (valid.length >= 2) {
        const maxVal = Math.max(...valid);
        const minVal = Math.min(...valid);
        if (maxVal !== minVal) {
          rawValues.forEach((v, i) => {
            if (v === null) return;
            if (v === maxVal) cells[i].className = higherIsBetter ? "val-best" : "val-worst";
            else if (v === minVal) cells[i].className = higherIsBetter ? "val-worst" : "val-best";
          });
        }
      }
    }

    tbody.appendChild(row);
  }
}

function showLoading() { document.getElementById("loading").style.display = "flex"; }
function hideLoading() { document.getElementById("loading").style.display = "none"; }
