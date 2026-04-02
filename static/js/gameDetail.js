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

const YAKU_KR = {"門前清自摸和":"멘젠쯔모","立直":"리치","一発":"일발","平和":"핑후","断幺九":"탕야오","一盃口":"이페코","混一色":"혼일색","清一色":"청일색","七対子":"치또이","三色同順":"삼색동순","一気通貫":"일기통관","対々和":"또이또이","混全帯幺九":"찬타","三色同刻":"삼색동각","混老頭":"혼노두","三暗刻":"산안커","小三元":"소삼원","二盃口":"량페코","純全帯幺九":"준찬타","嶺上開花":"영상개화","海底摸月":"해저로월","河底撈魚":"하저로어","槍槓":"창깡","両立直":"더블리치","国士無双":"국사무쌍","国士無双十三面待ち":"국사무쌍 13면대기","四暗刻":"스안커","四暗刻単騎待ち":"스안커 단기","大三元":"대삼원","小四喜":"소사희","大四喜":"대사희","字一色":"자일색","緑一色":"녹일색","清老頭":"청노두","九蓮宝燈":"구련보등","九蓮宝燈九面待ち":"순정구련보등","純正九蓮宝燈":"순정구련보등","流し満貫":"유국만관","数え役満":"헤아림 역만","役牌 白":"역패 백","役牌 發":"역패 발","役牌 中":"역패 중","自風 東":"자풍 동","自風 南":"자풍 남","自風 西":"자풍 서","自風 北":"자풍 북","場風 東":"장풍 동","場風 南":"장풍 남","場風 西":"장풍 서","場風 北":"장풍 북","Riichi":"리치","Ippatsu":"일발","Pinfu":"핑후","Tanyao":"탕야오","Iipeiko":"이페코","Honitsu":"혼일색","Chinitsu":"청일색","Chiitoitsu":"치또이","Toitoi":"또이또이","Sanankou":"산안커","Shousangen":"소삼원","Chanta":"찬타","Ittsu":"일기통관","Sanshoku":"삼색동순","Sanshoku Doukou":"삼색동각","Honroutou":"혼노두","Junchan":"준찬타","Ryanpeikou":"량페코","Rinshan Kaihou":"영상개화","Haitei":"해저로월","Houtei":"하저로어","Chankan":"창깡","Tsumo":"멘젠쯔모","Yakuhai":"역패","Double Riichi":"더블리치","Kokushi Musou":"국사무쌍","Kokushi Musou 13":"국사무쌍 13면대기","Suuankou":"스안커","Suuankou Tanki":"스안커 단기","Daisangen":"대삼원","Shousuushii":"소사희","Daisuushii":"대사희","Tsuuiisou":"자일색","Ryuuiisou":"녹일색","Chinroutou":"청노두","Chuuren Poutou":"구련보등","Junsei Chuuren Poutou":"순정구련보등"};

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

    // 판수/부수/등급 정보
    let hanFuStr = "";
    let tierBadge = "";
    if (r.yakus && r.yakus.length > 0) {
      const y0 = r.yakus[0];
      if (y0.tier) {
        const tierClass = {"역만":"tier-yakuman","삼배만":"tier-sanbaiman","배만":"tier-baiman","하네만":"tier-haneman","만관":"tier-mangan"}[y0.tier] || "";
        tierBadge = ` <span class="tier-badge ${tierClass}">${y0.tier}</span>`;
      }
      if (y0.han && y0.fu) {
        hanFuStr = `${y0.han}판 ${y0.fu}부`;
      } else if (y0.han) {
        hanFuStr = `${y0.han}판`;
      }
    }

    // 역 + 도라 (하단 행)
    let yakuLine = "";
    if (r.yakus && r.yakus.length > 0) {
      const yakuNames = r.yakus.flatMap(y => y.yakus).map(y => YAKU_KR[y] || y);
      const doraMerged = {};
      r.yakus.forEach(y => {
        if (y.dora) {
          for (const [k, v] of Object.entries(y.dora)) {
            if (v > 0) doraMerged[k] = (doraMerged[k] || 0) + v;
          }
        }
      });
      const doraParts = Object.entries(doraMerged).map(([k, v]) => `${k} ${v}`);
      const allParts = [...yakuNames, ...doraParts];
      if (allParts.length > 0) {
        yakuLine = `<div class="round-yakus">${allParts.join(" / ")}</div>`;
      }
    }

    // 플레이어 점수 그리드 (우측)
    const playerCols = names.map((name, i) => {
      const change = r.scoreChanges[i] || 0;
      const color = change > 0 ? "var(--color-best)" : change < 0 ? "var(--color-worst)" : "var(--text-tertiary)";
      const sign = change > 0 ? "+" : "";
      return `<div class="round-pcol">
        <div class="pname">${name}</div>
        <div class="pscore" style="color:${color};">${sign}${change.toLocaleString()}</div>
      </div>`;
    }).join("");

    // 결과 정보 라인 (좌측)
    let resultLine = resultBadge;
    if (winnerName) resultLine += `<span style="font-weight:500;color:var(--text-primary);">${winnerName}</span>`;
    if (hanFuStr) resultLine += `<span style="font-size:12px;color:var(--text-tertiary);">${hanFuStr}</span>`;
    if (tierBadge) resultLine += tierBadge;

    return `<div class="round-block">
      <div class="round-header">${r.label}</div>
      <div class="round-body">
        <div class="round-result-info">
          <div class="round-result-line">${resultLine}</div>
        </div>
        <div class="round-players">${playerCols}</div>
      </div>
      ${yakuLine}
    </div>`;
  }).join("");
}

