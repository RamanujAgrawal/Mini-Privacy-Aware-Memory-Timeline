// API Base URL
const API_BASE = window.location.origin;

// State
let currentPermissions = {};
let currentCategoryFilter = "all";
let currentSearch = "";
let currentStartDate = "";
let currentEndDate = "";
let currentPage = 1;
const pageSize = 10;
let totalEvents = 0;

// Category icons & styling metadata
const categoryMeta = {
  conversation: {
    icon: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>`,
    label: "Conversation",
    class: "cat-conversation"
  },
  location: {
    icon: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z"/><circle cx="12" cy="10" r="3"/></svg>`,
    label: "Location",
    class: "cat-location"
  },
  physiological: {
    icon: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
    label: "Physiological",
    class: "cat-physiological"
  },
  note: {
    icon: `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`,
    label: "Note",
    class: "cat-note"
  }
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

// Search & Date Filter Elements
const searchInput = document.getElementById("searchInput");
const clearSearchBtn = document.getElementById("clearSearchBtn");
const startDateInput = document.getElementById("startDateInput");
const endDateInput = document.getElementById("endDateInput");
const resetFiltersBtn = document.getElementById("resetFiltersBtn");

// Navigation Tabs
const navTabs = document.querySelectorAll(".nav-tab");
const viewPanels = document.querySelectorAll(".view-panel");

// Modal elements
const createModal = document.getElementById("createModal");
const openCreateModalBtn = document.getElementById("openCreateModalBtn");
const closeCreateModalBtn = document.getElementById("closeCreateModalBtn");
const cancelCreateBtn = document.getElementById("cancelCreateBtn");
const createEventForm = document.getElementById("createEventForm");

// Export Modal Elements
const exportModal = document.getElementById("exportModal");
const openExportModalBtn = document.getElementById("openExportModalBtn");
const closeExportModalBtn = document.getElementById("closeExportModalBtn");
const cancelExportBtn = document.getElementById("cancelExportBtn");
const executeExportBtn = document.getElementById("executeExportBtn");
const includeAuditTrail = document.getElementById("includeAuditTrail");

// User Profile Modal Elements
const profileModal = document.getElementById("profileModal");
const userProfileChip = document.getElementById("userProfileChip");
const closeProfileModalBtn = document.getElementById("closeProfileModalBtn");
const closeProfileBtn = document.getElementById("closeProfileBtn");

// Probe elements
const probeEventId = document.getElementById("probeEventId");
const runProbeBtn = document.getElementById("runProbeBtn");
const probeResult = document.getElementById("probeResult");
const toast = document.getElementById("toast");

// Simulator elements & state
const toggleSimBtn = document.getElementById("toggleSimBtn");
const simBtnText = document.getElementById("simBtnText");
let simIntervalId = null;

const simEventsPool = [
  { type: "conversation", title: "Discussion with Product Designer", content: "Talked about spatial audio transcription and user privacy boundaries." },
  { type: "location", title: "Transit: Metro Station Departure", content: "Location ping: 4th & King Caltrain Station. GPS accuracy: 4.2m." },
  { type: "physiological", title: "Heart Rate Baseline Reading", content: "Current heart rate: 76 BPM. Ambient temperature: 21°C." },
  { type: "note", title: "Voice Memo: Chronis Feature Idea", content: "Add semantic clustering to automatically group conversation topics." },
  { type: "location", title: "Arrived at Fitness Center", content: "Location ping: Equinox SOMA. Geo-fence entered." },
  { type: "physiological", title: "Elevated Heart Rate Detected", content: "Cardio activity detected: 135 BPM during incline sprint." }
];

async function postSimulatedEvent(specificType = null) {
  let pool = simEventsPool;
  if (specificType) {
    pool = simEventsPool.filter(e => e.type === specificType);
    if (!pool.length) {
      pool = [{ type: specificType, title: `Manual ${specificType} capture`, content: `Captured telemetry for category: ${specificType}` }];
    }
  }
  const item = pool[Math.floor(Math.random() * pool.length)];
  try {
    const res = await fetch(`${API_BASE}/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(item)
    });
    if (res.ok) {
      const created = await res.json();
      showToast(`⚡ Telemetry Ingested: Simulated ${created.type} event #${created.id}`);
      await fetchEvents();
    }
  } catch (err) {
    console.error("Simulation error:", err);
    showToast(`Simulation error: ${err.message}`, "error");
  }
}

function toggleSimulation() {
  if (simIntervalId) {
    clearInterval(simIntervalId);
    simIntervalId = null;
    toggleSimBtn.classList.remove("sim-active");
    simBtnText.textContent = "Auto-Stream: OFF";
    showToast("Live simulation paused");
  } else {
    toggleSimBtn.classList.add("sim-active");
    simBtnText.textContent = "Auto-Stream: LIVE";
    showToast("Live simulation started (new event every 6s)");
    postSimulatedEvent();
    simIntervalId = setInterval(postSimulatedEvent, 6000);
  }
}

if (toggleSimBtn) {
  toggleSimBtn.addEventListener("click", toggleSimulation);
}

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

// Format ISO date to readable string in India Standard Time (IST, UTC+5:30)
function formatDate(isoStr) {
  if (!isoStr) return "";
  let s = String(isoStr).trim();
  s = s.replace(" ", "T");
  if (!s.endsWith("Z") && !/[+-]\d{2}:?\d{2}$/.test(s)) {
    s += "Z";
  }
  const d = new Date(s);
  return d.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
  }) + " IST";
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
    if (currentSearch) {
      url += `&q=${encodeURIComponent(currentSearch)}`;
    }
    if (currentStartDate) {
      url += `&start_date=${encodeURIComponent(currentStartDate)}`;
    }
    if (currentEndDate) {
      url += `&end_date=${encodeURIComponent(currentEndDate)}`;
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

// Search & Date Filter Handlers
let searchDebounceTimeout = null;
if (searchInput) {
  searchInput.addEventListener("input", (e) => {
    const val = e.target.value.trim();
    if (clearSearchBtn) {
      clearSearchBtn.classList.toggle("hidden", !val);
    }
    clearTimeout(searchDebounceTimeout);
    searchDebounceTimeout = setTimeout(() => {
      currentSearch = val;
      currentPage = 1;
      fetchEvents();
    }, 350);
  });
}

if (clearSearchBtn) {
  clearSearchBtn.addEventListener("click", () => {
    searchInput.value = "";
    clearSearchBtn.classList.add("hidden");
    currentSearch = "";
    currentPage = 1;
    fetchEvents();
  });
}

if (startDateInput) {
  startDateInput.addEventListener("change", (e) => {
    const val = e.target.value;
    currentStartDate = val ? new Date(val).toISOString() : "";
    currentPage = 1;
    fetchEvents();
  });
}

if (endDateInput) {
  endDateInput.addEventListener("change", (e) => {
    const val = e.target.value;
    currentEndDate = val ? new Date(val).toISOString() : "";
    currentPage = 1;
    fetchEvents();
  });
}

if (resetFiltersBtn) {
  resetFiltersBtn.addEventListener("click", () => {
    if (searchInput) searchInput.value = "";
    if (clearSearchBtn) clearSearchBtn.classList.add("hidden");
    if (startDateInput) startDateInput.value = "";
    if (endDateInput) endDateInput.value = "";
    currentSearch = "";
    currentStartDate = "";
    currentEndDate = "";
    currentCategoryFilter = "all";
    document.querySelectorAll(".btn-filter").forEach(b => {
      b.classList.toggle("active", b.getAttribute("data-type") === "all");
    });
    currentPage = 1;
    fetchEvents();
    showToast("All search and date filters reset");
  });
}

// Wearable Simulator Specific Buttons
document.querySelectorAll(".btn-sim").forEach(btn => {
  btn.addEventListener("click", () => {
    const simType = btn.getAttribute("data-sim-type");
    postSimulatedEvent(simType);
  });
});

// Export Modal Handlers
if (openExportModalBtn) {
  openExportModalBtn.addEventListener("click", () => {
    exportModal.classList.remove("hidden");
  });
}

if (closeExportModalBtn) {
  closeExportModalBtn.addEventListener("click", () => exportModal.classList.add("hidden"));
}

if (cancelExportBtn) {
  cancelExportBtn.addEventListener("click", () => exportModal.classList.add("hidden"));
}

if (executeExportBtn) {
  executeExportBtn.addEventListener("click", async () => {
    const formatRadio = document.querySelector('input[name="exportFormat"]:checked');
    const selectedFormat = formatRadio ? formatRadio.value : "json";
    const includeAudit = includeAuditTrail ? includeAuditTrail.checked : true;

    executeExportBtn.disabled = true;
    executeExportBtn.textContent = "Generating Export...";

    try {
      const res = await fetch(`${API_BASE}/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          format: selectedFormat,
          include_audit_trail: includeAudit
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Export failed");
      }

      if (selectedFormat === "csv") {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `chronis_memory_export_${Date.now()}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } else {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `chronis_memory_export_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      }

      exportModal.classList.add("hidden");
      showToast(`📥 Export downloaded successfully (${selectedFormat.toUpperCase()})`);
    } catch (err) {
      console.error("Export error:", err);
      showToast(`Export error: ${err.message}`, "error");
    } finally {
      executeExportBtn.disabled = false;
      executeExportBtn.textContent = "Download Export";
    }
  });
}

// User Profile Modal Handlers
if (userProfileChip) {
  userProfileChip.addEventListener("click", () => {
    profileModal.classList.remove("hidden");
  });
}

if (closeProfileModalBtn) {
  closeProfileModalBtn.addEventListener("click", () => profileModal.classList.add("hidden"));
}

if (closeProfileBtn) {
  closeProfileBtn.addEventListener("click", () => profileModal.classList.add("hidden"));
}

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
