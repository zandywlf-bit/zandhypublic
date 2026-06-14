# System Requirements Specification
## Production Report & Distributor PO Dashboard

### Version 1.0 | June 2026

---

## 1. Introduction

### 1.1 Purpose
This document provides a detailed technical specification for building the Production Report & Distributor PO Dashboard. It defines the data models, API endpoints, user interface components, data processing logic, and deployment architecture required for implementation.

### 1.2 Scope
The system consists of three primary modules:
1. **Distributor PO Upload Module** – Accepts and stores distributor purchase order Excel files
2. **Factory Production Upload Module** – Accepts and stores factory production report Excel files  
3. **Comparison Dashboard Module** – Compares distributor requests vs. factory production and displays results

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (Client)                      │
│  HTML + CSS + JavaScript (Bootstrap 5 + Chart.js)        │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP / HTTPS
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Web Server (Nginx Reverse Proxy)            │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Application Server (Python Flask)           │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Upload APIs │  │ Dashboard    │  │ Data Export   │  │
│  │ (PO + Prod) │  │ APIs         │  │ APIs          │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│  ┌──────────────────────────────────────────────────┐   │
│  │         Data Processing Engine (Pandas)          │   │
│  │  - Excel parsing & validation                    │   │
│  │  - Merge logic                                   │   │
│  │  - Comparison calculation                        │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────┐
│              File Storage (Local Filesystem)             │
│  /data/distributor_po/  &  /data/factory_report/        │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Data Models

### 3.1 Distributor PO Excel Schema

**File Location:** `data/distributor_po/{factory_name}/{year}/{season}/po_data.xlsx`

| Column Name | Data Type | Validation Rules |
|-------------|-----------|------------------|
| Date of Request | Date (YYYY-MM-DD) | Must be valid date, not in future |
| Type of Season | String | Must be one of: Summer, Winter, Fall, Spring |
| Product Name | String | Required, max 255 chars |
| Quantity of Product | Integer | Must be > 0 |

**Python Pandas Schema:**
```python
po_dtypes = {
    'Date of Request': 'datetime64[ns]',
    'Type of Season': 'str',
    'Product Name': 'str',
    'Quantity of Product': 'int64'
}
```

### 3.2 Factory Production Excel Schema

**File Location:** `data/factory_report/{year}/{season}/{factory_name}_production.xlsx`

| Column Name | Data Type | Validation Rules |
|-------------|-----------|------------------|
| Date of Report | Date (YYYY-MM-DD) | Must be valid date, not in future |
| Product Name | String | Required, max 255 chars |
| Amount of Product Created | Integer | Must be > 0 |

**Python Pandas Schema:**
```python
prod_dtypes = {
    'Date of Report': 'datetime64[ns]',
    'Product Name': 'str',
    'Amount of Product Created': 'int64'
}
```

### 3.3 Comparison Result Model

```python
class ComparisonResult:
    product_name: str
    requested_quantity: int      # Sum from PO data
    produced_quantity: int       # Sum from Production data
    completion_percentage: float # (produced / requested) * 100
    status: str                  # "Complete", "Partial", "Missing", "Over-Produced"
```

**Status Logic:**
| Condition | Status |
|-----------|--------|
| Produced ≥ Requested | Complete |
| 0 < Produced < Requested | Partial |
| Produced = 0 | Missing |

---

## 4. API Specifications

### 4.1 Distributor PO Upload API

**Endpoint:** `POST /api/upload/po`

**Request Parameters (multipart/form-data):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| factory_name | String | Yes | Name of the factory |
| year | Integer | Yes | Year (e.g., 2026) |
| season | String | Yes | Summer/Winter/Fall/Spring |
| file | File | Yes | Excel .xlsx file |

**Response (200):**
```json
{
    "status": "success",
    "message": "PO data uploaded successfully",
    "data": {
        "factory_name": "Factory A",
        "year": 2026,
        "season": "Summer",
        "file_path": "data/distributor_po/Factory A/2026/summer/po_data.xlsx",
        "rows_added": 150,
        "total_rows": 1500
    }
}
```

**Response (400 - Validation Error):**
```json
{
    "status": "error",
    "message": "Invalid Excel format",
    "errors": [
        "Missing required column: 'Product Name'",
        "Column 'Quantity of Product' must contain positive integers"
    ]
}
```

### 4.2 Factory Production Upload API

