// Dashboard JavaScript - Report viewing, table rendering, chart

let chartInstance = null;

document.addEventListener('DOMContentLoaded', function () {
    const viewBtn = document.getElementById('viewReportBtn');
    if (viewBtn) {
        viewBtn.addEventListener('click', function () {
            loadReport();
        });
    }

    // Allow pressing Enter on filter selects to trigger report
    const filterSelects = ['reportFactory', 'reportYear', 'reportSeason'];
    filterSelects.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    loadReport();
                }
            });
        }
    });
});

/**
 * Load comparison report based on selected filters
 */
function loadReport() {
    const factory = document.getElementById('reportFactory').value;
    const year = document.getElementById('reportYear').value;
    const season = document.getElementById('reportSeason').value;

    // Validate filters
    if (!factory || !year || !season) {
        showReportError('Please select Factory, Year, and Season before viewing the report.');
        return;
    }

    // Show loading, hide other sections
    document.getElementById('reportLoading').classList.remove('d-none');
    document.getElementById('reportContent').classList.add('d-none');
    document.getElementById('reportEmpty').classList.add('d-none');
    document.getElementById('reportError').classList.add('d-none');

    // Fetch report data
    const url = `/api/report/compare?factory_name=${encodeURIComponent(factory)}&year=${encodeURIComponent(year)}&season=${encodeURIComponent(season)}`;

    fetch(url)
        .then(response => response.json())
        .then(data => {
            document.getElementById('reportLoading').classList.add('d-none');

            if (data.status === 'success') {
                renderReport(data.data);
            } else {
                showReportError(data.message);
            }
        })
        .catch(error => {
            document.getElementById('reportLoading').classList.add('d-none');
            showReportError('Failed to load report. Please try again.');
            console.error('Report error:', error);
        });
}

/**
 * Render the full report with summary, table, and chart
 */
function renderReport(data) {
    const summary = data.summary;
    const comparison = data.comparison;

    // Update summary cards
    document.getElementById('totalProducts').textContent = summary.total_products;
    document.getElementById('completeCount').textContent = summary.complete;
    document.getElementById('partialCount').textContent = summary.partial;
    document.getElementById('missingCount').textContent = summary.missing;

    // Update overall progress
    document.getElementById('overallPct').textContent = summary.overall_completion_pct + '%';
    document.getElementById('totalRequested').textContent = formatNumber(summary.total_requested);
    document.getElementById('totalProduced').textContent = formatNumber(summary.total_produced);

    const overallBar = document.getElementById('overallProgressBar');
    const pct = summary.overall_completion_pct;
    overallBar.style.width = pct + '%';
    overallBar.textContent = pct + '%';

    // Color the overall bar based on completion
    if (pct >= 100) {
        overallBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-success';
    } else if (pct >= 50) {
        overallBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-warning';
    } else {
        overallBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-danger';
    }

    // Render comparison table
    renderTable(comparison);

    // Render chart
    renderChart(comparison);

    // Show report content
    document.getElementById('reportContent').classList.remove('d-none');
}

/**
 * Render the comparison table
 */
function renderTable(comparison) {
    const tbody = document.getElementById('comparisonTableBody');
    tbody.innerHTML = '';

    if (comparison.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No products found in comparison</td></tr>';
        return;
    }

    comparison.forEach(item => {
        const row = document.createElement('tr');
        const statusClass = item.status === 'Complete' ? 'table-success'
            : item.status === 'Partial' ? 'table-warning'
                : 'table-danger';

        row.className = statusClass;

        // Progress bar color
        const barColor = item.status === 'Complete' ? 'bg-success'
            : item.status === 'Partial' ? 'bg-warning'
                : 'bg-danger';

        row.innerHTML = `
            <td><strong>${item.product_name}</strong></td>
            <td class="text-end">${formatNumber(item.requested_qty)}</td>
            <td class="text-end">${formatNumber(item.produced_qty)}</td>
            <td class="text-end">${item.completion_pct}%</td>
            <td class="text-center">${getStatusBadge(item.status)}</td>
            <td>
                <div class="progress" style="height: 20px;">
                    <div class="progress-bar ${barColor}" 
                         style="width: ${item.completion_pct}%">
                        ${item.completion_pct}%
                    </div>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

/**
 * Render Chart.js bar chart
 */
function renderChart(comparison) {
    const ctx = document.getElementById('completionChart').getContext('2d');

    // Destroy previous chart instance if exists
    if (chartInstance) {
        chartInstance.destroy();
    }

    const labels = comparison.map(item => item.product_name);
    const data = comparison.map(item => item.completion_pct);
    const colors = comparison.map(item =>
        item.status === 'Complete' ? '#28a745'
            : item.status === 'Partial' ? '#ffc107'
                : '#dc3545'
    );

    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Completion %',
                data: data,
                backgroundColor: colors,
                borderColor: colors.map(c => c),
                borderWidth: 1,
                borderRadius: 4,
                maxBarThickness: 60
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function (value) {
                            return value + '%';
                        }
                    },
                    title: {
                        display: true,
                        text: 'Completion %'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Product Name'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.parsed.y + '% Complete';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Show error message in report area
 */
function showReportError(message) {
    document.getElementById('reportError').classList.remove('d-none');
    document.getElementById('reportErrorMessage').textContent = message;
    document.getElementById('reportContent').classList.add('d-none');
}