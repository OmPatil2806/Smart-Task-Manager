/* 
   MNEMOSYNE — Frontend Logic
 */

const API = "";
const $ = id => document.getElementById(id);

const state = {
  user: null, tasks: [],
  filter: "all", priority: "all", search: "",
};

//  Chart instance 
let priorityChart = null;

//  API 
async function api(method, path, body = null) {
  try {
    const opts = { method, credentials: "include",
                   headers: { "Content-Type": "application/json" } };
    if (body) opts.body = JSON.stringify(body);
    const res  = await fetch(API + path, opts);
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, data };
  } catch { return { ok: false, data: { error: "Cannot reach server." } }; }
}

//  Toast 
let _tt;
function toast(msg, type = "") {
  const el = $("toast");
  el.textContent = msg;
  el.className   = `toast ${type}`;
  clearTimeout(_tt);
  _tt = setTimeout(() => el.classList.add("hidden"), 3000);
}

//  Auth screens 
function showAuth() {
  $("auth-screen").classList.add("active");
  $("dashboard-screen").classList.remove("active");
}
function showDash() {
  $("auth-screen").classList.remove("active");
  $("dashboard-screen").classList.add("active");
  $("sidebar-username").textContent = state.user?.username || "Guest";
  $("user-avatar").textContent = (state.user?.username || "G")[0].toUpperCase();
  loadTasks(); loadStats();
}

async function init() {
  const { ok, data } = await api("GET", "/me");
  if (ok && data.user) { state.user = data.user; showDash(); }
  else showAuth();
}

// Auth tabs 
document.querySelectorAll(".atab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".atab").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    $(`${btn.dataset.tab}-panel`).classList.add("active");
  });
});

$("login-btn").addEventListener("click", async () => {
  const u = $("login-username").value.trim();
  const p = $("login-password").value.trim();
  $("login-error").textContent = "";
  if (!u || !p) { $("login-error").textContent = "Fill in all fields."; return; }
  $("login-btn").disabled = true;
  const { ok, data } = await api("POST", "/login", { username: u, password: p });
  $("login-btn").disabled = false;
  if (ok) { state.user = data.user; showDash(); }
  else $("login-error").textContent = data.error || "Login failed.";
});

$("signup-btn").addEventListener("click", async () => {
  const u = $("signup-username").value.trim();
  const p = $("signup-password").value.trim();
  $("signup-error").textContent = "";
  if (!u || !p) { $("signup-error").textContent = "Fill in all fields."; return; }
  $("signup-btn").disabled = true;
  const { ok, data } = await api("POST", "/signup", { username: u, password: p });
  $("signup-btn").disabled = false;
  if (ok) { state.user = data.user; showDash(); }
  else $("signup-error").textContent = data.error || "Signup failed.";
});

["login-username","login-password"].forEach(id =>
  $(id).addEventListener("keydown", e => e.key === "Enter" && $("login-btn").click()));
["signup-username","signup-password"].forEach(id =>
  $(id).addEventListener("keydown", e => e.key === "Enter" && $("signup-btn").click()));

$("logout-btn").addEventListener("click", async () => {
  await api("POST", "/logout");
  state.user = null; state.tasks = [];
  if (priorityChart) { priorityChart.destroy(); priorityChart = null; }
  showAuth();
});

// Load 
async function loadTasks() {
  const { ok, data } = await api("GET", "/tasks");
  if (!ok) return;
  state.tasks = data.tasks || [];
  renderTasks(); updateCounts(); updateChart();
}

async function loadStats() {
  const { ok, data } = await api("GET", "/stats");
  if (!ok) return;
  const score = data.productivity_score;
  $("stat-score").textContent = score + "%";
  $("score-bar").style.width  = score + "%";
  $("stat-overdue").textContent = data.overdue;
  $("stat-today").textContent   = data.due_today;
  $("stat-high").textContent    = data.by_priority?.HIGH || 0;
  $("stat-sub").textContent = `${data.completed} of ${data.total} tasks completed`;
}

