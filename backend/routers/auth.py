from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..core import database, security, config
from ..core.logger import get_logger, log_security_event
from ..models import models
from ..schemas import schemas

router = APIRouter()
log = get_logger("firevision.auth")


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    log.info(f"Login attempt – username={form_data.username!r} ip={client_ip}")

    user = db.query(models.User).filter(
        or_(
            models.User.email == form_data.username,
            models.User.name == form_data.username,
        )
    ).first()

    if not user or not security.verify_password(form_data.password, user.password_hash):
        log_security_event(
            "LOGIN_FAILED",
            f"ip={client_ip} username={form_data.username!r} – bad credentials",
        )
        log.warning(f"Failed login for username={form_data.username!r} ip={client_ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = security.create_refresh_token(data={"sub": user.email})

    log.success(f"Login successful – user={user.email} ip={client_ip}")
    log_security_event("LOGIN_SUCCESS", f"ip={client_ip} user={user.email}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=schemas.Token)
async def refresh_access_token(
    request: Request,
    refresh_token: str,
    db: Session = Depends(database.get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    email = security.verify_refresh_token(refresh_token)

    if not email:
        log_security_event(
            "TOKEN_REFRESH_FAILED",
            f"ip={client_ip} – invalid or expired refresh token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=config.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    new_refresh_token = security.create_refresh_token(data={"sub": user.email})

    log.info(f"Token refreshed – user={user.email} ip={client_ip}")

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }
