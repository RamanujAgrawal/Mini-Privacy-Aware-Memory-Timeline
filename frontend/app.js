// API Base URL
const API_BASE = window.location.origin;

// State
let currentPermissions = {};
let currentCategoryFilter = "all";
let currentPage = 1;
const pageSize = 10;
let totalEvents = 0;

// Category icons & styling metadata
const categoryMeta = {
  conversation: { icon: "💬", label: "Conversation", class: "cat-conversation" },
  location: { icon: "📍", label: "Location", class: "cat-location" },
  physiological: { icon: "❤️", label: "Physiological", class: "cat-physiological" },
  note: { icon: "📝", label: "Note", class: "cat-note" }
};

// DOM Elements
const permissionsGrid = document.getElementById("permissionsGrid");
const eventsList = document.getElementById("eventsList");
const eventsCount = document.getElementById("eventsCount");
const categoryFilters = document.getElementById("categoryFilters");
const prevPageBtn = document.getElementById("prevPageBtn");
const nextPageBtn = document.getElementById("nextPageBtn");
const pageInfo = document.getElementById("pageInfo");
const auditList = document.getElementById("auditList");
const refreshAuditBtn = document.getElementById("refreshAuditBtn");
const refreshAllBtn = document.getElementById("refreshAllBtn");

// Navigation Tabs
const navTabs = document.querySelectorAll(".nav-tab");
const viewPanels = document.querySelectorAll(".view-panel");

// Modal elements
const createModal = document.getElementById("createModal");
const openCreateModalBtn = document.getElementById("openCreateModalBtn");
const closeCreateModalBtn = document.getElementById("closeCreateModalBtn");
const cancelCreateBtn = document.getElementById("cancelCreateBtn");
const createEventForm = document.getElementById("createEventForm");

// Probe elements
const probeEventId = document.getElementById("probeEventId");
const runProbeBtn = document.getElementById("runProbeBtn");
const probeResult = document.getElementById("probeResult");
const toast = document.getElementById("toast");

// Navigation Tab Switcher
function switchView(viewName) {
  navTabs.forEach(tab => {
    tab.classList.toggle("active", tab.dataset.view === viewName);
  });
  viewPanels.forEach(panel => {
    panel.classList.toggle("active", panel.id === `view-${viewName}`);
  });
  window.location.hash = viewName;
  if (viewName === "audit") {
    fetchAuditLog();
  }
}

navTabs.forEach(tab => {
  tab.addEventListener("click", () => switchView(tab.dataset.view));
});

// Toast helper
function showToast(message, type = "success") {
  toast.textContent = message;
  toast.className = `toast toast-${type}`;
  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, 3500);
}

// Format ISO date to readable string
function formatDate(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

// -------------------------------------------------------------
// Privacy Permissions
// -------------------------------------------------------------
async function fetchPermissions() {
  try {
    const res = await fetch(`${API_BASE}/permissions`);
    if (!res.ok) throw new Error("Failed to load permissions");
    const data = await res.json();
    currentPermissions = data.permissions;
    renderPermissions();
  } catch (err) {
    console.error("Error fetching permissions:", err);
    permissionsGrid.innerHTML = `<div class="error-text">Failed to load permissions: ${err.message}</div>`;
  }
}

function renderPermissions() {
  permissionsGrid.innerHTML = "";
  const categories = ["conversation", "location", "physiological", "note"];

  categories.forEach(cat => {
    const isEnabled = currentPermissions[cat] !== false; // default true
    const meta = categoryMeta[cat] || { icon: "📌", label: cat, class: "" };

    const card = document.createElement("div");
    card.className = `toggle-card ${isEnabled ? "" : "disabled-category"}`;

    card.innerHTML = `
      <div class="toggle-info">
        <div class="category-icon ${meta.class}">${meta.icon}</div>
        <div>
          <div class="toggle-name">${meta.label}</div>
          <div class="toggle-status-text ${isEnabled ? 'active' : 'blocked'}">${isEnabled ? "Allowed" : "Blocked"}</div>
        </div>
      </div>
      <label class="switch">
        <input type="checkbox" data-category="${cat}" ${isEnabled ? "checked" : ""}>
        <span class="slider"></span>
      </label>
    `;

    const checkbox = card.querySelector("input");
    checkbox.addEventListener("change", async (e) => {
      const newStatus = e.target.checked;
      await updatePermission(cat, newStatus);
    });

    permissionsGrid.appendChild(card);
  });
}

async function updatePermission(category, isEnabled) {
  try {
    const res = await fetch(`${API_BASE}/permissions`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category, is_enabled: isEnabled })
    });
    if (!res.ok) throw new Error("Permission update rejected");
    
    currentPermissions[category] = isEnabled;
    renderPermissions();
    showToast(`'${category}' is now ${isEnabled ? "allowed" : "blocked"}`);
    
    // Refresh timeline and audit trail
    await fetchEvents();
  } catch (err) {
    console.error("Error updating permission:", err);
    showToast(`Failed to update permission: ${err.message}`, "error");
    renderPermissions();
  }
}

