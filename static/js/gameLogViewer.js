/**
 * gameLogViewer.js — 대국 기록 (v3)
 * - 페이지네이션, 배만/삼배만/역만 배지
 * - [신규] 날짜 구간 + 유저 필터
 */
let currentSeason = window.config ? window.config.season : "all";
let currentPage = 1;
const PER_PAGE = 30;
let seasonDates = { start: "", end: "" };
let filterDateFrom = "";
let filterDateTo = "";
let filterPlayer = "";

const urlSeason = new URLSearchParams(location.search).get("season");
if (urlSeason) { currentSeason = urlSeason; syncTabUI(currentSeason); }
const urlPage = new URLSearchParams(location.search).get("page");
if (urlPage) currentPage = parseInt(urlPage) || 1;

function syncTabUI(season) {
  document.querySelectorAll(".season-tabs .tab").forEach(t => {
    t.classList.toggle("active", t.dataset.season === String(season));
  });
}

document.querySelectorAll(".season-tabs .tab").forEach(tab => {
  tab.addEventListener("click", function () {
    document.querySelectorAll(".season-tabs .tab").forEach(t => t.classList.remove("active"));
    this.classList.add("active");
    currentSeason = this.dataset.season;
    currentPage = 1;
    resetFilter();
  });
});

window.addEventListener("popstate", () => {
  const p = new URLSearchParams(location.search);
  if (p.get("season")) { currentSeason = p.get("season"); syncTabUI(currentSeason); }
  if (p.get("page")) currentPage = parseInt(p.get("page")) || 1;
  loadGameLogs();
});

function updateURL() {
  const p = new URLSearchParams();
  p.set("season", currentSeason);
  if (currentPage > 1) p.set("page", currentPage);
  history.pushState({}, "", `?${p}`);
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("/stats/all");
    const data = await res.json();
    const sel = document.getElementById("playerFilter");
    (data.allPlayers || []).forEach(p => {
      const o = document.createElement("option");
      o.value = p; o.textContent = p;
      sel.appendChild(o);
    });
  } catch (e) { /* ignore */ }
  loadGameLogs();
});

