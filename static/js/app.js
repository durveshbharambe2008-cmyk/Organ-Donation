// Main Application Logic
let currentUser = null;
let organsCache = [];

document.addEventListener('DOMContentLoaded', async () => {
  try {
    const authData = await api.get('/api/auth/me');
    currentUser = authData.username;
    const usernameElem = document.getElementById('current-username');
    if (usernameElem) usernameElem.textContent = currentUser;
  } catch (err) {
    window.location.href = '/login.html';
    return;
  }

  // Pre-load organs for dropdowns
  loadOrgansCache();

  // Setup sidebar navigation
  setupNavigation();

  // Setup signout button
  const signoutBtn = document.getElementById('btn-signout');
  if (signoutBtn) {
    signoutBtn.addEventListener('click', async () => {
      try {
        await api.post('/api/auth/logout');
      } catch (err) {
        // proceed anyway
      }
      window.location.href = '/login.html';
    });
  }

  // Setup transplant form submit
  setupTransplantForm();

  // Initial routing
  handleRoute();
});

async function loadOrgansCache() {
  try {
    organsCache = await api.get('/api/organs');
  } catch (err) {
    console.error('Failed to load organs list', err);
  }
}

function setupNavigation() {
  window.addEventListener('hashchange', handleRoute);
  document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      const page = item.getAttribute('data-page');
      window.location.hash = page;
    });
  });
}

function handleRoute() {
  const hash = window.location.hash.replace('#', '') || 'dashboard';
  const validPages = ['dashboard', 'donors', 'recipients', 'donations', 'requests', 'matches'];
  const activePage = validPages.includes(hash) ? hash : 'dashboard';

  document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
    item.classList.toggle('active', item.getAttribute('data-page') === activePage);
  });

  const pageActions = document.getElementById('page-actions');
  if (pageActions) pageActions.innerHTML = '';

  switch (activePage) {
    case 'dashboard':
      showDashboard();
      break;
    case 'donors':
      showDonors();
      break;
    case 'recipients':
      showRecipients();
      break;
    case 'donations':
      showDonations();
      break;
    case 'requests':
      showRequests();
      break;
    case 'matches':
      showMatchesAndTransplants();
      break;
  }
}

function setPageHeader(title, subtitle, actionBtnHtml = '') {
  document.getElementById('page-title').textContent = title;
  document.getElementById('page-subtitle').textContent = subtitle;
  const actionsContainer = document.getElementById('page-actions');
  if (actionsContainer) actionsContainer.innerHTML = actionBtnHtml;
}

// ============================================================================
// 1. Dashboard View
// ============================================================================
async function showDashboard() {
  setPageHeader('Hospital Dashboard', 'Summary metrics, available organs and recent transplants');
  const container = document.getElementById('content-body');
  container.innerHTML = '<p class="text-muted">Loading dashboard metrics...</p>';

  try {
    const data = await api.get('/api/dashboard');
    const { totals, availableByOrgan, recentTransplants } = data;

    container.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Registered Donors</div>
          <div class="stat-value">${totals.donors}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Waiting Recipients</div>
          <div class="stat-value">${totals.recipients}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Available Donations</div>
          <div class="stat-value" style="color: var(--primary);">${totals.availableDonations}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Waiting Requests</div>
          <div class="stat-value" style="color: #c2410c;">${totals.waitingRequests}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Completed Transplants</div>
          <div class="stat-value" style="color: #15803d;">${totals.transplants}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title">Available Organs by Type</h2>
        </div>
        <div class="card-body" id="available-organs-table-container"></div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title">Recent Transplants</h2>
        </div>
        <div class="card-body" id="recent-transplants-table-container"></div>
      </div>
    `;

    // Render Available Organs Table
    ui.renderTable(
      'available-organs-table-container',
      [
        { key: 'organ_name', label: 'Organ Name' },
        { key: 'available', label: 'Available Count', render: (val) => `<strong>${val}</strong>` }
      ],
      availableByOrgan
    );

    // Render Recent Transplants Table
    ui.renderTable(
      'recent-transplants-table-container',
      [
        { key: 'transplant_id', label: 'ID' },
        { key: 'organ_name', label: 'Organ' },
        { key: 'donor', label: 'Donor' },
        { key: 'patient', label: 'Recipient' },
        { key: 'transplant_date', label: 'Date' },
        { key: 'outcome', label: 'Outcome', render: (val) => ui.badge(val) }
      ],
      recentTransplants
    );
  } catch (err) {
    container.innerHTML = `<div class="dialog-error">Failed to load dashboard: ${ui.escapeHtml(err.message)}</div>`;
  }
}

// ============================================================================
// 2. Donors View
// ============================================================================
let donorsList = [];

async function showDonors() {
  setPageHeader(
    'Registered Donors',
    'Manage hospital organ donors (age 18+ required)',
    '<button class="btn btn-primary" onclick="openDonorForm()">+ Register Donor</button>'
  );

  const container = document.getElementById('content-body');
  container.innerHTML = `
    <div class="card">
      <div class="table-filter-bar">
        <input type="text" class="search-input" id="search-donors" placeholder="Search by name or phone..." oninput="filterDonorsTable()">
        <select class="filter-select" id="filter-donors-blood" onchange="filterDonorsTable()">
          <option value="">All Blood Groups</option>
          <option value="A+">A+</option><option value="A-">A-</option>
          <option value="B+">B+</option><option value="B-">B-</option>
          <option value="AB+">AB+</option><option value="AB-">AB-</option>
          <option value="O+">O+</option><option value="O-">O-</option>
        </select>
        <span class="filter-count" id="donors-count-badge"></span>
      </div>
      <div class="card-body" id="donors-table-container">Loading donors...</div>
    </div>
  `;

  try {
    donorsList = await api.get('/api/donors');
    filterDonorsTable();
  } catch (err) {
    document.getElementById('donors-table-container').innerHTML =
      `<div class="dialog-error">Failed to load donors: ${ui.escapeHtml(err.message)}</div>`;
  }
}

function filterDonorsTable() {
  const query = (document.getElementById('search-donors')?.value || '').toLowerCase().trim();
  const blood = document.getElementById('filter-donors-blood')?.value || '';

  const filtered = donorsList.filter(d => {
    const matchesQuery = !query || d.name.toLowerCase().includes(query) || d.phone.includes(query);
    const matchesBlood = !blood || d.blood_group === blood;
    return matchesQuery && matchesBlood;
  });

  const countBadge = document.getElementById('donors-count-badge');
  if (countBadge) countBadge.textContent = `Showing ${filtered.length} of ${donorsList.length}`;

  ui.renderTable(
    'donors-table-container',
    [
      { key: 'donor_id', label: 'ID' },
      { key: 'name', label: 'Name' },
      { key: 'age', label: 'Age' },
      { key: 'gender', label: 'Gender' },
      { key: 'blood_group', label: 'Blood Group', render: (val) => ui.badge(val) },
      { key: 'phone', label: 'Phone' },
      { key: 'registered_on', label: 'Registered On' }
    ],
    filtered,
    (row) => `
      <button class="btn-link" onclick="openDonorForm(${row.donor_id})">Edit</button>
      <button class="btn-link btn-link-danger" onclick="deleteDonor(${row.donor_id})">Delete</button>
    `
  );
}

async function openDonorForm(donorId = null) {
  const isEdit = donorId !== null;
  let donor = null;

  if (isEdit) {
    try {
      const donors = await api.get('/api/donors');
      donor = donors.find(d => d.donor_id === donorId);
      if (!donor) throw new Error('Donor not found.');
    } catch (err) {
      ui.showToast(err.message, 'error');
      return;
    }
  }

  const fieldsHtml = `
    <div class="form-group">
      <label for="donor-name">Full Name <span class="required">*</span></label>
      <input type="text" id="donor-name" name="name" required minlength="2" value="${isEdit ? ui.escapeHtml(donor.name) : ''}">
    </div>
    <div class="form-group">
      <label for="donor-age">Age (18 to 100) <span class="required">*</span></label>
      <input type="number" id="donor-age" name="age" min="18" max="100" required value="${isEdit ? donor.age : ''}">
    </div>
    <div class="form-group">
      <label for="donor-gender">Gender <span class="required">*</span></label>
      <select id="donor-gender" name="gender" required>
        <option value="M" ${isEdit && donor.gender === 'M' ? 'selected' : ''}>Male (M)</option>
        <option value="F" ${isEdit && donor.gender === 'F' ? 'selected' : ''}>Female (F)</option>
        <option value="Other" ${isEdit && donor.gender === 'Other' ? 'selected' : ''}>Other</option>
      </select>
    </div>
    <div class="form-group">
      <label for="donor-blood-group">Blood Group ${isEdit ? '(Fixed)' : '<span class="required">*</span>'}</label>
      ${isEdit 
        ? `<div class="readonly-box">${ui.escapeHtml(donor.blood_group)} (Cannot be modified after registration)</div>`
        : `<select id="donor-blood-group" name="blood_group" required>
             <option value="">Select blood group...</option>
             <option value="A+">A+</option><option value="A-">A-</option>
             <option value="B+">B+</option><option value="B-">B-</option>
             <option value="AB+">AB+</option><option value="AB-">AB-</option>
             <option value="O+">O+</option><option value="O-">O-</option>
           </select>`
      }
    </div>
    <div class="form-group">
      <label for="donor-phone">Phone Number (10 digits) <span class="required">*</span></label>
      <input type="tel" id="donor-phone" name="phone" required pattern="[0-9]{10}" maxlength="10" placeholder="10-digit mobile number" value="${isEdit ? ui.escapeHtml(donor.phone) : ''}">
    </div>
  `;

  openGenericDialog({
    title: isEdit ? 'Edit Donor' : 'Register New Donor',
    fieldsHtml,
    submitLabel: isEdit ? 'Save Changes' : 'Register Donor',
    onSubmit: async (form) => {
      const name = form.name.value.trim();
      const age = parseInt(form.age.value, 10);
      const gender = form.gender.value;
      const phone = form.phone.value.replace(/[\s-]/g, '').trim();

      if (name.length < 2) {
        throw new Error('Full name must be at least 2 characters.');
      }
      if (isNaN(age) || age < 18 || age > 100) {
        throw new Error('Donor age must be between 18 and 100.');
      }
      if (!/^[0-9]{10}$/.test(phone)) {
        throw new Error('Phone number must be exactly 10 digits (e.g. 9820011111).');
      }

      const payload = { name, age, gender, phone };

      if (!isEdit) {
        payload.blood_group = form.blood_group.value;
        await api.post('/api/donors', payload);
        ui.showToast('Donor registered successfully.', 'success');
      } else {
        await api.put(`/api/donors/${donorId}`, payload);
        ui.showToast('Donor updated successfully.', 'success');
      }
      showDonors();
    }
  });
}

async function deleteDonor(donorId) {
  const confirmed = await ui.confirmDelete('Are you sure you want to delete this donor? Allowed only if no donation records exist.');
  if (!confirmed) return;

  try {
    const res = await api.delete(`/api/donors/${donorId}`);
    ui.showToast(res.message || 'Donor deleted successfully.', 'success');
    showDonors();
  } catch (err) {
    ui.showToast(err.message, 'error');
  }
}

// ============================================================================
// 3. Recipients View
// ============================================================================
let recipientsList = [];

async function showRecipients() {
  setPageHeader(
    'Waiting Patients (Recipients)',
    'Manage patients registered for organ reception',
    '<button class="btn btn-primary" onclick="openRecipientForm()">+ Register Recipient</button>'
  );

  const container = document.getElementById('content-body');
  container.innerHTML = `
    <div class="card">
      <div class="table-filter-bar">
        <input type="text" class="search-input" id="search-recipients" placeholder="Search by name or phone..." oninput="filterRecipientsTable()">
        <select class="filter-select" id="filter-recipients-blood" onchange="filterRecipientsTable()">
          <option value="">All Blood Groups</option>
          <option value="A+">A+</option><option value="A-">A-</option>
          <option value="B+">B+</option><option value="B-">B-</option>
          <option value="AB+">AB+</option><option value="AB-">AB-</option>
          <option value="O+">O+</option><option value="O-">O-</option>
        </select>
        <span class="filter-count" id="recipients-count-badge"></span>
      </div>
      <div class="card-body" id="recipients-table-container">Loading recipients...</div>
    </div>
  `;

  try {
    recipientsList = await api.get('/api/recipients');
    filterRecipientsTable();
  } catch (err) {
    document.getElementById('recipients-table-container').innerHTML =
      `<div class="dialog-error">Failed to load recipients: ${ui.escapeHtml(err.message)}</div>`;
  }
}

function filterRecipientsTable() {
  const query = (document.getElementById('search-recipients')?.value || '').toLowerCase().trim();
  const blood = document.getElementById('filter-recipients-blood')?.value || '';

  const filtered = recipientsList.filter(r => {
    const matchesQuery = !query || r.name.toLowerCase().includes(query) || r.phone.includes(query);
    const matchesBlood = !blood || r.blood_group === blood;
    return matchesQuery && matchesBlood;
  });

  const countBadge = document.getElementById('recipients-count-badge');
  if (countBadge) countBadge.textContent = `Showing ${filtered.length} of ${recipientsList.length}`;

  ui.renderTable(
    'recipients-table-container',
    [
      { key: 'recipient_id', label: 'ID' },
      { key: 'name', label: 'Name' },
      { key: 'age', label: 'Age' },
      { key: 'gender', label: 'Gender' },
      { key: 'blood_group', label: 'Blood Group', render: (val) => ui.badge(val) },
      { key: 'phone', label: 'Phone' },
      { key: 'registered_on', label: 'Registered On' }
    ],
    filtered,
    (row) => `
      <button class="btn-link" onclick="openRecipientForm(${row.recipient_id})">Edit</button>
      <button class="btn-link btn-link-danger" onclick="deleteRecipient(${row.recipient_id})">Delete</button>
    `
  );
}

async function openRecipientForm(recipientId = null) {
  const isEdit = recipientId !== null;
  let recipient = null;

  if (isEdit) {
    try {
      const recipients = await api.get('/api/recipients');
      recipient = recipients.find(r => r.recipient_id === recipientId);
      if (!recipient) throw new Error('Recipient not found.');
    } catch (err) {
      ui.showToast(err.message, 'error');
      return;
    }
  }

  const fieldsHtml = `
    <div class="form-group">
      <label for="recipient-name">Full Name <span class="required">*</span></label>
      <input type="text" id="recipient-name" name="name" required minlength="2" value="${isEdit ? ui.escapeHtml(recipient.name) : ''}">
    </div>
    <div class="form-group">
      <label for="recipient-age">Age (0 - 100) <span class="required">*</span></label>
      <input type="number" id="recipient-age" name="age" min="0" max="100" required value="${isEdit ? recipient.age : ''}">
    </div>
    <div class="form-group">
      <label for="recipient-gender">Gender <span class="required">*</span></label>
      <select id="recipient-gender" name="gender" required>
        <option value="M" ${isEdit && recipient.gender === 'M' ? 'selected' : ''}>Male (M)</option>
        <option value="F" ${isEdit && recipient.gender === 'F' ? 'selected' : ''}>Female (F)</option>
        <option value="Other" ${isEdit && recipient.gender === 'Other' ? 'selected' : ''}>Other</option>
      </select>
    </div>
    <div class="form-group">
      <label for="recipient-blood-group">Blood Group ${isEdit ? '(Fixed)' : '<span class="required">*</span>'}</label>
      ${isEdit 
        ? `<div class="readonly-box">${ui.escapeHtml(recipient.blood_group)} (Cannot be modified after registration)</div>`
        : `<select id="recipient-blood-group" name="blood_group" required>
             <option value="">Select blood group...</option>
             <option value="A+">A+</option><option value="A-">A-</option>
             <option value="B+">B+</option><option value="B-">B-</option>
             <option value="AB+">AB+</option><option value="AB-">AB-</option>
             <option value="O+">O+</option><option value="O-">O-</option>
           </select>`
      }
    </div>
    <div class="form-group">
      <label for="recipient-phone">Phone Number (10 digits) <span class="required">*</span></label>
      <input type="tel" id="recipient-phone" name="phone" required pattern="[0-9]{10}" maxlength="10" placeholder="10-digit mobile number" value="${isEdit ? ui.escapeHtml(recipient.phone) : ''}">
    </div>
  `;

  openGenericDialog({
    title: isEdit ? 'Edit Recipient' : 'Register New Recipient',
    fieldsHtml,
    submitLabel: isEdit ? 'Save Changes' : 'Register Recipient',
    onSubmit: async (form) => {
      const name = form.name.value.trim();
      const age = parseInt(form.age.value, 10);
      const gender = form.gender.value;
      const phone = form.phone.value.replace(/[\s-]/g, '').trim();

      if (name.length < 2) {
        throw new Error('Full name must be at least 2 characters.');
      }
      if (isNaN(age) || age < 0 || age > 100) {
        throw new Error('Recipient age must be between 0 and 100.');
      }
      if (!/^[0-9]{10}$/.test(phone)) {
        throw new Error('Phone number must be exactly 10 digits (e.g. 9930011111).');
      }

      const payload = { name, age, gender, phone };

      if (!isEdit) {
        payload.blood_group = form.blood_group.value;
        await api.post('/api/recipients', payload);
        ui.showToast('Recipient registered successfully.', 'success');
      } else {
        await api.put(`/api/recipients/${recipientId}`, payload);
        ui.showToast('Recipient updated successfully.', 'success');
      }
      showRecipients();
    }
  });
}

async function deleteRecipient(recipientId) {
  const confirmed = await ui.confirmDelete('Are you sure you want to delete this recipient? Allowed only if no organ requests exist.');
  if (!confirmed) return;

  try {
    const res = await api.delete(`/api/recipients/${recipientId}`);
    ui.showToast(res.message || 'Recipient deleted successfully.', 'success');
    showRecipients();
  } catch (err) {
    ui.showToast(err.message, 'error');
  }
}

// ============================================================================
// 4. Donations View
// ============================================================================
let donationsList = [];

async function showDonations() {
  setPageHeader(
    'Organ Donations',
    'Track donated organs and their availability status',
    '<button class="btn btn-primary" onclick="openDonationForm()">+ Record Donation</button>'
  );

  const container = document.getElementById('content-body');
  container.innerHTML = `
    <div class="card">
      <div class="table-filter-bar">
        <input type="text" class="search-input" id="search-donations" placeholder="Search by donor name..." oninput="filterDonationsTable()">
        <select class="filter-select" id="filter-donations-organ" onchange="filterDonationsTable()">
          <option value="">All Organs</option>
          <option value="Kidney">Kidney</option>
          <option value="Liver">Liver</option>
          <option value="Heart">Heart</option>
          <option value="Lung">Lung</option>
          <option value="Pancreas">Pancreas</option>
          <option value="Cornea">Cornea</option>
        </select>
        <select class="filter-select" id="filter-donations-status" onchange="filterDonationsTable()">
          <option value="">All Statuses</option>
          <option value="AVAILABLE">AVAILABLE</option>
          <option value="ALLOCATED">ALLOCATED</option>
          <option value="EXPIRED">EXPIRED</option>
        </select>
        <span class="filter-count" id="donations-count-badge"></span>
      </div>
      <div class="card-body" id="donations-table-container">Loading donations...</div>
    </div>
  `;

  try {
    donationsList = await api.get('/api/donations');
    filterDonationsTable();
  } catch (err) {
    document.getElementById('donations-table-container').innerHTML =
      `<div class="dialog-error">Failed to load donations: ${ui.escapeHtml(err.message)}</div>`;
  }
}

function filterDonationsTable() {
  const query = (document.getElementById('search-donations')?.value || '').toLowerCase().trim();
  const organ = document.getElementById('filter-donations-organ')?.value || '';
  const status = document.getElementById('filter-donations-status')?.value || '';

  const filtered = donationsList.filter(d => {
    const matchesQuery = !query || d.donor.toLowerCase().includes(query);
    const matchesOrgan = !organ || d.organ_name === organ;
    const matchesStatus = !status || d.status === status;
    return matchesQuery && matchesOrgan && matchesStatus;
  });

  const countBadge = document.getElementById('donations-count-badge');
  if (countBadge) countBadge.textContent = `Showing ${filtered.length} of ${donationsList.length}`;

  ui.renderTable(
    'donations-table-container',
    [
      { key: 'donation_id', label: 'ID' },
      { key: 'donor', label: 'Donor', render: (val, row) => `${ui.escapeHtml(val)} (${ui.escapeHtml(row.blood_group)})` },
      { key: 'organ_name', label: 'Organ' },
      { key: 'donation_type', label: 'Type', render: (val) => ui.badge(val) },
      { key: 'status', label: 'Status', render: (val) => ui.badge(val) },
      { key: 'donation_date', label: 'Donation Date' }
    ],
    filtered,
    (row) => {
      if (row.status === 'ALLOCATED') {
        return '<span class="text-muted" style="font-size: 13px;">In use</span>';
      }
      return `<button class="btn-link" onclick="openDonationForm(${row.donation_id})">Edit</button>`;
    }
  );
}

async function openDonationForm(donationId = null) {
  const isEdit = donationId !== null;
  let donation = null;
  let donors = [];

  try {
    if (!organsCache.length) await loadOrgansCache();
    if (!isEdit) {
      donors = await api.get('/api/donors');
    } else {
      const donations = await api.get('/api/donations');
      donation = donations.find(d => d.donation_id === donationId);
      if (!donation) throw new Error('Donation not found.');
    }
  } catch (err) {
    ui.showToast(err.message, 'error');
    return;
  }

  const todayStr = new Date().toISOString().split('T')[0];

  let fieldsHtml = '';
  if (!isEdit) {
    const donorOptions = donors.map(d => `<option value="${d.donor_id}">${ui.escapeHtml(d.name)} (${d.blood_group}) - ID #${d.donor_id}</option>`).join('');
    const organOptions = organsCache.map(o => `<option value="${o.organ_id}">${ui.escapeHtml(o.organ_name)}</option>`).join('');

    fieldsHtml = `
      <div class="form-group">
        <label for="donation-donor">Donor <span class="required">*</span></label>
        <select id="donation-donor" name="donor_id" required>
          <option value="">Select registered donor...</option>
          ${donorOptions}
        </select>
      </div>
      <div class="form-group">
        <label for="donation-organ">Organ Donated <span class="required">*</span></label>
        <select id="donation-organ" name="organ_id" required>
          <option value="">Select organ type...</option>
          ${organOptions}
        </select>
      </div>
      <div class="form-group">
        <label for="donation-type">Donation Type <span class="required">*</span></label>
        <select id="donation-type" name="donation_type" required>
          <option value="LIVING">LIVING</option>
          <option value="DECEASED">DECEASED</option>
        </select>
      </div>
      <div class="form-group">
        <label for="donation-date">Donation Date <span class="required">*</span></label>
        <input type="date" id="donation-date" name="donation_date" required value="${todayStr}" max="${todayStr}">
      </div>
    `;
  } else {
    fieldsHtml = `
      <div class="form-group">
        <label>Donor</label>
        <div class="readonly-box">${ui.escapeHtml(donation.donor)} (${ui.escapeHtml(donation.blood_group)})</div>
      </div>
      <div class="form-group">
        <label>Organ</label>
        <div class="readonly-box">${ui.escapeHtml(donation.organ_name)}</div>
      </div>
      <div class="form-group">
        <label for="donation-type">Donation Type <span class="required">*</span></label>
        <select id="donation-type" name="donation_type" required>
          <option value="LIVING" ${donation.donation_type === 'LIVING' ? 'selected' : ''}>LIVING</option>
          <option value="DECEASED" ${donation.donation_type === 'DECEASED' ? 'selected' : ''}>DECEASED</option>
        </select>
      </div>
      <div class="form-group">
        <label for="donation-date">Donation Date <span class="required">*</span></label>
        <input type="date" id="donation-date" name="donation_date" required value="${donation.donation_date}" max="${todayStr}">
      </div>
      <div class="form-group">
        <label for="donation-status">Status <span class="required">*</span></label>
        <select id="donation-status" name="status" required>
          <option value="AVAILABLE" ${donation.status === 'AVAILABLE' ? 'selected' : ''}>AVAILABLE</option>
          <option value="EXPIRED" ${donation.status === 'EXPIRED' ? 'selected' : ''}>EXPIRED (Cannot be used)</option>
        </select>
      </div>
    `;
  }

  openGenericDialog({
    title: isEdit ? 'Edit Donation' : 'Record New Donation',
    fieldsHtml,
    submitLabel: isEdit ? 'Save Changes' : 'Record Donation',
    onSubmit: async (form) => {
      if (form.donation_date.value > todayStr) {
        throw new Error('Donation date cannot be in the future.');
      }
      if (!isEdit) {
        const payload = {
          donor_id: parseInt(form.donor_id.value, 10),
          organ_id: parseInt(form.organ_id.value, 10),
          donation_type: form.donation_type.value,
          donation_date: form.donation_date.value
        };
        await api.post('/api/donations', payload);
        ui.showToast('Donation recorded successfully.', 'success');
      } else {
        const payload = {
          donation_type: form.donation_type.value,
          donation_date: form.donation_date.value,
          status: form.status.value
        };
        await api.put(`/api/donations/${donationId}`, payload);
        ui.showToast('Donation updated successfully.', 'success');
      }
      showDonations();
    }
  });
}

