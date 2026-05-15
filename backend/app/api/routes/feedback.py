from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import date
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.feedback import Feedback, FeedbackCriterionMapping
from app.models.criteria import CriteriaMatrix
from app.models.employee import ManagerEmployeeVisibility
from app.schemas.feedback import (
    FeedbackCreate, FeedbackRead, FeedbackUpdate,
    FeedbackWithMappings, MappingCreate, MappingRead, MappingUpdate,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=FeedbackWithMappings)
async def create_feedback(
    body: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_employee_access(db, current_user, body.employee_id)

    status = "no_criterion" if not body.mappings else "draft"
    fb = Feedback(
        employee_id=body.employee_id,
        manager_id=current_user.user_id,
        period_id=body.period_id,
        feedback_date=body.feedback_date or date.today(),
        original_text=body.original_text,
        source=body.source,
        status=status,
    )
    db.add(fb)
    await db.flush()

    confirmed = all(m.manager_confirmed for m in body.mappings) if body.mappings else False
    for m_data in body.mappings:
        mapping = FeedbackCriterionMapping(
            feedback_id=fb.feedback_id,
            criterion_id=m_data.criterion_id,
            original_fragment=m_data.original_fragment,
            suggested_rating=m_data.suggested_rating,
            confirmed_rating=m_data.confirmed_rating,
            llm_explanation=m_data.llm_explanation,
            manager_confirmed=m_data.manager_confirmed,
        )
        db.add(mapping)

    if body.mappings and confirmed:
        fb.status = "confirmed"

    await db.commit()
    return await _load_feedback_with_mappings(db, fb.feedback_id)


@router.get("/", response_model=List[FeedbackWithMappings])
async def list_feedback(
    employee_id: Optional[uuid.UUID] = None,
    period_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Feedback)
        .where(Feedback.is_deleted == False, Feedback.manager_id == current_user.user_id)
        .options(selectinload(Feedback.mappings).selectinload(FeedbackCriterionMapping.criterion))
        .order_by(Feedback.feedback_date.desc(), Feedback.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if employee_id:
        query = query.where(Feedback.employee_id == employee_id)
    if period_id:
        query = query.where(Feedback.period_id == period_id)
    if status:
        query = query.where(Feedback.status == status)

    result = await db.execute(query)
    feedbacks = result.scalars().all()
    return [_enrich_feedback(fb) for fb in feedbacks]


@router.get("/{feedback_id}", response_model=FeedbackWithMappings)
async def get_feedback(
    feedback_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _load_feedback_with_mappings(db, feedback_id, current_user.user_id)


@router.patch("/{feedback_id}", response_model=FeedbackRead)
async def update_feedback(
    feedback_id: uuid.UUID,
    body: FeedbackUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Feedback).where(Feedback.feedback_id == feedback_id, Feedback.manager_id == current_user.user_id)
    )
    fb = result.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Фидбэк не найден")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(fb, field, value)
    await db.commit()
    await db.refresh(fb)
    return fb


@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Feedback).where(Feedback.feedback_id == feedback_id, Feedback.manager_id == current_user.user_id)
    )
    fb = result.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Фидбэк не найден")
    fb.is_deleted = True
    await db.commit()
    return {"ok": True}


