from __future__ import annotations
import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Summary(Base):
    __tablename__ = "summaries"

    summary_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.employee_id"), nullable=False)
    manager_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    period_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("periods.period_id"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    total_feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    mapped_feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    unmapped_feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    strengths: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    growth_areas: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    criterion_breakdown: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    top_criteria: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    repeating_patterns: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    rating_recommendation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    arguments_for: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    arguments_against: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    risks: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    disputed_areas: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    needs_attention: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    evidence_comments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    llm_model_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)

    employee: Mapped["Employee"] = relationship("Employee")
    manager: Mapped["User"] = relationship("User")
    period: Mapped["Period"] = relationship("Period", back_populates="summaries")
