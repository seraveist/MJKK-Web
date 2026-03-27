/**
 * matchup.js — 상성 분석
 * 같은 탁에서 마주쳤을 때의 승률/순위 분석
 */
let currentSeason = window.config ? window.config.season : "all";

// URL 복원
const params = new URLSearchParams(location.search);
if (params.get("season")) currentSeason = params.get("season");

// 시즌 탭
document.querySelectorAll(".season-tabs .tab").forEach(tab => {
  tab.addEventListener("click", function () {
    document.querySelectorAll(".season-tabs .tab").forEach(t => t.classList.remove("active"));
    this.classList.add("active");
    currentSeason = this.dataset.season;
    const p = new URLSearchParams(location.search);
    p.set("season", currentSeason);
    if (params.get("p1")) p.set("p1", params.get("p1"));
    if (params.get("p2")) p.set("p2", params.get("p2"));
    history.pushState({}, "", `?${p}`);
  });
});

// 초기화
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("/stats/all");
    const data = await res.json();
    const players = data.allPlayers || [];
    ["matchP1", "matchP2"].forEach((id, idx) => {
      const sel = document.getElementById(id);
      players.forEach(p => {
        const o = document.createElement("option");
        o.value = p; o.textContent = p;
        sel.appendChild(o);
      });
      if (players.length > idx + 1) sel.selectedIndex = idx;
    });

    // URL에서 복원
    if (params.get("p1")) document.getElementById("matchP1").value = params.get("p1");
    if (params.get("p2")) document.getElementById("matchP2").value = params.get("p2");
    if (params.get("p1") && params.get("p2")) loadMatchup();
  } catch (e) { console.error(e); }
});

async function loadMatchup() {
  const p1 = document.getElementById("matchP1").value;
  const p2 = document.getElementById("matchP2").value;

  if (p1 === p2) {
    document.getElementById("matchupResult").textContent = "다른 플레이어를 선택해주세요.";
    document.getElementById("matchupResult").style.display = "";
    document.getElementById("matchupSummary").style.display = "none";
    return;
  }

  // URL 업데이트
  const up = new URLSearchParams(location.search);
  up.set("season", currentSeason); up.set("p1", p1); up.set("p2", p2);
  history.pushState({}, "", `?${up}`);

  document.getElementById("loading").style.display = "flex";
  try {
    const res = await fetch(`/api/matchup?p1=${encodeURIComponent(p1)}&p2=${encodeURIComponent(p2)}&season=${currentSeason}`);
    const data = await res.json();

    if (data.error || data.totalGames === 0) {
      document.getElementById("matchupResult").textContent =
        data.message || data.error || "같은 탁에서 대국한 기록이 없습니다.";
      document.getElementById("matchupResult").style.display = "";
      document.getElementById("matchupSummary").style.display = "none";
      return;
    }

    document.getElementById("matchupResult").style.display = "none";
    document.getElementById("matchupSummary").style.display = "";

    renderSummaryCards(data);
    renderStatsTable(data);
    renderGamesTable(data);

  } catch (e) {
    console.error(e);
    document.getElementById("matchupResult").textContent = "오류가 발생했습니다.";
    document.getElementById("matchupResult").className = "error-state";
    document.getElementById("matchupResult").style.display = "";
  } finally {
    document.getElementById("loading").style.display = "none";
  }
}

