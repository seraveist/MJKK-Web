/**
 * compare.js — 플레이어 비교 (head-to-head)
 */
let currentSeason = window.config ? window.config.season : "all";
let currentCategory = "전체";

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
    history.pushState({}, "", `?${p}`);
  });
});

// 플레이어 목록 로드
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("/stats/all");
    const data = await res.json();
    const players = data.allPlayers || [];
    ["player1", "player2"].forEach((id, idx) => {
      const sel = document.getElementById(id);
      players.forEach(p => {
        const o = document.createElement("option");
        o.value = p; o.textContent = p;
        sel.appendChild(o);
      });
      if (players.length > idx + 1) sel.selectedIndex = idx;
    });

    // URL에서 플레이어 복원
    if (params.get("p1")) document.getElementById("player1").value = params.get("p1");
    if (params.get("p2")) document.getElementById("player2").value = params.get("p2");
    if (params.get("p1") && params.get("p2")) loadComparison();
  } catch (e) { console.error(e); }
});

async function loadComparison() {
  const p1 = document.getElementById("player1").value;
  const p2 = document.getElementById("player2").value;
  if (p1 === p2) {
    document.getElementById("compareResult").textContent = "다른 플레이어를 선택해주세요.";
    document.getElementById("compareResult").style.display = "";
    document.getElementById("compareTableWrap").style.display = "none";
    return;
  }

  // URL 업데이트
  const up = new URLSearchParams(location.search);
  up.set("season", currentSeason); up.set("p1", p1); up.set("p2", p2);
  history.pushState({}, "", `?${up}`);

  document.getElementById("loading").style.display = "flex";
  try {
    const [r1, r2] = await Promise.all([
      fetch(`/stats_api/${encodeURIComponent(p1)}?season=${currentSeason}`).then(r => r.json()),
      fetch(`/stats_api/${encodeURIComponent(p2)}?season=${currentSeason}`).then(r => r.json()),
    ]);

    if (r1.error || r2.error) {
      document.getElementById("compareResult").textContent = "데이터가 부족합니다.";
      document.getElementById("compareResult").style.display = "";
      document.getElementById("compareTableWrap").style.display = "none";
      return;
    }

    const s1 = enrichStats(r1.stats);
    const s2 = enrichStats(r2.stats);

    document.getElementById("p1Header").textContent = p1;
    document.getElementById("p2Header").textContent = p2;
    document.getElementById("compareResult").style.display = "none";
    document.getElementById("compareTableWrap").style.display = "";

    buildCatTabs();
    renderCompare(s1, s2);
  } catch (e) {
    console.error(e);
    document.getElementById("compareResult").textContent = "오류가 발생했습니다.";
    document.getElementById("compareResult").className = "error-state";
    document.getElementById("compareResult").style.display = "";
  } finally {
    document.getElementById("loading").style.display = "none";
  }
}

let cachedS1, cachedS2;
function renderCompare(s1, s2) {
  cachedS1 = s1; cachedS2 = s2;
  const tbody = document.getElementById("compareBody");
  tbody.innerHTML = "";

  for (const [key, { label, format, category, higherIsBetter }] of Object.entries(display_keys)) {
    if (currentCategory !== "전체" && category !== currentCategory) continue;

    const v1 = getNestedValue(s1, key);
    const v2 = getNestedValue(s2, key);
    if (v1 === undefined && v2 === undefined) continue;

    const row = document.createElement("tr");
    const tdLabel = document.createElement("td");
    tdLabel.textContent = label;

    const td1 = document.createElement("td");
    td1.textContent = formatValue(v1, format);

    const td2 = document.createElement("td");
    td2.textContent = formatValue(v2, format);

    // 더 좋은 쪽 하이라이팅
    if (higherIsBetter !== null && higherIsBetter !== undefined &&
        typeof v1 === "number" && typeof v2 === "number" && v1 !== v2) {
      const better1 = higherIsBetter ? v1 > v2 : v1 < v2;
      if (better1) { td1.className = "val-best"; td2.className = "val-worst"; }
      else { td2.className = "val-best"; td1.className = "val-worst"; }
    }

    row.appendChild(tdLabel);
    row.appendChild(td1);
    row.appendChild(td2);
    tbody.appendChild(row);
  }
}

function buildCatTabs() {
  const container = document.getElementById("compareCatTabs");
  container.innerHTML = "";
  ["전체", ...CATEGORIES].forEach(cat => {
    const btn = document.createElement("button");
    btn.className = "cat-tab" + (cat === currentCategory ? " active" : "");
    btn.textContent = cat;
    btn.addEventListener("click", () => {
      currentCategory = cat;
      document.querySelectorAll("#compareCatTabs .cat-tab").forEach(t => t.classList.remove("active"));
      btn.classList.add("active");
      if (cachedS1 && cachedS2) renderCompare(cachedS1, cachedS2);
    });
    container.appendChild(btn);
  });
}
