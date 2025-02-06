from datetime import datetime, timezone
import secrets
from typing import Optional
from pydantic import BaseModel

class TestUserConfig(BaseModel):
    """Configuración para usuarios de prueba"""
    valid_days: int = 30
    max_requests_per_day: int = 100

class TestUser(BaseModel):
    """Usuario de prueba"""
    api_key: str
    created_at: datetime
    last_active: Optional[datetime] = None
    request_count: int = 0
    config: TestUserConfig

    @classmethod
    def create_test_user(cls) -> "TestUser":
        return cls(
            api_key=secrets.token_urlsafe(32),
            created_at=datetime.now(timezone.utc),
            config=TestUserConfig()
        )

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        # Convertir las fechas a formato ISO
        if data.get('created_at'):
            data['created_at'] = data['created_at'].isoformat()
        if data.get('last_active'):
            data['last_active'] = data['last_active'].isoformat()
        return data

class ChatMessage(BaseModel):
    message: str
    model: str
