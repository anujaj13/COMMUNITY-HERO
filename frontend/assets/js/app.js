/* ============================================================
   Community Hero – app.js
   Full API integration with backend
   ============================================================ */

const API = window.API_BASE_URL || 'http://localhost:8000';

// ── Logging ────────────────────────────────────────────────
const LOG = {
  info: (msg, ...args) => console.log(`%c[INFO] ${msg}`, 'color: #6366f1; font-weight: bold;', ...args),
  warn: (msg, ...args) => console.warn(`%c[WARN] ${msg}`, 'color: #f59e0b; font-weight: bold;', ...args),
  error: (msg, ...args) => console.error(`%c[ERROR] ${msg}`, 'color: #ef4444; font-weight: bold;', ...args),
  debug: (msg, ...args) => console.debug(`%c[DEBUG] ${msg}`, 'color: #10b981;', ...args)
};

// ── State ──────────────────────────────────────────────────
let currentUser = null;
let allIssues = [];
let activeFilter = 'all';
let issueOffset = 0;
const PAGE_SIZE = 9;

// ── Init ───────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  LOG.info('Application initializing...');
  
  // Cold start handling: check backend health first
  const isHealthy = await checkBackendHealth();
  if (!isHealthy) {
    LOG.warn('Backend not ready. Please wait...');
    // You could show a specialized "Waking up services" UI here
  }

  initLoader();
  restoreSession();
  setupNavScroll();
  updateDeveloperLinks();
  setupFileDrop();
  loadDashboard();
  loadIssues();
  initMap();
  loadLeaderboard();
  loadPredictiveInsights();
});

/* ── Health Check ─────────────────────────────────────────── */
async function checkBackendHealth() {
  const loader = document.getElementById('pageLoader');
  const span = loader.querySelector('span') || document.createElement('span');
  if (!span.parentNode) loader.appendChild(span);
  
  let attempts = 0;
  const maxAttempts = 10;
  
  while (attempts < maxAttempts) {
    try {
      span.textContent = attempts === 0 ? 'Loading...' : `Waking up services... (${attempts}/${maxAttempts})`;
      const response = await fetch(`${API}/`, { method: 'GET' });
      if (response.ok) {
        LOG.info('Backend is healthy!');
        return true;
      }
    } catch (e) {
      LOG.debug(`Backend not ready yet (attempt ${attempts + 1})`);
    }
    attempts++;
    await new Promise(r => setTimeout(r, 2000));
  }
  
  span.textContent = 'Backend connection failed. Please refresh.';
  LOG.error('Backend failed to respond after several attempts.');
  return false;
}

/* ── Loader ───────────────────────────────────────────────── */
function initLoader() {
  LOG.debug('Hiding page loader in 1.8s');
  setTimeout(() => {
    document.getElementById('pageLoader').classList.add('hidden');
    LOG.debug('Page loader hidden');
  }, 1800);
}

/* ── Navbar scroll & mobile ───────────────────────────────── */
function setupNavScroll() {
  window.addEventListener('scroll', () => {
    const nb = document.getElementById('navbar');
    nb.style.boxShadow = window.scrollY > 20
      ? '0 4px 30px rgba(0,0,0,.12)'
      : '0 2px 20px rgba(0,0,0,.06)';
  });
}
function toggleMobileNav() {
  LOG.debug('Toggling mobile nav');
  document.getElementById('navLinks').classList.toggle('open');
}

/* ── Developer Links ───────────────────────────────────────── */
function updateDeveloperLinks() {
  const links = document.querySelectorAll('#developerLinks a');
  links.forEach(link => {
    const endpoint = link.getAttribute('data-endpoint');
    if (endpoint) {
      link.href = `${API}${endpoint}`;
    }
  });
}

/* ── Session ──────────────────────────────────────────────── */
function restoreSession() {
  const saved = localStorage.getItem('ch_user');
  if (saved) {
    try {
      currentUser = JSON.parse(saved);
      LOG.info(`Session restored for user: ${currentUser.username}`);
      updateNavbar();
    } catch (e) {
      LOG.error('Failed to restore session', e);
    }
  } else {
    LOG.info('No active session found.');
  }
}
function updateNavbar() {
  if (!currentUser) return;
  LOG.debug('Updating navbar for authenticated user');
  const el = document.getElementById('navActions');
  const initials = (currentUser.username || 'U').slice(0, 2).toUpperCase();
  const roleBadge = currentUser.role === 'admin' ? '<span style="background:var(--danger);color:#fff;padding:.25rem .5rem;border-radius:.25rem;font-size:.7rem;font-weight:700;margin-left:.25rem">ADMIN</span>'
    : currentUser.role === 'authority' ? '<span style="background:var(--primary);color:#fff;padding:.25rem .5rem;border-radius:.25rem;font-size:.7rem;font-weight:700;margin-left:.25rem">AUTHORITY</span>'
      : '';
  el.innerHTML = `
    <div class="user-pill">
      <div class="user-avatar">${initials}</div>
      <span class="user-name">${currentUser.username}${roleBadge}</span>
    </div>
    <button class="btn-login" onclick="logout()"><i class="fas fa-sign-out-alt"></i> Logout</button>`;
  // inject style once
  if (!document.getElementById('userPillStyle')) {
    const s = document.createElement('style');
    s.id = 'userPillStyle';
    s.textContent = `.user-pill{display:flex;align-items:center;gap:.5rem}.user-avatar{width:34px;height:34px;border-radius:50%;background:var(--grad);color:#fff;display:flex;align-items:center;justify-content:center;font-size:.8rem;font-weight:700}.user-name{font-weight:600;font-size:.9rem}`;
    document.head.appendChild(s);
  }
}
function logout() {
  LOG.info('Logging out user...');
  currentUser = null;
  localStorage.removeItem('ch_user');
  location.reload();
}

