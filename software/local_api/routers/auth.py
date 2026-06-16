from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth.auth_manager import AuthManager

router = APIRouter()
auth_manager = AuthManager()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(request: LoginRequest):
    """
    Local API Login endpoint.
    Attempts online login via Cloud API first, falls back to local SQLite if offline.
    """
    result = auth_manager.authenticate(request.username, request.password)
    
    if result["status"] == "success":
        return result
    elif result["status"] == "invalid_credentials":
        raise HTTPException(status_code=401, detail=result["message"])
    else:
        raise HTTPException(status_code=500, detail=result.get("message", "Authentication failed"))