async function loadGameLogs() {
  document.getElementById("loading").style.display = "flex";
  const tbody = document.getElementById("logBody");
  const info = document.getElementById("logInfo");

  try {
    let url = `/api/gamelogs?season=${currentSeason}&page=${currentPage}&per_page=${PER_PAGE}`;
    if (filterDateFrom) url += `&date_from=${filterDateFrom}`;
    if (filterDateTo) url += `&date_to=${filterDateTo}`;
    if (filterPlayer) url += `&player=${encodeURIComponent(filterPlayer)}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.season_dates) {
      seasonDates = data.season_dates;
      const fromEl = document.getElementById("dateFrom");
      const toEl = document.getElementById("dateTo");
      if (!filterDateFrom && seasonDates.start) fromEl.value = seasonDates.start;
      if (!filterDateTo && seasonDates.end) toEl.value = seasonDates.end;
      if (seasonDates.start) { fromEl.min = seasonDates.start; toEl.min = seasonDates.start; }
      if (seasonDates.end) { fromEl.max = seasonDates.end; toEl.max = seasonDates.end; }
    }

    if (data.error) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${data.error === "No game data found" ? "이 시즌의 대국 데이터가 없습니다." : data.error}</td></tr>`;
      info.textContent = "";
      document.getElementById("pagination").innerHTML = "";
      return;
    }

    const logs = data.logs || [];
    const pg = data.pagination || {};
    info.textContent = `총 ${pg.total || logs.length}국 (${pg.page || 1}/${pg.total_pages || 1} 페이지)`;

    if (logs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty-state">대국 기록이 없습니다.</td></tr>';
      document.getElementById("pagination").innerHTML = "";
      return;
    }

    tbody.innerHTML = "";
    const tierBadge = { "역만": "badge-yakuman", "삼배만": "badge-sanbaiman", "배만": "badge-baiman", "더블역만": "badge-double-yakuman", "트리플역만": "badge-double-yakuman" };

    logs.forEach(game => {
      const row = document.createElement("tr");
      const tdDate = document.createElement("td");
      tdDate.textContent = game.date || "-";
      tdDate.style.whiteSpace = "nowrap";
      row.appendChild(tdDate);

      const players = game.players || [];
      const bigHands = game.big_hands || {};

      for (let i = 0; i < 4; i++) {
        const td = document.createElement("td");
        if (players[i]) {
          const p = players[i];
          let badge = "";
          for (const [pName, bInfo] of Object.entries(bigHands)) {
            if (p.name === pName || (p.name && pName && p.name.includes(pName))) {
              const tier = typeof bInfo === "string" ? bInfo : bInfo.tier;
              const cls = tierBadge[tier] || (tier.includes("역만") ? "badge-double-yakuman" : "");
              badge = ` <span class="big-hand-badge ${cls}">${tier}</span>`;
              break;
            }
          }
          td.innerHTML = `<span style="font-weight:500;">${p.name}</span>${badge}<br>` +
            `<span style="font-size:12px;color:${p.score >= 0 ? "var(--color-best)" : "var(--color-worst)"};">${p.score >= 0 ? "+" : ""}${p.score.toLocaleString()}</span>` +
            `<span style="font-size:11px;color:var(--text-tertiary);margin-left:4px;">(${p.point >= 0 ? "+" : ""}${p.point.toFixed(1)})</span>`;
        }
        row.appendChild(td);
      }

      const tdLink = document.createElement("td");
      tdLink.style.whiteSpace = "nowrap";
      if (game.ref) {
        const a = document.createElement("a");
        a.href = `/games/${game.ref}`;
        a.textContent = "상세";
        a.className = "detail-link";
        a.style.cssText = "font-size:12px;margin-right:8px;";
        tdLink.appendChild(a);
      }
      if (game.viewer_url) {
        const a = document.createElement("a");
        a.href = game.viewer_url; a.target = "_blank"; a.rel = "noopener"; a.textContent = "tenhou";
        a.style.cssText = "color:var(--text-link);font-weight:500;text-decoration:none;font-size:12px;";
        tdLink.appendChild(a);
      }
      row.appendChild(tdLink);
      tbody.appendChild(row);
    });

    renderPagination(pg);

  } catch (e) {
    console.error("Error:", e);
    tbody.innerHTML = '<tr><td colspan="6" class="error-state">데이터를 불러오는 중 오류가 발생했습니다.</td></tr>';
    info.textContent = "";
  } finally {
    document.getElementById("loading").style.display = "none";
  }
}

function applyFilter() {
  const fromEl = document.getElementById("dateFrom");
  const toEl = document.getElementById("dateTo");
  let from = fromEl.value;
  let to = toEl.value;

  if (seasonDates.start && from && from < seasonDates.start) { from = seasonDates.start; fromEl.value = from; }
  if (seasonDates.end && to && to > seasonDates.end) { to = seasonDates.end; toEl.value = to; }
  if (from && to && from > to) { from = ""; to = ""; fromEl.value = ""; toEl.value = ""; }

  filterDateFrom = from;
  filterDateTo = to;
  filterPlayer = document.getElementById("playerFilter").value;
  currentPage = 1;
  updateURL();
  loadGameLogs();
}

function resetFilter() {
  filterDateFrom = "";
  filterDateTo = "";
  filterPlayer = "";
  document.getElementById("dateFrom").value = "";
  document.getElementById("dateTo").value = "";
  document.getElementById("playerFilter").value = "";
  currentPage = 1;
  updateURL();
  loadGameLogs();
}

function renderPagination(pg) {
  const container = document.getElementById("pagination");
  if (!pg || pg.total_pages <= 1) { container.innerHTML = ""; return; }

  let html = "";
  if (pg.page > 1) html += `<button class="pg-btn" onclick="goPage(${pg.page - 1})">이전</button>`;
  const start = Math.max(1, pg.page - 2);
  const end = Math.min(pg.total_pages, pg.page + 2);
  for (let i = start; i <= end; i++) {
    html += `<button class="pg-btn${i === pg.page ? " pg-active" : ""}" onclick="goPage(${i})">${i}</button>`;
  }
  if (pg.page < pg.total_pages) html += `<button class="pg-btn" onclick="goPage(${pg.page + 1})">다음</button>`;
  container.innerHTML = html;
}

function goPage(page) {
  currentPage = page;
  updateURL();
  loadGameLogs();
  window.scrollTo(0, 0);
}
