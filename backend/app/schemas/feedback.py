import uuid
from datetime import datetime, date
from pydantic import BaseModel, field_validator
from typing import Optional, List


class MappingCreate(BaseModel):
    criterion_id: uuid.UUID
    original_fragment: Optional[str] = None
    suggested_rating: Optional[str] = None
    confirmed_rating: Optional[str] = None
    llm_explanation: Optional[str] = None
    manager_confirmed: bool = False


class MappingRead(BaseModel):
    mapping_id: uuid.UUID
    feedback_id: uuid.UUID
    criterion_id: uuid.UUID
    criterion_name: Optional[str] = None
    original_fragment: Optional[str] = None
    suggested_rating: Optional[str] = None
    confirmed_rating: Optional[str] = None
    llm_explanation: Optional[str] = None
    manager_confirmed: bool
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MappingUpdate(BaseModel):
    criterion_id: Optional[uuid.UUID] = None
    original_fragment: Optional[str] = None
    confirmed_rating: Optional[str] = None
    manager_confirmed: Optional[bool] = None


class FeedbackCreate(BaseModel):
    employee_id: uuid.UUID
    period_id: Optional[uuid.UUID] = None
    feedback_date: Optional[date] = None
    original_text: str
    source: str = "telegram"
    mappings: List[MappingCreate] = []

    @field_validator("original_text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Комментарий не может быть пустым")
        return v


class FeedbackRead(BaseModel):
    feedback_id: uuid.UUID
    employee_id: uuid.UUID
    manager_id: uuid.UUID
    period_id: Optional[uuid.UUID] = None
    feedback_date: date
    original_text: str
    source: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FeedbackWithMappings(FeedbackRead):
    mappings: List[MappingRead] = []
    employee_name: Optional[str] = None
    manager_name: Optional[str] = None


class FeedbackUpdate(BaseModel):
    status: Optional[str] = None
    period_id: Optional[uuid.UUID] = None
