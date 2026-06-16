from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from .routers import auth, users, cameras, alerts
from .core import database
from .models import models

# Create database tables (better to use migrations in production, but ok for now)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="FireVision API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(cameras.router, prefix="/api/cameras", tags=["Cameras"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])

# Static Files for Dashboard
static_path = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)

dashboard_path = os.path.join(static_path, "dashboard")
if not os.path.exists(dashboard_path):
    os.makedirs(dashboard_path)

app.mount("/dashboard", StaticFiles(directory=dashboard_path, html=True), name="dashboard")

@app.get("/admin")
@app.get("/admin/")
async def serve_dashboard():
    return FileResponse(os.path.join(dashboard_path, "index.html"))

@app.get("/")
def read_root():
    return {"message": "Welcome to FireVision API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "FireVision API"}

import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = "".join(traceback.format_exception(None, exc, exc.__traceback__))
    print(f"CRITICAL ERROR: {error_msg}")
    import datetime
    with open("backend_error.log", "a") as f:
        f.write(f"\n--- ERROR at {datetime.datetime.now()} ---\n")
        f.write(error_msg)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )
