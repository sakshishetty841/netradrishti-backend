# NETRADRISHTI — AI-Assisted Diabetic Retinopathy Screening API Backend

NetraDrishti is a production-style Python FastAPI backend providing AI-assisted diabetic retinopathy screening, explainable Grad-CAM heatmaps, offline synchronization, role-based referral workflows (ASHA Worker $\rightarrow$ PHC Doctor $\rightarrow$ Specialist), audit logging, area analytics, and automated PDF report generation.

---

## 🚀 Quick Reference for API / Frontend Developers

| Key | Value |
|---|---|
| **Backend Framework** | Python 3.9+ / FastAPI |
| **Backend Entry Point** | `app/main.py` (`app.main:app`) |
| **Default Server Host** | `0.0.0.0` or `127.0.0.1` |
| **Default Server Port** | **8000** (`http://localhost:8000`) |
| **Interactive API Docs (Swagger UI)** | `http://localhost:8000/docs` |
| **ReDoc OpenAPI Documentation** | `http://localhost:8000/redoc` |
| **Database ORM** | SQLAlchemy 2.0+ with Alembic migrations |
| **Default Local DB** | SQLite (`netradrishti.db`) — Auto-seeded on startup |
| **AI Model Checkpoint** | `ml/models/dr_model_best.pth` (PyTorch EfficientNet-B0) |

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.9 or higher
- `pip` package manager
- `virtualenv` (recommended)

### 2. Environment Setup
```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On macOS / Linux:
source venv/bin/activate
# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### 3. Environment Variables Configuration (`.env`)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Key configurable variables in `.env`:
* `DATABASE_URL`: `sqlite:///./netradrishti.db` (Default) or `postgresql://user:pass@localhost:5432/netradrishti`
* `SECRET_KEY`: JWT authentication signing key
* `CORS_ORIGINS`: Allowed origins (Defaults to `http://localhost:3000`, `http://localhost:5173`, `http://127.0.0.1:5173`)
* `MEDIA_DIR`: Directory for storing fundus uploads and generated heatmaps (`./media`)

---

## 🗄️ Database & Seeding Setup

### Automatic Startup Seeding
On application startup, the backend automatically initializes database tables via SQLAlchemy `Base.metadata.create_all` and seeds default screening centers and demo users.

### Demo Seed Accounts

| Role | User ID | Password | Access / Permissions |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Full system administration & audit logs |
| **ASHA Worker** | `asha` | `asha123` | Field screenings, patient creation, image upload |
| **PHC Doctor** | `doctor` | `doctor123` | Primary health center review & referral routing |
| **Specialist** | `specialist` | `specialist123` | Ophthalmology specialist referral queue |

### Alembic Database Migrations (For Production / Schema Changes)
If transitioning to PostgreSQL or modifying database models in `app/db/models/`:
```bash
# Generate a new migration revision
alembic revision --autogenerate -m "Describe schema changes"

# Upgrade database to latest revision
alembic upgrade head
```

---

## 🏃 Starting the Server

To start the FastAPI backend development server:
```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📡 Backend API Service Catalog for Developers

The frontend or API developer can integrate with the following registered backend API routers:

### 1. DR Screening & Inference
* **`POST /predict`** *(Legacy / Primary Screening Endpoint)*
  * Accepts multipart file `image` and form data `eye` (`LEFT` | `RIGHT`).
  * Returns 5-class DR probabilities (`No DR`, `Mild NPDR`, `Moderate NPDR`, `Severe NPDR`, `Proliferative DR`), confidence score, quality score, Grad-CAM heatmap URL, clinical recommendation, and `requires_human_review` flag.

### 2. Authentication & User Management
* **`POST /auth/login`**: Authenticates user credentials and returns JWT `access_token` and `refresh_token`.
* **`POST /auth/logout`**: Invalidates user session and logs audit trail.
* **`GET /auth/me`**: Fetches profile of currently authenticated user.
* **`POST /auth/forgot-password`** & **`POST /auth/verify-otp`**: Password recovery workflow.

### 3. Screenings & Clinical Workflow
* **`GET /screenings`**: List screening records with filtering by status/district.
* **`POST /screenings`**: Submit a new patient screening.
* **`GET /screenings/{id}`**: Fetch detailed screening record with AI analysis and heatmap.

### 4. Patients & Referrals
* **`GET /patients`** & **`POST /patients`**: Patient registry and search.
* **`POST /referrals`**: Route high-risk cases to PHC doctors or Specialists.
* **`GET /specialists/queue`**: Ophthalmology specialist review queue.

### 5. Analytics, Reports & Sync
* **`GET /analytics/summary`**: Regional DR prevalence and screening statistics.
* **`GET /reports/{screening_id}/pdf`**: Download automated PDF clinical report.
* **`POST /sync/push`**: Idempotent offline screening queue synchronization.
* **`GET /health`**: System health check & AI model readiness status.

---

## 🧪 Testing

To execute the automated backend test suite:
```bash
PYTHONPATH=. pytest
```

---

## 📦 What to Commit & Send to API Developer

### Files to Commit to GitHub:
- `app/` directory (all backend source code)
- `ml/` directory (dataset loaders, evaluation scripts, PyTorch models)
- `alembic/` & `alembic.ini`
- `tests/`
- `.env.example`
- `.gitignore`
- `Dockerfile` & `docker-compose.yml`
- `pytest.ini`
- `requirements.txt`
- `README.md`

### Files NOT to Commit (Handled by `.gitignore`):
- `venv/`
- `.env`
- `*.db` (e.g., `netradrishti.db`)
- `media/` (uploaded images and generated heatmaps)
- `__pycache__/` & `.pytest_cache/`
