from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.summary import Summary
from app.schemas.summary import SummaryRead
from app.services.summary import SummaryService

router = APIRouter(prefix="/summary", tags=["summary"])


@router.post("/generate")
async def generate_summary(
    employee_id: uuid.UUID,
    period_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Синхронно — ждём пока LLM закончит (бот ждёт результат)
    service = SummaryService(db)
    await service.generate(employee_id, period_id, current_user.user_id)
    return {"message": "Summary сгенерирован", "status": "done"}


@router.get("/", response_model=Optional[SummaryRead])
async def get_summary(
    employee_id: uuid.UUID,
    period_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Summary).where(
            Summary.employee_id == employee_id,
            Summary.period_id == period_id,
            Summary.manager_id == current_user.user_id,
            Summary.is_current == True,
        ).order_by(Summary.generated_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()