// ============================================================================
// 5. Requests View
// ============================================================================
let requestsList = [];

async function showRequests() {
  setPageHeader(
    'Organ Requests (Waiting List)',
    'Prioritized patient waiting list ordered by medical urgency',
    '<button class="btn btn-primary" onclick="openRequestForm()">+ New Request</button>'
  );

  const container = document.getElementById('content-body');
  container.innerHTML = `
    <div class="card">
      <div class="table-filter-bar">
        <input type="text" class="search-input" id="search-requests" placeholder="Search by patient name..." oninput="filterRequestsTable()">
        <select class="filter-select" id="filter-requests-organ" onchange="filterRequestsTable()">
          <option value="">All Organs</option>
          <option value="Kidney">Kidney</option>
          <option value="Liver">Liver</option>
          <option value="Heart">Heart</option>
          <option value="Lung">Lung</option>
          <option value="Pancreas">Pancreas</option>
          <option value="Cornea">Cornea</option>
        </select>
        <select class="filter-select" id="filter-requests-urgency" onchange="filterRequestsTable()">
          <option value="">All Urgencies</option>
          <option value="CRITICAL">CRITICAL</option>
          <option value="HIGH">HIGH</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="LOW">LOW</option>
        </select>
        <select class="filter-select" id="filter-requests-status" onchange="filterRequestsTable()">
          <option value="">All Statuses</option>
          <option value="WAITING">WAITING</option>
          <option value="MATCHED">MATCHED</option>
          <option value="CLOSED">CLOSED</option>
        </select>
        <span class="filter-count" id="requests-count-badge"></span>
      </div>
      <div class="card-body" id="requests-table-container">Loading requests...</div>
    </div>
  `;

  try {
    requestsList = await api.get('/api/requests');
    filterRequestsTable();
  } catch (err) {
    document.getElementById('requests-table-container').innerHTML =
      `<div class="dialog-error">Failed to load requests: ${ui.escapeHtml(err.message)}</div>`;
  }
}