// ── 코멘트 ──
function loadComments() {
  const ref = window.config.ref;
  fetch(`/api/comments/${ref}`)
    .then(r => r.json())
    .then(data => {
      const list = document.getElementById("commentList");
      if (!data.comments || data.comments.length === 0) {
        list.innerHTML = '<div style="font-size:13px;color:var(--text-tertiary);">아직 코멘트가 없습니다.</div>';
        return;
      }
      list.innerHTML = data.comments.map(c => `
        <div style="padding:8px 0;border-bottom:1px solid var(--border-light);font-size:13px;">
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="font-weight:600;color:var(--text-heading);">${c.user_name}</span>
            ${c.is_highlight ? '<span style="font-size:10px;background:#fef3c7;color:#92400e;padding:1px 6px;border-radius:8px;">하이라이트</span>' : ''}
            <span style="font-size:11px;color:var(--text-tertiary);margin-left:auto;">${(c.created_at || '').slice(0, 16).replace('T', ' ')}</span>
            <button onclick="deleteComment('${c.id}')" style="font-size:11px;color:var(--color-worst);background:none;border:none;cursor:pointer;padding:2px 6px;">삭제</button>
          </div>
          <div style="margin-top:4px;color:var(--text-secondary);">${c.text}</div>
        </div>
      `).join("");
    })
    .catch(e => console.error("Comments load error:", e));
}

function deleteComment(commentId) {
  if (!confirm("코멘트를 삭제하시겠습니까?")) return;
  const ref = window.config.ref;
  fetch(`/api/comments/${ref}/${commentId}`, { method: "DELETE" })
    .then(r => r.json())
    .then(data => {
      if (data.error) { alert(data.error); return; }
      loadComments();
    })
    .catch(e => alert("삭제 실패"));
}

function submitComment() {
  const ref = window.config.ref;
  const name = document.getElementById("commentName").value.trim() || "익명";
  const text = document.getElementById("commentText").value.trim();
  const highlight = document.getElementById("commentHighlight").checked;
  if (!text) return;

  fetch(`/api/comments/${ref}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_name: name, text: text, is_highlight: highlight }),
  })
    .then(r => r.json())
    .then(data => {
      if (data.error) { alert(data.error); return; }
      document.getElementById("commentText").value = "";
      document.getElementById("commentHighlight").checked = false;
      loadComments();
    })
    .catch(e => alert("코멘트 등록 실패"));
}

// 페이지 로드 시 코멘트도 로딩
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(loadComments, 500);
});