**Endpoint:** `POST /api/upload/production`

**Request Parameters (multipart/form-data):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| factory_name | String | Yes | Name of the factory |
| year | Integer | Yes | Year |
| season | String | Yes | Summer/Winter/Fall/Spring |
| file | File | Yes | Excel .xlsx file |

**Response (200):**
```json
{
    "status": "success",
    "message": "Production report uploaded successfully",
    "data": {
        "factory_name": "Factory A",
        "year": 2026,
        "season": "Summer",
        "file_path": "data/factory_report/2026/summer/Factory A_production.xlsx",
        "rows_added": 80,
        "total_rows": 800
    }
}
```

### 4.3 Comparison Report API

**Endpoint:** `GET /api/report/compare`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| factory_name | String | Yes | Factory to filter by |
| year | Integer | Yes | Year to filter by |
| season | String | Yes | Season to filter by |

**Response (200):**
```json
{
    "status": "success",
    "data": {
        "filters": {
            "factory_name": "Factory A",
            "year": 2026,
            "season": "Summer"
        },
        "comparison": [
            {
                "product_name": "Product A",
                "requested_qty": 1000,
                "produced_qty": 750,
                "completion_pct": 75.0,
                "status": "Partial"
            },
            {
                "product_name": "Product B",
                "requested_qty": 500,
                "produced_qty": 500,
                "completion_pct": 100.0,
                "status": "Complete"
            }
        ],
        "summary": {
            "total_products": 2,
            "complete": 1,
            "partial": 1,
            "missing": 0,
            "overall_completion_pct": 83.33
        }
    }
}
```

### 4.4 Factory List API

**Endpoint:** `GET /api/factories`

**Response (200):**
```json
{
    "status": "success",
    "data": {
        "factories": ["Factory A", "Factory B", "Factory C"]
    }
}
```

### 4.5 Available Filters API

**Endpoint:** `GET /api/filters`

**Response (200):**
```json
{
    "status": "success",
    "data": {
        "factories": ["Factory A", "Factory B", "Factory C"],
        "years": [2024, 2025, 2026],
        "seasons": ["Summer", "Winter", "Fall", "Spring"]
    }
}
```

---

## 5. User Interface Specifications

### 5.1 Page Structure

The dashboard has **3 main pages/tabs**:

#### Tab 1: Distributor PO Upload
```
┌─────────────────────────────────────────────────────┐
│  Distributor PO Upload                              │
│  ┌─────────────────────────────────────────────┐   │
│  │ Factory Name:  [Dropdown ▼]                 │   │
│  │ Year:          [Dropdown ▼]                 │   │
│  │ Season:        [Dropdown ▼]                 │   │
│  │ File:          [Choose File]                │   │
│  │                        [📤 Upload]          │   │
│  └─────────────────────────────────────────────┘   │
│  Status message area                                │
└─────────────────────────────────────────────────────┘
```

#### Tab 2: Factory Production Upload
```
┌─────────────────────────────────────────────────────┐
│  Factory Production Report Upload                   │
│  ┌─────────────────────────────────────────────┐   │
│  │ Factory Name:  [Dropdown ▼]                 │   │
│  │ Year:          [Dropdown ▼]                 │   │
│  │ Season:        [Dropdown ▼]                 │   │
│  │ File:          [Choose File]                │   │
│  │                        [📤 Upload]          │   │
│  └─────────────────────────────────────────────┘   │
│  Status message area                                │
└─────────────────────────────────────────────────────┘
```

#### Tab 3: Comparison Dashboard
```
┌─────────────────────────────────────────────────────┐
│  Production vs Demand Report                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ Factory: [Dropdown ▼] Year: [Dropdown ▼]    │   │
│  │ Season:  [Dropdown ▼]           [🔍 View]   │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Summary Cards                                │   │
│  │ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐│   │
│  │ │Total   │ │Complete│ │Partial │ │Missing ││   │
│  │ │ 25     │ │ 12     │ │ 8      │ │ 5      ││   │
│  │ └────────┘ └────────┘ └────────┘ └────────┘│   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Comparison Table                             │   │
│  │ Product  │Req│Prod│ %  │ Status  │ Progress │   │
│  │──────────┼───┼────┼────┼─────────┼──────────│   │
│  │ Prod A   │1K │750 │75% │Partial  │███████░░░│   │
│  │ Prod B   │500│500 │100%│Complete │██████████│   │
│  │ Prod C   │300│ 0  │0%  │Missing  │░░░░░░░░░░│   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Chart: Completion % per Product (Bar Chart)  │   │
│  │ [Chart.js bar chart visualization]           │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 5.2 Color Scheme

| Element | Color | Hex Code |
|---------|-------|----------|
| Complete status | Green | #28a745 |
| Partial status | Orange/Amber | #ffc107 |
| Missing status | Red | #dc3545 |
| Primary button | Blue | #007bff |
| Background | Light Gray | #f8f9fa |
| Card backgrounds | White | #ffffff |

---

## 6. Data Processing Logic

### 6.1 Upload & Merge Flow

```
User submits file + metadata
        │
        ▼
