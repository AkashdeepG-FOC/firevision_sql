# 🔥 FireVision Pro

> **AI-powered real-time fire & smoke detection platform** — PyQt5 desktop client + FastAPI backend + YOLOv8/ONNX inference engine.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend (Desktop Client) Setup](#frontend-desktop-client-setup)
- [Environment Variables](#environment-variables)
- [Database Migrations (Alembic)](#database-migrations-alembic)
- [Docker Deployment](#docker-deployment)
- [API Reference](#api-reference)
- [AI / ONNX Inference](#ai--onnx-inference)
- [Logging & Monitoring](#logging--monitoring)
- [Security](#security)
- [CI/CD](#cicd)
- [Contributing](#contributing)

---

## Overview

FireVision Pro is a production-grade fire and smoke detection system that combines:

- **Real-time CCTV stream analysis** via an ONNX-accelerated YOLOv8 model
- **A PyQt5 desktop application** for live viewing, alert management, and camera configuration
- **A FastAPI REST backend** with JWT authentication, role-based access control, and MySQL persistence
- **Structured loguru logging** with daily rotation, error tracing, and a dedicated security audit trail

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Desktop Client (PyQt5)                 │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │  Login UI    │  │ Camera View  │  │ Alert Manager │ │
│  │ (login_      │  │ (widgets.py) │  │ (alerts_      │ │
│  │  dialog.py)  │  │              │  │  manager.py)  │ │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘ │
│         │                 │                  │         │
│         └────────────── REST API ────────────┘         │
│                           │                            │
│         ┌─────────────────▼──────────────────┐         │
│         │   Multiprocess Camera Pipeline      │         │
│         │   (app/camera/multiprocess_         │         │
│         │    pipeline.py)                     │         │
│         └─────────────────┬──────────────────┘         │
│                           │ frames (Queue)              │
│         ┌─────────────────▼──────────────────┐         │
│         │   ONNX Detector (app/ai/            │         │
│         │   onnx_detector.py)                 │         │
│         └────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
                            │ HTTPS / REST
┌───────────────────────────▼─────────────────────────────┐
│                  FastAPI Backend                         │
│                                                         │
│  /api/auth    → JWT login + refresh token rotation      │
│  /api/users   → RBAC user management                    │
│  /api/cameras → Camera CRUD                             │
│  /api/alerts  → Fire alert lifecycle management         │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  MySQL 8.0  (Alembic-managed schema)             │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop Client | Python 3.11, PyQt5 |
| AI Inference | YOLOv8 (Ultralytics), ONNX Runtime |
| Backend API | FastAPI, Uvicorn |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Database | MySQL 8.0, SQLAlchemy ORM, Alembic |
| Logging | Loguru (structured, rotating, async) |
| Rate Limiting | slowapi |
| Containerisation | Docker, Docker Compose |
| CI/CD | GitHub Actions |

---

## Project Structure

```
firevision_sql/
├── backend/                   # FastAPI REST API
│   ├── core/
│   │   ├── config.py          # Pydantic Settings (reads .env)
│   │   ├── database.py        # SQLAlchemy engine + session
│   │   ├── security.py        # JWT creation, bcrypt hashing
│   │   └── logger.py          # Loguru configuration (NEW)
│   ├── models/
│   │   └── models.py          # SQLAlchemy ORM models + indexes
│   ├── schemas/
│   │   └── schemas.py         # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py            # Login + refresh token endpoints
│   │   ├── users.py           # User CRUD + get_current_user dep
│   │   ├── cameras.py         # Camera CRUD
│   │   └── alerts.py          # Alert lifecycle
│   ├── alembic/               # DB migration scripts
│   ├── logs/                  # Runtime log files (auto-created)
│   ├── main.py                # App factory, middleware, routes
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env                   # Secret config (NOT in git)
│   └── .env.example           # Template for new installs
│
├── software/                  # PyQt5 Desktop Client
│   ├── app/
│   │   ├── ai/
│   │   │   ├── onnx_detector.py   # ONNX inference engine
│   │   │   └── export_yolo.py     # YOLOv8 → ONNX export helper
│   │   ├── camera/
│   │   │   └── multiprocess_pipeline.py  # GIL-free frame capture
│   │   ├── config/
│   │   │   └── settings.py        # Client config loader
│   │   └── ui/
│   │       ├── login_dialog.py    # Modern login UI
│   │       ├── widgets.py         # Camera/alert widgets
│   │       └── camera_location_manager.py
│   ├── main.py                # Application entry point
│   └── requirements.txt
│
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI pipeline
├── docker-compose.yml         # Full-stack orchestration
├── run_backend.bat            # Windows quick-start script
└── run_software.bat           # Windows desktop launcher
```

---

## Quick Start

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11+ |
| MySQL Server | 8.0+ |
| Git | any |
| Docker + Compose | optional (for containerised deploy) |

---

### Backend Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/firevision_sql.git
cd firevision_sql

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# 3. Install backend dependencies
cd backend
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your database credentials and secret keys

# 5. Create the MySQL database
mysql -u root -p -e "CREATE DATABASE firevision CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 6. Run Alembic migrations
alembic upgrade head

# 7. (Optional) Seed initial data
python seed_db.py

# 8. Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:  
- **Swagger UI**: http://localhost:8000/api/docs  
- **ReDoc**: http://localhost:8000/api/redoc  
- **Health check**: http://localhost:8000/health  

---

### Frontend (Desktop Client) Setup

```bash
# From the project root
cd software

# Install dependencies
pip install -r requirements.txt

# Ensure backend URL is configured in software/.env
# BACKEND_URL=http://localhost:8000

# Launch the desktop app
python main.py
```

> **ONNX Acceleration**: If you have a custom `best_m.pt` YOLOv8 model, export it to ONNX before first run:
> ```bash
> python app/ai/export_yolo.py
> ```

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in all values before starting the backend.

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | MySQL connection string | `mysql+mysqlconnector://root:@localhost:3306/firevision` |
| `SECRET_KEY` | JWT access token signing secret | *(must change)* |
| `REFRESH_TOKEN_SECRET_KEY` | JWT refresh token signing secret | *(must change)* |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000,...` |
| `RATE_LIMIT_LIMIT` | Global rate limit | `60/minute` |

> ⚠️ **Never commit your `.env` file.** It is listed in `.gitignore`.

Generate strong secrets with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Database Migrations (Alembic)

```bash
cd backend

# Apply all pending migrations
alembic upgrade head

# Create a new migration after changing models.py
alembic revision --autogenerate -m "describe your change"

# Rollback one step
alembic downgrade -1

# View migration history
alembic history --verbose
```

---

## Docker Deployment

The full stack (MySQL + FastAPI) can be launched with a single command:

```bash
# From the project root
docker compose up --build -d
```

> ⚠️ Update the `SECRET_KEY` and `REFRESH_TOKEN_SECRET_KEY` values in `docker-compose.yml` (or inject via environment) before deploying to production.

| Service | Port | Description |
|---|---|---|
| `firevision_db` | 3306 | MySQL 8.0 database |
| `firevision_api` | 8000 | FastAPI REST backend |

**Useful commands:**
```bash
# View running containers
docker compose ps

# Stream API logs
docker compose logs -f web

# Stop everything
docker compose down

# Stop and remove volumes (⚠️ deletes DB data)
docker compose down -v
```

---

## API Reference

Full interactive documentation is available at `/api/docs` (Swagger UI).

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/token` | Public | Login — returns access + refresh tokens |
| `POST` | `/api/auth/refresh` | Public | Rotate refresh token |
| `POST` | `/api/users/` | Public | Register a new user |
| `GET` | `/api/users/me` | Bearer | Get current user profile |
| `GET` | `/api/users/` | Bearer | List all users |
| `DELETE` | `/api/users/{id}` | Admin | Delete a user |
| `POST` | `/api/cameras/` | Bearer | Register a camera |
| `GET` | `/api/cameras/` | Bearer | List cameras (admin sees all) |
| `GET` | `/api/cameras/{id}` | Bearer | Get camera details |
| `DELETE` | `/api/cameras/{id}` | Bearer/Admin | Delete a camera |
| `POST` | `/api/alerts/` | Bearer | Create fire alert |
| `GET` | `/api/alerts/` | Bearer | List alerts (filterable) |
| `PATCH` | `/api/alerts/{id}` | Bearer | Update alert status |
| `GET` | `/health` | Public | Health check |

---

## AI / ONNX Inference

FireVision uses **YOLOv8** for fire and smoke detection, exported to **ONNX** for hardware-agnostic, high-performance inference via `onnxruntime`.

**Export your model:**
```bash
python software/app/ai/export_yolo.py
# Outputs: software/best_m.onnx
```

**Runtime providers** (auto-selected in priority order):
1. `TensorrtExecutionProvider` — NVIDIA TensorRT (best GPU performance)
2. `CUDAExecutionProvider` — NVIDIA CUDA
3. `CPUExecutionProvider` — CPU fallback (always available)

**Camera pipeline:**  
Frames are captured in a separate `multiprocessing.Process` (bypassing Python's GIL) and delivered to the UI thread via a `multiprocessing.Queue`. This prevents detection latency from blocking the UI.

---

## Logging & Monitoring

All backend logs are written to `backend/logs/` (auto-created on startup).

| Log File | Level | Rotation | Retention |
|---|---|---|---|
| `firevision_YYYY-MM-DD.log` | DEBUG+ | Daily at midnight | 30 days |
| `errors_YYYY-MM-DD.log` | ERROR+ | 50 MB | 90 days |
| `security_audit_YYYY-MM-DD.log` | WARNING (SECURITY tag) | 10 MB | 365 days |

**Security audit events logged automatically:**
- `LOGIN_SUCCESS` / `LOGIN_FAILED` — every authentication attempt with client IP
- `TOKEN_REFRESH_FAILED` — invalid or expired refresh token usage
- `AUTH_FAILURE` — any 401/403 HTTP response (via request middleware)

**Live log streaming:**
```bash
# Tail the current application log
Get-Content backend\logs\firevision_$(Get-Date -Format 'yyyy-MM-dd').log -Wait

# Docker
docker compose logs -f web
```

---

## Security

| Control | Implementation |
|---|---|
| Authentication | JWT Bearer tokens (access + refresh rotation) |
| Password storage | bcrypt via passlib |
| CORS | Whitelist-only via `CORS_ORIGINS` env var |
| Rate limiting | slowapi — configurable via `RATE_LIMIT_LIMIT` |
| HTTP security headers | `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy` |
| Role-based access | `admin` role required for destructive operations |
| Secret management | All secrets via `.env` — never hardcoded |
| Audit logging | Dedicated security audit log with 365-day retention |

---

## CI/CD

GitHub Actions pipeline (`.github/workflows/ci.yml`) runs automatically on every push/PR to `main`:

| Step | Tool |
|---|---|
| Linting | `flake8` |
| Type checking | `mypy` |
| Unit tests | `pytest` |
| Docker build validation | `docker build` |

---

## Contributing

1. Fork the repository and create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes and add tests where applicable
3. Run the linter: `flake8 backend/`
4. Submit a pull request — CI must pass before merge

---

*FireVision Pro — Built for rapid, reliable fire detection at scale.*
