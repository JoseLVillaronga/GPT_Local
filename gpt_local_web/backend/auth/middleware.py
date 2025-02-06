from datetime import datetime, timedelta, UTC
from fastapi import Depends, HTTPException, Header, Security, FastAPI, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
import jwt
from typing import Optional
from .manager import TestUserManager
from .models import TestUser

# Configuración
SECRET_KEY = "your-secret-key-here"  # TODO: Mover a configuración
ALGORITHM = "HS256"

user_manager = TestUserManager()

app = FastAPI()

origins = [
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_test_user(request: Request) -> Optional[TestUser]:
    x_api_key = request.headers.get('X-API-Key')
    
    if not x_api_key:
        raise HTTPException(status_code=401, detail="No API key provided")
    
    user = user_manager.get_user(x_api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if not user_manager.is_user_valid(x_api_key):
        raise HTTPException(status_code=403, detail="API key has expired")
    
    requests_today = user_manager.get_requests_today(x_api_key)
    max_requests = user_manager.get_max_requests_per_day(x_api_key)
    
    if requests_today >= max_requests:
        raise HTTPException(status_code=429, detail="Daily request limit exceeded")
    
    user_manager.update_user_activity(x_api_key)
    return user

def create_access_token(data: dict) -> str:
    """Crear token JWT para una sesión"""
    to_encode = data.copy()
    to_encode.update({
        "exp": datetime.now(UTC).timestamp() + 86400  # 1 día
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[dict]:
    """Verificar y decodificar token JWT"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )
