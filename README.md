# Compliance and Audit Automation Suite for Security Operations

A full-stack, enterprise-grade compliance automation platform built for physical security firms, manned guarding operations, and security contractors. The system guarantees that officer deployments, attendance logs, contractual requirements, labor laws, insurance rules, and audit activities are compliant, traceable, and tamper-evident through SHA-256 cryptographic hash-chaining.

---

## 🛡️ Architecture & Core Objectives

The platform provides a complete, auditable lifecycle:
$$\text{USER} \rightarrow \text{SITE} \rightarrow \text{SHIFT} \rightarrow \text{ASSIGNMENT} \rightarrow \text{CHECK-IN} \rightarrow \text{CHECK-OUT} \rightarrow \text{COMPLIANCE ENGINE} \rightarrow \text{EXCEPTION} \rightarrow \text{RESOLUTION} \rightarrow \text{AUDIT LEDGER} \rightarrow \text{REPORT}$$

### Architectural Highlights
- **Layered Backend Architecture:** Built with FastAPI, SQLAlchemy 2.x, Pydantic v2, and Alembic migrations. Domain logic isolated into Repository and Service layers.
- **Cryptographic Audit Ledger:** Immutable, append-only audit trail chained using parent SHA-256 hashes:
  $$\text{record\_hash} = \text{SHA256}(\text{previous\_hash} + \text{entity\_type} + \text{entity\_id} + \text{action} + \text{performed\_by} + \text{timestamp} + \text{metadata})$$
  Provides instant mathematical verification via `/api/audit/integrity` to detect any database tampering or unauthorized alterations.
- **Compliance Rules Engine:** Evaluates maximum daily hours, weekly hour caps, minimum mandatory rest gaps between consecutive shifts, overtime thresholds, and duplicate/conflicting shift assignments.
- **Geofence & QR Validation:**
  - **Haversine Distance Algorithm:** Validates guard check-in location against site GPS latitude/longitude and permitted boundary radius in meters.
  - **Secure Site QR Tokens:** Eliminates proxy check-ins by verifying cryptographically unique tokens physically posted at facility entry gates.
- **Automated Missed-Shift Detection:** Background scheduler continuously monitors scheduled shifts. If a guard fails to check in within the shift start time plus allowed grace threshold, the shift is marked as `MISSED`, a critical exception is raised, an immutable audit event is recorded, and supervisor alerts are dispatched.
- **Live Real-time WebSockets:** Pushes attendance updates, new exceptions, and notifications over `/ws/compliance` and `/ws/notifications` with seamless fallback.
- **Multi-Format Regulatory Reporting:** Generates signed compliance dossiers, incident records, and attendance logs exportable to JSON, CSV, and professional ReportLab PDF formats.

---

## 👥 Role-Based Access Control (RBAC) & Demo Accounts

All demo accounts are pre-seeded and use the default password: **`Password123!`**

| Role | Demo Email | Password | Allowed Capabilities |
| :--- | :--- | :--- | :--- |
| **ADMIN** | `admin@security-ops.com` | `Password123!` | Full user/site/shift administration, rule configuration, policy override, full audit inspection, report generation. |
| **SUPERVISOR** | `supervisor.jenkins@security-ops.com` | `Password123!` | View sites, manage guard assignments, monitor live attendance, resolve operational exceptions, review site compliance scores. |
| **AUDITOR** | `auditor.rostova@security-ops.com` | `Password123!` | Read-only inspection of users, sites, attendance, and exceptions. Cryptographic hash-chain integrity verification, regulatory report exports. |
| **GUARD** | `guard.001@security-ops.com` | `Password123!` | View personal shift schedule, acquire browser GPS coordinates, scan site QR code, perform check-in and check-out, view own compliance records. |

*Additional Seeded Guards:* `guard.002@security-ops.com` through `guard.005@security-ops.com`.

---

## 🚀 Running Locally from VS Code (Windows PowerShell)

### Prerequisites
- **Python 3.12+**
- **Node.js v18+ & npm**
- **PostgreSQL** (Optional: local PostgreSQL service or Docker. If PostgreSQL is not active, the backend automatically initializes an isolated SQLite database for instant zero-friction development).

---

### Step 1: Open Terminal in Workspace Root
Open VS Code in `project 2`:
```powershell
cd "c:\Users\Rathesh\OneDrive\Desktop\project\project 2"
```

---

### Step 2: Backend Setup
1. **Activate the Virtual Environment:**
   ```powershell
   # If .venv is already present:
   .\.venv\Scripts\Activate.ps1
   ```
   *(If creating a new virtual environment: `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1`)*

2. **Install Dependencies:**
   ```powershell
   cd backend
   pip install -r requirements.txt
   ```

3. **Run Alembic Migrations:**
   ```powershell
   python -m alembic upgrade head
   ```

4. **Seed Database with Demo Data (Idempotent):**
   ```powershell
   python -m app.database.seed
   ```