function filterRequestsTable() {
  const query = (document.getElementById('search-requests')?.value || '').toLowerCase().trim();
  const organ = document.getElementById('filter-requests-organ')?.value || '';
  const urgency = document.getElementById('filter-requests-urgency')?.value || '';
  const status = document.getElementById('filter-requests-status')?.value || '';

  const filtered = requestsList.filter(r => {
    const matchesQuery = !query || r.patient.toLowerCase().includes(query);
    const matchesOrgan = !organ || r.organ_name === organ;
    const matchesUrgency = !urgency || r.urgency === urgency;
    const matchesStatus = !status || r.status === status;
    return matchesQuery && matchesOrgan && matchesUrgency && matchesStatus;
  });

  const countBadge = document.getElementById('requests-count-badge');
  if (countBadge) countBadge.textContent = `Showing ${filtered.length} of ${requestsList.length}`;

  ui.renderTable(
    'requests-table-container',
    [
      { key: 'request_id', label: 'ID' },
      { key: 'patient', label: 'Patient', render: (val, row) => `${ui.escapeHtml(val)} (${ui.escapeHtml(row.blood_group)})` },
      { key: 'organ_name', label: 'Organ Needed' },
      { key: 'urgency', label: 'Urgency', render: (val) => ui.badge(val) },
      { key: 'status', label: 'Status', render: (val) => ui.badge(val) },
      { key: 'request_date', label: 'Request Date' },
      { 
        key: 'days_waiting', 
        label: 'Days Waiting', 
        render: (val, row) => row.status === 'WAITING' ? `<strong>${val} days</strong>` : '—' 
      }
    ],
    filtered,
    (row) => {
      if (row.status === 'MATCHED') {
        return '<span class="text-muted" style="font-size: 13px;">Matched</span>';
      }
      return `<button class="btn-link" onclick="openRequestForm(${row.request_id})">Edit</button>`;
    }
  );
}

