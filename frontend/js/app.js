/**
 * InsureFlow AI - Frontend Application
 * Interacts with FastAPI backend for Customers, Policies, Payments, Claims, and ChatGPT AI Agents
 */

const API_BASE = '/api/v1';

// App State
const state = {
  customers: [],
  policies: [],
  payments: [],
  claims: [],
  audits: [],
  aiStatus: null,
  activeTab: 'overview',
  chatHistory: [],
  currentReviewClaim: null,
};

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initModals();
  initForms();
  initChat();
  fetchAllData();
  fetchAIStatus();

  // Topbar actions
  document.getElementById('btn-refresh-all')?.addEventListener('click', () => {
    fetchAllData();
    showToast('Dashboard data refreshed', 'success');
  });

  document.getElementById('btn-top-chat')?.addEventListener('click', () => {
    switchTab('chat');
  });

  document.getElementById('btn-view-all-audits')?.addEventListener('click', () => {
    switchTab('audit');
  });
});

/* ==========================================================================
   Navigation
   ========================================================================== */
function initNavigation() {
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach((link) => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const tab = link.getAttribute('data-tab');
      if (tab) switchTab(tab);
    });
  });

  // Quick Action Buttons on Overview
  document.getElementById('btn-quick-customer')?.addEventListener('click', () => openModal('modal-customer'));
  document.getElementById('btn-quick-policy')?.addEventListener('click', () => openModal('modal-policy'));
  document.getElementById('btn-quick-claim')?.addEventListener('click', () => openModal('modal-claim'));
  document.getElementById('btn-quick-payment')?.addEventListener('click', () => openModal('modal-payment'));

  // Table action buttons
  document.getElementById('btn-add-customer-modal')?.addEventListener('click', () => openModal('modal-customer'));
  document.getElementById('btn-add-policy-modal')?.addEventListener('click', () => openModal('modal-policy'));
  document.getElementById('btn-add-claim-modal')?.addEventListener('click', () => openModal('modal-claim'));
  document.getElementById('btn-add-payment-modal')?.addEventListener('click', () => openModal('modal-payment'));
  document.getElementById('btn-open-settings')?.addEventListener('click', () => openModal('modal-settings'));
}

function switchTab(tabName) {
  state.activeTab = tabName;

  document.querySelectorAll('.nav-link').forEach((link) => {
    link.classList.toggle('active', link.getAttribute('data-tab') === tabName);
  });

  document.querySelectorAll('.tab-pane').forEach((pane) => {
    pane.classList.remove('active');
  });

  const activePane = document.getElementById(`pane-${tabName}`);
  if (activePane) activePane.classList.add('active');

  // Update Page Title
  const titles = {
    overview: 'Enterprise Overview',
    customers: 'Customer Accounts',
    policies: 'Insurance Policies Portfolio',
    payments: 'Collections & Payments',
    claims: 'Claims & AI Multi-Agent Adjudication',
    audit: 'AI Audit Trail (ai_runs & agent_results)',
    chat: 'ChatGPT Enterprise Copilot',
  };
  const titleEl = document.getElementById('page-title');
  if (titleEl) titleEl.textContent = titles[tabName] || 'Enterprise Dashboard';

  // Load tab-specific data if needed
  if (tabName === 'audit') fetchAudits();
}

/* ==========================================================================
   Modals
   ========================================================================== */
function initModals() {
  document.querySelectorAll('[data-close]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const modalId = btn.getAttribute('data-close');
      if (modalId) closeModal(modalId);
    });
  });

  document.querySelectorAll('.modal-backdrop').forEach((backdrop) => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) closeModal(backdrop.id);
    });
  });
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;

  // Pre-fill dropdowns if needed
  if (modalId === 'modal-policy') populateCustomerDropdown();
  if (modalId === 'modal-payment' || modalId === 'modal-claim') populatePolicyDropdown();

  modal.classList.add('active');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
}

/* ==========================================================================
   Data Fetching & Rendering
   ========================================================================== */
async function fetchAllData() {
  await Promise.all([
    fetchCustomers(),
    fetchPolicies(),
    fetchPayments(),
    fetchClaims(),
    fetchAudits(),
  ]);
  updateOverviewStats();
}

async function fetchAIStatus() {
  try {
    const res = await fetch(`${API_BASE}/ai/status`);
    if (!res.ok) return;
    const data = await res.json();
    state.aiStatus = data;

    const tagEl = document.getElementById('ai-engine-tag');
    if (tagEl) {
      tagEl.textContent = data.chatgpt_configured ? `ChatGPT (${data.model})` : 'AI Heuristic Mode';
      tagEl.style.color = data.chatgpt_configured ? 'var(--accent-emerald)' : 'var(--primary-light)';
    }

    const chatStatus = document.getElementById('chat-engine-status');
    if (chatStatus) {
      chatStatus.textContent = data.chatgpt_configured
        ? `Connected to OpenAI ${data.model} | Multi-Agent Adjudication Online`
        : `Running on InsureFlow Expert Heuristic Engine (Enter OpenAI API Key in Settings for live ChatGPT)`;
    }

    const keyStatusEl = document.getElementById('current-key-status');
    if (keyStatusEl) {
      keyStatusEl.textContent = `Current Key: ${data.api_key_masked}`;
    }

    const modelInput = document.getElementById('setting-model');
    if (modelInput && !modelInput.value) {
      modelInput.value = data.model || 'gpt-4o-mini';
    }
  } catch (err) {
    console.warn('Failed to load AI status', err);
  }
}

// 1. Customers
async function fetchCustomers() {
  try {
    const res = await fetch(`${API_BASE}/customers`);
    if (!res.ok) throw new Error('Failed to load customers');
    state.customers = await res.json();
    renderCustomersTable();
  } catch (err) {
    console.error(err);
  }
}

function renderCustomersTable() {
  const tbody = document.getElementById('tbody-customers');
  if (!tbody) return;

  if (state.customers.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-dim); padding: 30px;">No customers found. Click "+ New Customer" to add one.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.customers.map((c) => `
    <tr>
      <td><strong>#${c.customer_id}</strong></td>
      <td><strong>${escapeHtml(c.full_name)}</strong></td>
      <td><span style="color: var(--text-muted); font-family: var(--font-mono); font-size: 12px;">${escapeHtml(c.email)}</span></td>
      <td>${escapeHtml(c.phone)}</td>
      <td>${escapeHtml(c.date_of_birth)}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="filterCustomerPolicies(${c.customer_id})">View Policies</button>
      </td>
    </tr>
  `).join('');
}

// 2. Policies
async function fetchPolicies() {
  try {
    const res = await fetch(`${API_BASE}/policies`);
    if (!res.ok) throw new Error('Failed to load policies');
    state.policies = await res.json();
    renderPoliciesTable();
  } catch (err) {
    console.error(err);
  }
}

function renderPoliciesTable() {
  const tbody = document.getElementById('tbody-policies');
  if (!tbody) return;

  if (state.policies.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-dim); padding: 30px;">No policies issued yet. Click "+ Issue Policy" to add one.</td></tr>`;
    return;
  }

  const productNames = {
    1: 'Auto Insurance',
    2: 'Term Life',
    3: 'Health Plus',
    4: 'Homeowners',
  };

  tbody.innerHTML = state.policies.map((p) => `
    <tr>
      <td><strong style="color: var(--primary-light); font-family: var(--font-mono);">${escapeHtml(p.policy_number)}</strong></td>
      <td>Customer #${p.customer_id}</td>
      <td>${productNames[p.product_id] || `Product #${p.product_id}`}</td>
      <td style="font-size: 12px; color: var(--text-muted);">${escapeHtml(p.start_date)} → ${escapeHtml(p.end_date)}</td>
      <td><strong>$${Number(p.coverage_amount).toLocaleString()}</strong></td>
      <td>$${Number(p.premium_amount).toLocaleString()}</td>
      <td><span class="badge badge-${p.status}">${escapeHtml(p.status)}</span></td>
    </tr>
  `).join('');
}

// 3. Payments
async function fetchPayments() {
  try {
    const res = await fetch(`${API_BASE}/payments`);
    if (!res.ok) throw new Error('Failed to load payments');
    state.payments = await res.json();
    renderPaymentsTable();
  } catch (err) {
    console.error(err);
  }
}

function renderPaymentsTable() {
  const tbody = document.getElementById('tbody-payments');
  if (!tbody) return;

  if (state.payments.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-dim); padding: 30px;">No payment transactions recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.payments.map((py) => `
    <tr>
      <td><strong>#${py.payment_id}</strong></td>
      <td>Policy #${py.policy_id}</td>
      <td><code style="font-size: 12px; color: var(--accent-cyan);">${escapeHtml(py.transaction_reference)}</code></td>
      <td><strong style="color: var(--accent-emerald);">$${Number(py.amount).toLocaleString()}</strong></td>
      <td style="text-transform: capitalize;">${escapeHtml(py.payment_method.replace('_', ' '))}</td>
      <td style="font-size: 12px; color: var(--text-muted);">${py.payment_date ? py.payment_date.replace('T', ' ').substring(0, 19) : '-'}</td>
      <td><span class="badge badge-${py.status}">${escapeHtml(py.status)}</span></td>
    </tr>
  `).join('');
}

// 4. Claims
async function fetchClaims() {
  try {
    const res = await fetch(`${API_BASE}/claims`);
    if (!res.ok) throw new Error('Failed to load claims');
    state.claims = await res.json();
    renderClaimsTable();
  } catch (err) {
    console.error(err);
  }
}

function renderClaimsTable() {
  const tbody = document.getElementById('tbody-claims');
  if (!tbody) return;

  if (state.claims.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-dim); padding: 30px;">No claims submitted yet. Click "+ File New Claim".</td></tr>`;
    return;
  }

  tbody.innerHTML = state.claims.map((clm) => `
    <tr>
      <td><strong style="color: var(--primary-light); font-family: var(--font-mono);">${escapeHtml(clm.claim_number)}</strong></td>
      <td>Policy #${clm.policy_id}</td>
      <td>${escapeHtml(clm.incident_date)}</td>
      <td><strong style="color: #FFFFFF;">$${Number(clm.claim_amount).toLocaleString()}</strong></td>
      <td><span class="badge badge-${clm.status}">${escapeHtml(clm.status)}</span></td>
      <td style="max-width: 280px; font-size: 12px; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
        ${escapeHtml(clm.description)}
      </td>
      <td>
        <button class="btn btn-ai btn-sm" onclick="triggerAIReview(${clm.claim_id}, '${escapeHtml(clm.claim_number)}')">
          ⚡ Run AI Review
        </button>
      </td>
    </tr>
  `).join('');
}

// 5. AI Audit Trail
async function fetchAudits() {
  try {
    const res = await fetch(`${API_BASE}/claims/reviews/audit`);
    if (!res.ok) throw new Error('Failed to load audit records');
    state.audits = await res.json();
    renderAuditTable();
    renderOverviewAudits();
  } catch (err) {
    console.error(err);
  }
}

