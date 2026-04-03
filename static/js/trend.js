/**
 * trend.js — 우마 추이 + ELO 레이팅 + 시즌 비교 (v3)
 */
const CHART_COLORS = [
  "#5b8def","#ef6c6c","#4ecdc4","#f7b731","#a55eea",
  "#26de81","#fc5c65","#45aaf2","#fed330","#2bcbba",
  "#fd9644","#778ca3","#eb3b5a","#3867d6","#20bf6b","#8854d0","#fa8231",
];

let trendSeason = window.config.season;
let eloSeason = window.config.season;
let trendChart = null;
let eloChart = null;
let allPlayers = [];

// ── 메인 탭 전환 ──
document.querySelectorAll(".category-tabs .cat-tab").forEach(tab => {
  tab.addEventListener("click", function () {
    document.querySelectorAll(".category-tabs .cat-tab").forEach(t => t.classList.remove("active"));
    this.classList.add("active");
    const view = this.dataset.view;
    document.getElementById("trendView").style.display = view === "trend" ? "" : "none";
    document.getElementById("eloView").style.display = view === "elo" ? "" : "none";
    document.getElementById("seasonCmpView").style.display = view === "seasonCmp" ? "" : "none";
    document.getElementById("simulateView").style.display = view === "simulate" ? "" : "none";
    if (view === "elo") loadElo();
  });
});

// ── 초기화 ──
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("/stats/all");
    const data = await res.json();
    allPlayers = data.allPlayers || [];

    // 시즌 비교: 플레이어 셀렉트 (전체 유저)
    const sel = document.getElementById("seasonCmpPlayer");
    allPlayers.forEach(p => { const o = document.createElement("option"); o.value = p; o.textContent = p; sel.appendChild(o); });

    // 시뮬레이션 셀렉트 초기화
    ["simP1", "simP2", "simP3", "simP4"].forEach((id, idx) => {
      const s = document.getElementById(id);
      allPlayers.forEach(p => { const o = document.createElement("option"); o.value = p; o.textContent = p; s.appendChild(o); });
      if (allPlayers.length > idx) s.selectedIndex = idx;
    });

    // 활성 유저 기반 체크박스 빌드
    await rebuildPlayerChecks();

    // URL 파라미터로 탭 자동 전환
    const urlParams = new URLSearchParams(location.search);
    const viewParam = urlParams.get("view");
    const playerParam = urlParams.get("player");
    if (viewParam === "seasonCmp") {
      document.querySelectorAll(".category-tabs .cat-tab").forEach(t => {
        t.classList.toggle("active", t.dataset.view === "seasonCmp");
      });
      document.getElementById("trendView").style.display = "none";
      document.getElementById("eloView").style.display = "none";
      document.getElementById("seasonCmpView").style.display = "";
      document.getElementById("simulateView").style.display = "none";
      if (playerParam) sel.value = playerParam;
    } else {
      loadTrend();
    }
  } catch (e) { console.error(e); }
});

async function rebuildPlayerChecks() {
  // 현재 시즌 랭킹에서 대국 있는 유저만 추출
  let activePlayers = allPlayers;
  try {
    const rankRes = await fetch(`/ranking?season=${trendSeason}`);
    if (rankRes.ok) {
      const rankData = await rankRes.json();
      if (rankData.ranking) {
        const activeSet = new Set(rankData.ranking.filter(p => p.games > 0).map(p => p.name));
        activePlayers = allPlayers.filter(p => activeSet.has(p));
      }
    }
  } catch (e) { /* fallback to all */ }

  // 우마 추이 체크박스 재빌드
  const container = document.getElementById("trendPlayerChecks");
  container.innerHTML = "";
  activePlayers.forEach((p, i) => {
    const label = document.createElement("label");
    label.style.cssText = "display:flex;align-items:center;gap:4px;font-size:13px;cursor:pointer;";
    const cb = document.createElement("input");
    cb.type = "checkbox"; cb.value = p;
    if (i < 4) cb.checked = true;
    cb.addEventListener("change", loadTrend);
    label.appendChild(cb); label.append(p);
    container.appendChild(label);
  });

  // ELO 체크박스 재빌드
  const eloContainer = document.getElementById("eloPlayerChecks");
  eloContainer.innerHTML = "";
  activePlayers.forEach((p, i) => {
    const label = document.createElement("label");
    label.style.cssText = "display:flex;align-items:center;gap:4px;font-size:13px;cursor:pointer;";
    const cb = document.createElement("input");
    cb.type = "checkbox"; cb.value = p; cb.className = "elo-player-check";
    if (i < 4) cb.checked = true;
    cb.addEventListener("change", renderEloChart);
    label.appendChild(cb); label.append(p);
    eloContainer.appendChild(label);
  });
}

// ── 시즌 탭 (우마 추이) ──
document.querySelectorAll(".trend-season").forEach(tab => {
  tab.addEventListener("click", async function () {
    document.querySelectorAll(".trend-season").forEach(t => t.classList.remove("active"));
    this.classList.add("active");
    trendSeason = this.dataset.season;
    await rebuildPlayerChecks();
    loadTrend();
  });
});

// ── 시즌 탭 (ELO) ──
document.querySelectorAll(".elo-season").forEach(tab => {
  tab.addEventListener("click", async function () {
    document.querySelectorAll(".elo-season").forEach(t => t.classList.remove("active"));
    this.classList.add("active");
    eloSeason = this.dataset.season;
    trendSeason = this.dataset.season; // 체크박스 동기화용
    await rebuildPlayerChecks();
    loadElo();
  });
});

// ══════════════════════════════════════
// 우마 추이 차트
// ══════════════════════════════════════
async function loadTrend() {
  const selected = [...document.querySelectorAll("#trendPlayerChecks input:checked")].map(c => c.value);
  const emptyEl = document.getElementById("trendEmpty");

  if (selected.length === 0) {
    emptyEl.textContent = "플레이어를 선택해주세요."; emptyEl.style.display = "";
    if (trendChart) { trendChart.destroy(); trendChart = null; } return;
  }

  document.getElementById("loading").style.display = "flex";
  try {
    const res = await fetch(`/ranking?season=${trendSeason}`);
    const data = await res.json();
    if (data.error || !data.daily || data.daily.length === 0) {
      emptyEl.textContent = "이 시즌의 데이터가 없습니다."; emptyEl.style.display = "";
      if (trendChart) { trendChart.destroy(); trendChart = null; } return;
    }
    emptyEl.style.display = "none";
    const daily = [...data.daily].reverse();
    const datasets = selected.map((player, idx) => {
      let cum = 0;
      return { label: player, data: daily.map(d => { if (d.points[player] !== undefined) cum += d.points[player]; return cum; }),
        borderColor: CHART_COLORS[idx % CHART_COLORS.length], backgroundColor: "transparent", tension: 0.3, pointRadius: 2, borderWidth: 2 };
    });
    const ctx = document.getElementById("trendChart").getContext("2d");
    if (trendChart) trendChart.destroy();
    trendChart = new Chart(ctx, {
      type: "line", data: { labels: daily.map(d => (d.date || "").slice(0, 10)), datasets },
      options: { responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
        plugins: { legend: { position: "bottom", labels: { font: { size: 11 } } } },
        scales: { x: { ticks: { maxTicksLimit: 10, font: { size: 10 } } }, y: { title: { display: true, text: "누적 우마" } } } },
    });
  } catch (e) { console.error(e); emptyEl.textContent = "데이터 로드 오류"; emptyEl.style.display = "";
  } finally { document.getElementById("loading").style.display = "none"; }
}

// ══════════════════════════════════════
// ELO 레이팅
// ══════════════════════════════════════
let eloData = null;

