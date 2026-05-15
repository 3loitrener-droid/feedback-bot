import uuid
from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional


class PeriodCreate(BaseModel):
    period_name: str
    start_date: date
    end_date: date
    is_active: bool = True


class PeriodRead(BaseModel):
    period_id: uuid.UUID
    period_name: str
    start_date: date
    end_date: date
    is_active: bool

    model_config = {"from_attributes": True}