// -------------------------------------------------------------
// Timeline Events
// -------------------------------------------------------------
async function fetchEvents() {
  eventsCount.textContent = "Loading...";
  try {
    const offset = (currentPage - 1) * pageSize;
    let url = `${API_BASE}/events?limit=${pageSize}&offset=${offset}`;
    if (currentCategoryFilter !== "all") {
      url += `&type=${currentCategoryFilter}`;
    }

    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch events`);
    const data = await res.json();
    
    totalEvents = data.total;
    renderEvents(data.items);
    renderPagination();
  } catch (err) {
    console.error("Error fetching events:", err);
    eventsList.innerHTML = `
      <div class="empty-timeline">
        <h4>Error loading events</h4>
        <p>${err.message}</p>
      </div>
    `;
    eventsCount.textContent = "0 events";
  }
}

function renderEvents(items) {
  eventsList.innerHTML = "";
  eventsCount.textContent = `${totalEvents} event${totalEvents === 1 ? "" : "s"} visible`;

  if (!items || items.length === 0) {
    eventsList.innerHTML = `
      <div class="empty-timeline">
        <h4>No events visible</h4>
        <p>No memory events found for this filter. If a category is turned OFF in Privacy Controls, its events are strictly omitted by the backend API.</p>
      </div>
    `;
    return;
  }

  items.forEach(item => {
    const meta = categoryMeta[item.type] || { icon: "📌", label: item.type };
    const card = document.createElement("div");
    card.className = "event-card";
    card.setAttribute("data-type", item.type);

    card.innerHTML = `
      <div class="event-top">
        <span class="event-badge badge-${item.type}">${meta.icon} ${meta.label}</span>
        <span class="event-time">${formatDate(item.timestamp)}</span>
      </div>
      <div class="event-title">${escapeHtml(item.title)}</div>
      <div class="event-content">${escapeHtml(item.content)}</div>
      <div class="event-bottom">
        <span class="event-id-tag">ID: #${item.id}</span>
        <button class="btn-delete" data-id="${item.id}" title="Delete event">Delete</button>
      </div>
    `;

    card.querySelector(".btn-delete").addEventListener("click", () => deleteEvent(item.id));
    eventsList.appendChild(card);
  });
}

function renderPagination() {
  const totalPages = Math.ceil(totalEvents / pageSize) || 1;
  pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
  prevPageBtn.disabled = currentPage <= 1;
  nextPageBtn.disabled = currentPage >= totalPages;
}

async function deleteEvent(eventId) {
  if (!confirm(`Are you sure you want to delete event #${eventId}?`)) return;

  try {
    const res = await fetch(`${API_BASE}/events/${eventId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Delete failed");
    showToast(`Event #${eventId} deleted successfully`);
    await fetchEvents();
  } catch (err) {
    console.error("Delete error:", err);
    showToast(`Error deleting event: ${err.message}`, "error");
  }
}

// -------------------------------------------------------------
// Audit Log (View 2)
// -------------------------------------------------------------
async function fetchAuditLog() {
  try {
    const res = await fetch(`${API_BASE}/audit-log?limit=50`);
    if (!res.ok) throw new Error("Failed to fetch audit log");
    const data = await res.json();
    renderAuditLog(data.items);
  } catch (err) {
    console.error("Audit log error:", err);
    auditList.innerHTML = `<div class="audit-placeholder">Failed to load audit logs: ${err.message}</div>`;
  }
}

function renderAuditLog(items) {
  auditList.innerHTML = "";
  if (!items || items.length === 0) {
    auditList.innerHTML = `<div class="audit-placeholder">No audit entries recorded yet.</div>`;
    return;
  }

  items.forEach(item => {
    const entry = document.createElement("div");
    entry.className = "audit-entry";
    
    const resKey = (item.result || "").toLowerCase();
    let resClass = "res-allowed";
    if (resKey.includes("denied")) resClass = "res-denied";
    else if (resKey.includes("updated")) resClass = "res-updated";
    else if (resKey.includes("created")) resClass = "res-created";
    else if (resKey.includes("deleted")) resClass = "res-deleted";

    entry.innerHTML = `
      <div class="audit-entry-left">
        <span class="audit-action">${escapeHtml(item.action)}</span>
        <span class="audit-type-tag">${item.event_type || "general"}</span>
      </div>
      <div class="audit-entry-right">
        <span class="audit-result ${resClass}">${escapeHtml(item.result)}</span>
        <span class="audit-time">${formatDate(item.timestamp)}</span>
      </div>
    `;
    auditList.appendChild(entry);
  });
}

// -------------------------------------------------------------
// Direct API Probe (View 3)
// -------------------------------------------------------------
async function probeDirectEvent() {
  const id = probeEventId.value.trim();
  if (!id) return;

  probeResult.classList.remove("hidden", "allowed", "denied");
  probeResult.innerHTML = `Sending <code>GET /events/${id}</code>...`;

  try {
    const res = await fetch(`${API_BASE}/events/${id}`);
    const data = await res.json();

    if (res.status === 200) {
      probeResult.className = "probe-output allowed";
      probeResult.innerHTML = `
        <strong>HTTP 200 OK (Allowed)</strong><br>
        Event #${data.id} [${data.type}]: "${escapeHtml(data.title)}"<br>
        <em>Active privacy policy allows access to this category.</em>
      `;
    } else if (res.status === 403) {
      probeResult.className = "probe-output denied";
      probeResult.innerHTML = `
        <strong>HTTP 403 Forbidden (Blocked by Backend)</strong><br>
        Detail: ${escapeHtml(data.detail || data.message)}<br>
        <em>Security verification passed: A 'DENIED' entry was written to the Audit Trail.</em>
      `;
    } else if (res.status === 404) {
      probeResult.className = "probe-output denied";
      probeResult.innerHTML = `<strong>HTTP 404 Not Found</strong>: Event #${id} does not exist.`;
    } else {
      probeResult.className = "probe-output denied";
      probeResult.innerHTML = `<strong>HTTP ${res.status}</strong>: ${escapeHtml(JSON.stringify(data))}`;
    }
  } catch (err) {
    probeResult.className = "probe-output denied";
    probeResult.innerHTML = `Request error: ${err.message}`;
  }
}

// -------------------------------------------------------------
// Event Creation Modal
// -------------------------------------------------------------
openCreateModalBtn.addEventListener("click", () => {
  createEventForm.reset();
  createModal.classList.remove("hidden");
});

closeCreateModalBtn.addEventListener("click", () => createModal.classList.add("hidden"));
cancelCreateBtn.addEventListener("click", () => createModal.classList.add("hidden"));

createEventForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const category = document.getElementById("eventCategory").value;
  const title = document.getElementById("eventTitle").value.trim();
  const content = document.getElementById("eventContent").value.trim();

  if (!title || !content) {
    alert("Please enter both a title and content.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: category, title, content })
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Failed to create event");
    }
    const created = await res.json();
    createModal.classList.add("hidden");
    showToast(`Created event #${created.id} [${created.type}]`);
    await fetchEvents();
  } catch (err) {
    console.error("Create event error:", err);
    showToast(`Error creating event: ${err.message}`, "error");
  }
});

// Category Filter buttons
categoryFilters.addEventListener("click", (e) => {
  const btn = e.target.closest(".btn-filter");
  if (!btn) return;
  document.querySelectorAll(".btn-filter").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  currentCategoryFilter = btn.getAttribute("data-type");
  currentPage = 1;
  fetchEvents();
});

// Pagination handlers
prevPageBtn.addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage--;
    fetchEvents();
  }
});

nextPageBtn.addEventListener("click", () => {
  const totalPages = Math.ceil(totalEvents / pageSize);
  if (currentPage < totalPages) {
    currentPage++;
    fetchEvents();
  }
});

// Probe button handler
runProbeBtn.addEventListener("click", probeDirectEvent);

// Refresh handlers
refreshAuditBtn.addEventListener("click", fetchAuditLog);
refreshAllBtn.addEventListener("click", async () => {
  await fetchPermissions();
  await fetchEvents();
  showToast("Timeline and privacy refreshed");
});

// Helper: Escape HTML
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Initial Boot
async function init() {
  // Check hash route
  const hash = window.location.hash.replace("#", "");
  if (hash && ["timeline", "audit", "probe"].includes(hash)) {
    switchView(hash);
  }
  await fetchPermissions();
  await fetchEvents();
}

init();
