/**
 * userManagement.js — 유저 CRUD 관리
 */
let adminPassword = "";

function authenticate() {
  adminPassword = document.getElementById("adminPw").value;
  // 인증 확인은 첫 API 호출로 검증
  loadUsers();
}

async function loadUsers() {
  try {
    const res = await fetch("/admin/api/users", {
      headers: { "X-Admin-Password": adminPassword },
    });
    if (res.status === 403) {
      document.getElementById("authMsg").textContent = "비밀번호가 틀렸습니다.";
      document.getElementById("authMsg").className = "msg-error";
      return;
    }
    const data = await res.json();
    if (data.error) {
      document.getElementById("authMsg").textContent = data.error;
      document.getElementById("authMsg").className = "msg-error";
      return;
    }

    // 인증 성공 → 패널 전환
    document.getElementById("authSection").style.display = "none";
    document.getElementById("adminPanel").style.display = "";

    renderUserTable(data.users);
  } catch (e) {
    console.error(e);
    document.getElementById("authMsg").textContent = "오류가 발생했습니다.";
    document.getElementById("authMsg").className = "msg-error";
  }
}

function renderUserTable(users) {
  const tbody = document.getElementById("userBody");
  tbody.innerHTML = "";

  users.forEach(user => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${user.name}</td>
      <td style="font-size:12px;color:#888;">${user.aliases.join(", ")}</td>
      <td>
        <button onclick="editUser('${user.name.replace(/'/g, "\\'")}')" style="padding:4px 10px;border:1px solid #5b8def;background:#fff;color:#5b8def;border-radius:4px;cursor:pointer;font-size:12px;font-family:inherit;">수정</button>
        <button onclick="deleteUser('${user.name.replace(/'/g, "\\'")}')" style="padding:4px 10px;border:1px solid #dc2626;background:#fff;color:#dc2626;border-radius:4px;cursor:pointer;font-size:12px;margin-left:4px;font-family:inherit;">삭제</button>
      </td>
    `;
    tbody.appendChild(row);
  });
}

function editUser(name) {
  // 현재 테이블에서 해당 유저 찾기
  const rows = document.querySelectorAll("#userBody tr");
  for (const row of rows) {
    const cells = row.querySelectorAll("td");
    if (cells[0].textContent === name) {
      document.getElementById("userName").value = name;
      document.getElementById("userAliases").value = cells[1].textContent;
      document.getElementById("editingUser").value = name;
      break;
    }
  }
}

function clearForm() {
  document.getElementById("userName").value = "";
  document.getElementById("userAliases").value = "";
  document.getElementById("editingUser").value = "";
  document.getElementById("saveMsg").textContent = "";
}

async function saveUser() {
  const name = document.getElementById("userName").value.trim();
  const aliasesRaw = document.getElementById("userAliases").value.trim();
  const editingUser = document.getElementById("editingUser").value;
  const msgEl = document.getElementById("saveMsg");

  if (!name) {
    msgEl.textContent = "이름을 입력해주세요.";
    msgEl.className = "msg-error";
    return;
  }

  const aliases = aliasesRaw ? aliasesRaw.split(",").map(a => a.trim()).filter(a => a) : [name];

  try {
    const res = await fetch("/admin/api/users", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Password": adminPassword,
      },
      body: JSON.stringify({
        action: editingUser ? "update" : "add",
        originalName: editingUser || undefined,
        name,
        aliases,
      }),
    });

    const data = await res.json();
    if (data.error) {
      msgEl.textContent = data.error;
      msgEl.className = "msg-error";
    } else {
      msgEl.textContent = data.message;
      msgEl.className = "msg-success";
      clearForm();
      loadUsers();
    }
  } catch (e) {
    msgEl.textContent = "오류가 발생했습니다.";
    msgEl.className = "msg-error";
  }
}

async function deleteUser(name) {
  if (!confirm(`'${name}' 유저를 삭제하시겠습니까?`)) return;

  try {
    const res = await fetch("/admin/api/users", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Password": adminPassword,
      },
      body: JSON.stringify({ action: "delete", name }),
    });

    const data = await res.json();
    if (data.error) {
      alert(data.error);
    } else {
      loadUsers();
    }
  } catch (e) {
    alert("오류가 발생했습니다.");
  }
}
