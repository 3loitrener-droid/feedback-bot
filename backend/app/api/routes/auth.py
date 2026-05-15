from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import uuid

from app.db.session import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.core.security import create_access_token, create_magic_token, hash_token
from app.schemas.auth import MagicLinkRequest, TokenResponse, TelegramLinkRequest
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory magic link store (в prod — Redis)
_magic_links: dict[str, dict] = {}


@router.post("/magic-link")
async def request_magic_link(
    body: MagicLinkRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        # Не раскрываем, существует ли пользователь
        return {"message": "Если email зарегистрирован, на него отправлена ссылка"}

    token = create_magic_token()
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.magic_link_expire_minutes)
    _magic_links[token_hash] = {"user_id": str(user.user_id), "expires_at": expires_at}

    magic_url = f"{settings.app_url}/auth?token={token}"
    background_tasks.add_task(_send_magic_link_email, user.email, user.full_name, magic_url)

    if settings.environment == "development":
        return {"message": "Ссылка для входа (только в dev-режиме):", "magic_url": magic_url}
    return {"message": "Если email зарегистрирован, на него отправлена ссылка"}


@router.get("/verify", response_model=TokenResponse)
async def verify_magic_link(token: str, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(token)
    link_data = _magic_links.get(token_hash)
    if not link_data:
        raise HTTPException(status_code=400, detail="Невалидная или истёкшая ссылка")

    if datetime.now(timezone.utc) > link_data["expires_at"]:
        del _magic_links[token_hash]
        raise HTTPException(status_code=400, detail="Ссылка истекла")

    del _magic_links[token_hash]

    result = await db.execute(select(User).where(User.user_id == uuid.UUID(link_data["user_id"])))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    access_token = create_access_token(str(user.user_id), user.role)
    return TokenResponse(
        access_token=access_token,
        user_id=user.user_id,
        role=user.role,
        full_name=user.full_name,
    )


@router.post("/telegram-link", response_model=TokenResponse)
async def link_telegram(body: TelegramLinkRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    user.telegram_id = body.telegram_id
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(str(user.user_id), user.role)
    return TokenResponse(
        access_token=access_token,
        user_id=user.user_id,
        role=user.role,
        full_name=user.full_name,
    )


@router.post("/telegram-verify")
async def verify_by_telegram_id(telegram_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Telegram не привязан")

    access_token = create_access_token(str(user.user_id), user.role)
    return TokenResponse(
        access_token=access_token,
        user_id=user.user_id,
        role=user.role,
        full_name=user.full_name,
    )


class RegisterManagerRequest(BaseModel):
    full_name: str
    email: str
    role: str = "manager"


@router.post("/register", tags=["auth"])
async def register_user(
    body: RegisterManagerRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Создать нового пользователя (только admin). Потом он входит через magic link."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    user = User(
        user_id=uuid.uuid4(),
        full_name=body.full_name,
        email=body.email,
        role=body.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    return {"ok": True, "email": user.email, "role": user.role, "full_name": user.full_name}


async def _send_magic_link_email(email: str, name: str, url: str):
    print(f"[EMAIL] Magic link for {name} <{email}>: {url}")
