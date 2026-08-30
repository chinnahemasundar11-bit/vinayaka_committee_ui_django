# 🚩 Vinayaka Chavithi Youth Committee Management & Financial ERP Engine

An enterprise-grade, high-performance, and modular **Festival Funds & Expenditure Management Microservice System** built with **Django 5.0+, Python 3.12, PostgreSQL, Bootstrap 5, Pytest, and Web Bluetooth API**.

Designed specifically for **100% Zero-Cost Operations** (utilizing free open-source frameworks, native web APIs, and local PostgreSQL databases without paid cloud dependencies).

---

## 🌟 Key High-Value Features (100% Free & Zero-Cost)

### 1. 📱 PWA Mobile Offline Cash Receipt Collector
- **Offline Cash Queue**: Treasurers can collect donations on mobile devices even in remote locations without internet connectivity.
- **Background Auto-Sync**: Receipts are stored in `IndexedDB`/`LocalStorage` and automatically synced to the server once online via `/funds/api/sync-offline-receipts/`.

### 2. 📺 Live Public LED TV Wall of Honor & Ticker
- **Public Portal**: Unauthenticated live display at `/public/wall-of-honor/` designed for festival ground LED TV walls.
- **Real-Time Ticker**: Animated count-up counter, dynamic donor leaderboard, and recent contribution ticker scrolling in real-time.

### 3. 🔍 Public Donor Self-Verification QR Portal
- **Verification Badge**: Public endpoint at `/public/verify-receipt/<receipt_number>/` allowing donors to scan receipt QR codes and verify official record authenticity.

### 4. 🧠 AI Expense Predictor & Budget Analytics
- **Predictive Analytics**: Accessible at `/administration/analytics/expense-predictor/` calculating daily donation velocity, revenue forecasts, and surplus/deficit recommendations.

### 5. 🧪 Pluggable QA Pytest Dashboard Microservice (`qa_dashboard`)
- **Pluggable Architecture**: Self-contained Django microservice app (`qa_dashboard`) that can be plugged into **ANY Django application** seamlessly.
- **PostgreSQL Test Logging**: Automatically logs test runs (`TestRun`), individual test assertions (`TestResult`), and severity issues (`TestIssue`) directly into PostgreSQL via custom Pytest plugin (`qa_dashboard/pytest_plugin.py`).
- **QA Dashboard UI**: Interactive dashboard at `/qa-dashboard/` with 1-click "Run Pytest Suite" button and REST API metrics endpoints.

### 6. 🔐 Toggleable Multi-Factor Authentication (MFA) & OTP Reset
- **Site Setting Radio Toggle**: Admin can switch MFA ON/OFF in Site Settings (`MFA_ENABLED`). When ON, login requires 6-digit OTP verification; when OFF, direct login is enabled.
- **OTP Password Reset**: 6-digit OTP verification flow for resetting forgotten passwords.

### 7. 🖨️ Mobile Bluetooth ESC/POS Thermal Receipt Printer Engine
- **Web Bluetooth & Web Serial Drivers**: Integrated directly into `receipt_print.html` for instant receipt printing on handheld 58mm/80mm ESC/POS thermal bluetooth printers.

### 8. 📊 Executive Financial Excel (.xlsx) & Meeting Audit PDF Exporter
- **Excel Spreadsheet Exporter**: Generates styled `.xlsx` itemized financial ledgers using Python `openpyxl` (`/reports/export/excel/`).
- **Executive Audit PDF Statement**: Printable meeting audit statement template (`/reports/export/audit-pdf/`).

---

## 🧩 Reusing the `qa_dashboard` Microservice in Other Django Apps

The `qa_dashboard` module is designed as an independent, pluggable Django app. To use it in any other Django project:

1. **Copy App Folder**: Copy the `qa_dashboard/` directory into your target Django project.
2. **Add to `INSTALLED_APPS`**:
   ```python
   INSTALLED_APPS = [
       ...
       'qa_dashboard',
   ]
   ```
3. **Register URL Route**:
   ```python
   # urls.py
   path('qa-dashboard/', include('qa_dashboard.urls')),
   ```
4. **Run Migrations**:
   ```bash
   python manage.py migrate qa_dashboard
   ```
5. **Run Pytest with Plugin**:
   ```bash
   pytest testcases/ -p qa_dashboard.pytest_plugin
   ```

---

## 🚀 Quickstart & Installation

### Option A: Local Development Setup

1. **Clone Repository & Set Environment**:
   ```bash
   git clone https://github.com/chinnahemasundar11-bit/vinayaka_committee_ui_django.git
   cd vinayaka_committee_ui_django
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Migrations & Seed Sample Data**:
   ```bash
   python manage.py migrate
   python manage.py seed_data
   ```

4. **Start Development Server**:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
   Access application at `http://127.0.0.1:8000/`. Default Superuser: `9876543210` / `admin123`.

---

### Option B: Production Docker Compose Setup

Run multi-container architecture with **Gunicorn**, **PostgreSQL 15**, and **Nginx**:

```bash
docker-compose up -d --build
```
- **Application URL**: `http://localhost/`
- **QA Test Dashboard**: `http://localhost/qa-dashboard/`
- **Public Wall of Honor**: `http://localhost/public/wall-of-honor/`

---

## 🧪 Running Automated Test Suites

### 1. Pytest Suite (with PostgreSQL Result Logging):
```bash
pytest testcases/ -p qa_dashboard.pytest_plugin
```

### 2. Standard Django Test Suite:
```bash
python manage.py test --keepdb
```

---

## 📄 License & Credits
Built for **Vinayaka Youth Committee Management**. Designed with **100% Free Open-Source Technologies**.