Validate file type (.xlsx)
        │
        ▼
Validate column headers match schema
        │
        ▼
Read Excel into Pandas DataFrame
        │
        ▼
Validate data types and constraints
        │
        ▼
Check if target file already exists
   ┌────┴────┐
   │         │
  Yes       No
   │         │
   ▼         ▼
Read existing  Create new
DataFrame      DataFrame
        │
        ▼
Append new rows (pd.concat)
        │
        ▼
Drop duplicates (if any)
        │
        ▼
Sort by date
        │
        ▼
Write back to Excel (to_excel)
        │
        ▼
Return success response
```

### 6.2 Comparison Calculation Flow

```
User selects Factory, Year, Season
        │
        ▼
Construct PO file path: 
  data/distributor_po/{factory}/{year}/{season}/po_data.xlsx
        │
        ▼
Construct Production file path:
  data/factory_report/{year}/{season}/{factory}_production.xlsx
        │
        ▼
Read both Excel files into DataFrames
        │
        ▼
Group PO data by Product Name (sum Quantity)
        │
        ▼
Group Production data by Product Name (sum Amount)
        │
        ▼
Merge on Product Name (outer join, fill NaN with 0)
        │
        ▼
Calculate completion % per product
        │
        ▼
Assign status labels
        │
        ▼
Calculate summary statistics
        │
        ▼
Return JSON response
```

**Pseudo-code:**
```python
import pandas as pd

def compare_po_vs_production(factory, year, season):
    # Load data
    po_path = f"data/distributor_po/{factory}/{year}/{season}/po_data.xlsx"
    prod_path = f"data/factory_report/{year}/{season}/{factory}_production.xlsx"
    
    po_df = pd.read_excel(po_path)
    prod_df = pd.read_excel(prod_path)
    
    # Aggregate
    po_agg = po_df.groupby('Product Name')['Quantity of Product'].sum().reset_index()
    prod_agg = prod_df.groupby('Product Name')['Amount of Product Created'].sum().reset_index()
    
    # Merge
    merged = pd.merge(po_agg, prod_agg, on='Product Name', how='outer').fillna(0)
    
    # Calculate
    merged['Completion %'] = (merged['Amount of Product Created'] / merged['Quantity of Product']) * 100
    merged['Completion %'] = merged['Completion %'].clip(upper=100)
    
    # Status
    merged['Status'] = 'Missing'
    merged.loc[merged['Completion %'] >= 100, 'Status'] = 'Complete'
    merged.loc[(merged['Completion %'] > 0) & (merged['Completion %'] < 100), 'Status'] = 'Partial'
    
    return merged
