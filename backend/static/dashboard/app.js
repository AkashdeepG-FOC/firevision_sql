// ═══════════════════════════════════════════════════
//   FireGuard Dashboard — app.js
// ═══════════════════════════════════════════════════
const state = {
    token: localStorage.getItem('access_token') || null,
    user:  JSON.parse(localStorage.getItem('user_data')) || null,
    currentView: 'users',
    currentData:  [],
    allData:      []   // holds unfiltered copy for search
};

const API_BASE = window.location.origin;

// ─── DOM References ──────────────────────────────
const loginOverlay   = document.getElementById('login-overlay');
const loginForm      = document.getElementById('login-form');
const loginBtn       = document.getElementById('login-btn');
const dashboard      = document.getElementById('dashboard');
const navLinks       = document.querySelectorAll('.nav-link');
const contentArea    = document.getElementById('content-area');
const viewTitle      = document.getElementById('view-title');
const viewEyebrow    = document.getElementById('view-eyebrow');
const addBtn         = document.getElementById('add-btn');
const addBtnText     = document.getElementById('add-btn-text');
const logoutBtn      = document.getElementById('logout-btn');
const modalOverlay   = document.getElementById('modal-overlay');
const modalForm      = document.getElementById('modal-form');
const modalFields    = document.getElementById('modal-fields');
const modalTitle     = document.getElementById('modal-title');
const toastEl        = document.getElementById('toast');
const toastMsg       = document.getElementById('toast-msg');
const toastIcon      = toastEl.querySelector('.toast-icon i');
const statBarWrap    = document.getElementById('stat-bar-wrap');
const searchInput    = document.getElementById('search-input');
const alertBadge     = document.getElementById('alert-badge');

// ─── Init ────────────────────────────────────────
function init() {
    if (state.token) showDashboard();
    else             showLogin();
}

// ─── Auth ────────────────────────────────────────
async function login(email, password) {
    loginBtn.disabled  = true;
    loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in…';

    try {
        const fd = new FormData();
        fd.append('username', email);
        fd.append('password', password);

        const res = await fetch(`${API_BASE}/api/auth/token`, { method:'POST', body: fd });

        if (res.ok) {
            const data = await res.json();
            state.token = data.access_token;
            localStorage.setItem('access_token', state.token);

            const uRes = await fetch(`${API_BASE}/api/users/me`, {
                headers: { Authorization: `Bearer ${state.token}` }
            });
            if (uRes.ok) {
                state.user = await uRes.json();
                localStorage.setItem('user_data', JSON.stringify(state.user));
                showDashboard();
                showToast('Welcome back, ' + (state.user.name || 'Admin') + '!', 'success');
            }
        } else {
            const err = await res.json();
            showLoginError(err.detail || 'Invalid credentials. Please try again.');
        }
    } catch (e) {
        showLoginError('Connection failed: ' + e.message);
    } finally {
        loginBtn.disabled  = false;
        loginBtn.innerHTML = '<i class="fas fa-arrow-right-to-bracket"></i> Sign In';
    }
}

function logout() {
    state.token = state.user = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    showLogin();
}

// ─── Navigation ──────────────────────────────────
function switchView(view) {
    state.currentView = view;
    searchInput.value = '';

    navLinks.forEach(link => {
        link.classList.toggle('active', link.dataset.view === view);
    });

    switch (view) {
        case 'users':
            viewTitle.innerText   = 'User Management';
            viewEyebrow.innerText = 'Management';
            addBtnText.innerText  = 'Add User';
            addBtn.classList.remove('hidden');
            loadUsers();
            break;
        case 'cameras':
            viewTitle.innerText   = 'Camera Registry';
            viewEyebrow.innerText = 'Surveillance';
            addBtnText.innerText  = 'Register Camera';
            addBtn.classList.remove('hidden');
            loadCameras();
            break;
        case 'alerts':
            viewTitle.innerText   = 'Security Alerts';
            viewEyebrow.innerText = 'Monitoring';
            addBtn.classList.add('hidden');
            loadAlerts();
            break;
    }
}

// ─── Data Fetching ───────────────────────────────
async function fetchData(endpoint) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            headers: { Authorization: `Bearer ${state.token}` }
        });
        if (res.status === 401) { logout(); return []; }
        return res.ok ? await res.json() : [];
    } catch (e) {
        showToast('Error fetching data: ' + e.message, 'error');
        return [];
    }
}

function showLoader() {
    statBarWrap.innerHTML = '';
    contentArea.innerHTML = `
        <div class="loader">
            <div class="loader-spinner"></div>
            Loading ${state.currentView}…
        </div>`;
}

