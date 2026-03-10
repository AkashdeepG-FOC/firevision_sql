// State Management
const state = {
    token: localStorage.getItem('access_token') || null,
    user: JSON.parse(localStorage.getItem('user_data')) || null,
    currentView: 'users',
    currentData: []
};

// API Base URL
const API_BASE = window.location.origin;

// Elements
const app = document.getElementById('app');
const loginOverlay = document.getElementById('login-overlay');
const loginForm = document.getElementById('login-form');
const dashboard = document.getElementById('dashboard');
const navLinks = document.querySelectorAll('.nav-link');
const contentArea = document.getElementById('content-area');
const viewTitle = document.getElementById('view-title');
const addBtn = document.getElementById('add-btn');
const addBtnText = document.getElementById('add-btn-text');
const logoutBtn = document.getElementById('logout-btn');
const modalOverlay = document.getElementById('modal-overlay');
const modalForm = document.getElementById('modal-form');
const modalFields = document.getElementById('modal-fields');
const modalTitle = document.getElementById('modal-title');
const toastEl = document.getElementById('toast');

// Initialize
function init() {
    if (state.token) {
        showDashboard();
    } else {
        showLogin();
    }
}

// Auth Functions
async function login(email, password) {
    try {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${API_BASE}/api/auth/token`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            state.token = data.access_token;
            localStorage.setItem('access_token', state.token);

            // Fetch User Details
            const userResponse = await fetch(`${API_BASE}/api/users/me`, {
                headers: { 'Authorization': `Bearer ${state.token}` }
            });

            if (userResponse.ok) {
                state.user = await userResponse.json();
                localStorage.setItem('user_data', JSON.stringify(state.user));
                showDashboard();
                showToast('Welcome back, Admin!', 'success');
            }
        } else {
            const err = await response.json();
            showLoginError(err.detail || 'Invalid credentials');
        }
    } catch (error) {
        showLoginError('Connection failed: ' + error.message);
    }
}

function logout() {
    state.token = null;
    state.user = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
    showLogin();
}

// Navigation Functions
function switchView(view) {
    state.currentView = view;
    navLinks.forEach(link => {
        if (link.dataset.view === view) link.classList.add('active');
        else link.classList.remove('active');
    });

    switch (view) {
        case 'users':
            viewTitle.innerText = 'User Management';
            addBtnText.innerText = 'Add User';
            addBtn.classList.remove('hidden');
            loadUsers();
            break;
        case 'cameras':
            viewTitle.innerText = 'Camera Registry';
            addBtnText.innerText = 'Register Camera';
            addBtn.classList.remove('hidden');
            loadCameras();
            break;
        case 'alerts':
            viewTitle.innerText = 'Security Alerts';
            addBtn.classList.add('hidden');
            loadAlerts();
            break;
    }
}

// API Calls & Rendering
async function fetchData(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (response.status === 401) return logout();
        if (response.ok) return await response.json();
        return [];
    } catch (e) {
        showToast('Error fetching data: ' + e.message, 'error');
        return [];
    }
}

async function loadUsers() {
    contentArea.innerHTML = '<div class="loader">Loading users...</div>';
    const users = await fetchData('/api/users/');
    state.currentData = users;
    renderData();
}

async function loadCameras() {
    contentArea.innerHTML = '<div class="loader">Loading cameras...</div>';
    const cameras = await fetchData('/api/cameras/');
    state.currentData = cameras;
    renderData();
}

async function loadAlerts() {
    contentArea.innerHTML = '<div class="loader">Loading alerts...</div>';
    const alerts = await fetchData('/api/alerts/');
    state.currentData = alerts;
    renderData();
}

function renderData() {
    contentArea.innerHTML = '';
    if (state.currentData.length === 0) {
        contentArea.innerHTML = `<div class="empty-state">No ${state.currentView} found.</div>`;
        return;
    }

    state.currentData.forEach(item => {
        const card = createCard(item);
        contentArea.appendChild(card);
    });
}

function createCard(item) {
    const card = document.createElement('div');
    card.className = 'data-card';

    let content = '';
    if (state.currentView === 'users') {
        content = `
            <div class="card-top">
                <span class="badge badge-${item.role}">${item.role}</span>
                <span class="badge badge-active">ACTIVE</span>
            </div>
            <h3 class="card-title">${item.name || 'No Name'}</h3>
            <p class="card-info">ID: ${item.id}</p>
            <p class="card-info"><i class="fas fa-envelope"></i> ${item.email}</p>
            <p class="card-info"><i class="fas fa-calendar"></i> Added: ${new Date(item.created_at).toLocaleDateString()}</p>
            <div class="card-actions">
                <button class="btn btn-icon btn-delete" onclick="deleteUser(${item.id})"><i class="fas fa-trash"></i></button>
            </div>
        `;
    } else if (state.currentView === 'cameras') {
        content = `
            <div class="card-top">
                <span class="badge badge-${item.status}">${item.status}</span>
                <i class="fas fa-video"></i>
            </div>
            <h3 class="card-title">${item.camera_name}</h3>
            <p class="card-info">ID: ${item.id}</p>
            <p class="card-info"><i class="fas fa-network-wired"></i> ${item.ip_address}</p>
            <p class="card-info"><i class="fas fa-map-marker-alt"></i> ${item.location || 'Unknown'}</p>
            <div class="card-actions">
                <button class="btn btn-icon btn-delete" onclick="deleteCamera(${item.id})"><i class="fas fa-trash"></i></button>
            </div>
        `;
    } else if (state.currentView === 'alerts') {
        const isFire = item.alert_type.toLowerCase() === 'fire';
        content = `
            <div class="card-top">
                <span class="badge" style="background:${isFire ? '#ff2a68' : '#ffa000'}; color:white">${item.alert_type}</span>
                <span>${Math.round(item.confidence_score * 100)}%</span>
            </div>
            <h3 class="card-title">Camera #${item.camera_id}</h3>
            <p class="card-info"><i class="fas fa-clock"></i> ${new Date(item.detected_at).toLocaleString()}</p>
            <p class="card-info">Detected significant ${item.alert_type} activity.</p>
        `;
    }

    card.innerHTML = content;
    return card;
}

// Action Functions
async function deleteUser(id) {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
        const response = await fetch(`${API_BASE}/api/users/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (response.ok) {
            showToast('User deleted successfully', 'success');
            loadUsers();
        }
    } catch (e) {
        showToast('Delete failed: ' + e.message, 'error');
    }
}