async function openRequestForm(requestId = null) {
  const isEdit = requestId !== null;
  let reqItem = null;
  let recipients = [];

  try {
    if (!organsCache.length) await loadOrgansCache();
    if (!isEdit) {
      recipients = await api.get('/api/recipients');
    } else {
      const requests = await api.get('/api/requests');
      reqItem = requests.find(r => r.request_id === requestId);
      if (!reqItem) throw new Error('Request not found.');
    }
  } catch (err) {
    ui.showToast(err.message, 'error');
    return;
  }

  const todayStr = new Date().toISOString().split('T')[0];

  let fieldsHtml = '';
  if (!isEdit) {
    const recipientOptions = recipients.map(r => `<option value="${r.recipient_id}">${ui.escapeHtml(r.name)} (${r.blood_group}) - ID #${r.recipient_id}</option>`).join('');
    const organOptions = organsCache.map(o => `<option value="${o.organ_id}">${ui.escapeHtml(o.organ_name)}</option>`).join('');

    fieldsHtml = `
      <div class="form-group">
        <label for="request-recipient">Recipient (Patient) <span class="required">*</span></label>
        <select id="request-recipient" name="recipient_id" required>
          <option value="">Select registered patient...</option>
          ${recipientOptions}
        </select>
      </div>
      <div class="form-group">
        <label for="request-organ">Organ Needed <span class="required">*</span></label>
        <select id="request-organ" name="organ_id" required>
          <option value="">Select organ...</option>
          ${organOptions}
        </select>
      </div>
      <div class="form-group">
        <label for="request-urgency">Urgency Level <span class="required">*</span></label>
        <select id="request-urgency" name="urgency" required>
          <option value="CRITICAL">CRITICAL</option>
          <option value="HIGH">HIGH</option>
          <option value="MEDIUM" selected>MEDIUM</option>
          <option value="LOW">LOW</option>
        </select>
      </div>
      <div class="form-group">
        <label for="request-date">Request Date <span class="required">*</span></label>
        <input type="date" id="request-date" name="request_date" required value="${todayStr}" max="${todayStr}">
      </div>
    `;
  } else {
    fieldsHtml = `
      <div class="form-group">
        <label>Recipient (Patient)</label>
        <div class="readonly-box">${ui.escapeHtml(reqItem.patient)} (${ui.escapeHtml(reqItem.blood_group)})</div>
      </div>
      <div class="form-group">
        <label>Organ Needed</label>
        <div class="readonly-box">${ui.escapeHtml(reqItem.organ_name)}</div>
      </div>
      <div class="form-group">
        <label for="request-urgency">Urgency Level <span class="required">*</span></label>
        <select id="request-urgency" name="urgency" required>
          <option value="CRITICAL" ${reqItem.urgency === 'CRITICAL' ? 'selected' : ''}>CRITICAL</option>
          <option value="HIGH" ${reqItem.urgency === 'HIGH' ? 'selected' : ''}>HIGH</option>
          <option value="MEDIUM" ${reqItem.urgency === 'MEDIUM' ? 'selected' : ''}>MEDIUM</option>
          <option value="LOW" ${reqItem.urgency === 'LOW' ? 'selected' : ''}>LOW</option>
        </select>
      </div>
      <div class="form-group">
        <label for="request-date">Request Date <span class="required">*</span></label>
        <input type="date" id="request-date" name="request_date" required value="${reqItem.request_date}" max="${todayStr}">
      </div>
      <div class="form-group">
        <label for="request-status">Status <span class="required">*</span></label>
        <select id="request-status" name="status" required>
          <option value="WAITING" ${reqItem.status === 'WAITING' ? 'selected' : ''}>WAITING</option>
          <option value="CLOSED" ${reqItem.status === 'CLOSED' ? 'selected' : ''}>CLOSED (Patient withdrawn/closed)</option>
        </select>
      </div>
    `;
  }

  openGenericDialog({
    title: isEdit ? 'Edit Organ Request' : 'Record New Request',
    fieldsHtml,
    submitLabel: isEdit ? 'Save Changes' : 'Record Request',
    onSubmit: async (form) => {
      if (form.request_date.value > todayStr) {
        throw new Error('Request date cannot be in the future.');
      }
      if (!isEdit) {
        const payload = {
          recipient_id: parseInt(form.recipient_id.value, 10),
          organ_id: parseInt(form.organ_id.value, 10),
          urgency: form.urgency.value,
          request_date: form.request_date.value
        };
        await api.post('/api/requests', payload);
        ui.showToast('Request recorded successfully.', 'success');
      } else {
        const payload = {
          urgency: form.urgency.value,
          request_date: form.request_date.value,
          status: form.status.value
        };
        await api.put(`/api/requests/${requestId}`, payload);
        ui.showToast('Request updated successfully.', 'success');
      }
      showRequests();
    }
  });
}

