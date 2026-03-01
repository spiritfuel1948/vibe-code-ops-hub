// ═══════════════════════════════════════════════════════════════
//  TAB NAVIGATION
// ═══════════════════════════════════════════════════════════════

function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.sidebar-link').forEach(el => el.classList.remove('active'));
  const target = document.getElementById(tabId);
  if (target) target.classList.add('active');
  const link = document.querySelector(`.sidebar-link[data-tab="${tabId}"]`);
  if (link) link.classList.add('active');
  if (tabId === 'analytics') loadAnalytics();
}

document.querySelectorAll('.sidebar-link').forEach(link => {
  link.addEventListener('click', () => switchTab(link.dataset.tab));
});

// ═══════════════════════════════════════════════════════════════
//  TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ═══════════════════════════════════════════════════════════════
//  FORM HELPERS
// ═══════════════════════════════════════════════════════════════

function formToJson(form) {
  const data = {};
  const fd = new FormData(form);
  for (const [key, val] of fd.entries()) {
    if (form.querySelector(`[name="${key}"]`)?.type === 'checkbox') {
      data[key] = true;
    } else if (form.querySelector(`[name="${key}"]`)?.type === 'number') {
      data[key] = parseFloat(val) || 0;
    } else {
      data[key] = val;
    }
  }
  form.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    if (!fd.has(cb.name)) data[cb.name] = false;
  });
  return data;
}

async function apiPost(url, data) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return resp.json();
}

async function apiPut(url, data) {
  const resp = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return resp.json();
}

// ═══════════════════════════════════════════════════════════════
//  FORM SUBMISSIONS
// ═══════════════════════════════════════════════════════════════

document.getElementById('daily-log-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = formToJson(e.target);
  const res = await apiPost('/api/daily-log', data);
  if (res.success) { showToast('Daily log saved'); setTimeout(() => location.reload(), 500); }
  else showToast('Error saving log', 'error');
});

document.getElementById('video-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = formToJson(e.target);
  const res = await apiPost('/api/video', data);
  if (res.success) { showToast('Video added'); setTimeout(() => location.reload(), 500); }
  else showToast('Error adding video', 'error');
});

document.getElementById('hook-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = formToJson(e.target);
  const res = await apiPost('/api/hook', data);
  if (res.success) { showToast('Hook saved'); setTimeout(() => location.reload(), 500); }
  else showToast('Error saving hook', 'error');
});

document.getElementById('pipeline-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = formToJson(e.target);
  if (!data.assigned_to) data.assigned_to = null;
  const res = await apiPost('/api/pipeline', data);
  if (res.success) { showToast('Pipeline item added'); setTimeout(() => location.reload(), 500); }
  else showToast('Error adding item', 'error');
});

document.getElementById('vault-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = formToJson(e.target);
  const res = await apiPost('/api/vault', data);
  if (res.success) { showToast('Vault entry saved'); setTimeout(() => location.reload(), 500); }
  else showToast('Error saving entry', 'error');
});

document.getElementById('monetization-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = formToJson(e.target);
  const res = await apiPost('/api/monetization', data);
  if (res.success) { showToast('Entry logged'); setTimeout(() => location.reload(), 500); }
  else showToast('Error logging entry', 'error');
});

document.getElementById('pillar-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = formToJson(e.target);
  const res = await apiPost('/api/pillar', data);
  if (res.success) { showToast('Pillar added'); setTimeout(() => location.reload(), 500); }
  else showToast('Error adding pillar', 'error');
});

// ── Save Reflection ──
document.getElementById('save-reflection')?.addEventListener('click', async () => {
  const worked = document.getElementById('reflection-worked')?.value ?? '';
  const improve = document.getElementById('reflection-improve')?.value ?? '';
  const res = await apiPost('/api/reflection', { worked, improve });
  if (res.success) showToast('Reflection saved');
  else showToast('Error saving reflection', 'error');
});

// ── Celebration when all quotas met (once per session) ──
(function initCelebration() {
  if (document.body?.dataset.allQuotasMet !== 'true') return;
  if (sessionStorage.getItem('vibe-code-celebrated') === '1') return;
  sessionStorage.setItem('vibe-code-celebrated', '1');
  document.body.classList.add('celebration-active');
  setTimeout(() => document.body.classList.remove('celebration-active'), 2500);
})();

