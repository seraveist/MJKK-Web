/**
 * ranking.js — 대시보드 (랭킹 + 날짜별 점수)
 * - 에러/빈 상태 처리
 * - URL 상태 관리 (뒤로가기 지원)
 */
document.addEventListener("DOMContentLoaded", () => {
  let currentSeason = window.config ? window.config.season : "all";

  // URL에서 시즌 복원
  const urlSeason = new URLSearchParams(location.search).get("season");
  if (urlSeason) {
    currentSeason = urlSeason;
    syncTabUI(currentSeason);
  }

  // ── 시즌 탭 ──
  document.querySelectorAll(".season-tabs .tab").forEach(tab => {
    tab.addEventListener("click", function () {
      document.querySelectorAll(".season-tabs .tab").forEach(t => t.classList.remove("active"));
      this.classList.add("active");
      currentSeason = this.dataset.season;
      pushState({ season: currentSeason });
      loadRanking();
    });
  });

  // 뒤로가기/앞으로가기
  window.addEventListener("popstate", (e) => {
    if (e.state && e.state.season) {
      currentSeason = e.state.season;
      syncTabUI(currentSeason);
      loadRanking();
    }
  });

  function syncTabUI(season) {
    document.querySelectorAll(".season-tabs .tab").forEach(t => {
      t.classList.toggle("active", t.dataset.season === String(season));
    });
  }

  function pushState(state) {
    const params = new URLSearchParams(location.search);
    params.set("season", state.season);
    history.pushState(state, "", `?${params}`);
  }

  // ── 로딩/에러/빈 상태 ──
  function showLoading() {
    const el = document.getElementById("loading");
    if (el) el.style.display = "flex";
  }
  function hideLoading() {
    const el = document.getElementById("loading");
    if (el) el.style.display = "none";
  }

  function showEmptyState(container, message) {
    container.innerHTML = `<tr><td colspan="10" class="empty-state">${message}</td></tr>`;
  }

  function showErrorState(container, message) {
    container.innerHTML = `<tr><td colspan="10" class="error-state">${message}</td></tr>`;
  }

  // ── 랭킹 로드 ──
  async function loadRanking() {
    showLoading();
    const rankingBody = document.getElementById("rankingBody");
    const dateScoreBody = document.getElementById("dateScoreBody");
    const rankingInfo = document.getElementById("rankingInfo");

    try {
      const res = await fetch("/ranking?season=" + currentSeason);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();

      if (data.error) {
        showEmptyState(rankingBody, "이 시즌의 대국 데이터가 없습니다.");
        showEmptyState(dateScoreBody, "");
        if (rankingInfo) rankingInfo.textContent = "";
        return;
      }

      // 랭킹 테이블
      if (rankingBody) {
        rankingBody.innerHTML = "";
        const filtered = data.ranking.filter(p => p.games > 0);

        if (filtered.length === 0) {
          showEmptyState(rankingBody, "이 시즌에 대국 기록이 있는 플레이어가 없습니다.");
        } else {
          // 최고치 계산
          const maxSum = Math.max(...filtered.map(p => p.point_sum));
          const maxAvg = Math.max(...filtered.map(p => p.point_avg));

          filtered.forEach((player, i) => {
            const row = document.createElement("tr");
            const sumClass = player.point_sum === maxSum ? "val-best" : "";
            const avgClass = player.point_avg === maxAvg ? "val-best" : "";
            row.innerHTML = `
              <td><a href="/stats_page/${encodeURIComponent(player.name)}?season=${currentSeason}" style="color:#1a1a2e;font-weight:700;text-decoration:none;">${player.name}</a></td>
              <td>${player.games}</td>
              <td class="${sumClass}">${player.point_sum.toFixed(1)}</td>
              <td class="${avgClass}">${player.point_avg.toFixed(1)}</td>
            `;
            rankingBody.appendChild(row);
          });

          // 총 대국수
          const totalGamesRaw = filtered.reduce((s, p) => s + p.games, 0);
          const totalGames = Math.floor(totalGamesRaw / 4);
          const regulatedGames = Math.floor(totalGames * 0.3);
          if (rankingInfo) {
            rankingInfo.textContent = `규정 대국 수 ${regulatedGames} / 총 대국 수 ${totalGames}`;
          }
        }
      }

      // 날짜별 점수
      const headerElem = document.getElementById("dateScoreHeader");
      if (headerElem) {
        const headerRow = headerElem.querySelector("tr");
        if (headerRow) {
          headerRow.innerHTML = "<th>날짜</th>";
          (data.players || []).forEach(name => {
            const th = document.createElement("th");
            th.textContent = name;
            headerRow.appendChild(th);
          });
        }
      }

      if (dateScoreBody) {
        dateScoreBody.innerHTML = "";
        const daily = data.daily || [];
        if (daily.length === 0) {
          showEmptyState(dateScoreBody, "날짜별 점수 데이터가 없습니다.");
        } else {
          daily.forEach(entry => {
            const row = document.createElement("tr");
            const dateCell = document.createElement("td");
            dateCell.textContent = entry.date.split("-")[0];

            // 날짜 클릭 → 패보 재생 팝업
            if (entry.ref) {
              dateCell.style.cursor = "pointer";
              dateCell.style.color = "#5b8def";
              dateCell.style.textDecoration = "underline";
              dateCell.style.textDecorationStyle = "dotted";
              dateCell.addEventListener("click", (e) => {
                e.stopPropagation();
                showViewerPopup(e, entry.ref);
              });
            }

            row.appendChild(dateCell);
            (data.players || []).forEach(name => {
              const td = document.createElement("td");
              const val = entry.points[name];
              if (val !== undefined) {
                td.textContent = val.toFixed(1);
                if (val > 0) td.className = "val-best";
                else if (val < 0) td.className = "val-worst";
              } else {
                td.textContent = "-";
                td.style.color = "#ccc";
              }
              row.appendChild(td);
            });
            dateScoreBody.appendChild(row);
          });
        }
      }

    } catch (error) {
      console.error("Error loading ranking:", error);
      if (rankingBody) showErrorState(rankingBody, "데이터를 불러오는 중 오류가 발생했습니다.");
      if (dateScoreBody) dateScoreBody.innerHTML = "";
      if (rankingInfo) rankingInfo.textContent = "";
    } finally {
      hideLoading();
    }
  }

  loadRanking();

  // ── 패보 재생 팝업 ──
  let activePopup = null;

  function closePopup() {
    if (activePopup) { activePopup.remove(); activePopup = null; }
  }

  document.addEventListener("click", closePopup);

  async function showViewerPopup(e, ref) {
    closePopup();

    // 팝업 생성
    const popup = document.createElement("div");
    popup.className = "viewer-popup";
    popup.innerHTML = `<div class="viewer-popup-title">패보 재생</div><div class="viewer-popup-loading">불러오는 중...</div>`;
    
    // 위치 계산
    const rect = e.target.getBoundingClientRect();
    popup.style.position = "fixed";
    popup.style.left = Math.min(rect.left, window.innerWidth - 160) + "px";
    popup.style.top = (rect.bottom + 4) + "px";

    document.body.appendChild(popup);
    activePopup = popup;

    // API 호출
    try {
      const res = await fetch(`/api/viewer/${encodeURIComponent(ref)}`);
      const data = await res.json();

      if (data.error) {
        popup.querySelector(".viewer-popup-loading").textContent = "패보를 찾을 수 없습니다.";
        return;
      }

      popup.innerHTML = `<div class="viewer-popup-title">패보 재생</div>` +
        `<a href="${data.tenhou}" target="_blank" rel="noopener" class="viewer-popup-btn" onclick="event.stopPropagation()">천봉</a>` +
        `<a href="${data.majsoul}" target="_blank" rel="noopener" class="viewer-popup-btn viewer-popup-btn-sub" onclick="event.stopPropagation()">작혼(일본) <span style="font-size:10px;color:#aaa;">로그인 필요</span></a>` +
        `<a href="${data.majsoul_global}" target="_blank" rel="noopener" class="viewer-popup-btn viewer-popup-btn-sub" onclick="event.stopPropagation()">작혼(글로벌) <span style="font-size:10px;color:#aaa;">로그인 필요</span></a>`;
    } catch (err) {
      popup.querySelector(".viewer-popup-loading").textContent = "오류가 발생했습니다.";
    }
  }
});
