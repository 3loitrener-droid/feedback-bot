from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.models.criteria import CriteriaMatrix
from app.schemas.criteria import CriterionRead, CriterionCreate, CriterionUpdate

router = APIRouter(prefix="/criteria", tags=["criteria"])


@router.get("/", response_model=List[CriterionRead])
async def list_criteria(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(CriteriaMatrix).order_by(CriteriaMatrix.sort_order, CriteriaMatrix.criterion_name)
    if active_only:
        query = query.where(CriteriaMatrix.is_active == True)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=CriterionRead)
async def create_criterion(
    body: CriterionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    criterion = CriteriaMatrix(**body.model_dump())
    db.add(criterion)
    await db.commit()
    await db.refresh(criterion)
    return criterion


@router.patch("/{criterion_id}", response_model=CriterionRead)
async def update_criterion(
    criterion_id: uuid.UUID,
    body: CriterionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(CriteriaMatrix).where(CriteriaMatrix.criterion_id == criterion_id))
    criterion = result.scalar_one_or_none()
    if not criterion:
        raise HTTPException(status_code=404, detail="Критерий не найден")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(criterion, field, value)
    await db.commit()
    await db.refresh(criterion)
    return criterion


@router.delete("/{criterion_id}")
async def deactivate_criterion(
    criterion_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(CriteriaMatrix).where(CriteriaMatrix.criterion_id == criterion_id))
    criterion = result.scalar_one_or_none()
    if not criterion:
        raise HTTPException(status_code=404, detail="Критерий не найден")
    criterion.is_active = False
    await db.commit()
    return {"ok": True}