```

---

## 7. File Naming Conventions

### 7.1 Distributor PO

```
data/distributor_po/{factory_name}/{year}/{season}/po_data.xlsx
```

- `{factory_name}`: Sanitized (spaces replaced with underscores, no special chars)
- `{year}`: 4-digit year (e.g., 2026)
- `{season}`: lowercase (summer, winter, fall, spring)

### 7.2 Factory Production Report

```
data/factory_report/{year}/{season}/{factory_name}_production.xlsx
```

- `{factory_name}`: Sanitized (spaces replaced with underscores)
- `{year}`: 4-digit year
- `{season}`: lowercase

---

## 8. Validation Rules

### 8.1 File Upload Validation

| Rule | Implementation |
|------|----------------|
| File extension must be .xlsx | Check file extension |
| File size ≤ 10MB | Check content-length |
| Required columns exist | Check column headers |
| All rows have non-null required fields | Check for NaN |
| Quantity values are positive integers | Check dtype and value > 0 |
| Date format is valid | Try pd.to_datetime |
| Season value is in allowed list | Check against ["Summer","Winter","Fall","Spring"] |

### 8.2 Input Form Validation

| Field | Rule |
|-------|------|
| Factory Name | Must be selected, not empty |
| Year | 4-digit, between 2000-2099 |
| Season | Must be one of the 4 seasons |

---

## 9. Error Handling

### 9.1 HTTP Status Codes

| Code | Meaning | Use Case |
|------|---------|----------|
| 200 | Success | Successful upload, report generation |
| 400 | Bad Request | Invalid file format, missing columns |
| 404 | Not Found | No data found for selected filters |
| 413 | Payload Too Large | File exceeds 10MB limit |
| 415 | Unsupported Media Type | Non-Excel file uploaded |
| 500 | Internal Server Error | Unexpected server errors |

### 9.2 Error Response Format

```json
{
    "status": "error",
    "message": "Human-readable error description",
    "error_code": "INVALID_FILE_FORMAT",
    "details": ["Detail 1", "Detail 2"]
}
```

---

## 10. Directory Structure (Project)

```
/distributor-production-dashboard/
├── app.py                    # Flask application entry point
├── requirements.txt          # Python dependencies
├── config.py                 # Configuration settings
├── Dockerfile                # Docker build file
├── docker-compose.yml        # Docker compose for multi-service
├── .gitignore                # Git ignore rules
├── /docs/                    # Documentation
│   ├── PRD.md
│   ├── REQUIREMENTS.md
│   └── AGENT.md
├── /data/                    # Data storage (gitignored)
│   ├── /distributor_po/
│   └── /factory_report/
├── /modules/                 # Python modules
│   ├── __init__.py
│   ├── upload_handler.py     # Upload logic
│   ├── data_processor.py     # Data processing + comparison
│   ├── file_validator.py     # File validation
│   └── file_manager.py       # File system operations
├── /static/                  # Static assets
│   ├── /css/
│   │   └── style.css
│   ├── /js/
│   │   ├── main.js
│   │   ├── upload.js
│   │   └── dashboard.js
│   └── /img/
├── /templates/               # HTML templates
│   ├── index.html            # Main page (tabs)
│   ├── upload_po.html        # PO upload section
│   ├── upload_production.html# Production upload section
│   └── dashboard.html        # Comparison dashboard
└── /uploads/                 # Temp upload directory
    └── .gitkeep
```

---

## 11. Dependencies (requirements.txt)

```
Flask==3.0.0
pandas==2.1.3
openpyxl==3.1.2
Werkzeug==3.0.1
python-dotenv==1.0.0
gunicorn==21.2.0
```

---

## 12. Environment Variables (config.py)

```python
# config.py
import os

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'xlsx'}
    FACTORIES = ['Factory A', 'Factory B', 'Factory C']  # Configurable
    SEASONS = ['Summer', 'Winter', 'Fall', 'Spring']
    YEARS = [2024, 2025, 2026]
```

---

## 13. Deployment Requirements

### 13.1 Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
```

### 13.2 System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 1 core | 2 cores |
| RAM | 512 MB | 1 GB |
| Storage | 1 GB | 10 GB |
| Python | 3.9+ | 3.11+ |

---

## 14. Testing

### 14.1 Test Cases

| Test ID | Description | Expected Result |
|---------|-------------|-----------------|
| T-01 | Upload valid PO Excel | Data saved, success response |
| T-02 | Upload PO with missing columns | Error with column details |
| T-03 | Upload PO with invalid data types | Error with type details |
| T-04 | Upload duplicate PO data | Merged, no duplicates |
| T-05 | Upload valid Production Excel | Data saved, success response |
| T-06 | Compare with matching data | Correct completion % |
| T-07 | Compare with no matching data | All status = Missing |
| T-08 | Compare with full production | All status = Complete |
| T-09 | Upload file > 10MB | Error 413 |
| T-10 | Non-Excel file upload | Error 415 |

---

## 15. Future Enhancements

- PostgreSQL database for metadata storage
- AWS S3 for file storage
- Authentication & authorization
- Email notifications for low completion rates
- Historical trend charts
- Export reports to PDF/Excel
- Multiple file batch upload
- Real-time updates via WebSocket

---

*Document prepared by the Data Engineering Team | June 2026*