async function loadUsers() {
    showLoader();
    const users = await fetchData('/api/users/');
    state.currentData = state.allData = users;
    renderStatBar();
    renderData();
}
async function loadCameras() {
    showLoader();
    const cameras = await fetchData('/api/cameras/');
    state.currentData = state.allData = cameras;
    renderStatBar();
    renderData();
}
async function loadAlerts() {
    showLoader();
    const alerts = await fetchData('/api/alerts/');
    state.currentData = state.allData = alerts;
    renderStatBar();
    renderData();
    // Update badge
    if (alerts.length > 0) {
        alertBadge.style.display = 'inline';
        alertBadge.innerText = alerts.length > 99 ? '99+' : alerts.length;
    } else {
        alertBadge.style.display = 'none';
    }
}

// ─── Stat Bar ────────────────────────────────────
function renderStatBar() {
    const data = state.allData;
    let pills = '';

    if (state.currentView === 'users') {
        const admins    = data.filter(u => u.role === 'admin').length;
        const operators = data.filter(u => u.role === 'operator').length;
        pills = `
            <div class="stat-pill">
                <div class="stat-icon blue"><i class="fas fa-users"></i></div>
                <div><div class="stat-label">Total Users</div><div class="stat-value">${data.length}</div></div>
            </div>
            <div class="stat-pill">
                <div class="stat-icon red"><i class="fas fa-user-shield"></i></div>
                <div><div class="stat-label">Admins</div><div class="stat-value">${admins}</div></div>
            </div>
            <div class="stat-pill">
                <div class="stat-icon green"><i class="fas fa-user-gear"></i></div>
                <div><div class="stat-label">Operators</div><div class="stat-value">${operators}</div></div>
            </div>`;
    } else if (state.currentView === 'cameras') {
        const active   = data.filter(c => c.status === 'active').length;
        const inactive = data.filter(c => c.status !== 'active').length;
        pills = `
            <div class="stat-pill">
                <div class="stat-icon blue"><i class="fas fa-video"></i></div>
                <div><div class="stat-label">Total Cameras</div><div class="stat-value">${data.length}</div></div>
            </div>
            <div class="stat-pill">
                <div class="stat-icon green"><i class="fas fa-circle-check"></i></div>
                <div><div class="stat-label">Active</div><div class="stat-value">${active}</div></div>
            </div>
            <div class="stat-pill">
                <div class="stat-icon yellow"><i class="fas fa-circle-xmark"></i></div>
                <div><div class="stat-label">Inactive</div><div class="stat-value">${inactive}</div></div>
            </div>`;
    } else if (state.currentView === 'alerts') {
        const fires  = data.filter(a => a.alert_type?.toLowerCase() === 'fire').length;
        const smokes = data.filter(a => a.alert_type?.toLowerCase() !== 'fire').length;
        const avg    = data.length ? Math.round(data.reduce((s,a) => s + (a.confidence_score||0), 0) / data.length * 100) : 0;
        pills = `
            <div class="stat-pill">
                <div class="stat-icon red"><i class="fas fa-bell"></i></div>
                <div><div class="stat-label">Total Alerts</div><div class="stat-value">${data.length}</div></div>
            </div>
            <div class="stat-pill">
                <div class="stat-icon red"><i class="fas fa-fire"></i></div>
                <div><div class="stat-label">Fire</div><div class="stat-value">${fires}</div></div>
            </div>
            <div class="stat-pill">
                <div class="stat-icon yellow"><i class="fas fa-smog"></i></div>
                <div><div class="stat-label">Smoke/Other</div><div class="stat-value">${smokes}</div></div>
            </div>
            <div class="stat-pill">
                <div class="stat-icon green"><i class="fas fa-chart-simple"></i></div>
                <div><div class="stat-label">Avg Confidence</div><div class="stat-value">${avg}%</div></div>
            </div>`;
    }

    statBarWrap.innerHTML = `<div class="stat-bar">${pills}</div>`;
}