5. **Start FastAPI Backend Server:**
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   - **Interactive API Documentation (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
   - **Health Check Endpoint:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

### Step 3: Frontend Setup (In a New Terminal)
1. **Open Frontend Directory:**
   ```powershell
   cd "c:\Users\Rathesh\OneDrive\Desktop\project\project 2\frontend"
   ```

2. **Install Node Packages:**
   ```powershell
   npm install
   ```

3. **Start Vite Development Server:**
   ```powershell
   npm run dev
   ```
   - **Web Application URL:** [http://localhost:5173](http://localhost:5173)

---

## 🐳 Running with Docker Compose

To run the entire suite (PostgreSQL database, FastAPI backend, and React SPA frontend) in containerized mode:

```powershell
docker compose up --build
```

- **Frontend Application:** [http://localhost:5173](http://localhost:5173)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **API Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Running Automated Tests

To execute the full test suite covering Authentication, MFA, RBAC permissions, Site geofences, Assignment rules, Attendance check-in/out, SHA-256 hash chaining, and Report generation:

```powershell
cd backend
python -m pytest -v
```

Output:
```text
tests/test_assignments.py::test_valid_assignment_creation PASSED
tests/test_assignments.py::test_duplicate_same_shift_assignment_rejected PASSED
tests/test_assignments.py::test_admin_override_on_assignment PASSED
tests/test_attendance.py::test_guard_valid_checkin_and_checkout PASSED
tests/test_attendance.py::test_invalid_qr_code_rejected PASSED
tests/test_attendance.py::test_guard_cannot_checkin_other_guards_assignment PASSED
tests/test_audit_chain.py::test_audit_log_creation_and_integrity PASSED
tests/test_audit_chain.py::test_audit_tamper_detection PASSED
tests/test_auth.py::test_successful_login PASSED
tests/test_auth.py::test_invalid_password_login PASSED
tests/test_auth.py::test_nonexistent_user_login PASSED
tests/test_auth.py::test_mfa_flow PASSED
tests/test_rbac.py::test_admin_can_create_user PASSED
tests/test_rbac.py::test_supervisor_forbidden_to_create_user PASSED
tests/test_rbac.py::test_auditor_forbidden_to_create_site PASSED
tests/test_rbac.py::test_guard_cannot_inspect_other_guards PASSED
tests/test_reporting.py::test_generate_and_export_reports PASSED
tests/test_sites.py::test_create_and_fetch_site PASSED
tests/test_sites.py::test_site_qr_code_generation PASSED
tests/test_sites.py::test_site_compliance_score PASSED

======================= 20 passed in 2.84s =======================
```

---

## 📂 Project Structure

```text
project 2/
├── backend/
│   ├── alembic/                 # Alembic migration environment & versions
│   │   ├── versions/            # Database schema revision scripts
│   │   └── env.py
│   ├── app/
│   │   ├── api/                 # API routing and dependency injection
│   │   │   ├── routes/          # Domain endpoints (auth, users, sites, shifts, etc.)
│   │   │   ├── api.py           # Master API aggregator router
│   │   │   └── deps.py          # JWT authentication & strict RBAC dependencies
│   │   ├── core/                # System configuration, security, & sanitized logging
│   │   │   ├── config.py
│   │   │   ├── logging_config.py
│   │   │   └── security.py      # Password hashing, JWT, MFA, SHA-256 hash chaining
│   │   ├── database/            # Database session engine & idempotent seed script
│   │   │   ├── seed.py
│   │   │   └── session.py
│   │   ├── middleware/          # Audit HTTP logging & structured error envelopes
│   │   │   ├── audit_middleware.py
│   │   │   └── error_handler.py
│   │   ├── models/              # Declarative SQLAlchemy models (User, Site, Shift, Audit, etc.)
│   │   ├── repositories/        # Clean database querying & persistence layer
│   │   ├── schemas/             # Pydantic v2 schemas and validation contracts
│   │   ├── services/            # Business logic: compliance engine, attendance, audit chain
│   │   │   ├── assignment_service.py
│   │   │   ├── attendance_service.py
│   │   │   ├── audit_service.py
│   │   │   ├── auth_service.py
│   │   │   ├── compliance_engine.py
│   │   │   ├── notification_service.py
│   │   │   ├── report_service.py
│   │   │   ├── scheduler_service.py
│   │   │   ├── site_service.py
│   │   │   ├── user_service.py
│   │   │   └── websocket_manager.py
│   │   ├── utils/               # Haversine GPS geo calculation, QR generation, ReportLab PDF
│   │   └── main.py              # FastAPI application root & WebSocket endpoints
│   ├── tests/                   # Pytest test suite
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/common/   # Badge, Card, ScoreRing, Modal, Table
│   │   ├── context/             # AuthContext with session & role helpers
│   │   ├── hooks/               # useWebSocket hook with auto-reconnection
│   │   ├── layouts/             # Responsive enterprise AppLayout with live indicator
│   │   ├── pages/               # Enterprise dashboard pages (Admin, Supervisor, Auditor, Guard)
│   │   │   ├── AdminDashboard.jsx
│   │   │   ├── AssignmentsPage.jsx
│   │   │   ├── AttendancePage.jsx
│   │   │   ├── AuditorDashboard.jsx
│   │   │   ├── AuditPage.jsx
│   │   │   ├── CompliancePage.jsx
│   │   │   ├── GuardDashboard.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── MFAVerify.jsx
│   │   │   ├── ReportsPage.jsx
│   │   │   ├── ShiftsPage.jsx
│   │   │   ├── SitesPage.jsx
│   │   │   ├── SupervisorDashboard.jsx
│   │   │   └── UsersPage.jsx
│   │   ├── routes/              # Protected route routing definitions
│   │   ├── services/            # Centralized Axios client
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.js
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

## 🔒 Security Best Practices Implemented
1. **Never Log Sensitive Data:** Passwords, JWT secrets, and MFA TOTP secrets are excluded from logs using structured log sanitizers.
2. **Immutable Audit Chaining:** Audit records cannot be altered or removed through API routes. Altering any database cell causes `verify_integrity()` to fail and pinpoint the exact tampered row ID.
3. **No Frontend Secrets:** All API keys and secrets reside in backend configuration.
4. **CORS Hardening:** Whitelist restricted to configured origins.
5. **No Blind Frontend Validation:** All labor constraints, GPS bounds, and QR tokens are verified server-side.
