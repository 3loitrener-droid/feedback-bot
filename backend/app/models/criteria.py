from __future__ import annotations
import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Numeric, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CriteriaMatrix(Base):
    __tablename__ = "criteria_matrix"

    criterion_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    criterion_name: Mapped[str] = mapped_column(String(255), nullable=False)
    below_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    meet_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    exceeds_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    weight: Mapped[float] = mapped_column(Numeric(3, 1), default=1.0)
    is_key_criterion: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    mappings: Mapped[List["FeedbackCriterionMapping"]] = relationship("FeedbackCriterionMapping", back_populates="criterion")
