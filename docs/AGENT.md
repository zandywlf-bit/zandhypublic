# AI Agent Implementation Guide
## Production Report & Distributor PO Dashboard

### Agent Version: Build Agent v1.0 | June 2026

---

## 1. Agent Identity

**Name:** Production Dashboard Builder Agent  
**Role:** Senior Data Engineer + Full-Stack Developer  
**Objective:** Build a complete, production-ready online dashboard system for tracking distributor purchase orders against factory production reports.

---

## 2. Agent Instructions

### 2.1 Core Principles

1. **Data Integrity First** – Always validate input data before processing. Never silently drop or corrupt data.
2. **Public Accessibility** – The dashboard must be accessible without authentication. Design for public use from day one.
3. **Excel-Centric** – All data is stored in Excel files on the local filesystem. No database is required.
4. **Merge, Don't Overwrite** – When uploading new data for the same factory/year/season, always merge with existing data.
5. **User-Friendly UI** – The interface should be intuitive, with clear labels, dropdowns, and visual feedback.

### 2.2 Technology Stack

| Component | Technology | Justification |
|-----------|------------|---------------|
| Backend | Python Flask | Lightweight, easy to deploy, excellent Excel support via Pandas |
| Frontend | HTML + CSS + JavaScript + Bootstrap 5 | Zero build tools needed, works everywhere |
| Data Processing | Pandas + openpyxl | Industry standard for Excel manipulation |
| Charts | Chart.js | Lightweight, CDN-hostable, no build step |
| Deployment | Docker + Gunicorn | Portable, scalable, production-grade |

### 2.3 Project Structure to Build

```
/project-root/
├── app.py                   # Main Flask application
├── config.py                # Configuration
├── requirements.txt         # Dependencies
├── Dockerfile               # Container build
├── docker-compose.yml       # Multi-service orchestration
├── .gitignore
├── /modules/
│   ├── __init__.py
│   ├── upload_handler.py    # Handles Excel upload & merge
│   ├── data_processor.py    # Comparison & reporting logic
│   ├── file_validator.py    # Excel validation
│   └── file_manager.py      # File system operations
├── /templates/
│   ├── index.html           # Main page with tabs
│   ├── upload_po.html       # PO upload form
│   ├── upload_production.html # Production upload form
│   └── dashboard.html       # Comparison dashboard
├── /static/
│   ├── /css/
│   │   └── style.css        # Custom styles
│   └── /js/
│       ├── main.js          # Tab switching, form handling
│       ├── upload.js        # Upload API calls
│       └── dashboard.js     # Dashboard rendering & chart
├── /data/                   # Created at runtime
│   ├── /distributor_po/
│   └── /factory_report/
└── /uploads/                # Temp upload directory
```

---

## 3. Step-by-Step Implementation Plan

### Phase 1: Project Foundation

#### Step 1.1: Initialize Project
```bash
mkdir distributor-production-dashboard
cd distributor-production-dashboard
python -m venv venv
pip install flask pandas openpyxl
```

**Files to create:**
- `requirements.txt`
- `config.py`
- `app.py` (minimal Flask app)
- `.gitignore`

#### Step 1.2: Create Data Directories
```bash
mkdir -p data/distributor_po data/factory_report uploads
touch uploads/.gitkeep
```

---

### Phase 2: Backend Modules

#### Step 2.1: File Manager (`modules/file_manager.py`)

**Responsibilities:**
- Create directory paths as needed
- Sanitize folder names (replace spaces, special chars)
- Check if files exist
- List available factories, years, seasons from filesystem