//  Chart 
function updateChart() {
  const high   = state.tasks.filter(t => t.priority === "HIGH"   && t.status === "pending").length;
  const medium = state.tasks.filter(t => t.priority === "MEDIUM" && t.status === "pending").length;
  const low    = state.tasks.filter(t => t.priority === "LOW"    && t.status === "pending").length;
  const done   = state.tasks.filter(t => t.status === "completed").length;

  const ctx = $("priority-chart").getContext("2d");

  if (priorityChart) priorityChart.destroy();

  priorityChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["High", "Medium", "Low", "Done"],
      datasets: [{
        data: [high, medium, low, done],
        backgroundColor: ["#e8341c", "#d97706", "#059669", "#e4e4df"],
        borderColor: "#ffffff",
        borderWidth: 3,
        hoverOffset: 4,
      }]
    },
    options: {
      responsive: false,
      cutout: "68%",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.raw}`
          },
          backgroundColor: "#1a1a18",
          padding: 10,
          cornerRadius: 8,
          titleFont: { family: "Inter" },
          bodyFont:  { family: "Inter" },
        }
      },
      animation: { animateRotate: true, duration: 600 }
    }
  });
}

// Filter tasks 
function getFiltered() {
  const today = new Date().toISOString().split("T")[0];
  let t = [...state.tasks];
  if      (state.filter === "pending")   t = t.filter(x => x.status === "pending");
  else if (state.filter === "completed") t = t.filter(x => x.status === "completed");
  else if (state.filter === "overdue")   t = t.filter(x => x.is_overdue);
  else if (state.filter === "today")     t = t.filter(x => x.due_date === today && x.status === "pending");
  if (state.priority !== "all")          t = t.filter(x => x.priority === state.priority);
  if (state.search) {
    const q = state.search.toLowerCase();
    t = t.filter(x => x.title.toLowerCase().includes(q) ||
                      (x.description||"").toLowerCase().includes(q));
  }
  return t;
}

// Render 
function renderTasks() {
  const tasks = getFiltered();
  const list  = $("task-list");
  list.innerHTML = "";

  if (!tasks.length) { $("empty-state").classList.remove("hidden"); return; }
  $("empty-state").classList.add("hidden");

  tasks.forEach((task, i) => {
    const card = document.createElement("div");
    card.className = `task-card${task.status==="completed"?" completed":""}${task.is_overdue?" overdue":""}`;
    card.dataset.priority = task.priority;
    card.style.animationDelay = `${i * 0.05}s`;

    // Due date tag
    let dueMeta = "";
    if (task.due_date) {
      const label = new Date(task.due_date + "T00:00:00")
        .toLocaleDateString("en-US", { month:"short", day:"numeric" });
      if      (task.is_overdue)          dueMeta = `<span class="meta-tag overdue-tag">⚠ Overdue · ${label}</span>`;
      else if (task.days_until_due === 0) dueMeta = `<span class="meta-tag today-tag">Today</span>`;
      else if (task.days_until_due === 1) dueMeta = `<span class="meta-tag today-tag">Tomorrow</span>`;
      else                                dueMeta = `<span class="meta-tag">${label}</span>`;
    }

    const priorityIcon = { HIGH:"▲", MEDIUM:"◆", LOW:"▼" }[task.priority] || "◆";

    card.innerHTML = `
      <div class="task-check">${task.status==="completed"?"✓":""}</div>
      <div class="task-body">
        <div class="task-title">${esc(task.title)}</div>
        ${task.description ? `<div class="task-desc">${esc(task.description)}</div>` : ""}
        <div class="task-meta">
          <span class="priority-badge ${task.priority}">
            <span class="pi ${task.priority.toLowerCase()}">${priorityIcon}</span>
            ${task.priority}
          </span>
          ${dueMeta}
          ${task.category && task.category !== "other"
            ? `<span class="meta-tag cat-tag">${task.category}</span>` : ""}
        </div>
      </div>
      <div class="task-actions">
        <button class="action-btn edit-btn"  title="Edit">✎</button>
        <button class="action-btn delete"    title="Delete">✕</button>
      </div>`;

    card.querySelector(".task-check").addEventListener("click", () => toggleTask(task.id));
    card.querySelector(".edit-btn") .addEventListener("click", () => openEditModal(task));
    card.querySelector(".delete")   .addEventListener("click", () => deleteTask(task.id));
    list.appendChild(card);
  });
}

function updateCounts() {
  const today = new Date().toISOString().split("T")[0];
  $("count-all")      .textContent = state.tasks.length;
  $("count-pending")  .textContent = state.tasks.filter(t => t.status==="pending").length;
  $("count-completed").textContent = state.tasks.filter(t => t.status==="completed").length;
  $("count-overdue")  .textContent = state.tasks.filter(t => t.is_overdue).length;
  $("count-today")    .textContent = state.tasks.filter(t => t.due_date===today && t.status==="pending").length;
}

// Actions 
async function toggleTask(id) {
  const { ok, data } = await api("PATCH", `/tasks/${id}/toggle`);
  if (!ok) { toast("Update failed.", "error"); return; }
  const idx = state.tasks.findIndex(t => t.id === id);
  if (idx !== -1) state.tasks[idx] = data.task;
  renderTasks(); updateCounts(); updateChart(); loadStats();
  toast(data.task.status === "completed" ? "Task completed 🎉" : "Task reopened", "success");
}

async function deleteTask(id) {
  const { ok } = await api("DELETE", `/tasks/${id}`);
  if (!ok) { toast("Delete failed.", "error"); return; }
  state.tasks = state.tasks.filter(t => t.id !== id);
  renderTasks(); updateCounts(); updateChart(); loadStats();
  toast("Task deleted.");
}

//  Nav
document.querySelectorAll(".nav-item[data-filter]").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    state.filter = btn.dataset.filter;
    const labels = {all:"All Tasks",pending:"Pending",completed:"Completed",overdue:"Overdue",today:"Due Today"};
    $("page-title").textContent = labels[state.filter] || "Tasks";
    renderTasks();
  });
});

document.querySelectorAll(".pf").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".pf").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    state.priority = btn.dataset.priority;
    renderTasks();
  });
});

$("search-input").addEventListener("input", e => { state.search = e.target.value; renderTasks(); });

// Modal 
let _predicted = "MEDIUM";

function openNewModal() {
  $("modal-title").textContent = "New Task";
  $("save-btn-text").textContent = "Create Task";
  $("edit-task-id").value = "";
  $("task-title").value = $("task-desc").value = $("task-due").value = "";
  $("task-category").value = "other";
  $("predicted-priority").textContent = "—";
  $("predicted-priority").className   = "priority-badge neutral";
  $("confidence-bars").innerHTML      = "";
  _predicted = "MEDIUM";
  $("task-modal").classList.remove("hidden");
  setTimeout(() => $("task-title").focus(), 60);
}

function openEditModal(task) {
  $("modal-title").textContent = "Edit Task";
  $("save-btn-text").textContent = "Save Changes";
  $("edit-task-id").value      = task.id;
  $("task-title").value        = task.title;
  $("task-desc").value         = task.description || "";
  $("task-due").value          = task.due_date    || "";
  $("task-category").value     = task.category    || "other";
  const icon = { HIGH:"▲", MEDIUM:"◆", LOW:"▼" }[task.priority];
  $("predicted-priority").innerHTML  = `<span class="pi ${task.priority.toLowerCase()}">${icon}</span> ${task.priority}`;
  $("predicted-priority").className  = `priority-badge ${task.priority}`;
  $("confidence-bars").innerHTML     = "";
  _predicted = task.priority;
  $("task-modal").classList.remove("hidden");
}

function closeModal()    { $("task-modal").classList.add("hidden"); }

$("open-modal-btn") .addEventListener("click", openNewModal);
$("close-modal-btn").addEventListener("click", closeModal);
$("cancel-btn")     .addEventListener("click", closeModal);
$("task-modal")     .addEventListener("click", e => { if (e.target===$("task-modal")) closeModal(); });
document.addEventListener("keydown", e => { if (e.key==="Escape") { closeModal(); closeKwModal(); } });

// Predict 
$("predict-btn").addEventListener("click", async () => {
  const title = $("task-title").value.trim();
  if (!title) { toast("Enter a title first.", "error"); return; }
  const btn = $("predict-btn");
  btn.disabled = true; btn.textContent = "…";
  const { ok, data } = await api("POST", "/predict-priority", {
    title, description: $("task-desc").value.trim(),
    due_date: $("task-due").value || null, category: $("task-category").value,
  });
  btn.disabled = false; btn.textContent = "Predict";
  if (!ok) { toast("Prediction failed.", "error"); return; }
  _predicted = data.priority;
  const icon = { HIGH:"▲", MEDIUM:"◆", LOW:"▼" }[data.priority];
  const badge = $("predicted-priority");
  badge.innerHTML = `<span class="pi ${data.priority.toLowerCase()}">${icon}</span> ${data.priority}`;
  badge.className = `priority-badge ${data.priority}`;
  if (data.confidence) {
    const bars   = $("confidence-bars");
    const colors = { HIGH:"#e8341c", MEDIUM:"#d97706", LOW:"#059669" };
    bars.innerHTML = Object.entries(data.confidence).map(([cls, pct]) => `
      <div class="conf-bar-wrap">
        <div class="conf-bar-bg">
          <div class="conf-bar-fill" style="width:${Math.round(pct*100)}%;background:${colors[cls]}"></div>
        </div>
        <span>${cls[0]}:${Math.round(pct*100)}%</span>
      </div>`).join("");
  }
  toast(`Priority: ${data.priority}`);
});

// Save Task 
$("save-task-btn").addEventListener("click", async () => {
  const title = $("task-title").value.trim();
  if (!title) { toast("Title is required.", "error"); $("task-title").focus(); return; }

  // Auto-predict if not yet done
  if ($("predicted-priority").textContent.trim() === "—") {
    const { ok, data } = await api("POST", "/predict-priority", {
      title, description: $("task-desc").value.trim(),
      due_date: $("task-due").value || null, category: $("task-category").value,
    });
    if (ok) { _predicted = data.priority; }
  }

  const payload = {
    title, description: $("task-desc").value.trim(),
    due_date: $("task-due").value || null,
    category: $("task-category").value, priority: _predicted,
  };

  const editId = $("edit-task-id").value;
  $("save-task-btn").disabled = true;
  const result = editId
    ? await api("PUT",  `/tasks/${editId}`, payload)
    : await api("POST", "/tasks",           payload);
  $("save-task-btn").disabled = false;

  if (!result.ok) { toast(result.data.error || "Save failed.", "error"); return; }

  if (editId) {
    const idx = state.tasks.findIndex(t => t.id === parseInt(editId));
    if (idx !== -1) state.tasks[idx] = result.data.task;
    toast("Task updated ✓", "success");
  } else {
    state.tasks.unshift(result.data.task);
    toast("Task created! 🚀", "success");
  }
  closeModal();
  renderTasks(); updateCounts(); updateChart(); loadStats();
});

// Keywords 
async function openKwModal() {
  const { ok, data } = await api("GET", "/keywords");
  if (!ok) { toast("Could not load settings.", "error"); return; }
  $("kw-high")  .value = (data.custom?.HIGH   || []).join(", ");
  $("kw-medium").value = (data.custom?.MEDIUM || []).join(", ");
  $("kw-low")   .value = (data.custom?.LOW    || []).join(", ");
  $("defaults-high")  .textContent = (data.defaults?.HIGH   || []).join(", ");
  $("defaults-medium").textContent = (data.defaults?.MEDIUM || []).join(", ");
  $("keywords-modal").classList.remove("hidden");
}
function closeKwModal() { $("keywords-modal").classList.add("hidden"); }

$("open-keywords-btn")  .addEventListener("click", openKwModal);
$("close-keywords-btn") .addEventListener("click", closeKwModal);
$("cancel-keywords-btn").addEventListener("click", closeKwModal);
$("keywords-modal")     .addEventListener("click", e => { if (e.target===$("keywords-modal")) closeKwModal(); });

$("save-keywords-btn").addEventListener("click", async () => {
  const parse = id => $(id).value.split(",").map(w => w.trim().toLowerCase()).filter(Boolean);
  const payload = { HIGH: parse("kw-high"), MEDIUM: parse("kw-medium"), LOW: parse("kw-low") };
  $("save-keywords-btn").disabled = true;
  const { ok } = await api("POST", "/keywords", payload);
  $("save-keywords-btn").disabled = false;
  if (!ok) { toast("Failed to save.", "error"); return; }
  const total = payload.HIGH.length + payload.MEDIUM.length + payload.LOW.length;
  toast(`Saved ${total} custom keyword${total !== 1 ? "s" : ""} ✓`, "success");
  closeKwModal();
});

// Util 
function esc(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

//  Boot 
init();
