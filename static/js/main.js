// Main JavaScript - Tab switching & common utilities

document.addEventListener('DOMContentLoaded', function () {
    // Auto-refresh filters when switching to dashboard tab
    const dashboardTab = document.getElementById('dashboard-tab');
    if (dashboardTab) {
        dashboardTab.addEventListener('shown.bs.tab', function () {
            refreshFilters();
        });
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (el) {
        return new bootstrap.Tooltip(el);
    });
});

/**
 * Refresh filter dropdowns from API
 */
function refreshFilters() {
    fetch('/api/filters')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const filters = data.data;
                updateDropdown('reportFactory', filters.factories);
                updateDropdown('reportYear', filters.years);
                updateDropdown('reportSeason', filters.seasons);

                // Also update upload form dropdowns
                updateDropdown('poFactory', filters.factories);
                updateDropdown('prodFactory', filters.factories);
            }
        })
        .catch(error => console.error('Failed to refresh filters:', error));
}

/**
 * Update a dropdown with new options
 */
function updateDropdown(elementId, options) {
    const select = document.getElementById(elementId);
    if (!select) return;

    const currentValue = select.value;
    select.innerHTML = '<option value="">-- Select --</option>';

    options.forEach(option => {
        const opt = document.createElement('option');
        opt.value = option;
        opt.textContent = option;
        select.appendChild(opt);
    });

    // Restore previous selection if still valid
    if (currentValue && options.includes(currentValue)) {
        select.value = currentValue;
    }
}

/**
 * Format number with commas
 */
function formatNumber(num) {
    return Number(num).toLocaleString();
}

/**
 * Get status badge HTML
 */
function getStatusBadge(status) {
    const statusConfig = {
        'Complete': { class: 'bg-success', icon: '✅' },
        'Partial': { class: 'bg-warning text-dark', icon: '⚠️' },
        'Missing': { class: 'bg-danger', icon: '❌' }
    };

    const config = statusConfig[status] || { class: 'bg-secondary', icon: '❓' };
    return `<span class="badge ${config.class}">${config.icon} ${status}</span>';
}