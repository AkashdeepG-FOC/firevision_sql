from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, users, cameras, alerts, logs
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
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])

@app.get("/")
def read_root():
    return {"message": "Welcome to FireVision API"}

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