/* ── Stats / Dashboard ────────────────────────────────────── */
async function loadDashboard() {
  LOG.info('Loading dashboard data...');
  try {
    const stats = await apiFetch('/api/stats/dashboard');
    LOG.debug('Dashboard stats received:', stats);
    animateCount('stat-users', stats.total_users);
    animateCount('stat-issues', stats.total_issues);
    animateCount('stat-verifications', stats.total_verifications);
    animateCount('stat-resolved', stats.resolved_issues);
    const rateEl = document.getElementById('stat-rate');
    if (rateEl) rateEl.textContent = Math.round(stats.resolution_rate) + '%';
  } catch (e) {
    LOG.error('Failed to load dashboard stats', e);
  }

  try {
    loadCategoryChart();
    loadTrending();
    loadRecent();
    loadStatusChart();
  } catch (e) {
    LOG.error('Error loading dashboard sub-components', e);
  }
}

function animateCount(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  LOG.debug(`Animating ${id} to ${target}`);
  const start = 0;
  const duration = 1200;
  const step = timestamp => {
    if (!step.start) step.start = timestamp;
    const progress = Math.min((timestamp - step.start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(eased * target);
    if (progress < 1) requestAnimationFrame(step);
    else el.textContent = target;
  };
  requestAnimationFrame(step);
}

async function loadCategoryChart() {
  const container = document.getElementById('categoryChart');
  if (!container) return;
  try {
    const data = await apiFetch('/api/issues/stats/by-category');
    if (!data.length) { container.innerHTML = '<p class="no-data">No data yet</p>'; return; }
    const max = Math.max(...data.map(d => d.count));
    container.innerHTML = data.map(d => `
      <div class="bar-row">
        <div class="bar-label">${categoryLabel(d.category)}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${max ? (d.count / max * 100) : 0}%"></div></div>
        <div class="bar-count">${d.count}</div>
      </div>`).join('');
  } catch (e) {
    container.innerHTML = '<p class="no-data">Could not load</p>';
  }
}

async function loadTrending() {
  const list = document.getElementById('trendingList');
  if (!list) return;
  try {
    const data = await apiFetch('/api/issues/trending/list?days=7');
    const rankClass = i => i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '';
    list.innerHTML = data.length ? data.slice(0, 6).map((issue, i) => `
      <li onclick="openIssueDetail(${issue.id})">
        <div class="trend-rank ${rankClass(i)}">${i + 1}</div>
        <div class="trend-info">
          <strong>${escHtml(issue.title)}</strong>
          <span>${escHtml(issue.address || '')}</span>
        </div>
        <span class="trend-verif"><i class="fas fa-check"></i> ${issue.verification_count}</span>
      </li>`).join('')
      : '<li style="padding:1rem;color:var(--text-muted);font-size:.875rem">No trending issues yet</li>';
  } catch (e) { }
}

async function loadRecent() {
  const list = document.getElementById('recentList');
  if (!list) return;
  try {
    const data = await apiFetch('/api/issues/?limit=6');
    list.innerHTML = data.length ? data.map(issue => `
      <li onclick="openIssueDetail(${issue.id})">
        <span class="recent-title">${escHtml(issue.title)}</span>
        <div class="recent-meta">
          <span class="priority-pill ${issue.priority}">${issue.priority}</span>
          <span style="font-size:.72rem;color:var(--text-muted)">${timeAgo(issue.created_at)}</span>
        </div>
      </li>`).join('')
      : '<li style="padding:1rem;color:var(--text-muted);font-size:.875rem">No issues yet</li>';
  } catch (e) { }
}

async function loadStatusChart() {
  const container = document.getElementById('statusChart');
  if (!container) return;
  try {
    const data = await apiFetch('/api/issues/');
    const totals = {};
    data.forEach(i => { totals[i.status] = (totals[i.status] || 0) + 1; });
    const statuses = ['reported', 'verified', 'in_progress', 'resolved'];
    const max = Math.max(...Object.values(totals), 1);
    container.innerHTML = statuses.map(s => `
      <div class="status-row">
        <div class="status-label">${s.replace('_', ' ')}</div>
        <div class="status-bar-track"><div class="status-bar-fill ${s}" style="width:${((totals[s] || 0) / max * 100)}%"></div></div>
        <div class="status-count">${totals[s] || 0}</div>
      </div>`).join('');
  } catch (e) { container.innerHTML = '<p class="no-data">No data yet</p>'; }
}

/* ── Issues Feed ──────────────────────────────────────────── */
async function loadIssues(reset = true) {
  if (reset) { issueOffset = 0; allIssues = []; }
  const container = document.getElementById('issuesList');

  if (reset) {
    container.innerHTML = `<div class="issues-skeleton">
      <div class="skeleton-card"></div>
      <div class="skeleton-card"></div>
      <div class="skeleton-card"></div>
    </div>`;
  }

  try {
    const params = new URLSearchParams({ limit: PAGE_SIZE, skip: issueOffset });
    if (activeFilter !== 'all') params.append('status', activeFilter);
    const data = await apiFetch(`/api/issues/?${params}`);

    if (reset) allIssues = data;
    else allIssues = [...allIssues, ...data];

    issueOffset += data.length;
    renderIssues(allIssues);
    document.getElementById('loadMoreBtn').style.display = data.length === PAGE_SIZE ? '' : 'none';
  } catch (e) {
    container.innerHTML = '<div class="empty-state"><i class="fas fa-wifi-slash"></i><h3>Could not connect to backend</h3><p>Make sure the backend server is running on http://localhost:8000</p></div>';
  }
}

function renderIssues(issues) {
  const container = document.getElementById('issuesList');
  const search = document.getElementById('issueSearch').value.toLowerCase();
  const filtered = search ? issues.filter(i =>
    i.title.toLowerCase().includes(search) ||
    (i.description || '').toLowerCase().includes(search) ||
    (i.address || '').toLowerCase().includes(search)
  ) : issues;

  if (!filtered.length) {
    container.innerHTML = `<div class="empty-state">
      <i class="fas fa-search"></i>
      <h3>No issues found</h3>
      <p>${search ? 'Try a different search term.' : 'Be the first to report an issue!'}</p>
    </div>`;
    return;
  }

  container.innerHTML = filtered.map(issue => `
    <div class="issue-card" onclick="openIssueDetail(${issue.id})">
      <div class="issue-card-header">
        <div class="issue-card-title">${escHtml(issue.title)}</div>
        <span class="priority-pill ${issue.priority}">${issue.priority}</span>
      </div>
      <div class="issue-card-meta">
        <span><i class="fas fa-tag"></i> ${categoryLabel(issue.category)}</span>
        <span><i class="fas fa-map-marker-alt"></i> ${escHtml(issue.address || 'Unknown')}</span>
        <span><i class="fas fa-clock"></i> ${timeAgo(issue.created_at)}</span>
      </div>
      <div class="issue-card-desc">${escHtml(issue.description || '')}</div>
      <div class="issue-card-footer">
        <span class="status-badge ${issue.status}">${issue.status.replace('_', ' ')}</span>
        <span class="verify-count"><i class="fas fa-check-double"></i> ${issue.verification_count} verified</span>
      </div>
    </div>`).join('');
}

function filterIssues() { renderIssues(allIssues); }

function setFilter(btn, filter) {
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  activeFilter = filter;
  loadIssues(true);
}

function loadMoreIssues() { loadIssues(false); }

/* ── Issue Detail ─────────────────────────────────────────── */
async function openIssueDetail(id) {
  const modal = document.getElementById('issueDetailModal');
  const content = document.getElementById('issueDetailContent');
  content.innerHTML = '<div style="padding:2rem;text-align:center"><i class="fas fa-spinner fa-spin" style="font-size:2rem;color:var(--primary)"></i></div>';
  modal.classList.add('open');
  try {
    const issue = await apiFetch(`/api/issues/${id}`);

    // Debug logging for authority button visibility
    if (isAuthority()) {
      LOG.debug(`Issue Detail Debug:`, {
        issue_id: id,
        assigned_to_id: issue.assigned_to_id,
        assigned_to_id_type: typeof issue.assigned_to_id,
        current_user_id: currentUser?.id,
        current_user_id_type: typeof currentUser?.id,
        matches: parseInt(issue.assigned_to_id) === parseInt(currentUser?.id)
      });
    }

    let mediaHtml = '';
    if (issue.image_url) {
      mediaHtml = `<div class="detail-media"><img src="${API}/${issue.image_url}" alt="${escHtml(issue.title)}"></div>`;
    } else if (issue.video_url) {
      mediaHtml = `<div class="detail-media"><video src="${API}/${issue.video_url}" controls></video></div>`;
    }

    // Check if current user is the issue owner
    const isOwner = currentUser && currentUser.id === issue.reported_by_id;

    // Check if current user is the assigned resolver (handle type mismatch)
    const isAssignedResolver = currentUser && issue.assigned_to_id &&
      parseInt(issue.assigned_to_id) === parseInt(currentUser.id);

    // Check if this is an uncategorized issue (category is "other" and likely AI failed)
    const isUncategorized = issue.category === 'other';
    const hasAiErrorMsg = isUncategorized && (
      issue.title === 'Unidentified Issue' ||
      issue.description.includes('unable to analyze') ||
      issue.description.includes('provide details manually')
    );

    content.innerHTML = `
      <div class="detail-header">
        <div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-bottom:.75rem">
          <span class="status-badge ${issue.status}">${issue.status.replace('_', ' ')}</span>
          <span class="priority-pill ${issue.priority}">${issue.priority}</span>
          <span class="priority-pill medium" style="background:rgba(99,102,241,.1);color:var(--primary)">${categoryLabel(issue.category)}</span>
        </div>
        <h2>${escHtml(issue.title)}</h2>
        <p style="color:var(--text-muted);font-size:.875rem"><i class="fas fa-clock"></i> ${timeAgo(issue.created_at)} &nbsp;•&nbsp; <i class="fas fa-check-double"></i> ${issue.verification_count} verifications &nbsp;•&nbsp; <i class="fas fa-star"></i> Impact ${Math.round(issue.impact_score)}</p>
      </div>
      ${mediaHtml}
      ${isOwner && hasAiErrorMsg ? `
        <div style="background: rgba(251, 146, 60, 0.1); border-left: 4px solid rgb(251, 146, 60); padding: 1rem; margin: 1rem 0; border-radius: 0.25rem;">
          <p style="color: rgb(124, 45, 18); font-size: 0.875rem; margin: 0;">
            <i class="fas fa-info-circle"></i> <strong>Unable to Auto-Categorize:</strong> The AI service couldn't automatically categorize this issue. You can edit it now to provide more specific details and categorize it correctly.
          </p>
        </div>
      ` : ''}
      <div class="issue-detail-grid">
        <div class="issue-detail-full detail-section">
          <div class="detail-label">Description</div>
          <div class="detail-value">${escHtml(issue.description || '')}</div>
        </div>
        <div class="detail-section">
          <div class="detail-label">Location</div>
          <div class="detail-value"><i class="fas fa-map-marker-alt" style="color:var(--primary)"></i> ${escHtml(issue.address || 'N/A')}</div>
        </div>
        <div class="detail-section">
          <div class="detail-label">Coordinates</div>
          <div class="detail-value">${issue.latitude?.toFixed(4)}, ${issue.longitude?.toFixed(4)}</div>
        </div>
      </div>
      <div class="detail-actions">
        ${isOwner ? `<button class="btn btn-primary" onclick="openEditIssueModal(${issue.id}, '${escHtml(issue.title)}', '${escHtml((issue.description || '').replace(/'/g, "\\'"))}', '${issue.category}', '${issue.priority}')"><i class="fas fa-edit"></i> Edit Report</button>` : ''}
        ${currentUser && !isAuthority() && issue.status !== 'resolved' && issue.status !== 'closed' ? `<button class="btn-verify" onclick="verifyIssue(${issue.id})"><i class="fas fa-check-circle"></i> Verify this Issue</button>` : ''}
        ${isAuthority() && !issue.assigned_to_id && issue.status !== 'resolved' && issue.status !== 'closed' ? `<button class="btn btn-success" onclick="assignIssue(${issue.id})"><i class="fas fa-hand-paper"></i> Claim Issue</button>` : ''}
        ${isAuthority() && isAssignedResolver && issue.status !== 'resolved' && issue.status !== 'closed' ? `
          <div style="display:flex;gap:.5rem;flex-wrap:wrap">
            <button class="btn btn-info" onclick="updateIssueStatus(${issue.id}, 'in_progress')"><i class="fas fa-spinner"></i> In Progress</button>
            <button class="btn btn-success" onclick="resolveIssue(${issue.id}, 'Issue resolved by authority')"><i class="fas fa-check"></i> Mark Resolved</button>
          </div>
        ` : ''}
        ${issue.status === 'resolved' ? `<div style="background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);padding:0.75rem;border-radius:0.375rem;color:var(--success);font-weight:600;text-align:center"><i class="fas fa-lock"></i> This issue is resolved and locked</div>` : ''}
        ${issue.status === 'closed' ? `<div style="background:rgba(100,116,139,0.1);border:1px solid rgba(100,116,139,0.3);padding:0.75rem;border-radius:0.375rem;color:var(--text-muted);font-weight:600;text-align:center"><i class="fas fa-lock"></i> This issue is closed and locked</div>` : ''}
        ${!currentUser ? `<button class="btn btn-ghost" style="background:var(--primary);color:#fff" onclick="openLoginModal()"><i class="fas fa-sign-in-alt"></i> Login to Verify</button>` : ''}
        <button class="btn btn-secondary" onclick="closeIssueDetail()"><i class="fas fa-times"></i> Close</button>
      </div>`;
  } catch (e) {
    content.innerHTML = '<p style="padding:2rem;text-align:center;color:var(--danger)">Could not load issue details.</p>';
  }
  // Inject resolution forecast badge asynchronously after content renders
  if (document.getElementById('issueDetailContent')) {
    loadResolutionForecast(id);
  }
}

function closeIssueDetail() {
  document.getElementById('issueDetailModal').classList.remove('open');
}

function openEditIssueModal(issueId, title, description, category, priority) {
  const editModal = document.getElementById('editIssueModal');
  if (!editModal) {
    LOG.error('Edit modal not found in DOM');
    return;
  }

  // Populate the form with current values
  document.getElementById('editIssueId').value = issueId;
  document.getElementById('editIssueTitle').value = title;
  document.getElementById('editIssueDescription').value = description;
  document.getElementById('editIssueCategory').value = category;
  document.getElementById('editIssuePriority').value = priority;

  editModal.classList.add('open');
  LOG.debug(`Edit modal opened for issue ${issueId}`);
}

function closeEditIssueModal() {
  document.getElementById('editIssueModal').classList.remove('open');
}

async function handleEditIssueSubmit(e) {
  e.preventDefault();
  if (!currentUser) {
    showToast('Please log in', 'info');
    return;
  }

  const issueId = document.getElementById('editIssueId').value;
  const btn = document.getElementById('editIssueSubmitBtn');

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

  try {
    const updateData = {
      title: document.getElementById('editIssueTitle').value.trim(),
      description: document.getElementById('editIssueDescription').value.trim(),
      category: document.getElementById('editIssueCategory').value,
      priority: document.getElementById('editIssuePriority').value
    };

    if (!updateData.title) {
      showToast('Title is required', 'error');
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-save"></i> Save Changes';
      return;
    }

    if (!updateData.description) {
      showToast('Description is required', 'error');
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-save"></i> Save Changes';
      return;
    }

    await apiFetch(`/api/issues/${issueId}?user_id=${currentUser.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updateData)
    });

    showToast('Issue updated successfully!', 'success');
    closeEditIssueModal();
    closeIssueDetail();
    loadIssues(true);
    loadDashboard();
    loadMapPins();
  } catch (err) {
    LOG.error('Edit issue error:', err);
    showToast('Error: ' + (err.message || 'Could not update issue'), 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-save"></i> Save Changes';
  }
}