// ─── Render Cards ────────────────────────────────
function renderData() {
    contentArea.innerHTML = '';
    if (!state.currentData.length) {
        contentArea.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>No ${state.currentView} found.</p>
            </div>`;
        return;
    }
    state.currentData.forEach(item => contentArea.appendChild(createCard(item)));
}

function createCard(item) {
    const card = document.createElement('div');
    card.className = 'data-card';

    let html = '';
    if (state.currentView === 'users') {
        const roleClass = item.role === 'admin' ? 'badge-admin' : 'badge-operator';
        const initials  = (item.name || 'U').split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase();
        html = `
            <div class="card-top">
                <div class="card-icon-wrap" style="background:#f3f4f6;color:#374151;font-weight:700;font-size:.85rem;letter-spacing:0;">
                    ${initials}
                </div>
                <span class="badge ${roleClass}">${item.role}</span>
            </div>
            <h3 class="card-title">${escHtml(item.name || 'Unnamed User')}</h3>
            <p class="card-info"><i class="fas fa-envelope"></i>${escHtml(item.email)}</p>
            <p class="card-info"><i class="fas fa-hashtag"></i>ID: ${item.id}</p>
            <p class="card-info"><i class="fas fa-calendar-days"></i>Joined: ${fmtDate(item.created_at)}</p>
            <div class="card-divider"></div>
            <div class="card-actions">
                <span class="badge badge-active" style="margin-right:auto;">● Active</span>
                <button class="btn btn-icon btn-delete" title="Delete user" onclick="deleteUser(${item.id})">
                    <i class="fas fa-trash-can"></i>
                </button>
            </div>`;
    } else if (state.currentView === 'cameras') {
        const statusClass = item.status === 'active' ? 'badge-active' : 'badge-inactive';
        html = `
            <div class="card-top">
                <div class="card-icon-wrap">
                    <i class="fas fa-video"></i>
                </div>
                <span class="badge ${statusClass}">${item.status || 'unknown'}</span>
            </div>
            <h3 class="card-title">${escHtml(item.camera_name)}</h3>
            <p class="card-info"><i class="fas fa-network-wired"></i>${escHtml(item.ip_address)}</p>
            <p class="card-info"><i class="fas fa-location-dot"></i>${escHtml(item.location || 'Location not set')}</p>
            <p class="card-info"><i class="fas fa-hashtag"></i>Camera ID: ${item.id}</p>
            <div class="card-divider"></div>
            <div class="card-actions">
                <button class="btn btn-icon btn-delete" title="Delete camera" onclick="deleteCamera(${item.id})">
                    <i class="fas fa-trash-can"></i>
                </button>
            </div>`;
    } else if (state.currentView === 'alerts') {
        const isFire   = item.alert_type?.toLowerCase() === 'fire';
        const pct      = Math.round((item.confidence_score || 0) * 100);
        const badgeCls = isFire ? 'badge-fire' : 'badge-smoke';
        const iconCls  = isFire ? 'fa-fire' : 'fa-smog';
        html = `
            <div class="card-top">
                <div class="card-icon-wrap" style="background:${isFire ? 'var(--red-bg)' : 'var(--yellow-bg)'};color:${isFire ? 'var(--red)' : 'var(--yellow)'};">
                    <i class="fas ${iconCls}"></i>
                </div>
                <span class="badge ${badgeCls}">${escHtml(item.alert_type)}</span>
            </div>
            <h3 class="card-title">Camera #${item.camera_id}</h3>
            <p class="card-info"><i class="fas fa-clock"></i>${fmtDate(item.detected_at, true)}</p>
            <p class="card-info"><i class="fas fa-circle-info"></i>Detected ${escHtml(item.alert_type)} activity</p>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width:${pct}%"></div>
            </div>
            <p class="card-info" style="margin-top:.45rem;font-size:.75rem;">
                <i class="fas fa-gauge-high"></i>Confidence: <strong>${pct}%</strong>
            </p>`;
    }

    card.innerHTML = html;
    return card;
}

// ─── Actions ─────────────────────────────────────
async function deleteUser(id) {
    if (!confirm('Delete this user? This cannot be undone.')) return;
    try {
        const res = await fetch(`${API_BASE}/api/users/${id}`, {
            method: 'DELETE',
            headers: { Authorization: `Bearer ${state.token}` }
        });
        if (res.ok) { showToast('User deleted', 'success'); loadUsers(); }
        else showToast('Delete failed', 'error');
    } catch (e) { showToast('Error: ' + e.message, 'error'); }
}
async function deleteCamera(id) {
    if (!confirm('Remove this camera? This cannot be undone.')) return;
    try {
        const res = await fetch(`${API_BASE}/api/cameras/${id}`, {
            method: 'DELETE',
            headers: { Authorization: `Bearer ${state.token}` }
        });
        if (res.ok) { showToast('Camera removed', 'success'); loadCameras(); }
        else showToast('Delete failed', 'error');
    } catch (e) { showToast('Error: ' + e.message, 'error'); }
}

// ─── Search ──────────────────────────────────────
searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim().toLowerCase();
    if (!q) {
        state.currentData = state.allData;
    } else {
        state.currentData = state.allData.filter(item => {
            const v = state.currentView;
            if (v === 'users')   return (item.name||'' + item.email||'').toLowerCase().includes(q);
            if (v === 'cameras') return (item.camera_name||'' + item.ip_address||'').toLowerCase().includes(q);
            if (v === 'alerts')  return (item.alert_type||'' + item.camera_id).toString().toLowerCase().includes(q);
            return false;
        });
    }
    renderData();
});

// ─── UI Helpers ───────────────────────────────────
function showLogin() {
    loginOverlay.classList.add('active');
    dashboard.classList.add('hidden');
}

function showDashboard() {
    loginOverlay.classList.remove('active');
    dashboard.classList.remove('hidden');
    // Update avatar
    const name = state.user?.name || 'Admin';
    document.getElementById('user-name').innerText = name;
    document.getElementById('user-role').innerText = (state.user?.role || 'admin').toUpperCase();
    document.getElementById('user-avatar').src =
        `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=E84040&color=fff&bold=true&size=80`;
    switchView(state.currentView);
}

function showLoginError(msg) {
    const el = document.getElementById('login-error');
    el.innerText = msg;
    el.classList.add('active');
}

let toastTimer;
function showToast(msg, type = 'success') {
    clearTimeout(toastTimer);
    toastMsg.innerText = msg;
    toastEl.className = `toast ${type}`;
    toastIcon.className = type === 'success' ? 'fas fa-circle-check' : 'fas fa-circle-xmark';
    toastEl.classList.remove('hidden');
    toastTimer = setTimeout(() => toastEl.classList.add('hidden'), 3500);
}

// ─── Modal ───────────────────────────────────────
function renderModalFields() {
    if (state.currentView === 'users') {
        modalFields.innerHTML = `
            <div class="input-group">
                <i class="fas fa-user"></i>
                <input type="text" id="m-name" placeholder="Full Name" required>
            </div>
            <div class="input-group">
                <i class="fas fa-envelope"></i>
                <input type="email" id="m-email" placeholder="Email Address" required>
            </div>
            <div class="input-group">
                <i class="fas fa-lock"></i>
                <input type="password" id="m-pass" placeholder="Password" required>
            </div>
            <div class="input-group">
                <i class="fas fa-user-tag"></i>
                <select id="m-role">
                    <option value="operator">Operator</option>
                    <option value="admin">Admin</option>
                </select>
            </div>`;
    } else {
        modalFields.innerHTML = `
            <div class="input-group">
                <i class="fas fa-video"></i>
                <input type="text" id="c-name" placeholder="Camera Name" required>
            </div>
            <div class="input-group">
                <i class="fas fa-network-wired"></i>
                <input type="text" id="c-ip" placeholder="IP Address or Stream URL" required>
            </div>
            <div class="input-group">
                <i class="fas fa-location-dot"></i>
                <input type="text" id="c-loc" placeholder="Location (e.g. Floor 2, Gate A)">
            </div>`;
    }
}

// ─── Event Listeners ──────────────────────────────
loginForm.addEventListener('submit', e => {
    e.preventDefault();
    document.getElementById('login-error').innerText = '';
    login(document.getElementById('email').value, document.getElementById('password').value);
});

logoutBtn.addEventListener('click', logout);

navLinks.forEach(link => {
    link.addEventListener('click', e => { e.preventDefault(); switchView(link.dataset.view); });
});

addBtn.addEventListener('click', () => {
    modalTitle.innerText = state.currentView === 'users' ? 'Add New User' : 'Register Camera';
    renderModalFields();
    modalOverlay.classList.add('active');
});

document.querySelectorAll('.btn-close, .btn-close-modal').forEach(btn => {
    btn.addEventListener('click', () => modalOverlay.classList.remove('active'));
});

modalForm.addEventListener('submit', async e => {
    e.preventDefault();
    const submitBtn = modalForm.querySelector('button[type="submit"]');
    submitBtn.disabled  = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving…';

    try {
        const isUser = state.currentView === 'users';
        const endpoint = isUser ? '/api/users/' : '/api/cameras/';
        const payload  = isUser
            ? { name: document.getElementById('m-name').value,
                email: document.getElementById('m-email').value,
                password: document.getElementById('m-pass').value,
                role: document.getElementById('m-role').value }
            : { camera_name: document.getElementById('c-name').value,
                ip_address: document.getElementById('c-ip').value,
                location: document.getElementById('c-loc').value,
                status: 'active',
                user_id: state.user?.id };

        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${state.token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            showToast('Created successfully!', 'success');
            modalOverlay.classList.remove('active');
            modalForm.reset();
            isUser ? loadUsers() : loadCameras();
        } else {
            const err = await res.json();
            showToast('Save failed: ' + (err.detail || 'Unknown error'), 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    } finally {
        submitBtn.disabled  = false;
        submitBtn.innerHTML = '<i class="fas fa-check"></i> Save Changes';
    }
});

// ─── Helpers ──────────────────────────────────────
function escHtml(str) {
    return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function fmtDate(iso, withTime = false) {
    if (!iso) return '—';
    const d = new Date(iso);
    return withTime ? d.toLocaleString() : d.toLocaleDateString();
}

// ─── Boot ─────────────────────────────────────────
init();