**Key Functions:**
```python
def sanitize_name(name: str) -> str:
    """Replace spaces with underscores, remove special chars"""
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')

def ensure_dir(path: str) -> str:
    """Create directory if not exists, return path"""
    os.makedirs(path, exist_ok=True)
    return path

def get_po_path(factory: str, year: int, season: str) -> str:
    """Construct full path for PO data file"""
    return os.path.join(
        Config.DATA_DIR, 'distributor_po',
        sanitize_name(factory), str(year), season.lower(), 'po_data.xlsx'
    )

def get_production_path(factory: str, year: int, season: str) -> str:
    """Construct full path for Production data file"""
    return os.path.join(
        Config.DATA_DIR, 'factory_report',
        str(year), season.lower(), f'{sanitize_name(factory)}_production.xlsx'
    )

def list_available_factories() -> list:
    """Scan filesystem for factory directories"""
    po_dir = os.path.join(Config.DATA_DIR, 'distributor_po')
    if not os.path.exists(po_dir):
        return Config.FACTORIES  # fallback to config
    return sorted([d for d in os.listdir(po_dir) 
                   if os.path.isdir(os.path.join(po_dir, d))])

def list_available_years() -> list:
    """Scan filesystem for year directories across both PO and production"""
    years = set()
    for base in ['distributor_po', 'factory_report']:
        path = os.path.join(Config.DATA_DIR, base)
        if os.path.exists(path):
            for d in os.listdir(path):
                if d.isdigit():
                    years.add(int(d))
    return sorted(years, reverse=True) or Config.YEARS
```

#### Step 2.2: File Validator (`modules/file_validator.py`)

**Responsibilities:**
- Validate file extension (.xlsx only)
- Validate file size (max 10MB)
- Validate Excel structure (required columns exist)
- Validate data types and constraints

**Key Functions:**
```python
def validate_file_extension(filename: str) -> bool:
    """Check if file has .xlsx extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def validate_po_columns(df: pd.DataFrame) -> tuple:
    """Check PO Excel has required columns. Returns (is_valid, errors)"""
    required = ['Date of Request', 'Type of Season', 'Product Name', 'Quantity of Product']
    missing = [col for col in required if col not in df.columns]
    return (len(missing) == 0, missing)

def validate_production_columns(df: pd.DataFrame) -> tuple:
    """Check Production Excel has required columns. Returns (is_valid, errors)"""
    required = ['Date of Report', 'Product Name', 'Amount of Product Created']
    missing = [col for col in required if col not in df.columns]
    return (len(missing) == 0, missing)

def validate_quantity_column(series: pd.Series) -> tuple:
    """Validate quantity values are positive integers"""
    errors = []
    if series.dtype not in ['int64', 'float64']:
        errors.append(f"Column must contain numbers, got {series.dtype}")
    if (series <= 0).any():
        errors.append("All values must be positive numbers")
    return (len(errors) == 0, errors)

def validate_season_column(series: pd.Series) -> tuple:
    """Validate season values"""
    valid_seasons = ['Summer', 'Winter', 'Fall', 'Spring']
    invalid = series[~series.isin(valid_seasons)].unique()
    if len(invalid) > 0:
        return (False, [f"Invalid season values: {list(invalid)}"])
    return (True, [])
```

#### Step 2.3: Upload Handler (`modules/upload_handler.py`)

**Responsibilities:**
- Receive uploaded files
- Validate them using file_validator
- Merge with existing data if file already exists
- Write/save the final Excel file

**Key Functions:**
```python
import pandas as pd
from modules.file_manager import get_po_path, get_production_path, ensure_dir
from modules.file_validator import validate_file_extension, validate_po_columns

def handle_po_upload(factory: str, year: int, season: str, uploaded_file) -> dict:
    """Process PO upload: validate, merge, save"""
    if not validate_file_extension(uploaded_file.filename):
        return {'status': 'error', 'message': 'Only .xlsx files are supported'}
    
    df = pd.read_excel(uploaded_file)
    is_valid, errors = validate_po_columns(df)
    if not is_valid:
        return {'status': 'error', 'message': 'Missing columns', 'errors': errors}
    
    # Merge with existing
    target_path = get_po_path(factory, year, season)
    ensure_dir(os.path.dirname(target_path))
    
    existing_rows = 0
    if os.path.exists(target_path):
        existing_df = pd.read_excel(target_path)
        existing_rows = len(existing_df)
        df = pd.concat([existing_df, df], ignore_index=True)
        df = df.drop_duplicates()
        df = df.sort_values('Date of Request')
    
    df.to_excel(target_path, index=False)
    
    return {
        'status': 'success',
        'message': 'PO data uploaded successfully',
        'rows_added': len(df) - existing_rows,
        'total_rows': len(df)
    }

def handle_production_upload(factory: str, year: int, season: str, uploaded_file) -> dict:
    """Process Production upload: validate, merge, save"""
    if not validate_file_extension(uploaded_file.filename):
        return {'status': 'error', 'message': 'Only .xlsx files are supported'}
    
    df = pd.read_excel(uploaded_file)
    is_valid, errors = validate_production_columns(df)
    if not is_valid:
        return {'status': 'error', 'message': 'Missing columns', 'errors': errors}
    
    target_path = get_production_path(factory, year, season)
    ensure_dir(os.path.dirname(target_path))
    
    existing_rows = 0
    if os.path.exists(target_path):
        existing_df = pd.read_excel(target_path)
        existing_rows = len(existing_df)
        df = pd.concat([existing_df, df], ignore_index=True)
        df = df.drop_duplicates()
        df = df.sort_values('Date of Report')
    
    df.to_excel(target_path, index=False)
    
    return {
        'status': 'success',
        'message': 'Production report uploaded successfully',
        'rows_added': len(df) - existing_rows,
        'total_rows': len(df)
    }
```