@router.post("/{feedback_id}/mappings", response_model=MappingRead)
async def add_mapping(
    feedback_id: uuid.UUID,
    body: MappingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fb = await _get_owned_feedback(db, feedback_id, current_user.user_id)
    mapping = FeedbackCriterionMapping(
        feedback_id=fb.feedback_id,
        criterion_id=body.criterion_id,
        original_fragment=body.original_fragment,
        suggested_rating=body.suggested_rating,
        confirmed_rating=body.confirmed_rating,
        llm_explanation=body.llm_explanation,
        manager_confirmed=body.manager_confirmed,
    )
    db.add(mapping)
    if fb.status == "no_criterion":
        fb.status = "draft"
    await db.commit()
    await db.refresh(mapping)

    criterion_result = await db.execute(
        select(CriteriaMatrix).where(CriteriaMatrix.criterion_id == mapping.criterion_id)
    )
    criterion = criterion_result.scalar_one_or_none()
    return MappingRead(
        mapping_id=mapping.mapping_id,
        feedback_id=mapping.feedback_id,
        criterion_id=mapping.criterion_id,
        criterion_name=criterion.criterion_name if criterion else None,
        original_fragment=mapping.original_fragment,
        suggested_rating=mapping.suggested_rating,
        confirmed_rating=mapping.confirmed_rating,
        llm_explanation=mapping.llm_explanation,
        manager_confirmed=mapping.manager_confirmed,
        confirmed_at=mapping.confirmed_at,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )


@router.patch("/{feedback_id}/mappings/{mapping_id}", response_model=MappingRead)
async def update_mapping(
    feedback_id: uuid.UUID,
    mapping_id: uuid.UUID,
    body: MappingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_feedback(db, feedback_id, current_user.user_id)
    result = await db.execute(
        select(FeedbackCriterionMapping).where(
            FeedbackCriterionMapping.mapping_id == mapping_id,
            FeedbackCriterionMapping.feedback_id == feedback_id,
        )
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=404, detail="Связка не найдена")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(mapping, field, value)
    await db.commit()
    await db.refresh(mapping)

    criterion_result = await db.execute(
        select(CriteriaMatrix).where(CriteriaMatrix.criterion_id == mapping.criterion_id)
    )
    criterion = criterion_result.scalar_one_or_none()
    return MappingRead(
        mapping_id=mapping.mapping_id,
        feedback_id=mapping.feedback_id,
        criterion_id=mapping.criterion_id,
        criterion_name=criterion.criterion_name if criterion else None,
        original_fragment=mapping.original_fragment,
        suggested_rating=mapping.suggested_rating,
        confirmed_rating=mapping.confirmed_rating,
        llm_explanation=mapping.llm_explanation,
        manager_confirmed=mapping.manager_confirmed,
        confirmed_at=mapping.confirmed_at,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )


@router.delete("/{feedback_id}/mappings/{mapping_id}")
async def delete_mapping(
    feedback_id: uuid.UUID,
    mapping_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_feedback(db, feedback_id, current_user.user_id)
    result = await db.execute(
        select(FeedbackCriterionMapping).where(
            FeedbackCriterionMapping.mapping_id == mapping_id,
            FeedbackCriterionMapping.feedback_id == feedback_id,
        )
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=404, detail="Связка не найдена")
    await db.delete(mapping)
    await db.commit()
    return {"ok": True}


async def _get_owned_feedback(db: AsyncSession, feedback_id: uuid.UUID, manager_id: uuid.UUID) -> Feedback:
    result = await db.execute(
        select(Feedback).where(Feedback.feedback_id == feedback_id, Feedback.manager_id == manager_id, Feedback.is_deleted == False)
    )
    fb = result.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Фидбэк не найден")
    return fb


async def _load_feedback_with_mappings(
    db: AsyncSession, feedback_id: uuid.UUID, manager_id: Optional[uuid.UUID] = None
) -> FeedbackWithMappings:
    query = (
        select(Feedback)
        .where(Feedback.feedback_id == feedback_id, Feedback.is_deleted == False)
        .options(selectinload(Feedback.mappings).selectinload(FeedbackCriterionMapping.criterion))
    )
    if manager_id:
        query = query.where(Feedback.manager_id == manager_id)
    result = await db.execute(query)
    fb = result.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Фидбэк не найден")
    return _enrich_feedback(fb)


def _enrich_feedback(fb: Feedback) -> FeedbackWithMappings:
    mappings = []
    for m in fb.mappings:
        mappings.append(MappingRead(
            mapping_id=m.mapping_id,
            feedback_id=m.feedback_id,
            criterion_id=m.criterion_id,
            criterion_name=m.criterion.criterion_name if m.criterion else None,
            original_fragment=m.original_fragment,
            suggested_rating=m.suggested_rating,
            confirmed_rating=m.confirmed_rating,
            llm_explanation=m.llm_explanation,
            manager_confirmed=m.manager_confirmed,
            confirmed_at=m.confirmed_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
        ))
    return FeedbackWithMappings(
        feedback_id=fb.feedback_id,
        employee_id=fb.employee_id,
        manager_id=fb.manager_id,
        period_id=fb.period_id,
        feedback_date=fb.feedback_date,
        original_text=fb.original_text,
        source=fb.source,
        status=fb.status,
        created_at=fb.created_at,
        updated_at=fb.updated_at,
        mappings=mappings,
    )


async def _check_employee_access(db: AsyncSession, user: User, employee_id: uuid.UUID):
    if user.role in ("admin", "hrbp"):
        return
    result = await db.execute(
        select(ManagerEmployeeVisibility).where(
            ManagerEmployeeVisibility.manager_id == user.user_id,
            ManagerEmployeeVisibility.employee_id == employee_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Нет доступа к этому сотруднику")
