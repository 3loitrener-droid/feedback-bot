import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class EmployeeCreate(BaseModel):
    full_name: str
    position: Optional[str] = None
    level: Optional[str] = None
    team_id: Optional[uuid.UUID] = None
    manager_id: Optional[uuid.UUID] = None


class EmployeeRead(BaseModel):
    employee_id: uuid.UUID
    full_name: str
    position: Optional[str] = None
    level: Optional[str] = None
    status: str
    manager_id: Optional[uuid.UUID] = None

    model_config = {"from_attributes": True}


class EmployeeStats(BaseModel):
    employee_id: uuid.UUID
    full_name: str
    position: Optional[str] = None
    level: Optional[str] = None
    total_feedback: int = 0
    mapped_feedback: int = 0
    unmapped_feedback: int = 0
    rating_recommendation: Optional[str] = None
    top_strengths: List[str] = []
    top_growth_areas: List[str] = []