async function verifyIssue(issueId) {
  if (!currentUser) { showToast('Please log in to verify issues', 'info'); return; }
  try {
    await apiFetch(`/api/verifications/?user_id=${currentUser.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ issue_id: issueId, is_confirmed: true, severity_level: 'medium' })
    });

    // Update user reputation locally
    currentUser.reputation_score = (currentUser.reputation_score || 0) + 15;
    localStorage.setItem('ch_user', JSON.stringify(currentUser));

    showToast('Issue verified! +15 reputation points', 'success');
    await loadIssues(true);
    await loadDashboard();
    closeIssueDetail();
  } catch (e) {
    const errorMsg = e.message || '';
    if (errorMsg.includes('locked') || errorMsg.includes('resolved') || errorMsg.includes('closed')) {
      showToast('Cannot verify a resolved or closed issue', 'warning');
    } else if (errorMsg.includes('Already verified')) {
      showToast('You have already verified this issue', 'info');
    } else {
      showToast('Error verifying issue: ' + errorMsg, 'error');
    }
  }
}

/* ── Resolver / Authority Functions ────────────────────────── */
function isAuthority() {
  return currentUser && (currentUser.role === 'authority' || currentUser.role === 'admin');
}

async function assignIssue(issueId) {
  if (!isAuthority()) {
    showToast('Only authorities can claim issues', 'info');
    return;
  }
  try {
    LOG.info(`Claiming issue ${issueId} by authority ${currentUser.id}`);

    const res = await apiFetch(`/api/resolvers/${issueId}/assign?resolver_id=${currentUser.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estimated_resolution_date: null })
    });

    LOG.debug(`Issue ${issueId} assigned successfully`, res);

    // Update current user reputation locally
    currentUser.reputation_score = (currentUser.reputation_score || 0) + 25;
    localStorage.setItem('ch_user', JSON.stringify(currentUser));

    showToast('Issue claimed! +25 reputation points', 'success');

    // Close modal first to show changes
    closeIssueDetail();

    // Then reload data to refresh UI
    LOG.debug('Reloading issues and dashboard after claim...');
    await loadIssues(true);
    await loadDashboard();

    LOG.info(`Claim complete for issue ${issueId}`);
  } catch (e) {
    LOG.error('Error assigning issue', e);
    showToast('Could not claim issue: ' + (e.message || 'Error'), 'error');
  }
}

