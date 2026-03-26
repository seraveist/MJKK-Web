/**
 * gameLogViewer.js — 대국 기록 열람
 * - 시즌별 대국 목록
 * - 순위별 정렬 표시
 * - tenhou.net/5 패보 뷰어 링크 생성
 */

let currentSeason = window.config ? window.config.season : "all";

// URL 복원
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

// 시즌 탭
document.querySelectorAll(".season-tabs .tab").forEach(tab => {
  tab.addEventListener("click", function () {
    document.querySelectorAll(".season-tabs .tab").forEach(t => t.classList.remove("active"));
    this.classList.add("active");
    currentSeason = this.dataset.season;
    const p = new URLSearchParams(location.search);
    p.set("season", currentSeason);
    history.pushState({}, "", `?${p}`);
    loadGameLogs();
  });
});

window.addEventListener("popstate", () => {
  const s = new URLSearchParams(location.search).get("season");
  if (s) { currentSeason = s; syncTabUI(s); loadGameLogs(); }
});

document.addEventListener("DOMContentLoaded", () => loadGameLogs());

async function loadGameLogs() {
  document.getElementById("loading").style.display = "flex";
  const tbody = document.getElementById("logBody");
  const info = document.getElementById("logInfo");

  try {
    const res = await fetch(`/api/gamelogs?season=${currentSeason}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.error) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state">${
        data.error === "No game data found" ? "이 시즌의 대국 데이터가 없습니다." : data.error
      }</td></tr>`;
      info.textContent = "";
      return;
    }

    const logs = data.logs || [];
    info.textContent = `총 ${logs.length}국`;

    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty-state">대국 기록이 없습니다.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    logs.forEach(game => {
      const row = document.createElement("tr");

      // 날짜
      const tdDate = document.createElement("td");
      tdDate.textContent = game.date || "-";
      tdDate.style.whiteSpace = "nowrap";
      row.appendChild(tdDate);

      // 플레이어 순위별 표시
      const players = game.players || [];
      for (let i = 0; i < 4; i++) {
        const td = document.createElement("td");
        if (players[i]) {
          const p = players[i];
          td.innerHTML = `<span style="font-weight:500;">${p.name}</span><br>` +
            `<span style="font-size:11px;color:#888;">${p.score}` +
            `<span style="${p.point >= 0 ? 'color:#2563eb' : 'color:#dc2626'}">(${p.point >= 0 ? '+' : ''}${p.point.toFixed(1)})</span></span>`;
        } else {
          td.textContent = "-";
        }
        row.appendChild(td);
      }

      // 패보 링크 (tenhou + 작혼 일본 + 작혼 글로벌)
      const tdLink = document.createElement("td");
      tdLink.style.whiteSpace = "nowrap";
      if (game.viewer_url) {
        const aTenhou = document.createElement("a");
        aTenhou.href = game.viewer_url;
        aTenhou.target = "_blank";
        aTenhou.rel = "noopener";
        aTenhou.textContent = "tenhou";
        aTenhou.style.cssText = "color:#5b8def;font-weight:500;text-decoration:none;font-size:12px;";
        aTenhou.addEventListener("mouseenter", () => aTenhou.style.textDecoration = "underline");
        aTenhou.addEventListener("mouseleave", () => aTenhou.style.textDecoration = "none");
        tdLink.appendChild(aTenhou);
      }
      if (game.majsoul_url) {
        if (game.viewer_url) tdLink.appendChild(document.createTextNode(" / "));
        const aMjsJp = document.createElement("a");
        aMjsJp.href = game.majsoul_url;
        aMjsJp.target = "_blank";
        aMjsJp.rel = "noopener";
        aMjsJp.textContent = "작혼(일본)";
        aMjsJp.title = "작혼 로그인 필요";
        aMjsJp.style.cssText = "color:#888;font-weight:500;text-decoration:none;font-size:12px;";
        aMjsJp.addEventListener("mouseenter", () => aMjsJp.style.textDecoration = "underline");
        aMjsJp.addEventListener("mouseleave", () => aMjsJp.style.textDecoration = "none");
        tdLink.appendChild(aMjsJp);
      }
      if (game.majsoul_global_url) {
        tdLink.appendChild(document.createTextNode(" / "));
        const aMjsGl = document.createElement("a");
        aMjsGl.href = game.majsoul_global_url;
        aMjsGl.target = "_blank";
        aMjsGl.rel = "noopener";
        aMjsGl.textContent = "작혼(글로벌)";
        aMjsGl.title = "작혼 로그인 필요";
        aMjsGl.style.cssText = "color:#888;font-weight:500;text-decoration:none;font-size:12px;";
        aMjsGl.addEventListener("mouseenter", () => aMjsGl.style.textDecoration = "underline");
        aMjsGl.addEventListener("mouseleave", () => aMjsGl.style.textDecoration = "none");
        tdLink.appendChild(aMjsGl);
      }
      if (!game.viewer_url && !game.majsoul_url && !game.majsoul_global_url) {
        tdLink.textContent = "-";
        tdLink.style.color = "#ccc";
      }
      row.appendChild(tdLink);

      tbody.appendChild(row);
    });

  } catch (e) {
    console.error("Error:", e);
    tbody.innerHTML = `<tr><td colspan="6" class="error-state">데이터를 불러오는 중 오류가 발생했습니다.</td></tr>`;
    info.textContent = "";
  } finally {
    document.getElementById("loading").style.display = "none";
  }
}