async function loadElo(force) {
  document.getElementById("loading").style.display = "flex";
  const emptyEl = document.getElementById("eloEmpty");
  const infoEl = document.getElementById("eloInfo");
  if (force) infoEl.textContent = "재계산 중...";
  try {
    const url = `/api/elo?season=${eloSeason}${force ? "&force=1" : ""}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.error || !data.ratings) {
      emptyEl.textContent = "ELO 데이터가 없습니다."; emptyEl.style.display = "";
      document.getElementById("eloRankingWrap").style.display = "none";
      infoEl.textContent = "";
      return;
    }
    eloData = data;
    emptyEl.style.display = "none";
    document.getElementById("eloRankingWrap").style.display = "";

    // 업데이트 시각
    if (data.updated_at) {
      infoEl.textContent = `마지막 계산: ${data.updated_at.slice(0, 19).replace("T", " ")}`;
    } else {
      infoEl.textContent = force ? "계산 완료" : "";
    }

    // 레이팅 테이블
    const sorted = Object.entries(data.ratings).sort((a, b) => b[1] - a[1]);
    const tbody = document.getElementById("eloBody");
    tbody.innerHTML = "";
    sorted.forEach(([name, rating]) => {
      const diff = Math.round(rating - 1500);
      const color = diff > 0 ? "var(--color-best)" : diff < 0 ? "var(--color-worst)" : "var(--text-tertiary)";
      const sign = diff > 0 ? "+" : "";
      const row = document.createElement("tr");
      row.innerHTML = `<td>${name}</td><td style="font-weight:600;">${Math.round(rating)}</td>
        <td style="color:${color};font-weight:600;">${sign}${diff}</td>`;
      tbody.appendChild(row);
    });

    renderEloChart();
  } catch (e) { console.error(e); emptyEl.textContent = "ELO 로드 오류"; emptyEl.style.display = "";
  } finally { document.getElementById("loading").style.display = "none"; }
}

function renderEloChart() {
  if (!eloData || !eloData.history) return;
  const selected = [...document.querySelectorAll(".elo-player-check:checked")].map(c => c.value);
  if (selected.length === 0) { if (eloChart) { eloChart.destroy(); eloChart = null; } return; }

  const datasets = selected.map((player, idx) => {
    const hist = eloData.history[player] || [];
    return { label: player, data: hist.map(h => h.rating),
      borderColor: CHART_COLORS[idx % CHART_COLORS.length], backgroundColor: "transparent", tension: 0.3, pointRadius: 1, borderWidth: 2 };
  });

  const maxLen = Math.max(...selected.map(p => (eloData.history[p] || []).length));
  const labels = Array.from({ length: maxLen }, (_, i) => i + 1);

  const ctx = document.getElementById("eloChart").getContext("2d");
  if (eloChart) eloChart.destroy();
  eloChart = new Chart(ctx, {
    type: "line", data: { labels, datasets },
    options: { responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "bottom", labels: { font: { size: 11 } } } },
      scales: { x: { title: { display: true, text: "대국" }, ticks: { maxTicksLimit: 15, font: { size: 10 } } },
        y: { title: { display: true, text: "ELO 레이팅" } } } },
  });
}

// ══════════════════════════════════════
// 시즌 비교
// ══════════════════════════════════════
async function loadSeasonCompare() {
  const player = document.getElementById("seasonCmpPlayer").value;
  const seasons = [...document.querySelectorAll(".season-check:checked")].map(c => c.value);
  const emptyEl = document.getElementById("seasonCmpEmpty");
  const tableWrap = document.getElementById("seasonCmpTableWrap");

  if (!player || seasons.length === 0) {
    emptyEl.textContent = "플레이어와 시즌을 선택해주세요."; emptyEl.style.display = ""; tableWrap.style.display = "none"; return;
  }
  document.getElementById("loading").style.display = "flex";
  try {
    const results = await Promise.all(
      seasons.map(s => fetch(`/stats_api/${encodeURIComponent(player)}?season=${s}`).then(r => r.json()).then(d => ({ season: s, stats: d.error ? null : enrichStats(d.stats) })))
    );
    const valid = results.filter(r => r.stats);
    if (valid.length === 0) { emptyEl.textContent = "선택한 시즌에 데이터가 없습니다."; emptyEl.style.display = ""; tableWrap.style.display = "none"; return; }
    emptyEl.style.display = "none"; tableWrap.style.display = "";

    const header = document.getElementById("seasonCmpHeader");
    header.innerHTML = "<th>항목</th>";
    valid.forEach(r => { const th = document.createElement("th"); th.textContent = `시즌 ${r.season}`; header.appendChild(th); });

    const tbody = document.getElementById("seasonCmpBody");
    tbody.innerHTML = "";
    for (const [key, { label, format, higherIsBetter }] of Object.entries(display_keys)) {
      const values = valid.map(r => getNestedValue(r.stats, key));
      if (values.every(v => v === undefined)) continue;
      const row = document.createElement("tr");
      row.innerHTML = `<td>${label}</td>`;
      const nums = values.map(v => typeof v === "number" ? v : null);
      const validNums = nums.filter(v => v !== null);
      const maxV = validNums.length >= 2 ? Math.max(...validNums) : null;
      const minV = validNums.length >= 2 ? Math.min(...validNums) : null;
      values.forEach((v, i) => {
        const td = document.createElement("td");
        td.textContent = formatValue(v, format);
        if (higherIsBetter !== null && higherIsBetter !== undefined && maxV !== null && minV !== null && maxV !== minV) {
          if (nums[i] === maxV) td.className = higherIsBetter ? "val-best" : "val-worst";
          else if (nums[i] === minV) td.className = higherIsBetter ? "val-worst" : "val-best";
        }
        row.appendChild(td);
      });
      tbody.appendChild(row);
    }
  } catch (e) { console.error(e); emptyEl.textContent = "오류가 발생했습니다."; emptyEl.className = "error-state"; emptyEl.style.display = "";
  } finally { document.getElementById("loading").style.display = "none"; }
}

// ══════════════════════════════════════
// 대국 시뮬레이션
// ══════════════════════════════════════
let simChart = null;

async function runSimulation() {
  const players = ["simP1", "simP2", "simP3", "simP4"].map(id => document.getElementById(id).value);
  const unique = new Set(players);
  const emptyEl = document.getElementById("simEmpty");
  const resultEl = document.getElementById("simResult");

  if (unique.size !== 4) {
    emptyEl.textContent = "4명 모두 다른 플레이어를 선택해주세요.";
    emptyEl.style.display = "";
    resultEl.style.display = "none";
    return;
  }

  document.getElementById("loading").style.display = "flex";
  try {
    const res = await fetch(`/api/simulate?players=${players.join(",")}&season=${eloSeason}`);
    const data = await res.json();
    if (data.error) {
      emptyEl.textContent = data.error;
      emptyEl.style.display = "";
      resultEl.style.display = "none";
      return;
    }

    emptyEl.style.display = "none";
    resultEl.style.display = "";
    document.getElementById("simInfo").textContent = `${data.simulations.toLocaleString()}회 시뮬레이션 결과`;

    const labels = data.players.map(p => `${p.name} (${Math.round(p.rating)})`);
    const datasets = [
      { label: "1위", data: data.players.map(p => p.first), backgroundColor: "rgba(245,158,11,0.7)" },
      { label: "2위", data: data.players.map(p => p.second), backgroundColor: "rgba(91,141,239,0.7)" },
      { label: "3위", data: data.players.map(p => p.third), backgroundColor: "rgba(156,163,175,0.7)" },
      { label: "4위", data: data.players.map(p => p.fourth), backgroundColor: "rgba(239,108,108,0.7)" },
    ];

    const ctx = document.getElementById("simChart").getContext("2d");
    if (simChart) simChart.destroy();
    simChart = new Chart(ctx, {
      type: "bar",
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { stacked: true, ticks: { font: { size: 11 } } },
          y: { stacked: true, max: 100, title: { display: true, text: "확률 (%)" } },
        },
        plugins: {
          legend: { position: "bottom", labels: { font: { size: 11 } } },
          tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y}%` } },
        },
      },
    });
  } catch (e) {
    console.error(e);
    emptyEl.textContent = "시뮬레이션 오류";
    emptyEl.style.display = "";
  } finally {
    document.getElementById("loading").style.display = "none";
  }
}
