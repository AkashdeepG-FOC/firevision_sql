import time
import os
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from .routers import auth, users, cameras, alerts
from .core import database
from .models import models
from .core.config import settings
from .core.logger import get_logger, log_security_event

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ─── Module logger ─────────────────────────────────────────────────────────────
log = get_logger("firevision.main")

# ─── App initialisation ────────────────────────────────────────────────────────
app = FastAPI(
    title="FireVision API",
    version="1.0.0",
    description="Production-grade fire detection and alert management API.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

log.info("FireVision API starting up – environment loaded from .env")

# ─── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_LIMIT])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

log.info(f"CORS origins configured: {settings.cors_origins_list}")

# ─── Security Headers Middleware ───────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
    return response

# ─── Request Logging & Timing Middleware ───────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"

    response = await call_next(request)

    elapsed_ms = (time.perf_counter() - start) * 1000
    status = response.status_code

    level = "INFO"
    if status >= 500:
        level = "ERROR"
    elif status >= 400:
        level = "WARNING"

    log.log(
        level,
        f"{request.method} {request.url.path} → {status} "
        f"[{elapsed_ms:.1f}ms] ip={client_ip}",
    )

    # Flag suspicious 401/403 patterns to the security audit log
    if status in (401, 403):
        log_security_event(
            "AUTH_FAILURE",
            f"ip={client_ip} method={request.method} path={request.url.path} status={status}",
        )

    return response

# ─── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,    prefix="/api/auth",    tags=["Authentication"])
app.include_router(users.router,   prefix="/api/users",   tags=["Users"])
app.include_router(cameras.router, prefix="/api/cameras", tags=["Cameras"])
app.include_router(alerts.router,  prefix="/api/alerts",  tags=["Alerts"])

log.info("All routers registered: auth, users, cameras, alerts")

# ─── Static Files ──────────────────────────────────────────────────────────────
static_path = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_path, exist_ok=True)

dashboard_path = os.path.join(static_path, "dashboard")
os.makedirs(dashboard_path, exist_ok=True)

app.mount("/dashboard", StaticFiles(directory=dashboard_path, html=True), name="dashboard")

# ─── Basic Routes ──────────────────────────────────────────────────────────────
@app.get("/admin")
@app.get("/admin/")
async def serve_dashboard():
    return FileResponse(os.path.join(dashboard_path, "index.html"))

@app.get("/", tags=["Health"])
def read_root():
    return {"message": "Welcome to FireVision API", "version": "1.0.0"}

@app.get("/health", tags=["Health"])
def health_check():
    log.debug("Health check requested")
    return {"status": "ok", "service": "FireVision API", "version": "1.0.0"}

# ─── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = "".join(traceback.format_exception(None, exc, exc.__traceback__))
    log.error(
        f"Unhandled exception on {request.method} {request.url.path}\n{tb}"
    )
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )

# ─── Startup / Shutdown Events ─────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    log.success("🔥 FireVision API is live and ready to serve requests.")

@app.on_event("shutdown")
async def shutdown_event():
    log.info("FireVision API shutting down gracefully.")
