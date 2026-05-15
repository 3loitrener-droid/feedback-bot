from __future__ import annotations
import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, BigInteger, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_team_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("teams.team_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    users: Mapped[List["User"]] = relationship("User", back_populates="team")
    employees: Mapped[List["Employee"]] = relationship("Employee", back_populates="team")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="manager")
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("teams.team_id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="users")
    feedbacks: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="manager", foreign_keys="Feedback.manager_id")
    visibility: Mapped[List["ManagerEmployeeVisibility"]] = relationship("ManagerEmployeeVisibility", back_populates="manager", foreign_keys="ManagerEmployeeVisibility.manager_id")
