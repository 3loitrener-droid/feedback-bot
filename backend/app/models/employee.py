from __future__ import annotations
import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    level: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("teams.team_id"), nullable=True)
    manager_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="employees")
    manager: Mapped[Optional["User"]] = relationship("User", foreign_keys=[manager_id])
    feedbacks: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="employee")
    visibility_entries: Mapped[List["ManagerEmployeeVisibility"]] = relationship("ManagerEmployeeVisibility", back_populates="employee")


class ManagerEmployeeVisibility(Base):
    __tablename__ = "manager_employee_visibility"

    manager_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("employees.employee_id"), primary_key=True)
    granted_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    manager: Mapped["User"] = relationship("User", back_populates="visibility", foreign_keys=[manager_id])
    employee: Mapped["Employee"] = relationship("Employee", back_populates="visibility_entries")