function renderAuditTable() {
  const tbody = document.getElementById('tbody-audit');
  if (!tbody) return;

  if (state.audits.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color: var(--text-dim); padding: 30px;">No AI adjudication runs executed yet. Run an AI Review on any claim to generate audit records.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.audits.map((a) => {
    const agentCount = a.agents ? a.agents.length : 0;
    const dateFormatted = a.created_at ? a.created_at.replace('T', ' ').substring(0, 19) : '-';
    return `
      <tr>
        <td><strong>#${a.run_id}</strong></td>
        <td><strong style="color: var(--primary-light); font-family: var(--font-mono);">${escapeHtml(a.claim_number || `Claim #${a.claim_id}`)}</strong></td>
        <td>${escapeHtml(a.policy_number || '-')}</td>
        <td><strong>$${Number(a.claim_amount || 0).toLocaleString()}</strong></td>
        <td><span class="badge badge-${a.final_result}">${escapeHtml(a.final_result.replace(/_/g, ' '))}</span></td>
        <td><span class="badge" style="background: rgba(99, 102, 241, 0.15); color: var(--primary-light);">${agentCount} Agents</span></td>
        <td style="font-size: 12px; color: var(--text-dim);">${dateFormatted}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="viewAuditDetails(${a.run_id})">Inspect Logs</button>
        </td>
      </tr>
    `;
  }).join('');
}

function renderOverviewAudits() {
  const tbody = document.getElementById('tbody-overview-audits');
  if (!tbody) return;

  if (state.audits.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-dim); padding: 30px;">No AI runs yet. Click "Run AI Review" on a claim to begin audit logging.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.audits.slice(0, 5).map((a) => {
    const agentCount = a.agents ? a.agents.length : 0;
    const dateFormatted = a.created_at ? a.created_at.replace('T', ' ').substring(0, 19) : '-';
    return `
      <tr>
        <td><strong>#${a.run_id}</strong></td>
        <td><strong>${escapeHtml(a.claim_number || `Claim #${a.claim_id}`)}</strong></td>
        <td>${escapeHtml(a.policy_number || '-')}</td>
        <td>$${Number(a.claim_amount || 0).toLocaleString()}</td>
        <td><span class="badge badge-${a.final_result}">${escapeHtml(a.final_result.replace(/_/g, ' '))}</span></td>
        <td>${agentCount} Active Agents</td>
        <td style="font-size: 12px; color: var(--text-dim);">${dateFormatted}</td>
      </tr>
    `;
  }).join('');
}

function updateOverviewStats() {
  const custEl = document.getElementById('stat-customers');
  if (custEl) custEl.textContent = state.customers.length;

  const polEl = document.getElementById('stat-policies');
  if (polEl) {
    const activeCount = state.policies.filter((p) => p.status === 'active').length;
    polEl.textContent = activeCount;
  }

  const clmEl = document.getElementById('stat-claims');
  if (clmEl) clmEl.textContent = state.claims.length;

  const aiEl = document.getElementById('stat-ai-runs');
  if (aiEl) aiEl.textContent = state.audits.length;
}

/* ==========================================================================
   AI Claim Review Pipeline
   ========================================================================== */
window.triggerAIReview = async function (claimId, claimNumber) {
  state.currentReviewClaim = { id: claimId, number: claimNumber };
  showToast(`Initiating 4-Agent AI review for ${claimNumber}...`, 'info');

  try {
    const res = await fetch(`${API_BASE}/claims/${claimId}/review`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'AI review failed');
    }

    const reviewData = await res.json();
    renderAIReviewModal(reviewData);
    openModal('modal-ai-review');
    showToast(`AI review completed: ${reviewData.final_result}`, 'success');

    // Refresh claims & audits in the background
    fetchClaims();
    fetchAudits();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

function renderAIReviewModal(data) {
  document.getElementById('ai-modal-claim-number').textContent = `Review: ${data.claim.claim_number}`;
  document.getElementById('ai-modal-run-id').textContent = `Run ID #${data.run_id} | ${data.workflow_type}`;

  const badgeEl = document.getElementById('ai-modal-result-badge');
  badgeEl.className = `badge badge-${data.final_result}`;
  badgeEl.textContent = data.final_result.replace(/_/g, ' ');

  const adjudication = data.ai_adjudication || {};
  const riskScore = adjudication.risk_score !== undefined ? adjudication.risk_score : 20;

  const circleEl = document.getElementById('ai-risk-score-circle');
  circleEl.textContent = riskScore;
  circleEl.className = 'risk-circle';
  if (riskScore >= 60) circleEl.classList.add('danger');
  else if (riskScore >= 35) circleEl.classList.add('warning');

  const recEl = document.getElementById('ai-recommendation-text');
  recEl.textContent = adjudication.recommendation || data.final_result;
  recEl.style.color = (adjudication.recommendation === 'approve' || data.final_result === 'checks_completed')
    ? 'var(--accent-emerald)'
    : 'var(--accent-rose)';

  const reasoningEl = document.getElementById('ai-modal-reasoning');
  reasoningEl.textContent = adjudication.summary_reasoning || 'Automated multi-agent checks verified eligibility and policy constraints.';

  // Render 4 Agent Cards
  const cardsContainer = document.getElementById('ai-agent-cards-container');
  cardsContainer.innerHTML = (data.agents || []).map((ag) => {
    const isOk = ag.outcome === 'no_issue_detected';
    const outcomeBadge = isOk
      ? `<span class="badge badge-active">Passed</span>`
      : `<span class="badge badge-human_review_required">Flagged</span>`;

    let findingsHtml = '';
    const f = ag.findings || {};

    if (ag.agent_name === 'chatgpt_adjudication_agent') {
      const redFlags = f.red_flags || [];
      const obs = f.key_observations || [];
      findingsHtml = `
        <li class="agent-finding-item"><strong>Model:</strong> ${escapeHtml(f.model || 'gpt-4o-mini')} (${escapeHtml(f.provider || 'AI')})</li>
        <li class="agent-finding-item"><strong>Confidence:</strong> ${Math.round((f.confidence_score || 0.9) * 100)}%</li>
        ${redFlags.map((rf) => `<li class="agent-finding-item flag">⚠️ ${escapeHtml(rf)}</li>`).join('')}
        ${obs.map((o) => `<li class="agent-finding-item">🔍 ${escapeHtml(o)}</li>`).join('')}
      `;
    } else {
      const checks = f.checks || [];
      if (checks.length === 0) {
        findingsHtml = `<li class="agent-finding-item" style="color: var(--accent-emerald);">✓ All standard parameters verified without discrepancies.</li>`;
      } else {
        findingsHtml = checks.map((c) => `<li class="agent-finding-item flag">⚠️ ${escapeHtml(c)}</li>`).join('');
      }
    }

    return `
      <div class="agent-card">
        <div class="agent-card-header">
          <div class="agent-name">
            <span>🤖</span>
            <span>${escapeHtml(ag.agent_name.replace(/_/g, ' '))}</span>
          </div>
          ${outcomeBadge}
        </div>
        <ul class="agent-finding-list">
          ${findingsHtml}
        </ul>
      </div>
    `;
  }).join('');
}

window.viewAuditDetails = async function (runId) {
  try {
    const res = await fetch(`${API_BASE}/claims/reviews/runs/${runId}`);
    if (!res.ok) throw new Error('Failed to retrieve run details');
    const runData = await res.json();
    renderAIReviewModal({
      run_id: runData.run_id,
      claim: {
        claim_number: runData.claim_number,
        claim_status: runData.claim_status,
      },
      workflow_type: runData.workflow_type,
      final_result: runData.final_result,
      agents: runData.agents,
      ai_adjudication: runData.agents.find((a) => a.agent_name === 'chatgpt_adjudication_agent')?.findings || {},
    });
    openModal('modal-ai-review');
  } catch (err) {
    showToast(err.message, 'error');
  }
};

/* ==========================================================================
   Forms Submission
   ========================================================================== */
function initForms() {
  // Add Customer
  document.getElementById('form-customer')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      full_name: document.getElementById('cust-name').value.trim(),
      email: document.getElementById('cust-email').value.trim(),
      phone: document.getElementById('cust-phone').value.trim(),
      date_of_birth: document.getElementById('cust-dob').value,
    };

    try {
      const res = await fetch(`${API_BASE}/customers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to create customer');
      }

      showToast('Customer created successfully', 'success');
      closeModal('modal-customer');
      e.target.reset();
      fetchCustomers();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Issue Policy
  document.getElementById('form-policy')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      policy_number: document.getElementById('pol-number').value.trim(),
      customer_id: parseInt(document.getElementById('pol-customer').value, 10),
      product_id: parseInt(document.getElementById('pol-product').value, 10),
      start_date: document.getElementById('pol-start').value,
      end_date: document.getElementById('pol-end').value,
      coverage_amount: parseFloat(document.getElementById('pol-coverage').value),
      premium_amount: parseFloat(document.getElementById('pol-premium').value),
      status: document.getElementById('pol-status').value,
    };

    try {
      const res = await fetch(`${API_BASE}/policies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to issue policy');
      }

      showToast('Policy issued successfully', 'success');
      closeModal('modal-policy');
      e.target.reset();
      fetchPolicies();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Record Payment
  document.getElementById('form-payment')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      policy_id: parseInt(document.getElementById('pay-policy').value, 10),
      amount: parseFloat(document.getElementById('pay-amount').value),
      payment_method: document.getElementById('pay-method').value,
      status: document.getElementById('pay-status').value,
      transaction_reference: document.getElementById('pay-ref').value.trim(),
    };

    try {
      const res = await fetch(`${API_BASE}/payments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to record payment');
      }

      showToast('Payment recorded successfully', 'success');
      closeModal('modal-payment');
      e.target.reset();
      fetchPayments();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // File Claim
  document.getElementById('form-claim')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      claim_number: document.getElementById('clm-number').value.trim(),
      policy_id: parseInt(document.getElementById('clm-policy').value, 10),
      incident_date: document.getElementById('clm-date').value,
      claim_amount: parseFloat(document.getElementById('clm-amount').value),
      description: document.getElementById('clm-desc').value.trim(),
      status: 'submitted',
    };

    try {
      const res = await fetch(`${API_BASE}/claims`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to file claim');
      }

      showToast('Claim submitted successfully', 'success');
      closeModal('modal-claim');
      e.target.reset();
      fetchClaims();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // AI & ChatGPT Settings
  document.getElementById('form-settings')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const apiKey = document.getElementById('setting-api-key').value.trim();
    const model = document.getElementById('setting-model').value.trim();
    const baseUrl = document.getElementById('setting-base-url').value.trim();

    const payload = {};
    if (apiKey) payload.openai_api_key = apiKey;
    if (model) payload.openai_model = model;
    if (baseUrl) payload.openai_base_url = baseUrl;

    try {
      const res = await fetch(`${API_BASE}/ai/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Failed to update AI settings');

      showToast('AI Settings updated successfully', 'success');
      closeModal('modal-settings');
      fetchAIStatus();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Discuss claim with Copilot button
  document.getElementById('btn-ask-chatgpt-claim')?.addEventListener('click', () => {
    closeModal('modal-ai-review');
    switchTab('chat');
    if (state.currentReviewClaim) {
      const prompt = `Analyze Claim #${state.currentReviewClaim.number} and summarize key underwriting risk indicators and recommended next steps.`;
      document.getElementById('input-chat').value = prompt;
      document.getElementById('form-chat').dispatchEvent(new Event('submit'));
    }
  });
}

// Helpers for dropdowns
function populateCustomerDropdown() {
  const select = document.getElementById('pol-customer');
  if (!select) return;
  select.innerHTML = '<option value="">Select customer...</option>' +
    state.customers.map((c) => `<option value="${c.customer_id}">${escapeHtml(c.full_name)} (#${c.customer_id})</option>`).join('');
}

function populatePolicyDropdown() {
  const selects = [document.getElementById('pay-policy'), document.getElementById('clm-policy')];
  const optionsHtml = '<option value="">Select policy...</option>' +
    state.policies.map((p) => `<option value="${p.policy_id}">${escapeHtml(p.policy_number)} (Cust #${p.customer_id} - ${p.status})</option>`).join('');

  selects.forEach((sel) => {
    if (sel) sel.innerHTML = optionsHtml;
  });
}

window.filterCustomerPolicies = function (customerId) {
  switchTab('policies');
};

/* ==========================================================================
   ChatGPT Copilot Integration
   ========================================================================== */
function initChat() {
  const form = document.getElementById('form-chat');
  const input = document.getElementById('input-chat');
  const clearBtn = document.getElementById('btn-clear-chat');

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    appendChatMessage('user', message);
    input.value = '';

    // Add typing indicator
    const typingId = appendTypingIndicator();

    try {
      const res = await fetch(`${API_BASE}/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          history: state.chatHistory.slice(-6),
        }),
      });

      removeTypingIndicator(typingId);

      if (!res.ok) throw new Error('AI Assistant response error');
      const data = await res.json();

      appendChatMessage('assistant', data.reply, data.provider);
      state.chatHistory.push({ role: 'user', content: message });
      state.chatHistory.push({ role: 'assistant', content: data.reply });
    } catch (err) {
      removeTypingIndicator(typingId);
      appendChatMessage('assistant', `⚠️ *Unable to reach AI service: ${err.message}*`);
    }
  });

  // Quick Action Pills
  document.querySelectorAll('.quick-pill').forEach((pill) => {
    pill.addEventListener('click', () => {
      const prompt = pill.getAttribute('data-prompt');
      if (prompt && input) {
        input.value = prompt;
        form.dispatchEvent(new Event('submit'));
      }
    });
  });

  clearBtn?.addEventListener('click', () => {
    const chatContainer = document.getElementById('chat-messages');
    chatContainer.innerHTML = `
      <div class="message-bubble assistant">
        <h3>Conversation reset.</h3>
        <p>How else can I assist with your policies, claims, or underwriting workflows today?</p>
      </div>
    `;
    state.chatHistory = [];
    showToast('Chat history cleared', 'info');
  });
}

function appendChatMessage(role, content, provider = null) {
  const chatMessages = document.getElementById('chat-messages');
  if (!chatMessages) return;

  const bubble = document.createElement('div');
  bubble.className = `message-bubble ${role}`;

  let formatted = formatMarkdown(content);
  if (provider && role === 'assistant') {
    formatted += `<div style="font-size: 10px; color: var(--text-dim); margin-top: 8px; border-top: 1px solid var(--border-subtle); padding-top: 4px;">Powered by: ${escapeHtml(provider)}</div>`;
  }

  bubble.innerHTML = formatted;
  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendTypingIndicator() {
  const chatMessages = document.getElementById('chat-messages');
  const id = `typing-${Date.now()}`;
  const el = document.createElement('div');
  el.id = id;
  el.className = 'message-bubble assistant';
  el.style.opacity = '0.7';
  el.innerHTML = `<em>InsureFlow AI is reasoning...</em>`;
  chatMessages.appendChild(el);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

/* ==========================================================================
   Utilities
   ========================================================================== */
function formatMarkdown(text) {
  if (!text) return '';
  let html = escapeHtml(text);

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h4>$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3>$1</h3>');

  // Bold & Italic
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Blockquotes
  html = html.replace(/^\&gt; (.*$)/gim, '<blockquote>$1</blockquote>');

  // Unordered list items
  html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

  // Inline code
  html = html.replace(/`(.*?)`/g, '<code style="background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono); font-size: 12px;">$1</code>');

  // Line breaks
  html = html.replace(/\n\n/g, '<br><br>');
  html = html.replace(/\n/g, '<br>');

  return html;
}

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
    <span>${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = '0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