#### Step 2.4: Data Processor (`modules/data_processor.py`)

**Responsibilities:**
- Load both PO and Production Excel files
- Aggregate quantities by product
- Compare and calculate completion percentages
- Generate summary statistics

**Key Functions:**
```python
import pandas as pd
from modules.file_manager import get_po_path, get_production_path

def compare_po_vs_production(factory: str, year: int, season: str) -> dict:
    """Main comparison engine"""
    po_path = get_po_path(factory, year, season)
    prod_path = get_production_path(factory, year, season)
    
    # Check if files exist
    if not os.path.exists(po_path):
        return {'status': 'error', 'message': f'No PO data found for {factory}, {year}, {season}'}
    if not os.path.exists(prod_path):
        return {'status': 'error', 'message': f'No Production data found for {factory}, {year}, {season}'}
    
    po_df = pd.read_excel(po_path)
    prod_df = pd.read_excel(prod_path)
    
    # Aggregate by product
    po_agg = po_df.groupby('Product Name')['Quantity of Product'].sum().reset_index()
    prod_agg = prod_df.groupby('Product Name')['Amount of Product Created'].sum().reset_index()
    
    # Merge
    merged = pd.merge(po_agg, prod_agg, on='Product Name', how='outer').fillna(0)
    
    # Rename for clarity
    merged.columns = ['product_name', 'requested_qty', 'produced_qty']
    merged['requested_qty'] = merged['requested_qty'].astype(int)
    merged['produced_qty'] = merged['produced_qty'].astype(int)
    
    # Calculate completion
    merged['completion_pct'] = round(
        (merged['produced_qty'] / merged['requested_qty'].replace(0, 1)) * 100, 1
    )
    merged['completion_pct'] = merged['completion_pct'].clip(upper=100)
    
    # Status
    def assign_status(row):
        if row['completion_pct'] >= 100:
            return 'Complete'
        elif row['completion_pct'] > 0:
            return 'Partial'
        else:
            return 'Missing'
    
    merged['status'] = merged.apply(assign_status, axis=1)
    
    # Summary
    total = len(merged)
    complete = len(merged[merged['status'] == 'Complete'])
    partial = len(merged[merged['status'] == 'Partial'])
    missing = len(merged[merged['status'] == 'Missing'])
    
    overall_pct = round(
        (merged['produced_qty'].sum() / merged['requested_qty'].sum()) * 100, 2
    ) if merged['requested_qty'].sum() > 0 else 0
    
    comparison_list = merged.to_dict('records')
    
    return {
        'status': 'success',
        'data': {
            'filters': {
                'factory_name': factory,
                'year': year,
                'season': season
            },
            'comparison': comparison_list,
            'summary': {
                'total_products': total,
                'complete': int(complete),
                'partial': int(partial),
                'missing': int(missing),
                'overall_completion_pct': overall_pct
            }
        }
    }
```

---

### Phase 3: Flask Application (app.py)

**Responsibilities:**
- Serve HTML templates
- Expose REST API endpoints
- Handle file uploads
- Serve static assets

```python
# app.py - Main Flask Application
from flask import Flask, render_template, request, jsonify
import os
from config import Config
from modules.upload_handler import handle_po_upload, handle_production_upload
from modules.data_processor import compare_po_vs_production
from modules.file_manager import list_available_factories, list_available_years

app = Flask(__name__)
app.config.from_object(Config)

# Ensure data directories exist
os.makedirs(app.config['DATA_DIR'], exist_ok=True)
os.makedirs(os.path.join(app.config['DATA_DIR'], 'distributor_po'), exist_ok=True)
os.makedirs(os.path.join(app.config['DATA_DIR'], 'factory_report'), exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """Serve main dashboard page"""
    factories = list_available_factories()
    years = list_available_years()
    return render_template('index.html', 
                         factories=factories, 
                         years=years, 
                         seasons=Config.SEASONS)

@app.route('/api/upload/po', methods=['POST'])
def upload_po():
    """API endpoint for Distributor PO upload"""
    factory = request.form.get('factory_name')
    year = request.form.get('year')
    season = request.form.get('season')
    file = request.files.get('file')
    
    if not all([factory, year, season, file]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    result = handle_po_upload(factory, int(year), season, file)
    status_code = 200 if result['status'] == 'success' else 400
    return jsonify(result), status_code

@app.route('/api/upload/production', methods=['POST'])
def upload_production():
    """API endpoint for Factory Production upload"""
    factory = request.form.get('factory_name')
    year = request.form.get('year')
    season = request.form.get('season')
    file = request.files.get('file')
    
    if not all([factory, year, season, file]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
    
    result = handle_production_upload(factory, int(year), season, file)
    status_code = 200 if result['status'] == 'success' else 400
    return jsonify(result), status_code

@app.route('/api/report/compare')
def get_comparison():
    """API endpoint to get comparison report"""
    factory = request.args.get('factory_name')
    year = request.args.get('year')
    season = request.args.get('season')
    
    if not all([factory, year, season]):
        return jsonify({'status': 'error', 'message': 'Missing filter parameters'}), 400
    
    result = compare_po_vs_production(factory, int(year), season)
    status_code = 200 if result['status'] == 'success' else 404
    return jsonify(result), status_code

@app.route('/api/factories')
def get_factories():
    """API endpoint to list available factories"""
    factories = list_available_factories()
    return jsonify({'status': 'success', 'data': {'factories': factories}})

@app.route('/api/filters')
def get_filters():
    """API endpoint to get all available filter options"""
    factories = list_available_factories()
    years = list_available_years()
    return jsonify({
        'status': 'success',
        'data': {
            'factories': factories,
            'years': years,
            'seasons': Config.SEASONS
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

---

### Phase 4: Frontend Templates

#### Step 4.1: Main Layout (`templates/index.html`)

**Requirements:**
- Bootstrap 5 CDN
- 3-tab interface (PO Upload, Production Upload, Dashboard)
- Responsive design
- Loading indicators

**Tab Structure:**
```html
<ul class="nav nav-tabs" id="mainTabs" role="tablist">
  <li class="nav-item">
    <a class="nav-link active" data-bs-toggle="tab" href="#poUpload">
      📦 Distributor PO Upload
    </a>
  </li>
  <li class="nav-item">
    <a class="nav-link" data-bs-toggle="tab" href="#productionUpload">
      🏭 Factory Production Upload
    </a>
  </li>
  <li class="nav-item">
    <a class="nav-link" data-bs-toggle="tab" href="#dashboard">
      📊 Production vs Demand Report
    </a>
  </li>