// ── Settings form ──
document.getElementById('settings-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = formToJson(e.target);
  const res = await apiPost('/api/settings', data);
  if (res.success) {
    showToast('Settings saved');
    setTimeout(loadSchedulerStatus, 300);
  }
  else showToast('Error saving settings', 'error');
});

// Load existing settings into form
(async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    const data = await res.json();
    const form = document.getElementById('settings-form');
    if (!form) return;
    Object.entries(data).forEach(([key, val]) => {
      const input = form.querySelector(`[name="${key}"]`);
      if (!input) return;
      if (input.type === 'checkbox') {
        input.checked = String(val).toLowerCase() === 'true';
      } else {
        input.value = val;
      }
    });
    const cronUrlEl = document.getElementById('cron-url');
    if (cronUrlEl) {
      const token = data.cron_token || '';
      cronUrlEl.value = `${window.location.origin}/api/cron/run-automation?token=${token}`;
    }
    loadSchedulerStatus();
  } catch (e) { /* settings not loaded yet */ }
})();

async function loadSchedulerStatus() {
  try {
    const res = await fetch('/api/scheduler-status');
    const data = await res.json();
    const el = document.getElementById('scheduler-status');
    if (!el || !data.success) return;
    el.textContent = `Scheduler: ${data.scheduler_running ? 'running' : 'stopped'} | Enabled: ${data.automation_enabled ? 'yes' : 'no'} | Time: ${String(data.automation_hour).padStart(2, '0')}:${String(data.automation_minute).padStart(2, '0')} | Job loaded: ${data.job_present ? 'yes' : 'no'}`;
  } catch (e) {
    // no-op
  }
}

// ── Partner settings ──
document.querySelectorAll('.partner-settings-form').forEach(form => {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const pid = form.dataset.id;
    const data = formToJson(form);
    const res = await apiPut(`/api/partner/${pid}`, data);
    if (res.success) showToast('Partner updated');
    else showToast('Error updating partner', 'error');
  });
});

// ── Email form ──
document.getElementById('email-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const recipients = [];
  e.target.querySelectorAll('input[name="recipients"]:checked').forEach(cb => recipients.push(cb.value));
  const subject = document.getElementById('email-subject').value;
  const body = document.getElementById('email-body').value;
  const templateType = document.getElementById('email-template-select').value || 'custom';
  if (!recipients.length) { showToast('Select at least one recipient', 'error'); return; }
  const res = await apiPost('/api/send-email', { recipients, subject, body, template_type: templateType });
  if (res.success) { showToast('Email sent!'); setTimeout(() => location.reload(), 500); }
  else showToast(res.message || 'Email failed', 'error');
});

document.getElementById('ab-test-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = formToJson(e.target);
  if (Number(data.video_a_id) === Number(data.video_b_id)) {
    showToast('Video A and B must be different', 'error');
    return;
  }
  const res = await apiPost('/api/ab-tests', data);
  if (res.success) { showToast('A/B test created'); setTimeout(() => location.reload(), 400); }
  else showToast('Failed to create A/B test', 'error');
});

async function pickWinner(testId, winnerVideoId) {
  const res = await apiPut(`/api/ab-tests/${testId}/winner`, { winner_video_id: winnerVideoId });
  if (res.success) { showToast('Winner saved'); setTimeout(() => location.reload(), 300); }
  else showToast(res.error || 'Failed to save winner', 'error');
}

document.getElementById('btn-weekly-digest')?.addEventListener('click', async () => {
  const res = await fetch('/api/weekly-digest');
  const data = await res.json();
  if (!data.success) {
    showToast('Failed to generate digest', 'error');
    return;
  }
  const target = document.getElementById('weekly-digest-result');
  target.innerHTML = `Videos: ${data.total_videos} | Views: ${data.total_views.toLocaleString()} | Avg 3s Retention: ${data.avg_retention_3s}%`;
  showToast('Weekly digest generated');
});

document.getElementById('btn-save-password')?.addEventListener('click', async () => {
  const pw = document.getElementById('app-password')?.value || '';
  const res = await apiPost('/api/settings', { app_password: pw });
  if (res.success) showToast('App password saved');
  else showToast('Failed to save password', 'error');
});