// ============================================================================
// 6. Matching & Transplants View
// ============================================================================
let matchesList = [];
let transplantsList = [];

async function showMatchesAndTransplants() {
  setPageHeader(
    'Matching & Transplants',
    'Compatible donor-recipient pairs and transplant surgical outcomes'
  );

  const container = document.getElementById('content-body');
  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <h2 class="card-title">Possible Matches (Exact Blood Group &amp; Organ Type)</h2>
      </div>
      <div class="table-filter-bar">
        <input type="text" class="search-input" id="search-matches" placeholder="Search by donor or recipient..." oninput="filterMatchesTable()">
        <select class="filter-select" id="filter-matches-organ" onchange="filterMatchesTable()">
          <option value="">All Organs</option>
          <option value="Kidney">Kidney</option>
          <option value="Liver">Liver</option>
          <option value="Heart">Heart</option>
          <option value="Lung">Lung</option>
          <option value="Pancreas">Pancreas</option>
          <option value="Cornea">Cornea</option>
        </select>
        <span class="filter-count" id="matches-count-badge"></span>
      </div>
      <div class="card-body" id="matches-table-container">Loading compatible matches...</div>
    </div>

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">Completed Transplants</h2>
      </div>
      <div class="table-filter-bar">
        <input type="text" class="search-input" id="search-transplants" placeholder="Search by donor, patient or surgeon..." oninput="filterTransplantsTable()">
        <select class="filter-select" id="filter-transplants-organ" onchange="filterTransplantsTable()">
          <option value="">All Organs</option>
          <option value="Kidney">Kidney</option>
          <option value="Liver">Liver</option>
          <option value="Heart">Heart</option>
          <option value="Lung">Lung</option>
          <option value="Pancreas">Pancreas</option>
          <option value="Cornea">Cornea</option>
        </select>
        <select class="filter-select" id="filter-transplants-outcome" onchange="filterTransplantsTable()">
          <option value="">All Outcomes</option>
          <option value="SUCCESSFUL">SUCCESSFUL</option>
          <option value="COMPLICATIONS">COMPLICATIONS</option>
          <option value="FAILED">FAILED</option>
        </select>
        <span class="filter-count" id="transplants-count-badge"></span>
      </div>
      <div class="card-body" id="transplants-table-container">Loading completed transplants...</div>
    </div>
  `;

  loadMatchesTable();
  loadTransplantsTable();
}

async function loadMatchesTable() {
  try {
    matchesList = await api.get('/api/matches');
    filterMatchesTable();
  } catch (err) {
    document.getElementById('matches-table-container').innerHTML =
      `<div class="dialog-error">Failed to load matches: ${ui.escapeHtml(err.message)}</div>`;
  }
}

function filterMatchesTable() {
  const query = (document.getElementById('search-matches')?.value || '').toLowerCase().trim();
  const organ = document.getElementById('filter-matches-organ')?.value || '';

  const filtered = matchesList.filter(m => {
    const matchesQuery = !query || m.donor.toLowerCase().includes(query) || m.patient.toLowerCase().includes(query);
    const matchesOrgan = !organ || m.organ_name === organ;
    return matchesQuery && matchesOrgan;
  });

  const countBadge = document.getElementById('matches-count-badge');
  if (countBadge) countBadge.textContent = `Showing ${filtered.length} of ${matchesList.length}`;

  ui.renderTable(
    'matches-table-container',
    [
      { key: 'donor', label: 'Donor', render: (val, row) => `${ui.escapeHtml(val)} (${ui.escapeHtml(row.blood_group)})` },
      { key: 'patient', label: 'Recipient (Patient)', render: (val, row) => `${ui.escapeHtml(val)} (${ui.escapeHtml(row.blood_group)})` },
      { key: 'organ_name', label: 'Organ Type' },
      { key: 'urgency', label: 'Urgency', render: (val) => ui.badge(val) },
      { key: 'days_waiting', label: 'Waiting Time', render: (val) => `<strong>${val} days</strong>` }
    ],
    filtered,
    (row) => `
      <button class="btn btn-sm btn-primary" onclick="openRecordTransplantModal(${JSON.stringify(row).replace(/"/g, '&quot;')})">
        Record Transplant
      </button>
    `
  );
}

async function loadTransplantsTable() {
  try {
    transplantsList = await api.get('/api/transplants');
    filterTransplantsTable();
  } catch (err) {
    document.getElementById('transplants-table-container').innerHTML =
      `<div class="dialog-error">Failed to load transplants: ${ui.escapeHtml(err.message)}</div>`;
  }
}

function filterTransplantsTable() {
  const query = (document.getElementById('search-transplants')?.value || '').toLowerCase().trim();
  const organ = document.getElementById('filter-transplants-organ')?.value || '';
  const outcome = document.getElementById('filter-transplants-outcome')?.value || '';

  const filtered = transplantsList.filter(t => {
    const matchesQuery = !query || t.donor.toLowerCase().includes(query) || t.patient.toLowerCase().includes(query) || t.surgeon_name.toLowerCase().includes(query);
    const matchesOrgan = !organ || t.organ_name === organ;
    const matchesOutcome = !outcome || t.outcome === outcome;
    return matchesQuery && matchesOrgan && matchesOutcome;
  });

  const countBadge = document.getElementById('transplants-count-badge');
  if (countBadge) countBadge.textContent = `Showing ${filtered.length} of ${transplantsList.length}`;

  ui.renderTable(
    'transplants-table-container',
    [
      { key: 'transplant_id', label: 'ID' },
      { key: 'organ_name', label: 'Organ' },
      { key: 'donor', label: 'Donor' },
      { key: 'patient', label: 'Recipient' },
      { key: 'surgeon_name', label: 'Surgeon' },
      { key: 'transplant_date', label: 'Date' },
      { key: 'outcome', label: 'Outcome', render: (val) => ui.badge(val) }
    ],
    filtered,
    (row) => `
      <button class="btn-link" onclick="openEditTransplantModal(${JSON.stringify(row).replace(/"/g, '&quot;')})">Edit</button>
    `
  );
}

function openRecordTransplantModal(match) {
  const dialog = document.getElementById('transplant-dialog');
  const errorBox = document.getElementById('transplant-dialog-error');
  errorBox.style.display = 'none';

  document.getElementById('transplant-donation-id').value = match.donation_id;
  document.getElementById('transplant-request-id').value = match.request_id;
  document.getElementById('transplant-donor-info').textContent = `${match.donor} (${match.blood_group})`;
  document.getElementById('transplant-patient-info').textContent = `${match.patient} (${match.blood_group})`;
  document.getElementById('transplant-organ-info').textContent = `${match.organ_name} • ${match.urgency} urgency`;

  const todayStr = new Date().toISOString().split('T')[0];
  document.getElementById('transplant-surgeon').value = '';
  const dateInput = document.getElementById('transplant-date');
  dateInput.value = todayStr;
  dateInput.max = todayStr;
  document.getElementById('transplant-outcome').value = 'SUCCESSFUL';

  ui.openDialog(dialog);
}

function setupTransplantForm() {
  const form = document.getElementById('transplant-form');
  const errorBox = document.getElementById('transplant-dialog-error');
  const submitBtn = document.getElementById('transplant-submit-btn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorBox.style.display = 'none';

    const surgeon_name = form.surgeon_name.value.trim();
    if (surgeon_name.length < 2) {
      errorBox.textContent = 'Surgeon name must be at least 2 characters.';
      errorBox.style.display = 'block';
      return;
    }

    const todayStr = new Date().toISOString().split('T')[0];
    if (form.transplant_date.value > todayStr) {
      errorBox.textContent = 'Transplant date cannot be in the future.';
      errorBox.style.display = 'block';
      return;
    }

    const payload = {
      donation_id: parseInt(form.donation_id.value, 10),
      request_id: parseInt(form.request_id.value, 10),
      surgeon_name: surgeon_name,
      transplant_date: form.transplant_date.value,
      outcome: form.outcome.value
    };

    submitBtn.disabled = true;
    submitBtn.textContent = 'Saving...';

    try {
      await api.post('/api/transplants', payload);
      ui.closeDialog('transplant-dialog');
      ui.showToast('Transplant recorded successfully! Donation allocated & request matched.', 'success');
      showMatchesAndTransplants();
    } catch (err) {
      errorBox.textContent = err.message;
      errorBox.style.display = 'block';
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Confirm Transplant';
    }
  });
}

function openEditTransplantModal(transplant) {
  const todayStr = new Date().toISOString().split('T')[0];
  const fieldsHtml = `
    <div class="form-group">
      <label>Organ &amp; Participants</label>
      <div class="readonly-box">${ui.escapeHtml(transplant.organ_name)}: ${ui.escapeHtml(transplant.donor)} &rarr; ${ui.escapeHtml(transplant.patient)}</div>
    </div>
    <div class="form-group">
      <label for="edit-surgeon">Surgeon Name <span class="required">*</span></label>
      <input type="text" id="edit-surgeon" name="surgeon_name" required value="${ui.escapeHtml(transplant.surgeon_name)}">
    </div>
    <div class="form-group">
      <label for="edit-transplant-date">Transplant Date <span class="required">*</span></label>
      <input type="date" id="edit-transplant-date" name="transplant_date" required value="${transplant.transplant_date}" max="${todayStr}">
    </div>
    <div class="form-group">
      <label for="edit-outcome">Outcome <span class="required">*</span></label>
      <select id="edit-outcome" name="outcome" required>
        <option value="SUCCESSFUL" ${transplant.outcome === 'SUCCESSFUL' ? 'selected' : ''}>SUCCESSFUL</option>
        <option value="COMPLICATIONS" ${transplant.outcome === 'COMPLICATIONS' ? 'selected' : ''}>COMPLICATIONS</option>
        <option value="FAILED" ${transplant.outcome === 'FAILED' ? 'selected' : ''}>FAILED</option>
      </select>
    </div>
  `;

  openGenericDialog({
    title: `Edit Transplant Record #${transplant.transplant_id}`,
    fieldsHtml,
    submitLabel: 'Save Changes',
    onSubmit: async (form) => {
      if (form.transplant_date.value > todayStr) {
        throw new Error('Transplant date cannot be in the future.');
      }
      const payload = {
        surgeon_name: form.surgeon_name.value.trim(),
        transplant_date: form.transplant_date.value,
        outcome: form.outcome.value
      };
      await api.put(`/api/transplants/${transplant.transplant_id}`, payload);
      ui.showToast('Transplant record updated successfully.', 'success');
      loadTransplantsTable();
    }
  });
}

