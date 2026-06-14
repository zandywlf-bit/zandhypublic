# Product Requirements Document (PRD)
## Production Report & Distributor PO Dashboard

### Version 1.0 | June 2026

---

## 1. Executive Summary

This document outlines the requirements for an interactive online dashboard system designed to manage and reconcile **Distributor Purchase Orders (PO)** with **Factory Production Reports**. The system enables users to input, store, and compare distributor demand against factory production output across multiple factories, years, and seasons.

**Objective:** To provide a centralized, publicly accessible platform where clients can track production completeness against distributor requests in real-time.

---

## 2. Product Vision

Create a web-based dashboard that:
- Collects distributor stock requests (POs) with factory, year, and season granularity
- Collects factory production reports with the same granularity
- Compares demand vs. production and provides a **percentage completion report per product**
- Is publicly accessible for all clients

---

## 3. Target Users

| User Type | Description | Needs |
|-----------|-------------|-------|
| **Distributors** | Submit stock requests | Upload PO data, view fulfillment status |
| **Factory Managers** | Report production output | Upload production reports |
| **Clients / Management** | Monitor overall performance | View aggregated comparison reports |
| **Public Users** | General stakeholders | Access dashboard without authentication |

---

## 4. Functional Requirements

### 4.1 Data Input – Distributor PO Request

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | User can select **Factory Name** from a predefined list | P0 |
| FR-02 | User can select **Year** (dropdown or input) | P0 |
| FR-03 | User can select **Seasonality** (Summer, Winter, Fall, Spring) | P0 |
| FR-04 | System accepts Excel (.xlsx) file uploads for PO data | P0 |
| FR-05 | Uploaded PO Excel must contain columns: **Date of Request**, **Type of Season**, **Product Name**, **Quantity of Product** | P0 |
| FR-06 | Data is organized into a folder structure: `/data/distributor_po/{factory_name}/{year}/{season}/` | P0 |
| FR-07 | If the same factory, year, and season already exist, **merge** new data into the existing dataset (append rows) | P0 |

### 4.2 Data Input – Factory Production Report

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-08 | User can select **Factory Name** from a predefined list | P0 |
| FR-09 | User can select **Year** | P0 |
| FR-10 | User can select **Seasonality** (Summer, Winter, Fall, Spring) | P0 |
| FR-11 | System accepts Excel (.xlsx) file uploads for production data | P0 |
| FR-12 | Uploaded Production Excel must contain columns: **Date of Report**, **Product Name**, **Amount of Product Created** | P0 |
| FR-13 | Data is organized into a folder structure: `/data/factory_report/{year}/{season}/` | P0 |
| FR-14 | If the same factory, year, and season already exist, **merge** new data into the existing dataset | P0 |

### 4.3 Dashboard – Comparison & Reporting

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-15 | User can select **Factory Name**, **Year**, and **Season** to filter reports | P0 |
| FR-16 | System pulls the corresponding PO data and Production data based on the selected filters | P0 |
| FR-17 | System compares **Distributor Request** vs. **Factory Production** per product | P0 |
| FR-18 | System calculates and displays **Percentage of Completion** per product: `(Amount Produced / Quantity Requested) * 100` | P0 |
| FR-19 | Report displays a table with columns: Product Name, Requested Qty, Produced Qty, Completion %, Status (Complete/Partial/Missing) | P0 |
| FR-20 | Visual indicators (color-coded progress bars, charts) for quick status assessment | P1 |

### 4.4 Public Accessibility

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-21 | Dashboard must be accessible via public URL without login/authentication | P0 |
| FR-22 | Read-only access for public users (no data upload for unauthenticated users) | P0 |
| FR-23 | Responsive design for desktop and mobile browsers | P1 |

---

## 5. Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | **Performance** – Dashboard load time < 3 seconds | < 3s |
| NFR-02 | **Scalability** – Support up to 50 factories, 500 products | 50 factories / 500 products |
| NFR-03 | **Reliability** – Data integrity on concurrent uploads | 99.9% uptime |
| NFR-04 | **Usability** – Intuitive UI, minimal training required | Zero training |
| NFR-05 | **Security** – Upload validation (file type, column headers) | Validate all inputs |
| NFR-06 | **Portability** – Deployable on cloud (AWS/Azure/GCP) or local server | Docker containerized |

---

## 6. Data Folder Structure

```
/data/
├── distributor_po/
│   └── {factory_name}/
│       └── {year}/
│           ├── summer/
│           │   ├── po_data.xlsx
│           ├── winter/
│           │   └── po_data.xlsx
│           ├── fall/
│           │   └── po_data.xlsx
│           └── spring/
│               └── po_data.xlsx
└── factory_report/
    └── {year}/
        ├── summer/
        │   ├── {factory_name}_production.xlsx
        ├── winter/
        │   ├── {factory_name}_production.xlsx
        ├── fall/
        │   ├── {factory_name}_production.xlsx
        └── spring/
            └── {factory_name}_production.xlsx
```

---

## 7. Excel File Format Specifications

### Distributor PO Excel

| Column Name | Type | Required | Description |
|-------------|------|----------|-------------|
| Date of Request | Date (YYYY-MM-DD) | Yes | Date the PO was placed |
| Type of Season | Text | Yes | Summer / Winter / Fall / Spring |
| Product Name | Text | Yes | Name of the product requested |
| Quantity of Product | Number (Integer) | Yes | Quantity requested by distributor |

### Factory Production Report Excel

| Column Name | Type | Required | Description |
|-------------|------|----------|-------------|
| Date of Report | Date (YYYY-MM-DD) | Yes | Date of production report |
| Product Name | Text | Yes | Name of the product produced |
| Amount of Product Created | Number (Integer) | Yes | Quantity produced |

---

## 8. Comparison Report Output

| Product Name | Requested Qty | Produced Qty | Completion % | Status |
|--------------|---------------|--------------|--------------|--------|
| Product A | 1000 | 750 | 75% | Partial |
| Product B | 500 | 500 | 100% | Complete |
| Product C | 300 | 0 | 0% | Missing |

**Status Logic:**
- **Complete:** Completion % ≥ 100%
- **Partial:** 0% < Completion % < 100%
- **Missing:** Completion % = 0%

---

## 9. Tech Stack Recommendation

| Component | Technology |
|-----------|------------|
| Backend Framework | Python (Flask or FastAPI) |
| Frontend | HTML, CSS, JavaScript (Bootstrap 5) |
| Data Processing | Pandas (Python) |
| File Storage | Local filesystem (or S3/GCS for cloud) |
| Visualization | Chart.js or Plotly |
| Deployment | Docker + Docker Compose |
| Web Server | Nginx (reverse proxy) |

---

## 10. Release Milestones

| Milestone | Description | Timeline |
|-----------|-------------|----------|
| **MVP v1.0** | Core upload + comparison functionality | Week 1-2 |
| **v1.1** | Enhanced UI, progress bars, charts | Week 3 |
| **v1.2** | Public deployment, Docker setup | Week 4 |
| **v2.0** | Authentication, multi-user support | Future |

---

## 11. Success Metrics

- Number of factories onboarded
- Upload success rate
- Dashboard load time
- User satisfaction (feedback form)
- Data accuracy (manual spot-check)

---

*Document prepared by the Data Engineering Team | June 2026*