async function updateIssueStatus(issueId, newStatus) {
  if (!isAuthority()) {
    showToast('Only authorities can update status', 'info');
    return;
  }
  try {
    await apiFetch(`/api/resolvers/${issueId}/status?resolver_id=${currentUser.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus, notes: '' })
    });
    showToast(`Issue status updated to ${newStatus}`, 'success');
    await loadIssues(true);
    closeIssueDetail();
  } catch (e) {
    const errorMsg = e.message || '';
    if (errorMsg.includes('locked') || errorMsg.includes('resolved') || errorMsg.includes('closed')) {
      showToast('Cannot modify resolved or closed issues', 'warning');
    } else {
      showToast('Error updating status: ' + errorMsg, 'error');
    }
  }
}

async function resolveIssue(issueId, notes) {
  if (!isAuthority()) {
    showToast('Only authorities can resolve issues', 'info');
    return;
  }
  try {
    await apiFetch(`/api/resolvers/${issueId}/resolve?resolver_id=${currentUser.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resolution_notes: notes || 'Issue resolved' })
    });

    // Update current user reputation locally
    currentUser.reputation_score = (currentUser.reputation_score || 0) + 50;
    localStorage.setItem('ch_user', JSON.stringify(currentUser));

    showToast('Issue resolved! +50 reputation points', 'success');

    // Force reload issues and dashboard before closing modal
    await loadIssues(true);
    await loadDashboard();

    // Close modal after data is loaded
    closeIssueDetail();
  } catch (e) {
    const errorMsg = e.message || '';
    if (errorMsg.includes('locked') || errorMsg.includes('resolved') || errorMsg.includes('closed')) {
      showToast('Cannot modify resolved or closed issues', 'warning');
    } else if (errorMsg.includes('already assigned') || errorMsg.includes('claimed')) {
      showToast('This issue has already been claimed by another authority', 'warning');
    } else {
      showToast('Error resolving issue: ' + errorMsg, 'error');
    }
  }
}

async function getResolutionHistory(issueId) {
  try {
    const history = await apiFetch(`/api/resolvers/${issueId}/history`);
    LOG.debug('Resolution history fetched', history);

    if (!history || history.length === 0) {
      return '<p class="text-muted">No resolution history yet</p>';
    }

    const html = history.map(h => `
      <div class="history-entry" style="border-bottom:1px solid #e5e7eb;padding:12px 0">
        <div style="font-weight:600;color:#374151">${h.status}</div>
        <div style="font-size:.85rem;color:#6b7280">${new Date(h.changed_at).toLocaleDateString()}</div>
        <div style="font-size:.9rem;margin-top:4px;color:#4b5563">${h.notes || 'No notes'}</div>
      </div>
    `).join('');

    return html;
  } catch (e) {
    LOG.error('Failed to load resolution history', e);
    return '<p class="text-muted">Could not load history</p>';
  }
}

/* ── Map ──────────────────────────────────────────────────── */
let _leafletMap = null;
let _mapMarkers = [];

function initMap() {
  const canvas = document.getElementById('issueMap');
  if (!canvas) return;

  // Initialize Leaflet Map
  _leafletMap = L.map('issueMap').setView([40.7128, -74.0060], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(_leafletMap);

  loadMapPins();
}

async function loadMapPins() {
  const countEl = document.getElementById('mapIssueCount');
  if (!_leafletMap) return;

  try {
    const issues = await apiFetch('/api/issues/?limit=100');

    // Clear old markers
    _mapMarkers.forEach(m => _leafletMap.removeLayer(m));
    _mapMarkers = [];

    const colors = { critical: '#f43f5e', high: '#f59e0b', medium: '#6366f1', low: '#10b981', resolved: '#22c55e' };

    issues.forEach(issue => {
      if (!issue.latitude || !issue.longitude) return;

      const color = issue.status === 'resolved' ? colors.resolved : (colors[issue.priority] || colors.medium);

      const marker = L.circleMarker([issue.latitude, issue.longitude], {
        radius: 8,
        fillColor: color,
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      }).addTo(_leafletMap);

      marker.bindPopup(`
        <div style="font-family:inherit">
          <strong style="display:block;margin-bottom:4px">${escHtml(issue.title)}</strong>
          <span class="status-badge ${issue.status}" style="font-size:10px">${issue.status}</span>
          <button class="btn btn-primary" style="padding:4px 8px;font-size:11px;margin-top:8px;width:100%" onclick="openIssueDetail(${issue.id})">Details</button>
        </div>
      `);

      _mapMarkers.push(marker);
    });

    if (countEl) countEl.textContent = `${issues.length} issue${issues.length !== 1 ? 's' : ''}`;

    // Fit bounds if markers exist
    if (_mapMarkers.length > 0) {
      const group = new L.featureGroup(_mapMarkers);
      _leafletMap.fitBounds(group.getBounds().pad(0.1));
    }
  } catch (e) {
    console.error('Map loading error:', e);
  }
}

/* ── Leaderboard ──────────────────────────────────────────── */
async function loadLeaderboard() {
  try {
    const users = await apiFetch('/api/users/');
    const sorted = users.sort((a, b) => b.reputation_score - a.reputation_score);
    renderTop3(sorted.slice(0, 3));
    renderLeaderboardTable(sorted.slice(0, 15));
  } catch (e) { }
}

function renderTop3(top) {
  const el = document.getElementById('top3Heroes');
  if (!el) return;
  const medals = ['🥇', '🥈', '🥉'];
  const rankClass = ['rank1', 'rank2', 'rank3'];
  const order = [1, 0, 2]; // visual order: 2nd, 1st, 3rd
  el.innerHTML = order.filter(i => top[i]).map(i => {
    const u = top[i];
    return `
      <div class="top3-card ${rankClass[i]}">
        <span class="top3-medal">${medals[i]}</span>
        <div class="top3-avatar">${(u.username || 'U').slice(0, 2).toUpperCase()}</div>
        <div class="top3-name">${escHtml(u.username)}</div>
        <span class="top3-score">${u.reputation_score} pts</span>
      </div>`;
  }).join('');
}

function renderLeaderboardTable(users) {
  const tbody = document.getElementById('leaderboardBody');
  if (!tbody) return;
  const medals = ['🥇', '🥈', '🥉'];
  tbody.innerHTML = users.map((u, i) => `
    <tr>
      <td class="lb-rank">${i < 3 ? medals[i] : i + 1}</td>
      <td>
        <div class="lb-user">
          <div class="lb-avatar">${(u.username || 'U').slice(0, 2).toUpperCase()}</div>
          <div>
            <div class="lb-username">
              ${escHtml(u.username)}
              ${u.role === 'admin' ? '<span style="background:var(--danger);color:#fff;padding:.2rem .4rem;border-radius:.2rem;font-size:.65rem;font-weight:700;margin-left:.25rem">ADMIN</span>' : u.role === 'authority' ? '<span style="background:var(--primary);color:#fff;padding:.2rem .4rem;border-radius:.2rem;font-size:.65rem;font-weight:700;margin-left:.25rem">AUTH</span>' : ''}
            </div>
            <div style="font-size:.78rem;color:var(--text-muted)">${escHtml(u.full_name || '')}</div>
          </div>
        </div>
      </td>
      <td class="lb-score">${u.reputation_score}</td>
      <td><span class="lb-badge-count">${u.badges_earned}</span></td>
      <td>${u.issues_reported || 0}</td>
    </tr>`).join('');
}

/* ── Report Form ──────────────────────────────────────────── */
async function handleReportSubmit(e) {
  e.preventDefault();
  if (!currentUser) {
    showToast('Please log in to report an issue', 'info');
    openLoginModal();
    return;
  }

  const form = e.target;
  const btn = document.getElementById('submitBtn');
  const fileInput = document.getElementById('fileInput');
  const aiStatus = document.getElementById('aiProcessingStatus');

  if (!fileInput.files[0]) {
    showToast('Please upload a photo or video', 'error'); return;
  }

  const lat = document.getElementById('issueLat').value;
  const lng = document.getElementById('issueLng').value;
  const address = document.getElementById('issueAddress').value;

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
  if (aiStatus) aiStatus.style.display = 'block';

  try {
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('context', form.context.value.trim());
    formData.append('priority', form.priority.value);
    formData.append('latitude', lat);
    formData.append('longitude', lng);
    formData.append('address', address);

    // If we have AI results, send them to skip re-analysis in backend
    if (form.dataset.aiTitle) {
      formData.append('title', form.dataset.aiTitle);
      formData.append('description', form.dataset.aiDescription);
    }

    const issue = await apiFetch(`/api/issues/ai-report?user_id=${currentUser.id}`, {
      method: 'POST',
      body: formData
    });

    showToast('AI analysis complete! Issue reported successfully', 'success');
    form.reset();
    delete form.dataset.aiTitle;
    delete form.dataset.aiDescription;
    document.getElementById('aiPanel').style.display = 'none';
    document.getElementById('fileUploadText').textContent = 'Upload Issue Media';
    document.getElementById('fileDropzone').classList.remove('has-file');
    if (aiStatus) aiStatus.style.display = 'none';

    loadIssues(true);
    loadDashboard();
    loadMapPins();
    setTimeout(() => scrollToSection('issues'), 500);
  } catch (err) {
    showToast('Failed to submit: ' + (err.message || 'Server error'), 'error');
    if (aiStatus) aiStatus.style.display = 'none';
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit with AI Analysis';
  }
}

async function handleFileSelect(input) {
  const txt = document.getElementById('fileUploadText');
  const drop = document.getElementById('fileDropzone');

  if (input.files[0]) {
    const file = input.files[0];
    txt.textContent = file.name;
    drop.classList.add('has-file');
    // Just update the file name display, no automatic AI analysis
  }
}

function renderAIResult(result) {
  const content = document.getElementById('aiPanelContent');

  const tagsHtml = (result.tags || []).map(t => `<span class="ai-chip tag">#${t}</span>`).join('');

  let dupsHtml = '';
  if (result.duplicates && result.duplicates.length > 0) {
    dupsHtml = `
      <div class="ai-dup-alert">
        <div class="ai-dup-alert-header"><i class="fas fa-exclamation-triangle"></i> Possible Duplicates Found</div>
        <ul class="ai-dup-list">
          ${result.duplicates.map(d => `
            <li class="ai-dup-item">
              <a onclick="openIssueDetail(${d.id})">${escHtml(d.title)}</a>
              <span class="ai-dup-score">${Math.round(d.similarity_score * 100)}% match</span>
            </li>
          `).join('')}
        </ul>
      </div>
    `;
  }

  content.innerHTML = `
    <div class="ai-row">
      <span class="ai-label">Issue:</span>
      <strong style="font-size: 0.95rem; color: var(--primary)">${escHtml(result.title)}</strong>
    </div>
    <div class="ai-row">
      <span class="ai-label">Category:</span>
      <span class="ai-chip category">${categoryLabel(result.category)}</span>
      <span class="ai-label" style="margin-left: 1rem">Priority:</span>
      <span class="ai-chip priority ${result.priority}">${result.priority.toUpperCase()}</span>
    </div>
    <div class="ai-summary">${escHtml(result.summary || 'Visual analysis complete.')}</div>
    <div class="ai-row" style="margin-top: 0.25rem">${tagsHtml}</div>
    ${dupsHtml}
    <div class="ai-apply-hint">AI has drafted a <strong>detailed description</strong> for your report.</div>
  `;

  // Store the full description in a data attribute or similar to use on submit
  document.getElementById('reportForm').dataset.aiDescription = result.description;
  document.getElementById('reportForm').dataset.aiTitle = result.title;
}

function getCurrentLocation() {
  if (!navigator.geolocation) { showToast('Geolocation not supported', 'error'); return; }
  navigator.geolocation.getCurrentPosition(
    pos => {
      document.getElementById('issueLat').value = pos.coords.latitude;
      document.getElementById('issueLng').value = pos.coords.longitude;
      document.getElementById('issueAddress').value = `${pos.coords.latitude.toFixed(5)}, ${pos.coords.longitude.toFixed(5)}`;
      showToast('Location captured!', 'success');
    },
    () => showToast('Could not get location. Try entering it manually.', 'error')
  );
}

/* ── File Drop ────────────────────────────────────────────── */
function setupFileDrop() {
  const zone = document.getElementById('fileDropzone');
  if (!zone) return;
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const fi = document.getElementById('fileInput');
    fi.files = e.dataTransfer.files;
    handleFileSelect(fi);
  });
}

/* ── Auth ─────────────────────────────────────────────────── */
async function handleLogin(e) {
  e.preventDefault();
  const btn = document.getElementById('loginBtn');
  const form = e.target;
  const username = form.username.value.trim();

  LOG.info(`Attempting login for user: ${username}`);
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';

  try {
    const res = await apiFetch(
      `/api/users/login?username=${encodeURIComponent(username)}&password=${encodeURIComponent(form.password.value)}`,
      { method: 'POST' }
    );
    LOG.info(`Login successful for user: ${res.username}`);
    currentUser = res;
    localStorage.setItem('ch_user', JSON.stringify(res));
    showToast(`Welcome back, ${res.username}! 👋`, 'success');
    closeLoginModal();
    updateNavbar();
    loadLeaderboard();
  } catch (err) {
    LOG.warn(`Login failed: ${err.message}`);
    showToast('Invalid username or password', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
  }
}

async function handleSignup(e) {
  e.preventDefault();
  const btn = document.getElementById('signupBtn');
  const form = e.target;
  const username = form.username.value.trim();

  LOG.info(`Attempting registration for user: ${username}`);
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating account...';

  try {
    await apiFetch('/api/users/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        full_name: form.full_name.value.trim(),
        username: username,
        email: form.email.value.trim(),
        password: form.password.value
      })
    });
    LOG.info(`Account created for ${username}`);
    showToast('Account created! Please sign in.', 'success');
    closeSignupModal();
    setTimeout(openLoginModal, 400);
  } catch (err) {
    LOG.error(`Registration failed: ${err.message}`);
    showToast('Could not create account: ' + (err.message || 'Username or email already taken'), 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-user-plus"></i> Create Account';
  }
}

/* ── Modal helpers ────────────────────────────────────────── */
function openLoginModal() { document.getElementById('loginModal').classList.add('open'); }
function closeLoginModal() { document.getElementById('loginModal').classList.remove('open'); }
function openSignupModal() { document.getElementById('signupModal').classList.add('open'); }
function closeSignupModal() { document.getElementById('signupModal').classList.remove('open'); }
function switchToSignup() { closeLoginModal(); openSignupModal(); }
function switchToLogin() { closeSignupModal(); openLoginModal(); }
function closeModalOnOverlay(e, id) { if (e.target.id === id) document.getElementById(id).classList.remove('open'); }

function togglePassword(id) {
  const inp = document.getElementById(id);
  inp.type = inp.type === 'password' ? 'text' : 'password';
}

/* ── Toast ────────────────────────────────────────────────── */
function showToast(msg, type = 'success') {
  const icons = { success: 'fa-check-circle', error: 'fa-times-circle', info: 'fa-info-circle' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<i class="fas ${icons[type] || icons.success}"></i><span class="toast-msg">${escHtml(msg)}</span><button class="toast-close" onclick="removeToast(this.parentElement)"><i class="fas fa-times"></i></button>`;
  document.getElementById('toastContainer').appendChild(toast);
  setTimeout(() => removeToast(toast), 4500);
}
function removeToast(el) {
  el.classList.add('removing');
  setTimeout(() => el.remove(), 300);
}

/* ── Utilities ────────────────────────────────────────────── */
function scrollToSection(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  document.getElementById('navLinks').classList.remove('open');
}

function escHtml(str) {
  if (!str) return '';
  return String(str).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 30) return `${d}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

const CATEGORY_LABELS = {
  pothole: '🕳️ Pothole', water_leak: '💧 Water Leak', streetlight: '💡 Streetlight',
  waste_management: '🗑️ Waste', road_damage: '🛣️ Road Damage', flooding: '🌊 Flooding',
  public_facility: '🏛️ Public Facility', safety: '🔒 Safety', other: '❓ Other'
};
function categoryLabel(cat) { return CATEGORY_LABELS[cat] || cat || 'Unknown'; }

async function apiFetch(path, opts = {}) {
  const url = API + path;
  // Don't try to parse FormData - just log that it exists
  const bodyDesc = opts.body
    ? (opts.body instanceof FormData ? 'FormData' : JSON.parse(opts.body))
    : '';
  LOG.debug(`FETCH: ${opts.method || 'GET'} ${url}`, bodyDesc);

  try {
    const res = await fetch(url, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      LOG.error(`FETCH ERROR: ${res.status} ${url}`, err);
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    LOG.debug(`FETCH SUCCESS: ${url}`, data);
    return data;
  } catch (error) {
    if (!(error instanceof Error)) {
      LOG.error(`NETWORK ERROR: ${url}`, error);
    }
    throw error;
  }
}

function hideAiPanel() {
  const panel = document.getElementById('aiPanel');
  if (panel) panel.style.display = 'none';
  _lastAiResult = null;
}


/* ============================================================
   Predictive Insights
   ============================================================ */

async function loadPredictiveInsights() {
  LOG.info('Loading predictive insights...');
  try {
    const data = await apiFetch('/api/ai/insights');
    LOG.debug('Insights received:', data);
    _renderInsights(data);
  } catch (e) {
    LOG.error('Failed to load predictive insights', e);
    _showInsightsSparse('Predictive insights could not be loaded. The AI service may be unavailable.');
  }
}

async function refreshInsights() {
  LOG.info('Refreshing predictive insights...');
  const btn = document.getElementById('refreshInsightsBtn');
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-rotate-right fa-spin"></i> Refreshing...'; }
  document.getElementById('insightsGrid').style.display = 'none';
  document.getElementById('insightNarrative').style.display = 'none';
  document.getElementById('insightsSparseState').style.display = 'none';
  document.getElementById('insightsLoading').style.display = 'grid';
  await loadPredictiveInsights();
  if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-rotate-right"></i> Refresh'; }
}

function _renderInsights(data) {
  document.getElementById('insightsLoading').style.display = 'none';

  // Handle sparse data or errors
  if (data.sparse_data || (!data.at_risk_issues?.length && !data.category_trends?.length && !data.hotspot_clusters?.length)) {
    _showInsightsSparse(data.summary_narrative || 'Keep reporting issues to unlock AI-powered insights!');
    return;
  }

  // Show the grid
  document.getElementById('insightsGrid').style.display = 'grid';

  // Render each card
  renderAtRiskIssues(data.at_risk_issues || []);
  renderCategoryTrends(data.category_trends || []);
  renderHotspots(data.hotspot_clusters || []);

  // Narrative callout
  if (data.summary_narrative) {
    renderInsightsSummary(data.summary_narrative);
  }

  // Timestamp footer
  const tsEl = document.getElementById('insightsTimestamp');
  if (tsEl && data.generated_at) {
    const d = new Date(data.generated_at + 'Z');
    tsEl.textContent = `Generated ${timeAgo(data.generated_at)}`;
  }
}

function _showInsightsSparse(msg) {
  document.getElementById('insightsLoading').style.display = 'none';
  document.getElementById('insightsGrid').style.display = 'none';
  document.getElementById('insightNarrative').style.display = 'none';
  const sparseEl = document.getElementById('insightsSparseState');
  const sparseMsg = document.getElementById('insightsSparseMsg');
  if (sparseMsg) sparseMsg.textContent = msg;
  if (sparseEl) sparseEl.style.display = 'block';
}

function renderAtRiskIssues(issues) {
  const list = document.getElementById('atRiskList');
  if (!list) return;
  if (!issues.length) {
    list.innerHTML = `<div class="insight-empty"><i class="fas fa-check-circle" style="color:#34d399"></i>No at-risk issues detected. Community is healthy!</div>`;
    return;
  }
  list.innerHTML = issues.map(item => `
    <li class="at-risk-item" onclick="openIssueDetail(${item.id})">
      <div class="at-risk-item-title">${escHtml(item.title)}</div>
      <div class="at-risk-item-reason">${escHtml(item.reason)}</div>
      <div class="at-risk-item-footer">
        <span class="risk-badge ${item.risk_level}">${item.risk_level}</span>
        <span style="font-size:.72rem;color:rgba(255,255,255,.35)">ID #${item.id} &rsaquo;</span>
      </div>
    </li>
  `).join('');
}

function renderCategoryTrends(trends) {
  const container = document.getElementById('categoryTrendList');
  if (!container) return;
  if (!trends.length) {
    container.innerHTML = `<div class="insight-empty"><i class="fas fa-chart-bar"></i>No category trend data yet.</div>`;
    return;
  }
  const maxAbs = Math.max(...trends.map(t => Math.abs(t.change_pct)), 1);
  const arrowIcon = d => d === 'rising' ? '↑' : d === 'falling' ? '↓' : '→';
  const pctLabel = t => t.direction === 'stable' ? '—' :
    (t.change_pct > 0 ? '+' : '') + t.change_pct + '%';

  container.innerHTML = trends.map(t => `
    <div>
      <div class="trend-row">
        <span class="trend-label">${categoryLabel(t.category)}</span>
        <div class="trend-bar-track">
          <div class="trend-bar-fill ${t.direction}" style="width:${Math.abs(t.change_pct) / maxAbs * 100}%"></div>
        </div>
        <span class="trend-arrow ${t.direction}">${arrowIcon(t.direction)}</span>
        <span class="trend-pct ${t.direction}">${pctLabel(t)}</span>
      </div>
      ${t.insight ? `<div class="trend-insight-text">${escHtml(t.insight)}</div>` : ''}
    </div>
  `).join('');
}

function renderHotspots(clusters) {
  const container = document.getElementById('hotspotList');
  if (!container) return;
  if (!clusters.length) {
    container.innerHTML = `<div class="insight-empty"><i class="fas fa-map"></i>No geographic hotspots detected.</div>`;
    return;
  }
  container.innerHTML = clusters.map(c => `
    <div class="hotspot-item">
      <span class="hotspot-icon ${c.severity}"><i class="fas fa-location-dot"></i></span>
      <div>
        <div class="hotspot-label">${escHtml(c.label)}
          <span class="hotspot-chip ${c.severity}">${c.severity}</span>
        </div>
        <div class="hotspot-meta">
          ${c.issue_count} open issue${c.issue_count !== 1 ? 's' : ''} &nbsp;&bull;&nbsp;
          Mainly <strong style="color:rgba(255,255,255,.7)">${categoryLabel(c.dominant_category)}</strong>
        </div>
      </div>
    </div>
  `).join('');
}

function renderInsightsSummary(text) {
  const el = document.getElementById('insightNarrative');
  if (!el) return;
  el.innerHTML = `
    <span class="insight-narrative-icon"><i class="fas fa-robot"></i></span>
    <span class="insight-narrative-text">${escHtml(text)}</span>
  `;
  el.style.display = 'flex';
}

async function loadResolutionForecast(issueId) {
  try {
    const data = await apiFetch(`/api/ai/insights/resolution-forecast/${issueId}`);
    if (data.error || !data.estimated_days) return;

    // Find the detail actions div and prepend the forecast badge
    const content = document.getElementById('issueDetailContent');
    if (!content) return;
    const actionsDiv = content.querySelector('.detail-actions');
    if (!actionsDiv) return;

    const badge = document.createElement('div');
    badge.style.marginBottom = '.75rem';
    badge.innerHTML = `
      <div class="forecast-badge confidence-${data.confidence}">
        <i class="fas fa-clock-rotate-left"></i>
        <strong>~${data.estimated_days} day${data.estimated_days !== 1 ? 's' : ''} to resolve</strong>
        &nbsp;<span style="opacity:.7;font-weight:400">(${data.confidence} confidence)</span>
      </div>
      ${data.rationale ? `<div style="font-size:.75rem;color:var(--text-muted);margin-top:.3rem;padding-left:.25rem">${escHtml(data.rationale)}</div>` : ''}
    `;
    actionsDiv.parentNode.insertBefore(badge, actionsDiv);
    LOG.debug(`Resolution forecast for issue ${issueId}: ${data.estimated_days} days (${data.confidence})`);
  } catch (e) {
    LOG.warn(`Could not load resolution forecast for issue ${issueId}`, e);
  }
}