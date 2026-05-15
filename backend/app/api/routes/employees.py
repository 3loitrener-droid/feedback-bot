from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.models.employee import Employee, ManagerEmployeeVisibility
from app.models.feedback import Feedback, FeedbackCriterionMapping
from app.models.summary import Summary
from app.schemas.employee import EmployeeRead, EmployeeCreate, EmployeeStats

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=List[EmployeeRead])
async def list_my_employees(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role in ("admin", "hrbp"):
        result = await db.execute(select(Employee).where(Employee.status == "active"))
    else:
        subq = select(ManagerEmployeeVisibility.employee_id).where(
            ManagerEmployeeVisibility.manager_id == current_user.user_id
        )
        result = await db.execute(
            select(Employee).where(Employee.employee_id.in_(subq), Employee.status == "active")
        )
    return result.scalars().all()


@router.get("/stats", response_model=List[EmployeeStats])
async def list_employees_with_stats(
    period_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role in ("admin", "hrbp"):
        emp_result = await db.execute(select(Employee).where(Employee.status == "active"))
    else:
        subq = select(ManagerEmployeeVisibility.employee_id).where(
            ManagerEmployeeVisibility.manager_id == current_user.user_id
        )
        emp_result = await db.execute(
            select(Employee).where(Employee.employee_id.in_(subq), Employee.status == "active")
        )
    employees = emp_result.scalars().all()

    stats = []
    for emp in employees:
        fb_query = select(Feedback).where(
            Feedback.employee_id == emp.employee_id,
            Feedback.is_deleted == False,
            Feedback.manager_id == current_user.user_id,
        )
        if period_id:
            fb_query = fb_query.where(Feedback.period_id == period_id)
        fb_result = await db.execute(fb_query)
        feedbacks = fb_result.scalars().all()

        total = len(feedbacks)
        no_criterion = sum(1 for f in feedbacks if f.status == "no_criterion")
        mapped = total - no_criterion

        # Ищем последний summary
        sum_query = select(Summary).where(
            Summary.employee_id == emp.employee_id,
            Summary.manager_id == current_user.user_id,
            Summary.is_current == True,
        ).order_by(Summary.generated_at.desc()).limit(1)
        if period_id:
            sum_query = sum_query.where(Summary.period_id == period_id)
        sum_result = await db.execute(sum_query)
        summary = sum_result.scalar_one_or_none()

        stats.append(EmployeeStats(
            employee_id=emp.employee_id,
            full_name=emp.full_name,
            position=emp.position,
            level=emp.level,
            total_feedback=total,
            mapped_feedback=mapped,
            unmapped_feedback=no_criterion,
            rating_recommendation=summary.rating_recommendation if summary else None,
            top_strengths=[s["criterion_name"] for s in (summary.strengths or [])[:2]],
            top_growth_areas=[g["criterion_name"] for g in (summary.growth_areas or [])[:2]],
        ))
    return stats


@router.get("/{employee_id}", response_model=EmployeeRead)
async def get_employee(
    employee_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_access(db, current_user, employee_id)
    result = await db.execute(select(Employee).where(Employee.employee_id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    return emp


@router.post("/", response_model=EmployeeRead)
async def create_employee(
    body: EmployeeCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    emp = Employee(**body.model_dump())
    db.add(emp)
    await db.commit()
    await db.refresh(emp)
    return emp


async def _check_access(db: AsyncSession, user: User, employee_id: uuid.UUID):
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