document.getElementById('btn-run-automation')?.addEventListener('click', async () => {
  const res = await apiPost('/api/run-automation', {});
  if (!res.success) {
    showToast('Automation failed', 'error');
    return;
  }
  const target = document.getElementById('automation-result');
  const sentCount = (res.reminders || []).length;
  target.textContent = sentCount ? `Sent ${sentCount} reminder(s).` : 'No reminders needed right now.';
  showToast('Automation run complete');
});

document.getElementById('btn-logout')?.addEventListener('click', async () => {
  const res = await apiPost('/api/logout', {});
  if (res.success) window.location.href = '/login';
});

// ═══════════════════════════════════════════════════════════════
//  EMAIL TEMPLATE LOADER
// ═══════════════════════════════════════════════════════════════

function loadEmailTemplate(key) {
  if (!key || !EMAIL_TEMPLATES[key]) {
    document.getElementById('email-subject').value = '';
    document.getElementById('email-body').value = '';
    return;
  }
  document.getElementById('email-subject').value = EMAIL_TEMPLATES[key].subject;
  document.getElementById('email-body').value = EMAIL_TEMPLATES[key].body;
}

// ═══════════════════════════════════════════════════════════════
//  DELETE & PIPELINE ACTIONS
// ═══════════════════════════════════════════════════════════════

async function deleteItem(model, id) {
  if (!confirm('Delete this item?')) return;
  const res = await fetch(`/api/delete/${model}/${id}`, { method: 'DELETE' });
  const data = await res.json();
  if (data.success) { showToast('Deleted'); setTimeout(() => location.reload(), 300); }
  else showToast('Error deleting', 'error');
}

async function movePipeline(id, newStatus) {
  const res = await apiPut(`/api/pipeline/${id}`, { status: newStatus });
  if (res.success) { showToast('Moved'); setTimeout(() => location.reload(), 300); }
}

// ═══════════════════════════════════════════════════════════════
//  ANALYTICS CHARTS
// ═══════════════════════════════════════════════════════════════

const chartDefaults = {
  color: '#e0e0f0',
  borderColor: 'rgba(31,31,58,.5)',
};
Chart.defaults.color = '#8888a0';
Chart.defaults.borderColor = 'rgba(31,31,58,.5)';

let chartsLoaded = false;

async function loadAnalytics() {
  if (chartsLoaded) return;
  chartsLoaded = true;
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();
    renderDailyChart(data.daily);
    renderPlatformChart(data.platforms);
    renderFormatChart(data.formats);
    renderTopVideos(data.top_videos);
  } catch (e) {
    console.error('Analytics load failed:', e);
  }
}

function renderDailyChart(daily) {
  const ctx = document.getElementById('chart-daily');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: daily.map(d => d.date.slice(5)),
      datasets: [{
        label: 'Videos',
        data: daily.map(d => d.count),
        backgroundColor: '#7c6cf0',
        borderRadius: 4,
      }],
    },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });
}

function renderPlatformChart(platforms) {
  const ctx = document.getElementById('chart-platforms');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: platforms.map(p => p.platform),
      datasets: [{
        data: platforms.map(p => p.count),
        backgroundColor: ['#00c897', '#f0834d', '#ef4444', '#3b82f6', '#eab308'],
      }],
    },
    options: { responsive: true },
  });
}

function renderFormatChart(formats) {
  const ctx = document.getElementById('chart-formats');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: formats.map(f => f.format),
      datasets: [
        { label: 'Avg Retention %', data: formats.map(f => f.avg_retention), backgroundColor: '#7c6cf0', borderRadius: 4 },
        { label: 'Count', data: formats.map(f => f.count), backgroundColor: '#00c897', borderRadius: 4 },
      ],
    },
    options: { responsive: true, scales: { y: { beginAtZero: true } } },
  });
}

function renderTopVideos(videos) {
  const container = document.getElementById('top-videos-list');
  if (!container) return;
  if (!videos.length) { container.innerHTML = '<p class="muted">No videos yet.</p>'; return; }
  container.innerHTML = videos.map(v =>
    `<div class="top-item"><span>${v.topic || 'Untitled'} <span class="muted">(${v.platform})</span></span><span class="top-item-views">${(v.views || 0).toLocaleString()} views</span></div>`
  ).join('');
}
