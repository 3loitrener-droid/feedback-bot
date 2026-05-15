from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.models.period import Period
from app.schemas.period import PeriodRead, PeriodCreate

router = APIRouter(prefix="/periods", tags=["periods"])


@router.get("/", response_model=List[PeriodRead])
async def list_periods(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Period).order_by(Period.start_date.desc()))
    return result.scalars().all()


@router.post("/", response_model=PeriodRead)
async def create_period(
    body: PeriodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    period = Period(**body.model_dump())
    db.add(period)
    await db.commit()
    await db.refresh(period)
    return period


@router.patch("/{period_id}/activate")
async def activate_period(
    period_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Period).where(Period.period_id == period_id))
    period = result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Период не найден")
    period.is_active = True
    await db.commit()
    return {"ok": True}


@router.patch("/{period_id}/close")
async def close_period(
    period_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Period).where(Period.period_id == period_id))
    period = result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Период не найден")
    period.is_active = False
    await db.commit()
    return {"ok": True}
