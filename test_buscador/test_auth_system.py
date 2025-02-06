import unittest
import jwt
from datetime import datetime, timezone, UTC
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import secrets
import uuid
import json
import os
from typing import Optional, Dict, List

# Modelos
class TestUserConfig(BaseModel):
    max_requests_per_day: int = 1000
    allowed_models: List[str] = ["all"]
    allowed_services: List[str] = ["gpt4all", "ollama"]

class TestUser(BaseModel):
    id: str
    api_key: str
    created_at: datetime
    last_active: datetime
    request_count: Dict[str, int] = {}
    config: TestUserConfig

    @classmethod
    def create_test_user(cls) -> "TestUser":
        return cls(
            id=str(uuid.uuid4()),
            api_key=secrets.token_urlsafe(32),
            created_at=datetime.now(UTC),
            last_active=datetime.now(UTC),
            config=TestUserConfig()
        )

class ChatMessage(BaseModel):
    message: str
    model: str

class TestUserManager:
    def __init__(self):
        self.users: Dict[str, TestUser] = {}
        self.test_users_file = "data/test_users.json"
        self.load_test_users()
    
    def load_test_users(self):
        if os.path.exists(self.test_users_file):
            with open(self.test_users_file, 'r') as f:
                data = json.load(f)
                self.users = {
                    k: TestUser(**v) for k, v in data.items()
                }
    
    def save_test_users(self):
        os.makedirs(os.path.dirname(self.test_users_file), exist_ok=True)
        with open(self.test_users_file, 'w') as f:
            json.dump(
                {k: v.dict() for k, v in self.users.items()},
                f,
                default=str
            )
    
    def create_test_user(self) -> TestUser:
        user = TestUser.create_test_user()
        self.users[user.api_key] = user
        self.save_test_users()
        return user
    
    def get_user(self, api_key: str) -> Optional[TestUser]:
        return self.users.get(api_key)
    
    def update_user_activity(self, api_key: str):
        if user := self.users.get(api_key):
            today = datetime.now(UTC).date().isoformat()
            user.request_count[today] = user.request_count.get(today, 0) + 1
            user.last_active = datetime.now(UTC)
            self.save_test_users()

# Configuración de FastAPI para pruebas
app = FastAPI()
api_key_header = APIKeyHeader(name="X-API-Key")
SECRET_KEY = "test_secret_key"  # Solo para pruebas
user_manager = TestUserManager()

async def get_test_user(api_key: str = Security(api_key_header)) -> TestUser:
    if user := user_manager.get_user(api_key):
        today = datetime.now(UTC).date().isoformat()
        if user.request_count.get(today, 0) >= user.config.max_requests_per_day:
            raise HTTPException(
                status_code=429,
                detail="Daily request limit exceeded"
            )
        
        user_manager.update_user_activity(api_key)
        return user
        
    raise HTTPException(
        status_code=401,
        detail="Invalid API key"
    )

# Endpoints de prueba
@app.post("/api/test-user/new")
async def create_test_user():
    user = user_manager.create_test_user()
    return {
        "api_key": user.api_key,
        "config": user.config.dict()
    }

@app.post("/api/session/new")
async def create_session(
    model: str,
    service: str,
    test_user: TestUser = Depends(get_test_user)
):
    if "all" not in test_user.config.allowed_models and \
       model not in test_user.config.allowed_models:
        raise HTTPException(
            status_code=403,
            detail="Model not allowed for this test user"
        )
    
    session_id = str(uuid.uuid4())
    token_data = {
        "session_id": session_id,
        "user_id": test_user.id,
        "model": model,
        "service": service,
        "exp": datetime.now(timezone.utc).timestamp() + 86400  # 1 día
    }
    
    token = jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm="HS256"
    )
    
    return {
        "access_token": token,
        "session_id": session_id
    }

@app.get("/api/models")
async def get_models(test_user: TestUser = Depends(get_test_user)):
    # Simular lista de modelos para prueba
    return {
        "models": ["orca-mini-3b", "phi-2", "mistral-7b"]
    }

@app.post("/api/chat/{session_id}")
async def chat(
    session_id: str,
    message: ChatMessage,
    test_user: TestUser = Depends(get_test_user)
):
    # Simular respuesta de chat para prueba
    return {
        "response": "Respuesta de prueba",
        "session_id": session_id
    }

# Tests
class TestAuthSystem(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Asegurarnos que user_manager es el mismo que usa la app
        self.user_manager = user_manager
        
    def test_create_test_user(self):
        # Probar creación de usuario
        response = self.client.post("/api/test-user/new")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("api_key", data)
        
        # Verificar que podemos usar la API key
        headers = {"X-API-Key": data["api_key"]}
        models_response = self.client.get("/api/models", headers=headers)
        self.assertEqual(models_response.status_code, 200)
        
    def test_session_flow(self):
        # Crear usuario de prueba
        user_response = self.client.post("/api/test-user/new")
        api_key = user_response.json()["api_key"]
        headers = {"X-API-Key": api_key}
        
        # Iniciar sesión de chat
        params = {
            "model": "orca-mini-3b",
            "service": "gpt4all"
        }
        chat_response = self.client.post(
            "/api/session/new",
            headers=headers,
            params=params
        )
        self.assertEqual(chat_response.status_code, 200)
        session_data = chat_response.json()
        self.assertIn("access_token", session_data)
        
        # Probar chat con token
        chat_headers = {
            "Authorization": f"Bearer {session_data['access_token']}",
            "X-API-Key": api_key
        }
        message_response = self.client.post(
            f"/api/chat/{session_data['session_id']}",
            headers=chat_headers,
            json={
                "message": "Hola",
                "model": "orca-mini-3b"
            }
        )
        self.assertEqual(message_response.status_code, 200)
        
    def test_rate_limiting(self):
        # Crear usuario con límite bajo para pruebas
        response = self.client.post("/api/test-user/new")
        api_key = response.json()["api_key"]
        
        # Modificar el límite del usuario
        user = self.user_manager.get_user(api_key)
        user.config.max_requests_per_day = 2
        self.user_manager.save_test_users()
        
        headers = {"X-API-Key": api_key}
        
        # Primera petición - debería funcionar
        response1 = self.client.get("/api/models", headers=headers)
        self.assertEqual(response1.status_code, 200)
        
        # Segunda petición - debería funcionar
        response2 = self.client.get("/api/models", headers=headers)
        self.assertEqual(response2.status_code, 200)
        
        # Tercera petición - debería fallar por límite
        response3 = self.client.get("/api/models", headers=headers)
        self.assertEqual(response3.status_code, 429)

if __name__ == "__main__":
    unittest.main()