function renderSummaryCards(data) {
  const s = data.stats;
  const container = document.getElementById("summaryCards");

  const cards = [
    {
      label: "동탁 대국 수",
      value: `${data.totalGames}국`,
      sub: "",
    },
    {
      label: "상대 전적",
      value: `${s.p1_wins} : ${s.draws} : ${s.p2_wins}`,
      sub: `${data.p1} ${s.p1_win_rate}% — ${data.p2} ${s.p2_win_rate}%`,
    },
    {
      label: "평균 순위",
      value: `${s.p1_avg_rank} vs ${s.p2_avg_rank}`,
      sub: s.p1_avg_rank < s.p2_avg_rank ? `${data.p1} 우세` :
           s.p2_avg_rank < s.p1_avg_rank ? `${data.p2} 우세` : "동등",
    },
    {
      label: "평균 우마",
      value: `${s.p1_avg_point > 0 ? "+" : ""}${s.p1_avg_point} vs ${s.p2_avg_point > 0 ? "+" : ""}${s.p2_avg_point}`,
      sub: "",
    },
  ];

  container.innerHTML = cards.map(c => `
    <div style="background:var(--bg-table-header);border-radius:10px;padding:16px;text-align:center;">
      <div style="font-size:12px;color:var(--text-tertiary);margin-bottom:6px;">${c.label}</div>
      <div style="font-size:20px;font-weight:700;color:var(--text-heading);">${c.value}</div>
      ${c.sub ? `<div style="font-size:11px;color:var(--text-tertiary);margin-top:4px;">${c.sub}</div>` : ""}
    </div>
  `).join("");
}

function renderStatsTable(data) {
  const s = data.stats;
  document.getElementById("mh1").textContent = data.p1;
  document.getElementById("mh2").textContent = data.p2;

  const rows = [
    ["평균 순위", s.p1_avg_rank, s.p2_avg_rank, false],
    ["평균 우마", s.p1_avg_point, s.p2_avg_point, true],
    ["우마 합산", s.p1_total_point, s.p2_total_point, true],
    ["상위 순위 횟수 (승)", s.p1_wins, s.p2_wins, true],
    ["1위 횟수", `${s.p1_first_count} (${s.p1_first_rate}%)`, `${s.p2_first_count} (${s.p2_first_rate}%)`, null],
    ["4위 횟수", `${s.p1_last_count} (${s.p1_last_rate}%)`, `${s.p2_last_count} (${s.p2_last_rate}%)`, null],
  ];

  const tbody = document.getElementById("matchupBody");
  tbody.innerHTML = "";
  rows.forEach(([label, v1, v2, higherBetter]) => {
    const row = document.createElement("tr");
    const td0 = document.createElement("td"); td0.textContent = label;
    const td1 = document.createElement("td");
    const td2 = document.createElement("td");

    if (typeof v1 === "number") {
      td1.textContent = v1 % 1 === 0 ? v1 : v1.toFixed(2);
      td2.textContent = v2 % 1 === 0 ? v2 : v2.toFixed(2);
      if (higherBetter !== null && v1 !== v2) {
        const p1Better = higherBetter ? v1 > v2 : v1 < v2;
        if (p1Better) { td1.className = "val-best"; td2.className = "val-worst"; }
        else { td2.className = "val-best"; td1.className = "val-worst"; }
      }
    } else {
      td1.textContent = v1;
      td2.textContent = v2;
    }

    row.append(td0, td1, td2);
    tbody.appendChild(row);
  });
}

function renderGamesTable(data) {
  document.getElementById("gh1").textContent = `${data.p1} 순위`;
  document.getElementById("gh2").textContent = `${data.p2} 순위`;
  const tbody = document.getElementById("matchupGamesBody");
  tbody.innerHTML = "";

  data.games.forEach(g => {
    const row = document.createElement("tr");
    const rankStyle = (r) => r === 1 ? "font-weight:600;color:var(--color-best);" : r === 4 ? "color:var(--color-worst);" : "";
    const pointColor = (p) => p >= 0 ? "color:var(--color-best);" : "color:var(--color-worst);";

    row.innerHTML = `
      <td style="white-space:nowrap;">${g.date || "-"}</td>
      <td style="${rankStyle(g.p1_rank)}">${g.p1_rank}위</td>
      <td style="${rankStyle(g.p2_rank)}">${g.p2_rank}위</td>
      <td style="${pointColor(g.p1_point)}">${g.p1_point >= 0 ? "+" : ""}${g.p1_point.toFixed(1)}</td>
      <td style="${pointColor(g.p2_point)}">${g.p2_point >= 0 ? "+" : ""}${g.p2_point.toFixed(1)}</td>
    `;
    tbody.appendChild(row);
  });
}
