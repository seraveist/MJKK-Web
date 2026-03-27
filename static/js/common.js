/**
 * common.js — 공통 유틸리티 모듈
 * 각 페이지 JS에서 중복되던 패턴을 통합.
 * 기존 JS 파일은 그대로 동작하며, 이 파일을 추가로 로드하면
 * 새로운 페이지에서 간편하게 사용 가능.
 */

const MjkkUtils = {
  /**
   * 로딩 오버레이 표시/숨김
   */
  showLoading() {
    const el = document.getElementById("loading");
    if (el) el.style.display = "flex";
  },
  hideLoading() {
    const el = document.getElementById("loading");
    if (el) el.style.display = "none";
  },

  /**
   * API 호출 래퍼 (에러 처리 포함)
   */
  async fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },

  /**
   * 테이블에 빈 상태 / 에러 상태 표시
   */
  showEmptyState(container, message, colspan) {
    container.innerHTML = `<tr><td colspan="${colspan || 10}" class="empty-state">${message}</td></tr>`;
  },
  showErrorState(container, message, colspan) {
    container.innerHTML = `<tr><td colspan="${colspan || 10}" class="error-state">${message}</td></tr>`;
  },

  /**
   * 시즌 탭 초기화 (공통 패턴)
   * @param {string} selector - 탭 버튼 셀렉터
   * @param {string} currentSeason - 현재 시즌
   * @param {function} onChange - 시즌 변경 콜백
   */
  initSeasonTabs(selector, currentSeason, onChange) {
    document.querySelectorAll(selector).forEach(tab => {
      tab.classList.toggle("active", tab.dataset.season === String(currentSeason));
      tab.addEventListener("click", function () {
        document.querySelectorAll(selector).forEach(t => t.classList.remove("active"));
        this.classList.add("active");
        onChange(this.dataset.season);
      });
    });
  },

  /**
   * URL 쿼리 파라미터 관리
   */
  getParam(name) {
    return new URLSearchParams(location.search).get(name);
  },
  pushParams(params) {
    const p = new URLSearchParams(location.search);
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) p.set(k, v);
    });
    history.pushState(params, "", `?${p}`);
  },

  /**
   * 값 포맷팅 (statsConfig의 format과 호환)
   */
  formatValue(value, format) {
    if (value === undefined || value === null) return "-";
    switch (format) {
      case "percent":
        return (value * 100).toFixed(1) + "%";
      case "float":
        return typeof value === "number" ? value.toFixed(2) : value;
      case "int":
        return typeof value === "number" ? Math.round(value).toLocaleString() : value;
      default:
        return String(value);
    }
  },

  /**
   * 중첩 객체에서 키 경로로 값 추출
   * "winGame.avg" → obj.winGame.avg
   */
  getNestedValue(obj, keyPath) {
    return keyPath.split(".").reduce((o, k) => (o && o[k] !== undefined ? o[k] : undefined), obj);
  },

  /**
   * 플레이어 목록 로드 (select 요소에 옵션 추가)
   */
  async loadPlayerOptions(selectIds) {
    const res = await fetch("/stats/all");
    const data = await res.json();
    const players = data.allPlayers || [];

    (Array.isArray(selectIds) ? selectIds : [selectIds]).forEach((id, idx) => {
      const sel = document.getElementById(id);
      if (!sel) return;
      players.forEach(p => {
        const o = document.createElement("option");
        o.value = p; o.textContent = p;
        sel.appendChild(o);
      });
      if (players.length > idx + 1) sel.selectedIndex = idx;
    });

    return players;
  },
};

// 전역 사용 가능
window.MjkkUtils = MjkkUtils;
