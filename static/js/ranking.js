document.addEventListener("DOMContentLoaded", () => {
    // active 탭 요소 안전하게 조회; 없으면 "all"
    const activeTabEl = document.querySelector(".season-tabs .tab.active");
    let currentSeason = activeTabEl ? activeTabEl.getAttribute("data-season") : "all";
    // index.html에서는 플레이어 선택 없이 랭킹 데이터 조회
    
    // 탭 클릭 이벤트 리스너 등록: 시즌 변경 시 loadRanking() 호출
    const tabs = document.querySelectorAll(".season-tabs .tab");
    tabs.forEach(tab => {
      tab.addEventListener("click", function(){
        tabs.forEach(t => t.classList.remove("active"));
        this.classList.add("active");
        currentSeason = this.getAttribute("data-season");
        loadRanking();  // 무조건 호출
      });
    });

    function showLoading() {
      const loadingElem = document.getElementById("loading");
      if (loadingElem) {
        loadingElem.style.display = "flex";
      }
    }
    function hideLoading() {
      const loadingElem = document.getElementById("loading");
      if (loadingElem) {
        loadingElem.style.display = "none";
      }
    }

    async function loadRanking() {
      showLoading();
      try {
        const res = await fetch("/ranking?season=" + currentSeason);
        const data = await res.json();

        // 랭킹 테이블 업데이트
        const rankingTable = document.getElementById("rankingBody");
        if (rankingTable) {
          rankingTable.innerHTML = "";
          const filteredRanking = data.ranking.filter(player => player.games > 0);
          filteredRanking.forEach(player => {
            const row = document.createElement("tr");
            // 플레이어 이름 클릭 시 stats_page로 이동 (HTML 렌더링 페이지)
            row.innerHTML = `
              <td><a href="/stats_page/${player.name}?season=${currentSeason}">${player.name}</a></td>
              <td>${player.games}</td>
              <td>${player.point_sum.toFixed(1)}</td>
              <td>${player.point_avg.toFixed(1)}</td>
            `;
            rankingTable.appendChild(row);
          });
          
          // 총 대국수 계산: filteredRanking의 게임 수 합산
          const totalGamesRaw = filteredRanking.reduce((sum, player) => sum + player.games, 0);
          const totalGames = Math.floor(totalGamesRaw / 4); // 전체 게임수
          const regulatedGames = Math.floor(totalGames * 0.3); // 규정 대국수: 전체 게임수의 30%

          // rankingInfo 영역에 출력
          document.getElementById("rankingInfo").textContent =
            `규정 대국 수 ${regulatedGames} / 총 대국 수 ${totalGames}`;
        } else {
          console.error("rankingBody 요소를 찾을 수 없습니다.");
        }

        // 날짜별 점수 기록 업데이트
        const headerElem = document.getElementById("dateScoreHeader");
        if (headerElem) {
          const headerRow = headerElem.querySelector("tr");
          if (headerRow) {
            headerRow.innerHTML = "<th style='min-width:80px;'>날짜</th>";
            data.players.forEach(name => {
              const th = document.createElement("th");
              th.textContent = name;
              th.style.minWidth = "80px";
              headerRow.appendChild(th);
            });
          } else {
            console.error("dateScoreHeader 내부에 <tr> 요소를 찾을 수 없습니다.");
          }
        } else {
          console.error("dateScoreHeader 요소를 찾을 수 없습니다.");
        }

        const dateScoreBody = document.getElementById("dateScoreBody");
        if (dateScoreBody) {
          dateScoreBody.innerHTML = "";
          data.daily.forEach(entry => {
            const row = document.createElement("tr");
            const dateCell = document.createElement("td");
            dateCell.textContent = entry.date.split("-")[0];
            dateCell.style.minWidth = "80px";
            row.appendChild(dateCell);
            data.players.forEach(name => {
              const td = document.createElement("td");
              td.textContent = entry.points[name] !== undefined ? entry.points[name].toFixed(1) : "-";
              td.style.minWidth = "80px";
              row.appendChild(td);
            });
            dateScoreBody.appendChild(row);
          });
        } else {
          console.error("dateScoreBody 요소를 찾을 수 없습니다.");
        }
      } catch (error) {
        console.error("Error loading ranking:", error);
      } finally {
        hideLoading();
      }
    }

    loadRanking();
  });