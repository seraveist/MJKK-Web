/**
 * ranking.js — 대시보드 (v3)
 * 요약 카드 + 메타 분석 + 시즌 어워드 + 역만 타임라인 + 랭킹 + 날짜별 점수
 */
document.addEventListener("DOMContentLoaded", () => {
  let currentSeason = window.config ? window.config.season : "all";
  let rankingFiltered = [];
  let rankingElo = {};
  let rankSortKey = "games";
  let rankSortDesc = true;

  const urlSeason = new URLSearchParams(location.search).get("season");
  if (urlSeason) { currentSeason = urlSeason; syncTabUI(currentSeason); }

  document.querySelectorAll(".season-tabs .tab").forEach(tab => {
    tab.addEventListener("click", function () {
      document.querySelectorAll(".season-tabs .tab").forEach(t => t.classList.remove("active"));
      this.classList.add("active");
      currentSeason = this.dataset.season;
      pushState({ season: currentSeason });
      loadAll();
    });
  });

  window.addEventListener("popstate", (e) => {
    if (e.state && e.state.season) {
      currentSeason = e.state.season;
      syncTabUI(currentSeason);
      loadAll();
    }
  });

  function syncTabUI(season) {
    document.querySelectorAll(".season-tabs .tab").forEach(t => {
      t.classList.toggle("active", t.dataset.season === String(season));
    });
  }

  function pushState(state) {
    const p = new URLSearchParams(location.search);
    p.set("season", state.season);
    history.pushState(state, "", `?${p}`);
  }

  function showLoading() { const el = document.getElementById("loading"); if (el) el.style.display = "flex"; }
  function hideLoading() { const el = document.getElementById("loading"); if (el) el.style.display = "none"; }

  async function loadAll() {
    showLoading();
    try {
      await Promise.all([loadRanking(), loadMeta(), loadAwards(), loadYakumanHistory()]);
    } finally {
      hideLoading();
    }
  }

  // ── 랭킹 + 요약 카드 ──
  async function loadRanking() {
    const rankingBody = document.getElementById("rankingBody");
    const dateScoreBody = document.getElementById("dateScoreBody");
    const rankingInfo = document.getElementById("rankingInfo");
    const summaryLine = document.getElementById("summaryLine");

    try {
      // 랭킹 + ELO 병렬 로딩
      const [rankRes, eloRes] = await Promise.all([
        fetch("/ranking?season=" + currentSeason),
        fetch("/api/elo?season=" + currentSeason).catch(() => null),
      ]);

      if (!rankRes.ok) throw new Error(`HTTP ${rankRes.status}`);
      const data = await rankRes.json();

      let eloRatings = {};
      try {
        if (eloRes && eloRes.ok) {
          const eloData = await eloRes.json();
          eloRatings = eloData.ratings || {};
        }
      } catch (e) { /* ELO 없어도 정상 진행 */ }

      if (data.error) {
        rankingBody.innerHTML = '<tr><td colspan="4" class="empty-state">이 시즌의 대국 데이터가 없습니다.</td></tr>';
        dateScoreBody.innerHTML = "";
        summaryLine.innerHTML = "";
        rankingInfo.textContent = "";
        return;
      }

      // 요약
      const filtered = data.ranking.filter(p => p.games > 0);
      const totalGames = filtered.reduce((s, p) => s + p.games, 0) / 4;
      const topPlayer = filtered.length > 0 ? [...filtered].sort((a, b) => b.games - a.games)[0] : null;
      const dates = (data.daily || []).map(d => d.date).filter(Boolean);
      const latestDate = dates.length > 0 ? dates[0] : "-";

      summaryLine.innerHTML = `
        <span class="s-item"><span class="s-label">총 대국</span><span class="s-val">${Math.round(totalGames)}국</span></span>
        <span class="s-sep">|</span>
        <span class="s-item"><span class="s-label">참가</span><span class="s-val">${filtered.length}명</span></span>
        <span class="s-sep">|</span>
        <span class="s-item"><span class="s-label">최근</span><span class="s-val">${latestDate}</span></span>
        <span class="s-sep">|</span>
        <span class="s-item"><span class="s-label">최다</span><span class="s-val">${topPlayer ? topPlayer.name + " " + topPlayer.games + "국" : "-"}</span></span>
      `;

      // 대국이 있는 유저 목록 (#2)
      const activePlayerNames = new Set(filtered.map(p => p.name));

      // 랭킹 데이터 저장 (정렬용)
      rankingFiltered = filtered;
      rankingElo = eloRatings;
      renderRankingTable();

      // 정렬 헤더 클릭 핸들러
      document.querySelectorAll(".sortable").forEach(th => {
        th.onclick = function () {
          const key = this.dataset.sort;
          if (rankSortKey === key) { rankSortDesc = !rankSortDesc; }
          else { rankSortKey = key; rankSortDesc = true; }
          // 화살표 업데이트
          document.querySelectorAll(".sortable").forEach(h => {
            const arrow = h.dataset.sort === rankSortKey ? (rankSortDesc ? " ▼" : " ▲") : "";
            h.textContent = h.textContent.replace(/ [▼▲]/, "") + arrow;
          });
          renderRankingTable();
        };
      });

      // 날짜별 점수 (#2: 대국 있는 유저만)
      if (dateScoreBody && data.daily) {
        const activePlayers = data.players.filter(name => activePlayerNames.has(name));

        const header = document.getElementById("dateScoreHeader").querySelector("tr");
        header.innerHTML = "<th>날짜</th>";
        activePlayers.forEach(name => {
          const th = document.createElement("th");
          th.textContent = name;
          header.appendChild(th);
        });

        dateScoreBody.innerHTML = "";
        data.daily.forEach(d => {
          const row = document.createElement("tr");
          const tdDate = document.createElement("td");
          tdDate.textContent = d.date;
          tdDate.style.whiteSpace = "nowrap";
          tdDate.style.cursor = "pointer";
          tdDate.addEventListener("click", () => showViewerPopup(d.ref, tdDate));
          row.appendChild(tdDate);

          activePlayers.forEach(name => {
            const td = document.createElement("td");
            const val = d.points[name];
            if (val !== undefined) {
              td.textContent = (val >= 0 ? "+" : "") + val.toFixed(1);
              td.style.color = val >= 0 ? "var(--color-best)" : "var(--color-worst)";
              td.style.fontWeight = "600";
            }
            row.appendChild(td);
          });
          dateScoreBody.appendChild(row);
        });
      }
    } catch (e) {
      console.error(e);
      rankingBody.innerHTML = '<tr><td colspan="4" class="error-state">데이터를 불러오는 중 오류가 발생했습니다.</td></tr>';
    }
  }

  // ── 랭킹 테이블 렌더링 (정렬 가능) ──
  function renderRankingTable() {
    const rankingBody = document.getElementById("rankingBody");
    const rankingInfo = document.getElementById("rankingInfo");
    if (!rankingBody || rankingFiltered.length === 0) {
      if (rankingBody) rankingBody.innerHTML = '<tr><td colspan="4" class="empty-state">대국 기록이 있는 플레이어가 없습니다.</td></tr>';
      return;
    }

    const sorted = [...rankingFiltered].sort((a, b) => {
      const va = a[rankSortKey] || 0;
      const vb = b[rankSortKey] || 0;
      return rankSortDesc ? vb - va : va - vb;
    });

    rankingBody.innerHTML = "";
    sorted.forEach(p => {
      const row = document.createElement("tr");
      const pointColor = p.point_sum >= 0 ? "var(--color-best)" : "var(--color-worst)";
      const avgColor = p.point_avg >= 0 ? "var(--color-best)" : "var(--color-worst)";
      const elo = rankingElo[p.name];
      const eloStr = elo ? Math.round(elo) : "";
      const eloDiff = elo ? Math.round(elo - 1500) : 0;
      const eloColor = eloDiff > 0 ? "var(--color-best)" : eloDiff < 0 ? "var(--color-worst)" : "var(--text-tertiary)";
      row.innerHTML = `<td><a href="/stats_page/${encodeURIComponent(p.name)}?season=${currentSeason}">${p.name}</a>${elo ? ` <span style="font-size:11px;color:${eloColor};font-weight:500;">${eloStr}</span>` : ""}</td>
        <td>${p.games}</td>
        <td style="color:${pointColor};font-weight:600;">${p.point_sum >= 0 ? "+" : ""}${p.point_sum.toFixed(1)}</td>
        <td style="color:${avgColor};font-weight:600;">${p.point_avg >= 0 ? "+" : ""}${p.point_avg.toFixed(2)}</td>`;
      rankingBody.appendChild(row);
    });

    const totalGames = rankingFiltered.reduce((s, p) => s + p.games, 0) / 4;
    const maxGames = Math.max(...rankingFiltered.map(p => p.games), 0);
    const minRequired = Math.max(3, Math.floor(maxGames * 0.3));
    rankingInfo.textContent = `${rankingFiltered.length}명 / ${Math.round(totalGames)}국 (기준: ${minRequired}국 이상)`;
  }

  // ── 메타 분석 ──
  const YAKU_EXCLUDE = new Set(["役牌 白","役牌 發","役牌 中","自風 東","自風 南","自風 西","自風 北","場風 東","場風 南","場風 西","場風 北"]);
  const YAKU_KR = {"門前清自摸和":"멘젠쯔모","立直":"리치","一発":"일발","平和":"핑후","断幺九":"탕야오","一盃口":"이페코","混一色":"혼일색","清一色":"청일색","七対子":"치또이","三色同順":"삼색동순","一気通貫":"일기통관","対々和":"또이또이","混全帯幺九":"찬타","三色同刻":"삼색동각","混老頭":"혼노두","三暗刻":"산안커","小三元":"소삼원","二盃口":"량페코","純全帯幺九":"준찬타","嶺上開花":"영상개화","海底摸月":"해저로월","河底撈魚":"하저로어","槍槓":"창깡"};

  async function loadMeta() {
    try {
      const res = await fetch(`/api/meta?season=${currentSeason}`);
      const data = await res.json();
      if (data.error) { document.getElementById("metaSection").style.display = "none"; return; }

      document.getElementById("metaSection").style.display = "";
      document.getElementById("metaRow").innerHTML = `
        <div class="meta-item">평균 화료율 <strong>${data.avg_win_rate}%</strong></div>
        <div class="meta-item">평균 방총률 <strong>${data.avg_chong_rate}%</strong></div>
        <div class="meta-item">평균 리치율 <strong>${data.avg_richi_rate || "-"}%</strong></div>
        <div class="meta-item">평균 후로율 <strong>${data.avg_fulu_rate || "-"}%</strong></div>
        <div class="meta-item">참가자 <strong>${data.total_players}명</strong></div>
      `;

      const yakuContainer = document.getElementById("topYakus");
      if (data.top_yakus && data.top_yakus.length > 0) {
        const filtered = data.top_yakus.filter(y => !YAKU_EXCLUDE.has(y.name));
        yakuContainer.innerHTML = filtered.slice(0, 10).map(y =>
          `<div class="yaku-chip">${YAKU_KR[y.name] || y.name}<span class="cnt">${y.count}</span></div>`
        ).join("");
      }
    } catch (e) {
      console.error("Meta load error:", e);
    }
  }

  // ── 시즌 어워드 ──
  async function loadAwards() {
    try {
      const res = await fetch(`/api/awards?season=${currentSeason}`);
      const data = await res.json();
      if (!data.awards || data.awards.length === 0) {
        document.getElementById("awardsSection").style.display = "none";
        return;
      }
      document.getElementById("awardsSection").style.display = "";
      const reportLink = document.getElementById("reportLink");
      if (reportLink) reportLink.href = `/report?season=${currentSeason}`;
      document.getElementById("awardGrid").innerHTML = data.awards.map(a =>
        `<div class="award-card"><div class="a-title">${a.title}</div><div class="a-winner">${a.winner}</div><div class="a-value">${a.value}</div></div>`
      ).join("");
    } catch (e) { console.error("Awards load error:", e); }
  }

  // ── 역만/삼배만 타임라인 ──
  async function loadYakumanHistory() {
    try {
      const res = await fetch(`/api/yakuman_history?season=${currentSeason}`);
      const data = await res.json();
      if (!data.history || data.history.length === 0) {
        document.getElementById("yakumanSection").style.display = "none";
        return;
      }
      document.getElementById("yakumanSection").style.display = "";
      document.getElementById("yakumanTimeline").innerHTML = data.history.map(h => {
        const yakuStr = h.tier.includes("역만") && h.yakus && h.yakus.length > 0 ? ` <span style="font-size:11px;color:var(--color-accent);">(${h.yakus.join(", ")})</span>` : "";
        const detailBtn = h.ref ? ` <a href="/games/${h.ref}" style="font-size:11px;color:var(--text-link);text-decoration:none;margin-left:4px;">상세 →</a>` : "";
        return `<div class="tl-item">
          <span class="tl-date">${h.date}</span>
          <span class="tl-badge ${h.tier === "삼배만" ? "tl-sanbaiman" : h.tier === "역만" ? "tl-yakuman" : "tl-double-yakuman"}">${h.tier}</span>
          <span style="font-weight:500;color:var(--text-primary);">${h.player}</span>${yakuStr}${detailBtn}
        </div>`;
      }).join("");
    } catch (e) { console.error("Yakuman history load error:", e); }
  }

  // ── 패보 팝업 (기존 유지) ──
  function showViewerPopup(ref, anchor) {
    document.querySelectorAll(".viewer-popup").forEach(p => p.remove());
    if (!ref) return;
    const popup = document.createElement("div");
    popup.className = "viewer-popup";
    popup.style.position = "absolute";
    popup.innerHTML = '<div class="viewer-popup-loading">로딩...</div>';
    const rect = anchor.getBoundingClientRect();
    popup.style.left = (rect.left + window.scrollX) + "px";
    popup.style.top = (rect.bottom + window.scrollY + 4) + "px";
    document.body.appendChild(popup);

    document.addEventListener("click", function handler(e) {
      if (!popup.contains(e.target) && e.target !== anchor) {
        popup.remove();
        document.removeEventListener("click", handler);
      }
    });

    fetch(`/api/viewer/${ref}`).then(r => r.json()).then(data => {
      if (data.error) { popup.querySelector(".viewer-popup-loading").textContent = "오류"; return; }
      popup.innerHTML = `<div class="viewer-popup-title">패보 재생</div>` +
        `<a href="${data.tenhou}" target="_blank" rel="noopener" class="viewer-popup-btn" onclick="event.stopPropagation()">천봉</a>` +
        `<a href="${data.majsoul}" target="_blank" rel="noopener" class="viewer-popup-btn viewer-popup-btn-sub" onclick="event.stopPropagation()">작혼(일본)</a>` +
        `<a href="${data.majsoul_global}" target="_blank" rel="noopener" class="viewer-popup-btn viewer-popup-btn-sub" onclick="event.stopPropagation()">작혼(글로벌)</a>`;
    }).catch(() => { popup.querySelector(".viewer-popup-loading").textContent = "오류"; });
  }

  loadAll();
});