async function deleteCamera(id) {
    if (!confirm('Are you sure you want to delete this camera?')) return;
    try {
        const response = await fetch(`${API_BASE}/api/cameras/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        if (response.ok) {
            showToast('Camera deleted successfully', 'success');
            loadCameras();
        }
    } catch (e) {
        showToast('Delete failed: ' + e.message, 'error');
    }
}

// UI Helpers
function showLogin() {
    loginOverlay.classList.add('active');
    dashboard.classList.add('hidden');
}

function showDashboard() {
    loginOverlay.classList.remove('active');
    dashboard.classList.remove('hidden');
    document.getElementById('user-name').innerText = state.user.name || 'Administrator';
    document.getElementById('user-role').innerText = state.user.role.toUpperCase();
    switchView(state.currentView);
}

function showLoginError(msg) {
    const errEl = document.getElementById('login-error');
    errEl.innerText = msg;
    errEl.classList.add('active');
}

function showToast(msg, type = 'success') {
    toastEl.innerText = msg;
    toastEl.className = `toast ${type}`;
    toastEl.classList.remove('hidden');
    setTimeout(() => toastEl.classList.add('hidden'), 3000);
}

// Event Listeners
loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    login(document.getElementById('email').value, document.getElementById('password').value);
});

logoutBtn.addEventListener('click', logout);

navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        switchView(link.dataset.view);
    });
});

addBtn.addEventListener('click', () => {
    modalOverlay.classList.add('active');
    modalTitle.innerText = state.currentView === 'users' ? 'Add User' : 'Register Camera';
    renderModalFields();
});

document.querySelectorAll('.btn-close, .btn-close-modal').forEach(btn => {
    btn.addEventListener('click', () => modalOverlay.classList.remove('active'));
});

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
            </div>
        `;
    } else {
        modalFields.innerHTML = `
            <div class="input-group">
                <i class="fas fa-video"></i>
                <input type="text" id="c-name" placeholder="Camera Name" required>
            </div>
            <div class="input-group">
                <i class="fas fa-network-wired"></i>
                <input type="text" id="c-ip" placeholder="IP Address or URL" required>
            </div>
            <div class="input-group">
                <i class="fas fa-map-marker-alt"></i>
                <input type="text" id="c-loc" placeholder="Location">
            </div>
        `;
    }
}

modalForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = modalForm.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerText = 'Saving...';

    try {
        let endpoint = state.currentView === 'users' ? '/api/users/' : '/api/cameras/';
        let payload = {};

        if (state.currentView === 'users') {
            payload = {
                name: document.getElementById('m-name').value,
                email: document.getElementById('m-email').value,
                password: document.getElementById('m-pass').value,
                role: document.getElementById('m-role').value
            };
        } else {
            payload = {
                camera_name: document.getElementById('c-name').value,
                ip_address: document.getElementById('c-ip').value,
                location: document.getElementById('c-loc').value,
                status: 'active',
                user_id: state.user.id
            };
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            showToast('Created successfully', 'success');
            modalOverlay.classList.remove('active');
            modalForm.reset();
            if (state.currentView === 'users') loadUsers();
            else loadCameras();
        } else {
            const err = await response.json();
            showToast('Save failed: ' + (err.detail || 'Unknown error'), 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerText = 'Save Changes';
    }
});

// Run Init
init();
