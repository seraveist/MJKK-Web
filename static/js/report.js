/**
 * report.js — 시즌 리포트
 */
let currentSeason = window.config.season;

document.querySelectorAll(".season-tabs .tab").forEach(tab => {
  tab.addEventListener("click", function () {
    document.querySelectorAll(".season-tabs .tab").forEach(t => t.classList.remove("active"));
    this.classList.add("active");
    currentSeason = this.dataset.season;
    loadReport();
  });
});

document.addEventListener("DOMContentLoaded", loadReport);

async function loadReport() {
  document.getElementById("loading").style.display = "flex";
  const container = document.getElementById("reportContent");
  const emptyEl = document.getElementById("reportEmpty");

  try {
    const res = await fetch(`/api/report?season=${currentSeason}`);
    const data = await res.json();
    if (data.error) { emptyEl.style.display = ""; container.innerHTML = ""; return; }

    emptyEl.style.display = "none";
    document.getElementById("reportTitle").textContent = `시즌 ${data.season} 리포트`;

    let html = "";

    // 요약
    html += `<div class="report-section">
      <h2>시즌 요약</h2>
      <div style="font-size:14px;color:var(--text-secondary);">
        총 <strong>${data.summary.total_games}</strong>국 · <strong>${data.summary.total_players}</strong>명 참가
      </div>
    </div>`;

    // 어워드
    if (data.awards && data.awards.length > 0) {
      html += `<div class="report-section"><h2>시즌 어워드</h2><div class="report-award-grid">`;
      data.awards.forEach(a => {
        html += `<div class="report-award"><div class="ra-title">${a.title}</div><div class="ra-winner">${a.winner}</div><div class="ra-value">${a.value}</div></div>`;
      });
      html += `</div></div>`;
    }

    // 랭킹
    if (data.ranking && data.ranking.length > 0) {
      html += `<div class="report-section"><h2>최종 순위</h2><table><thead><tr><th>#</th><th>이름</th><th>대국</th><th>우마 평균</th></tr></thead><tbody>`;
      data.ranking.forEach((p, i) => {
        const color = p.point_avg >= 0 ? "var(--color-best)" : "var(--color-worst)";
        html += `<tr><td>${i + 1}</td><td>${p.name}</td><td>${p.games}</td><td style="color:${color};font-weight:600;">${p.point_avg >= 0 ? "+" : ""}${p.point_avg.toFixed(2)}</td></tr>`;
      });
      html += `</tbody></table></div>`;
    }

    // ELO
    if (data.elo && Object.keys(data.elo).length > 0) {
      const entries = Object.entries(data.elo);
      const maxElo = Math.max(...entries.map(e => e[1]));
      const minElo = Math.min(...entries.map(e => e[1]));
      const range = maxElo - minElo || 1;
      html += `<div class="report-section"><h2>ELO 레이팅</h2>`;
      entries.forEach(([name, elo]) => {
        const pct = Math.max(10, ((elo - minElo) / range) * 100);
        html += `<div class="elo-bar"><span class="eb-name">${name}</span><div class="eb-fill" style="width:${pct}%;"></div><span class="eb-val">${Math.round(elo)}</span></div>`;
      });
      html += `</div>`;
    }

    // 하이라이트
    if (data.highlights && data.highlights.length > 0) {
      html += `<div class="report-section"><h2>역만 / 삼배만 기록</h2>`;
      data.highlights.forEach(h => {
        const cls = h.tier === "삼배만" ? "hl-sanbaiman" : h.tier === "역만" ? "hl-yakuman" : "hl-double-yakuman";
        const yakuStr = h.tier.includes("역만") && h.yakus && h.yakus.length > 0 ? ` <span style="font-size:11px;color:var(--color-accent);">(${h.yakus.join(", ")})</span>` : "";
        const detailBtn = h.ref ? ` <a href="/games/${h.ref}" style="font-size:11px;color:var(--text-link);text-decoration:none;margin-left:4px;">상세 →</a>` : "";
        html += `<div class="hl-item"><span class="hl-date">${h.date}</span><span class="hl-badge ${cls}">${h.tier}</span><span style="font-weight:500;">${h.player}</span>${yakuStr}${detailBtn}</div>`;
      });
      html += `</div>`;
    }

    container.innerHTML = html;
  } catch (e) {
    console.error(e);
    emptyEl.textContent = "리포트 로드 오류";
    emptyEl.style.display = "";
  } finally {
    document.getElementById("loading").style.display = "none";
  }
}
