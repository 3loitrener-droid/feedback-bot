import uuid
from typing import List
from datetime import datetime, date
from sqlalchemy import String, Boolean, DateTime, Date, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Period(Base):
    __tablename__ = "periods"

    period_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period_name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    feedbacks: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="period")
    summaries: Mapped[List["Summary"]] = relationship("Summary", back_populates="period")
