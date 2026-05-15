import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class CriterionCreate(BaseModel):
    criterion_name: str
    below_description: str = ""
    meet_description: str = ""
    exceeds_description: str = ""
    role: Optional[str] = None
    weight: float = 1.0
    is_key_criterion: bool = False
    sort_order: int = 0


class CriterionRead(BaseModel):
    criterion_id: uuid.UUID
    criterion_name: str
    below_description: str
    meet_description: str
    exceeds_description: str
    role: Optional[str] = None
    weight: float
    is_key_criterion: bool
    is_active: bool
    sort_order: int

    model_config = {"from_attributes": True}


class CriterionUpdate(BaseModel):
    criterion_name: Optional[str] = None
    below_description: Optional[str] = None
    meet_description: Optional[str] = None
    exceeds_description: Optional[str] = None
    weight: Optional[float] = None
    is_key_criterion: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
