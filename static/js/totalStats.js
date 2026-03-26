const display_keys = {
    "games": { label: "대국 수", format: "int", category: "기본" },
    "kuksu": { label: "총합 국 수", format: "int", category: "기본" },
    "kuksuji" : { label: "국 수지", format: "int", category: "기본" },
    "total.avg": { label: "평균순위", format: "float", category: "기본" },
    "total_first_count": { label: "1위 횟수", format: "int", category: "기본" },
    "total_second_count": { label: "2위 횟수", format: "int", category: "기본" },
    "total_third_count": { label: "3위 횟수", format: "int", category: "기본" },
    "total_fourth_count": { label: "4위 횟수", format: "int", category: "기본" },
    "first_rate": { label: "1위율", format: "percent", category: "기본" },
    "second_rate": { label: "2위율", format: "percent", category: "기본" },
    "third_rate": { label: "3위율", format: "percent", category: "기본" },
    "fourth_rate": { label: "4위율", format: "percent", category: "기본" },
    "endScore.avg": { label: "최종 점수 평균", format: "int", category: "기본" },
    "endScore.max": { label: "최종 점수 최고", format: "int", category: "기본" },
    "endScore.min": { label: "최종 점수 최저", format: "int", category: "기본" },
    "minusScore.avg": { label: "토비율", format: "percent", category: "기본" },
    "minusOther.avg": { label: "타가 들통률", format: "percent", category: "기본" },
    "east.avg": { label: "동 시작 평균 순위", format: "float", category: "기본" },
    "south.avg": { label: "남 시작 평균 순위", format: "float", category: "기본" },
    "west.avg": { label: "서 시작 평균 순위", format: "float", category: "기본" },
    "north.avg": { label: "북 시작 평균 순위", format: "float", category: "기본" },
    "winGame.avg": { label: "화료율", format: "percent", category: "화료 및 방총" },
    "winGame_score.avg": { label: "평균 타점", format: "int", category: "화료 및 방총" },
    "winGame_host.per": { label: "오야 화료율", format: "percent", category: "화료 및 방총" },
    "winGame_zimo.per": { label: "쯔모율", format: "percent", category: "화료 및 방총" },
    "winGame_dama.per": { label: "다마율", format: "percent", category: "화료 및 방총" },
    "winGame_round.avg": { label: "평균 화료 순수", format: "float", category: "화료 및 방총" },
    "chong.avg": { label: "방총률", format: "percent", category: "화료 및 방총" },
    "chong_score.avg": { label: "평균 방총", format: "int", category: "화료 및 방총" },
    "chong_host.per": { label: "방총시 오야율", format: "percent", category: "화료 및 방총" },
    "chong_fulu.per": { label: "방총시 후로율", format: "percent", category: "화료 및 방총" },
    "chong_richi.per": { label: "방총시 리치율", format: "percent", category: "화료 및 방총" },
    "dehost.avg": { label: "오야카부리율", format: "percent", category: "화료 및 방총" },
    "dehost_score.avg": { label: "오야카부리 평균", format: "int", category: "화료 및 방총" },
    "otherZimo.avg": { label: "피쯔모율", format: "percent", category: "화료 및 방총" },
    "richi.avg": { label: "리치율", format: "percent", category: "리치 및 후로" },
    "richi_winGame.per": { label: "리치 성공률", format: "percent", category: "리치 및 후로" },
    "richi_score.avg": { label: "리치 수지", format: "int", category: "리치 및 후로" },
    "richi_yifa.per": { label: "일발률", format: "percent", category: "리치 및 후로" },
    "richi_rong.per": { label: "리치시 론률", format: "percent", category: "리치 및 후로" },
    "richi_zimo.per": { label: "리치시 쯔모율", format: "percent", category: "리치 및 후로" },
    "richi_chong.per": { label: "리치시 방총률", format: "percent", category: "리치 및 후로" },
    "richi_draw.per": { label: "리치시 유국률", format: "percent", category: "리치 및 후로" },
    "richi_otherZimo.per": { label: "리치시 타가 쯔모율", format: "percent", category: "리치 및 후로" },
    "richi_machi.per": { label: "리치 다면율", format: "percent", category: "리치 및 후로" },
    "richi_first.per": { label: "리치 선제율", format: "percent", category: "리치 및 후로"  },
    "fulu.avg": { label: "후로율", format: "percent", category: "리치 및 후로" },
    "fulu_score.avg": { label: "후로 수지", format: "int", category: "리치 및 후로" },
    "fulu_zimo.per": { label: "후로시 쯔모율", format: "percent", category: "리치 및 후로" },
    "fulu_rong.per": { label: "후로시 론율", format: "percent", category: "리치 및 후로" },
    "fulu_chong.per": { label: "후로시 방총률", format: "percent", category: "리치 및 후로" },
    "dora.avg": { label: "평균 전체 도라갯수", format: "float", category: "도라" },
    "dora_outer.avg": { label: "평균 도라갯수", format: "float", category: "도라" },
    "dora_akai.avg": { label: "평균 적도라갯수", format: "float", category: "도라" },
    "dora_inner.avg": { label: "평균 뒷도라갯수", format: "float", category: "도라" },
    "dora.per": { label: "전체 도라율", format: "percent", category: "도라" },
    "dora_outer.per": { label: "일반 도라율", format: "percent", category: "도라" },
    "dora_akai.per": { label: "적도라율", format: "percent", category: "도라" },
    "dora_inner.per": { label: "뒷도라율", format: "percent", category: "도라" },
    "dora.max": { label: "최대 전체 도라갯수", format: "int", category: "도라" },
    "dora_outer.max": { label: "최대 도라갯수", format: "int", category: "도라" },
    "dora_akai.max": { label: "최대 적도라갯수", format: "int", category: "도라" },
    "dora_inner.max": { label: "최대 뒷도라갯수", format: "int", category: "도라" },
    "dora_inner_eff.avg": { label: "뒷도라 평균 변화점", format: "int", category: "도라" },
    "dora_inner_eff.per": { label: "뒷도라 유효율", format: "percent", category: "도라" },
    "dora_inner_eff.max": { label: "뒷도라 최대 변화점", format: "int", category: "도라" }
    };

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
    
    // 값 포맷팅 함수
    function formatValue(value, format) {
      if (isNaN(value)) return "-";
      switch (format) {
        case "int":
          return Math.floor(value).toLocaleString();
        case "float":
          return value.toFixed(1);
        case "percent":
          return (value * 100).toFixed(1) + "%";
        default:
          return value.toString();
      }
    }
    
    // 로딩 표시/숨김 함수
    function showLoading() {
      document.getElementById("loading").style.display = "flex";
    }
    function hideLoading() {
      document.getElementById("loading").style.display = "none";
    }
