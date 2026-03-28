/**
 * userManagement.js — 유저 CRUD + 백업 + 사전계산 (v3)
 */
let adminPassword = "";

function authenticate() {
  adminPassword = document.getElementById("adminPw").value;
  loadUsers();
}

async function loadUsers() {
  try {
    const res = await fetch("/admin/api/users", { headers: { "X-Admin-Password": adminPassword } });
    if (res.status === 403) {
      document.getElementById("authMsg").textContent = "비밀번호가 틀렸습니다.";
      document.getElementById("authMsg").className = "msg-error";
      return;
    }
    const data = await res.json();
    if (data.error) { document.getElementById("authMsg").textContent = data.error; document.getElementById("authMsg").className = "msg-error"; return; }

    document.getElementById("authSection").style.display = "none";
    document.getElementById("adminPanel").style.display = "";
    renderUserTable(data.users);
    loadBackupInfo();
    loadSettings();
  } catch (e) { document.getElementById("authMsg").textContent = "오류가 발생했습니다."; document.getElementById("authMsg").className = "msg-error"; }
}

function renderUserTable(users) {
  const tbody = document.getElementById("userBody");
  tbody.innerHTML = "";
  users.forEach(user => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${user.name}</td><td style="font-size:12px;color:var(--text-tertiary);">${user.aliases.join(", ")}</td>
      <td><button onclick="editUser('${user.name.replace(/'/g, "\\'")}')" style="padding:4px 10px;border:1px solid var(--color-accent);background:var(--bg-input);color:var(--color-accent);border-radius:4px;cursor:pointer;font-size:12px;font-family:inherit;">수정</button>
      <button onclick="deleteUser('${user.name.replace(/'/g, "\\'")}')" style="padding:4px 10px;border:1px solid var(--color-worst);background:var(--bg-input);color:var(--color-worst);border-radius:4px;cursor:pointer;font-size:12px;margin-left:4px;font-family:inherit;">삭제</button></td>`;
    tbody.appendChild(row);
  });
}

function editUser(name) {
  const rows = document.querySelectorAll("#userBody tr");
  for (const row of rows) {
    const cells = row.querySelectorAll("td");
    if (cells[0].textContent === name) {
      document.getElementById("userName").value = name;
      document.getElementById("userAliases").value = cells[1].textContent;
      document.getElementById("editingUser").value = name;
      document.getElementById("formTitle").textContent = "유저 수정";
      break;
    }
  }
}

function clearForm() {
  document.getElementById("userName").value = "";
  document.getElementById("userAliases").value = "";
  document.getElementById("editingUser").value = "";
  document.getElementById("saveMsg").textContent = "";
  document.getElementById("formTitle").textContent = "유저 추가";
}

async function saveUser() {
  const name = document.getElementById("userName").value.trim();
  const aliasesRaw = document.getElementById("userAliases").value.trim();
  const editingUser = document.getElementById("editingUser").value;
  const msgEl = document.getElementById("saveMsg");
  if (!name) { msgEl.textContent = "이름을 입력해주세요."; msgEl.className = "msg-error"; return; }
  const aliases = aliasesRaw ? aliasesRaw.split(",").map(a => a.trim()).filter(a => a) : [name];
  try {
    const res = await fetch("/admin/api/users", {
      method: "POST", headers: { "Content-Type": "application/json", "X-Admin-Password": adminPassword },
      body: JSON.stringify({ action: editingUser ? "update" : "add", originalName: editingUser || undefined, name, aliases }),
    });
    const data = await res.json();
    if (data.error) { msgEl.textContent = data.error; msgEl.className = "msg-error"; }
    else { msgEl.textContent = data.message; msgEl.className = "msg-success"; clearForm(); loadUsers(); }
  } catch (e) { msgEl.textContent = "오류가 발생했습니다."; msgEl.className = "msg-error"; }
}

async function deleteUser(name) {
  if (!confirm(`'${name}' 유저를 삭제하시겠습니까?`)) return;
  try {
    const res = await fetch("/admin/api/users", {
      method: "POST", headers: { "Content-Type": "application/json", "X-Admin-Password": adminPassword },
      body: JSON.stringify({ action: "delete", name }),
    });
    const data = await res.json();
    if (data.error) alert(data.error); else loadUsers();
  } catch (e) { alert("오류가 발생했습니다."); }
}

// ── [신규] 백업 ──
async function loadBackupInfo() {
  try {
    const res = await fetch("/admin/api/backup/info", { headers: { "X-Admin-Password": adminPassword } });
    const data = await res.json();
    document.getElementById("backupInfo").textContent = `대국 기록: ${data.game_logs}건, 유저: ${data.users}명`;
  } catch (e) { document.getElementById("backupInfo").textContent = "정보 로드 실패"; }
}

async function downloadBackup() {
  const msgEl = document.getElementById("backupMsg");
  msgEl.textContent = "백업 생성 중...";
  msgEl.className = "msg-info";
  try {
    const res = await fetch("/admin/api/backup", { method: "POST", headers: { "X-Admin-Password": adminPassword } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = res.headers.get("Content-Disposition")?.split("filename=")[1] || "mjkk_backup.json";
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    msgEl.textContent = "백업 다운로드 완료!";
    msgEl.className = "msg-success";
  } catch (e) { msgEl.textContent = "백업 실패: " + e.message; msgEl.className = "msg-error"; }
}

// ── [신규] 사전계산 트리거 ──
async function triggerPrecompute() {
  const msgEl = document.getElementById("precomputeMsg");
  msgEl.textContent = "재계산 시작 중...";
  msgEl.className = "msg-info";
  try {
    const res = await fetch("/admin/precompute", { method: "POST", headers: { "X-Admin-Password": adminPassword } });
    const data = await res.json();
    msgEl.textContent = data.message || "완료";
    msgEl.className = "msg-success";
  } catch (e) { msgEl.textContent = "오류: " + e.message; msgEl.className = "msg-error"; }
}

// ── [신규] 설정 관리 ──
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    const data = await res.json();
    const elo = data.elo_params || {};
    const awards = data.awards_config || {};
    document.getElementById("setEloK").value = elo.K || 6;
    document.getElementById("setEloNorm").value = elo.NORM || 8000;
    document.getElementById("setEloInitial").value = elo.initial || 1500;
    document.getElementById("setAwardsRatio").value = awards.min_games_ratio || 0.3;
  } catch (e) { console.error("Settings load error:", e); }
}

async function saveSettings() {
  const msgEl = document.getElementById("settingsMsg");
  msgEl.textContent = "저장 중...";
  msgEl.className = "msg-info";
  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Admin-Password": adminPassword },
      body: JSON.stringify({
        elo_params: {
          K: parseFloat(document.getElementById("setEloK").value) || 6,
          NORM: parseInt(document.getElementById("setEloNorm").value) || 8000,
          initial: parseInt(document.getElementById("setEloInitial").value) || 1500,
        },
        awards_config: {
          min_games_ratio: parseFloat(document.getElementById("setAwardsRatio").value) || 0.3,
          min_games_floor: 3,
        },
      }),
    });
    const data = await res.json();
    if (data.error) { msgEl.textContent = data.error; msgEl.className = "msg-error"; }
    else { msgEl.textContent = "설정이 저장되었습니다."; msgEl.className = "msg-success"; }
  } catch (e) { msgEl.textContent = "오류: " + e.message; msgEl.className = "msg-error"; }
}
