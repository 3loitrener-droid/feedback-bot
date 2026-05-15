from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.criteria import CriteriaMatrix
from app.llm.analyzer import FeedbackAnalyzer

router = APIRouter(prefix="/llm", tags=["llm"])


class AnalyzeRequest(BaseModel):
    original_text: str
    employee_name: str
    employee_position: Optional[str] = None
    employee_level: Optional[str] = None


class AnalyzeResponse(BaseModel):
    original_text: str
    needs_clarification: bool
    clarification_request: Optional[str] = None
    mappings: List[dict]


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_feedback(
    body: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    criteria_result = await db.execute(
        select(CriteriaMatrix).where(CriteriaMatrix.is_active == True).order_by(CriteriaMatrix.sort_order)
    )
    criteria = criteria_result.scalars().all()
    if not criteria:
        raise HTTPException(status_code=400, detail="Матрица критериев пуста")

    analyzer = FeedbackAnalyzer()
    result = await analyzer.analyze(
        original_text=body.original_text,
        employee_name=body.employee_name,
        employee_position=body.employee_position,
        employee_level=body.employee_level,
        criteria=criteria,
    )
    return result
