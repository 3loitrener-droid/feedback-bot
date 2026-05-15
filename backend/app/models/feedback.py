from __future__ import annotations
import uuid
from typing import Optional, List
from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, Date, Text, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.employee_id"), nullable=False)
    manager_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    period_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("periods.period_id"), nullable=True)
    feedback_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="telegram")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    # confirmed | draft | no_criterion | needs_review
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="feedbacks")
    manager: Mapped["User"] = relationship("User", back_populates="feedbacks", foreign_keys=[manager_id])
    period: Mapped[Optional["Period"]] = relationship("Period", back_populates="feedbacks")
    mappings: Mapped[List["FeedbackCriterionMapping"]] = relationship(
        "FeedbackCriterionMapping",
        back_populates="feedback",
        cascade="all, delete-orphan",
    )


class FeedbackCriterionMapping(Base):
    __tablename__ = "feedback_criterion_mappings"

    mapping_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feedback_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("feedback.feedback_id"), nullable=False)
    criterion_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("criteria_matrix.criterion_id"), nullable=False)
    original_fragment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_rating: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confirmed_rating: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    llm_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    feedback: Mapped["Feedback"] = relationship("Feedback", back_populates="mappings")
    criterion: Mapped["CriteriaMatrix"] = relationship("CriteriaMatrix", back_populates="mappings")
