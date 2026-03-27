/**
 * gameDetail.js — 대국 상세 분석
 * - 점수 흐름 차트 (Chart.js)
 * - 국별 결과 요약
 */
const PLAYER_COLORS = ["#5b8def", "#ef6c6c", "#4ecdc4", "#f7b731"];

document.addEventListener("DOMContentLoaded", async () => {
  const ref = window.config.ref;
  if (!ref) return;

  document.getElementById("loading").style.display = "flex";
  try {
    const res = await fetch(`/api/gamedetail/${encodeURIComponent(ref)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.error) {
      document.getElementById("detailEmpty").textContent = data.error;
      document.getElementById("detailEmpty").style.display = "";
      return;
    }

    renderTitle(data);
    renderFinalResult(data);
    renderViewerLinks(data);
    renderScoreFlowChart(data);
    renderRoundsList(data);

  } catch (e) {
    console.error(e);
    document.getElementById("detailEmpty").textContent = "데이터를 불러오는 중 오류가 발생했습니다.";
    document.getElementById("detailEmpty").style.display = "";
  } finally {
    document.getElementById("loading").style.display = "none";
  }
});

function renderTitle(data) {
  document.getElementById("detailTitle").textContent = `대국 상세 — ${data.date || ""}`;
}

function renderFinalResult(data) {
  const container = document.getElementById("finalResult");
  // 점수 순 정렬
  const sorted = [...data.players].sort((a, b) => b.score - a.score);

  container.innerHTML = sorted.map((p, idx) => {
    const rank = idx + 1;
    const rankClass = `rank-${rank}`;
    const pointStr = p.point >= 0 ? `+${p.point.toFixed(1)}` : p.point.toFixed(1);
    const pointColor = p.point >= 0 ? "var(--color-best)" : "var(--color-worst)";
    return `<div class="player-card">
      <span class="rank ${rankClass}">${rank}위</span>
      <span style="font-weight:600;">${p.name}</span>
      <span style="color:var(--text-tertiary);font-size:12px;">${p.score.toLocaleString()}</span>
      <span style="color:${pointColor};font-size:13px;font-weight:600;">${pointStr}</span>
    </div>`;
  }).join("");
}

function renderViewerLinks(data) {
  const container = document.getElementById("viewerLinks");
  const links = [];
  if (data.viewer_url) links.push(`<a href="${data.viewer_url}" target="_blank" rel="noopener">천봉 패보 뷰어</a>`);
  if (data.majsoul_url) links.push(`<a href="${data.majsoul_url}" target="_blank" rel="noopener">작혼 (일본)</a>`);
  if (data.majsoul_global_url) links.push(`<a href="${data.majsoul_global_url}" target="_blank" rel="noopener">작혼 (글로벌)</a>`);
  container.innerHTML = links.join("");
}

function renderScoreFlowChart(data) {
  const rounds = data.rounds || [];
  const names = data.names || [];

  if (rounds.length === 0) return;

  // 누적 점수 변동 기반 차트
  const labels = ["시작", ...rounds.map(r => r.label)];
  const datasets = names.map((name, i) => {
    const scores = [0]; // 시작점
    rounds.forEach(r => {
      scores.push(r.cumulativeChanges[i] || 0);
    });
    return {
      label: name,
      data: scores,
      borderColor: PLAYER_COLORS[i % PLAYER_COLORS.length],
      backgroundColor: "transparent",
      tension: 0.3,
      pointRadius: 3,
      borderWidth: 2,
    };
  });

  const ctx = document.getElementById("scoreFlowChart").getContext("2d");
  new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "bottom", labels: { font: { size: 11 } } },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y >= 0 ? "+" : ""}${ctx.parsed.y.toLocaleString()}`,
          },
        },
      },
      scales: {
        x: { ticks: { maxTicksLimit: 12, font: { size: 10 } } },
        y: { title: { display: true, text: "점수 변동" } },
      },
    },
  });
}

function renderRoundsList(data) {
  const container = document.getElementById("roundsList");
  const rounds = data.rounds || [];
  const names = data.names || [];

  if (rounds.length === 0) {
    container.innerHTML = '<div class="empty-state">국별 데이터가 없습니다.</div>';
    return;
  }

  container.innerHTML = rounds.map(r => {
    const resultBadge = {
      tsumo: '<span class="result-badge result-tsumo">쯔모</span>',
      ron: '<span class="result-badge result-ron">론</span>',
      draw: '<span class="result-badge result-draw">유국</span>',
      win: '<span class="result-badge result-win">화료</span>',
      unknown: "",
    }[r.resultType] || "";

    const winnerName = r.winner >= 0 && r.winner < names.length ? names[r.winner] : "";

    const scores = names.map((name, i) => {
      const change = r.scoreChanges[i] || 0;
      const color = change > 0 ? "var(--color-best)" : change < 0 ? "var(--color-worst)" : "var(--text-tertiary)";
      const sign = change > 0 ? "+" : "";
      return `<div class="round-score">
        <div style="font-size:12px;color:var(--text-tertiary);">${name}</div>
        <div style="color:${color};font-weight:${change !== 0 ? 600 : 400};">${sign}${change.toLocaleString()}</div>
      </div>`;
    }).join("");

    return `<div class="round-row">
      <div class="round-label">${r.label}</div>
      <div style="min-width:70px;">${resultBadge}${winnerName ? ` <span style="font-size:12px;color:var(--text-secondary);">${winnerName}</span>` : ""}</div>
      <div class="round-scores">${scores}</div>
    </div>`;
  }).join("");
}
