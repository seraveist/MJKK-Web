/**
 * trend.js — 우마 추이 + 시즌 비교
 */
const CHART_COLORS = [
  "#5b8def", "#ef6c6c", "#4ecdc4", "#f7b731", "#a55eea",
  "#26de81", "#fc5c65", "#45aaf2", "#fed330", "#2bcbba",
  "#fd9644", "#778ca3", "#eb3b5a", "#3867d6", "#20bf6b",
  "#8854d0", "#fa8231",
];

let trendSeason = window.config.season;
let trendChart = null;
let allPlayers = [];

// ── 메인 탭 전환 ──
document.querySelectorAll(".category-tabs .cat-tab").forEach(tab => {
  tab.addEventListener("click", function () {
    document.querySelectorAll(".category-tabs .cat-tab").forEach(t => t.classList.remove("active"));
    this.classList.add("active");
    const view = this.dataset.view;
    document.getElementById("trendView").style.display = view === "trend" ? "" : "none";
    document.getElementById("seasonCmpView").style.display = view === "seasonCmp" ? "" : "none";
  });
});

// ── 초기화 ──
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("/stats/all");
    const data = await res.json();
    allPlayers = data.allPlayers || [];

    // 우마 추이: 체크박스 생성
    const container = document.getElementById("trendPlayerChecks");
    allPlayers.forEach((p, i) => {
      const label = document.createElement("label");
      label.style.cssText = "display:flex;align-items:center;gap:4px;font-size:13px;cursor:pointer;";
      const cb = document.createElement("input");
      cb.type = "checkbox"; cb.value = p;
      if (i < 4) cb.checked = true; // 처음 4명 기본 선택
      cb.addEventListener("change", loadTrend);
      label.appendChild(cb);
      label.append(p);
      container.appendChild(label);
    });

    // 시즌 비교: 플레이어 셀렉트
    const sel = document.getElementById("seasonCmpPlayer");
    allPlayers.forEach(p => {
      const o = document.createElement("option");
      o.value = p; o.textContent = p;
      sel.appendChild(o);
    });

    loadTrend();
  } catch (e) { console.error(e); }
});

// ── 시즌 탭 (우마 추이) ──
document.querySelectorAll(".trend-season").forEach(tab => {
  tab.addEventListener("click", function () {
    document.querySelectorAll(".trend-season").forEach(t => t.classList.remove("active"));
    this.classList.add("active");
    trendSeason = this.dataset.season;
    loadTrend();
  });
});

// ══════════════════════════════════════
// 우마 추이 차트
// ══════════════════════════════════════
async function loadTrend() {
  const selected = [...document.querySelectorAll("#trendPlayerChecks input:checked")].map(c => c.value);
  const emptyEl = document.getElementById("trendEmpty");

  if (selected.length === 0) {
    emptyEl.textContent = "플레이어를 선택해주세요.";
    emptyEl.style.display = "";
    if (trendChart) { trendChart.destroy(); trendChart = null; }
    return;
  }

  document.getElementById("loading").style.display = "flex";
  try {
    const res = await fetch(`/ranking?season=${trendSeason}`);
    const data = await res.json();
    if (data.error || !data.daily || data.daily.length === 0) {
      emptyEl.textContent = "이 시즌의 데이터가 없습니다.";
      emptyEl.style.display = "";
      if (trendChart) { trendChart.destroy(); trendChart = null; }
      return;
    }

    emptyEl.style.display = "none";

    // daily를 날짜순(오래된→최신)으로 정렬
    const daily = [...data.daily].reverse();

    // 누적 우마 계산
    const datasets = selected.map((player, idx) => {
      let cumulative = 0;
      const points = daily.map(d => {
        const val = d.points[player];
        if (val !== undefined) cumulative += val;
        return cumulative;
      });
      return {
        label: player,
        data: points,
        borderColor: CHART_COLORS[idx % CHART_COLORS.length],
        backgroundColor: "transparent",
        tension: 0.3,
        pointRadius: 2,
        borderWidth: 2,
      };
    });

    const labels = daily.map(d => d.date);

    const ctx = document.getElementById("trendChart").getContext("2d");
    if (trendChart) trendChart.destroy();
    trendChart = new Chart(ctx, {
      type: "line",
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { position: "bottom", labels: { font: { size: 11 } } },
        },
        scales: {
          x: { display: true, ticks: { maxTicksLimit: 10, font: { size: 10 } } },
          y: { title: { display: true, text: "누적 우마" } },
        },
      },
    });
  } catch (e) {
    console.error(e);
    emptyEl.textContent = "데이터 로드 오류";
    emptyEl.style.display = "";
  } finally {
    document.getElementById("loading").style.display = "none";
  }
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
    emptyEl.textContent = "플레이어와 시즌을 선택해주세요.";
    emptyEl.style.display = "";
    tableWrap.style.display = "none";
    return;
  }

  document.getElementById("loading").style.display = "flex";
  try {
    // 선택한 시즌별로 통계 API 호출
    const results = await Promise.all(
      seasons.map(s =>
        fetch(`/stats_api/${encodeURIComponent(player)}?season=${s}`)
          .then(r => r.json())
          .then(d => ({ season: s, stats: d.error ? null : enrichStats(d.stats) }))
      )
    );

    const validResults = results.filter(r => r.stats);
    if (validResults.length === 0) {
      emptyEl.textContent = "선택한 시즌에 데이터가 없습니다.";
      emptyEl.style.display = "";
      tableWrap.style.display = "none";
      return;
    }

    emptyEl.style.display = "none";
    tableWrap.style.display = "";

    // 헤더
    const header = document.getElementById("seasonCmpHeader");
    header.innerHTML = "<th>항목</th>";
    validResults.forEach(r => {
      const th = document.createElement("th");
      th.textContent = `시즌 ${r.season}`;
      header.appendChild(th);
    });

    // 바디
    const tbody = document.getElementById("seasonCmpBody");
    tbody.innerHTML = "";

    for (const [key, { label, format, higherIsBetter }] of Object.entries(display_keys)) {
      const values = validResults.map(r => getNestedValue(r.stats, key));
      if (values.every(v => v === undefined)) continue;

      const row = document.createElement("tr");
      const tdLabel = document.createElement("td");
      tdLabel.textContent = label;
      row.appendChild(tdLabel);

      const numericVals = values.map(v => typeof v === "number" ? v : null);
      const validNums = numericVals.filter(v => v !== null);
      const maxVal = validNums.length >= 2 ? Math.max(...validNums) : null;
      const minVal = validNums.length >= 2 ? Math.min(...validNums) : null;

      values.forEach((v, i) => {
        const td = document.createElement("td");
        td.textContent = formatValue(v, format);

        if (higherIsBetter !== null && higherIsBetter !== undefined &&
            maxVal !== null && minVal !== null && maxVal !== minVal) {
          if (numericVals[i] === maxVal) td.className = higherIsBetter ? "val-best" : "val-worst";
          else if (numericVals[i] === minVal) td.className = higherIsBetter ? "val-worst" : "val-best";
        }

        row.appendChild(td);
      });

      tbody.appendChild(row);
    }
  } catch (e) {
    console.error(e);
    emptyEl.textContent = "오류가 발생했습니다.";
    emptyEl.className = "error-state";
    emptyEl.style.display = "";
  } finally {
    document.getElementById("loading").style.display = "none";
  }
}
