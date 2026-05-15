import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Any, List


class SummaryRead(BaseModel):
    summary_id: uuid.UUID
    employee_id: uuid.UUID
    period_id: uuid.UUID
    generated_at: datetime
    total_feedback_count: int
    mapped_feedback_count: int
    unmapped_feedback_count: int
    strengths: Optional[Any] = None
    growth_areas: Optional[Any] = None
    criterion_breakdown: Optional[Any] = None
    top_criteria: Optional[Any] = None
    repeating_patterns: Optional[Any] = None
    rating_recommendation: Optional[str] = None
    arguments_for: Optional[List[str]] = None
    arguments_against: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    disputed_areas: Optional[Any] = None
    needs_attention: Optional[Any] = None
    evidence_comments: Optional[Any] = None
    llm_model_version: Optional[str] = None

    model_config = {"from_attributes": True}