// ============================================================================
// Generic Modal Handler
// ============================================================================
let currentGenericSubmitHandler = null;

function openGenericDialog({ title, fieldsHtml, submitLabel = 'Save', onSubmit }) {
  const dialog = document.getElementById('form-dialog');
  const titleElem = document.getElementById('form-dialog-title');
  const errorBox = document.getElementById('form-dialog-error');
  const fieldsContainer = document.getElementById('form-fields-container');
  const submitBtn = document.getElementById('form-submit-btn');
  const form = document.getElementById('generic-form');

  titleElem.textContent = title;
  errorBox.style.display = 'none';
  errorBox.textContent = '';
  fieldsContainer.innerHTML = fieldsHtml;
  submitBtn.textContent = submitLabel;
  submitBtn.disabled = false;

  if (currentGenericSubmitHandler) {
    form.removeEventListener('submit', currentGenericSubmitHandler);
  }

  currentGenericSubmitHandler = async (e) => {
    e.preventDefault();
    errorBox.style.display = 'none';
    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Saving...';

    try {
      await onSubmit(form);
      ui.closeDialog('form-dialog');
    } catch (err) {
      errorBox.textContent = err.message;
      errorBox.style.display = 'block';
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  };

  form.addEventListener('submit', currentGenericSubmitHandler);
  ui.openDialog(dialog);
}
