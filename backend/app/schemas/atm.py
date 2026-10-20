from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models import AtmStatus


class AtmCreate(BaseModel):
    serial_number: str= Field(min_length=1, max_length= 50)
    model: str= Field(min_length= 1, max_length= 100)
    status: AtmStatus = AtmStatus.OFFLINE
    cash_level: int= Field(ge=0)
    branch_id: int

class AtmRead(AtmCreate):
    id: int
    is_active: bool
    deleted_at: datetime | None = None
    deleted_by: int | None = None
    model_config = ConfigDict(from_attributes=True)

class AtmUpdate(BaseModel):
    status: AtmStatus | None = None
    cash_level: int | None = Field(default=None, ge=0)
    branch_id: int | None = None