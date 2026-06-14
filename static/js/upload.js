// Upload JavaScript - Handles PO & Production file uploads

document.addEventListener('DOMContentLoaded', function () {
    // PO Upload Form
    const poForm = document.getElementById('poUploadForm');
    if (poForm) {
        poForm.addEventListener('submit', function (e) {
            e.preventDefault();
            submitUpload('po');
        });
    }

    // Production Upload Form
    const prodForm = document.getElementById('productionUploadForm');
    if (prodForm) {
        prodForm.addEventListener('submit', function (e) {
            e.preventDefault();
            submitUpload('production');
        });
    }
});

/**
 * Submit an upload to the server
 * @param {string} type - 'po' or 'production'
 */
function submitUpload(type) {
    const prefix = type === 'po' ? 'po' : 'prod';
    const endpoint = type === 'po' ? '/api/upload/po' : '/api/upload/production';

    const form = document.getElementById(prefix + 'UploadForm');
    const formData = new FormData(form);
    const btn = document.getElementById(prefix + 'UploadBtn');
    const spinner = document.getElementById(prefix + 'Spinner');
    const resultDiv = document.getElementById(prefix + 'UploadResult');

    // Validate file selected
    const fileInput = document.getElementById(prefix + 'File');
    if (!fileInput.files || fileInput.files.length === 0) {
        showUploadError(resultDiv, 'Please select an Excel file to upload.');
        return;
    }

    // Validate file extension
    const fileName = fileInput.files[0].name;
    if (!fileName.endsWith('.xlsx')) {
        showUploadError(resultDiv, 'Only .xlsx files are supported.');
        return;
    }

    // Disable button and show spinner
    btn.disabled = true;
    spinner.classList.remove('d-none');
    btn.textContent = 'Uploading...';
    resultDiv.innerHTML = '';

    // Send upload request
    fetch(endpoint, {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showUploadSuccess(resultDiv, data);
                form.reset();
                // Refresh filters to update available data
                refreshFilters();
            } else {
                showUploadError(resultDiv, data.message, data.errors);
            }
        })
        .catch(error => {
            showUploadError(resultDiv, 'Network error. Please try again.');
            console.error('Upload error:', error);
        })
        .finally(() => {
            btn.disabled = false;
            spinner.classList.add('d-none');
            btn.innerHTML = type === 'po' ? '📤 Upload PO Data' : '📤 Upload Production Report';
        });
}

/**
 * Display upload success message
 */
function showUploadSuccess(container, data) {
    const d = data.data;
    container.innerHTML = `
        <div class="alert alert-success">
            <strong>✅ ${data.message}</strong>
            <hr class="my-2">
            <small>
                Factory: ${d.factory_name} | ${d.season} ${d.year}<br>
                Rows added: ${formatNumber(d.rows_added)} | Total rows: ${formatNumber(d.total_rows)}
            </small>
        </div>
    `;
}

/**
 * Display upload error message
 */
function showUploadError(container, message, errors) {
    let errorDetails = '';
    if (errors && errors.length > 0) {
        errorDetails = '<hr class="my-2"><small><ul class="mb-0">';
        errors.forEach(err => {
            errorDetails += `<li>${err}</li>`;
        });
        errorDetails += '</ul></small>';
    }

    container.innerHTML = `
        <div class="alert alert-danger">
            <strong>❌ ${message}</strong>
            ${errorDetails}
        </div>
    `;
}