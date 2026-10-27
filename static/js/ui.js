// UI rendering and interaction utilities
const ui = {
  escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  },

  badge(value) {
    if (!value) return '';
    const val = String(value).toUpperCase();
    let badgeClass = 'badge-gray';

    switch (val) {
      case 'AVAILABLE':
      case 'WAITING':
        badgeClass = 'badge-blue';
        break;
      case 'ALLOCATED':
      case 'MATCHED':
      case 'SUCCESSFUL':
        badgeClass = 'badge-green';
        break;
      case 'EXPIRED':
      case 'CLOSED':
        badgeClass = 'badge-gray';
        break;
      case 'FAILED':
      case 'CRITICAL':
        badgeClass = 'badge-red';
        break;
      case 'HIGH':
      case 'COMPLICATIONS':
        badgeClass = 'badge-orange';
        break;
      case 'MEDIUM':
        badgeClass = 'badge-yellow';
        break;
      case 'LOW':
        badgeClass = 'badge-gray';
        break;
      case 'LIVING':
        badgeClass = 'badge-teal';
        break;
      case 'DECEASED':
        badgeClass = 'badge-slate';
        break;
    }

    return `<span class="badge ${badgeClass}">${this.escapeHtml(value)}</span>`;
  },

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('toast-fadeout');
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 300);
    }, 4000);
  },

  renderTable(container, columns, rows, actionsRenderer = null) {
    if (typeof container === 'string') {
      container = document.getElementById(container);
    }
    if (!container) return;

    const colCount = columns.length + (actionsRenderer ? 1 : 0);

    let html = '<div class="table-responsive"><table class="data-table"><thead><tr>';
    columns.forEach(col => {
      html += `<th>${this.escapeHtml(col.label)}</th>`;
    });
    if (actionsRenderer) {
      html += '<th class="th-actions">Actions</th>';
    }
    html += '</tr></thead><tbody>';

    if (!rows || rows.length === 0) {
      html += `<tr><td colspan="${colCount}" class="text-muted text-center" style="padding: 24px;">No records yet.</td></tr>`;
    } else {
      rows.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
          let cellContent = '';
          if (typeof col.render === 'function') {
            cellContent = col.render(row[col.key], row);
          } else {
            cellContent = this.escapeHtml(row[col.key] !== undefined ? row[col.key] : '—');
          }
          html += `<td>${cellContent}</td>`;
        });

        if (actionsRenderer) {
          const actionHtml = actionsRenderer(row);
          html += `<td class="td-actions">${actionHtml || '—'}</td>`;
        }
        html += '</tr>';
      });
    }

    html += '</tbody></table></div>';
    container.innerHTML = html;
  },

  confirmDelete(message = 'Delete this record? This cannot be undone.') {
    return new Promise((resolve) => {
      const dialog = document.getElementById('confirm-dialog');
      const msgElem = document.getElementById('confirm-dialog-msg');
      const confirmBtn = document.getElementById('confirm-dialog-btn');
      const cancelBtn = document.getElementById('confirm-cancel-btn');

      if (!dialog) {
        resolve(window.confirm(message));
        return;
      }

      msgElem.textContent = message;

      const handleConfirm = () => {
        cleanup();
        dialog.close();
        resolve(true);
      };

      const handleCancel = () => {
        cleanup();
        dialog.close();
        resolve(false);
      };

      const handleClose = () => {
        cleanup();
        resolve(false);
      };

      function cleanup() {
        confirmBtn.removeEventListener('click', handleConfirm);
        cancelBtn.removeEventListener('click', handleCancel);
        dialog.removeEventListener('close', handleClose);
      }

      confirmBtn.addEventListener('click', handleConfirm);
      cancelBtn.addEventListener('click', handleCancel);
      dialog.addEventListener('close', handleClose);

      dialog.showModal();
    });
  },

  openDialog(dialogId) {
    const dialog = typeof dialogId === 'string' ? document.getElementById(dialogId) : dialogId;
    if (dialog && typeof dialog.showModal === 'function') {
      dialog.showModal();
    }
  },

  closeDialog(dialogId) {
    const dialog = typeof dialogId === 'string' ? document.getElementById(dialogId) : dialogId;
    if (dialog && typeof dialog.close === 'function') {
      dialog.close();
    }
  }
};