</ul>
```

#### Step 4.2: PO Upload Form

**Fields:**
- Factory Name (dropdown, populated from API)
- Year (dropdown)
- Season (dropdown)
- File (file input, accept=".xlsx")

**Behavior:**
- Submit via AJAX to `/api/upload/po`
- Show success/error message
- Disable button during upload
- Show loading spinner

#### Step 4.3: Production Upload Form

**Fields:**
- Factory Name (dropdown)
- Year (dropdown)
- Season (dropdown)
- File (file input, accept=".xlsx")

**Behavior:**
- Submit via AJAX to `/api/upload/production`
- Show success/error message
- Disable button during upload
- Show loading spinner

#### Step 4.4: Dashboard Tab

**Filters Section:**
- Factory Name (dropdown)
- Year (dropdown)
- Season (dropdown)
- "View Report" button

**Report Content (appears after clicking View):**
1. **Summary Cards Row** (4 cards):
   - Total Products
   - Complete (green)
   - Partial (amber)
   - Missing (red)
2. **Comparison Table** with columns:
   - Product Name | Requested Qty | Produced Qty | Completion % | Status | Progress Bar
3. **Bar Chart** (Chart.js):
   - X-axis: Product Names
   - Y-axis: Completion %
   - Color-coded bars by status

#### Step 4.5: JavaScript Logic (`static/js/dashboard.js`)

**Key Functions:**
```javascript
// Load comparison report
function loadReport(factory, year, season) {
    showLoading();
    fetch(`/api/report/compare?factory_name=${factory}&year=${year}&season=${season}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                renderSummaryCards(data.data.summary);
                renderTable(data.data.comparison);
                renderChart(data.data.comparison);
            } else {
                showError(data.message);
            }
        })
        .catch(error => showError('Failed to load report'))
        .finally(hideLoading);
}

// Render summary cards
function renderSummaryCards(summary) {
    // Update 4 card elements with summary data
    document.getElementById('totalProducts').textContent = summary.total_products;
    document.getElementById('completeCount').textContent = summary.complete;
    document.getElementById('partialCount').textContent = summary.partial;
    document.getElementById('missingCount').textContent = summary.missing;
    document.getElementById('overallPct').textContent = summary.overall_completion_pct + '%';
}

// Render comparison table
function renderTable(comparison) {
    const tbody = document.getElementById('comparisonTableBody');
    tbody.innerHTML = '';
    comparison.forEach(item => {
        const row = document.createElement('tr');
        const statusClass = item.status === 'Complete' ? 'table-success' 
                          : item.status === 'Partial' ? 'table-warning' 
                          : 'table-danger';
        row.className = statusClass;
        row.innerHTML = `
            <td>${item.product_name}</td>
            <td>${item.requested_qty.toLocaleString()}</td>
            <td>${item.produced_qty.toLocaleString()}</td>
            <td>${item.completion_pct}%</td>
            <td><span class="badge bg-${item.status === 'Complete' ? 'success' : item.status === 'Partial' ? 'warning' : 'danger'}">${item.status}</span></td>
            <td>
                <div class="progress">
                    <div class="progress-bar bg-${item.status === 'Complete' ? 'success' : item.status === 'Partial' ? 'warning' : 'danger'}" 
                         style="width: ${item.completion_pct}%">
                        ${item.completion_pct}%
                    </div>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Render Chart.js bar chart
function renderChart(comparison) {
    const ctx = document.getElementById('completionChart').getContext('2d');
    const labels = comparison.map(item => item.product_name);
    const data = comparison.map(item => item.completion_pct);
    const colors = comparison.map(item => 
        item.status === 'Complete' ? '#28a745' 
        : item.status === 'Partial' ? '#ffc107' 
        : '#dc3545'
    );
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Completion %',
                data: data,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true, max: 100 }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}
```

---

### Phase 5: Configuration & Deployment

#### Step 5.1: Configuration (`config.py`)

```python
import os

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'xlsx'}
    
    # Default factory list (can be extended)
    FACTORIES = [
        'Factory A', 'Factory B', 'Factory C', 'Factory D', 'Factory E'
    ]
    
    SEASONS = ['Summer', 'Winter', 'Fall', 'Spring']
    YEARS = [2024, 2025, 2026]
```

#### Step 5.2: Docker Setup

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/distributor_po data/factory_report uploads

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "80:5000"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
```

---

## 4. Testing Strategy

### 4.1 Unit Tests to Run

```bash
# Test file validator
python -c "
from modules.file_validator import validate_file_extension
assert validate_file_extension('data.xlsx') == True
assert validate_file_extension('data.csv') == False
assert validate_file_extension('data.xls') == False
print('File validation tests passed')
"

# Test data processor
python -c "
from modules.data_processor import compare_po_vs_production
# Test with known data
result = compare_po_vs_production('Factory A', 2026, 'Summer')
print(result['status'])
print(f'Products compared: {len(result[\"data\"][\"comparison\"])}')
print(f'Summary: {result[\"data\"][\"summary\"]}')
"
```

