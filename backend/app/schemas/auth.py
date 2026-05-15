from pydantic import BaseModel, EmailStr
import uuid


class MagicLinkRequest(BaseModel):
    email: str


class TelegramLinkRequest(BaseModel):
    telegram_id: int
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    role: str
    full_name: str