### 4.2 Manual Testing Checklist

- [ ] Upload PO Excel → Verify file saved in correct directory
- [ ] Upload 2nd PO for same factory/year/season → Verify merged
- [ ] Upload Production Excel → Verify file saved
- [ ] Load dashboard with matching PO + Prod → Verify comparison
- [ ] Load dashboard with no PO → Verify error message
- [ ] Load dashboard with no Prod → Verify error message
- [ ] Upload invalid file type → Verify error message
- [ ] Upload file with wrong columns → Verify error message
- [ ] Test on mobile browser → Verify responsive layout
- [ ] Test public access (no auth required) → Verify page loads

---

## 5. Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| File upload fails silently | Check `MAX_CONTENT_LENGTH` in config |
| Excel merge creates duplicates | Add `drop_duplicates()` after concat |
| Chart not rendering | Ensure Chart.js CDN is loaded before canvas element |
| Data not persisting | Check Docker volume mounts |
| Path too long on Windows | Use `os.path.join()` consistently |
| Season case mismatch | Normalize to title case on input |
| Large file performance | Consider chunked reading for >100k rows |

---

## 6. Sample Test Data

### Sample PO Data (po_sample.xlsx)

| Date of Request | Type of Season | Product Name | Quantity of Product |
|-----------------|----------------|--------------|-------------------|
| 2026-06-01 | Summer | T-Shirt Basic | 1000 |
| 2026-06-01 | Summer | Denim Jeans | 500 |
| 2026-06-02 | Summer | Leather Belt | 300 |
| 2026-06-03 | Summer | Tropical Shirt | 800 |

### Sample Production Data (production_sample.xlsx)

| Date of Report | Product Name | Amount of Product Created |
|----------------|--------------|--------------------------|
| 2026-06-05 | T-Shirt Basic | 750 |
| 2026-06-06 | Denim Jeans | 500 |
| 2026-06-07 | Leather Belt | 100 |

### Expected Comparison Output for Above Data

| Product Name | Requested Qty | Produced Qty | Completion % | Status |
|--------------|---------------|--------------|--------------|--------|
| T-Shirt Basic | 1000 | 750 | 75.0% | Partial |
| Denim Jeans | 500 | 500 | 100.0% | Complete |
| Leather Belt | 300 | 100 | 33.3% | Partial |
| Tropical Shirt | 800 | 0 | 0.0% | Missing |

---

## 7. Implementation Order (Priority)

1. `config.py` – Configuration setup
2. `modules/file_manager.py` – Filesystem operations
3. `modules/file_validator.py` – Input validation
4. `modules/upload_handler.py` – Upload & merge logic
5. `modules/data_processor.py` – Comparison engine
6. `app.py` – Flask routes & API endpoints
7. `templates/index.html` – Main layout with tabs
8. `templates/upload_po.html` – PO upload form
9. `templates/upload_production.html` – Production upload form
10. `templates/dashboard.html` – Dashboard view
11. `static/js/main.js` – Tab switching & common JS
12. `static/js/upload.js` – Upload AJAX logic
13. `static/js/dashboard.js` – Dashboard rendering
14. `static/css/style.css` – Custom styling
15. `Dockerfile` & `docker-compose.yml` – Deployment

---

## 8. Final Verification

Before marking the task complete, verify:

```bash
# 1. App runs without errors
python app.py &
sleep 2

# 2. Homepage loads
curl http://localhost:5000/

# 3. Can upload a test file
curl -X POST -F "factory_name=Factory A" -F "year=2026" -F "season=Summer" -F "file=@test_data/po_sample.xlsx" http://localhost:5000/api/upload/po

# 4. Can get comparison report
curl "http://localhost:5000/api/report/compare?factory_name=Factory%20A&year=2026&season=Summer"

# 5. Kill background process
kill %1
```

---

*Agent Instructions prepared by the Data Engineering Team | June 2026*