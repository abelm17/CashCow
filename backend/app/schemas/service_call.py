from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import ServiceCallPriority, ServiceCallStatus

class ServiceCallBase(BaseModel):
    title: str = Field(min_length=3)
    priority: ServiceCallPriority
    status: ServiceCallStatus
    atm_id: int
    technician_id: int


class ServiceCallRead(ServiceCallBase):
    id: int
    is_active: bool
    deleted_at: datetime | None = None
    deleted_by: int | None = None
    model_config= ConfigDict(from_attributes= True)

class ServiceCallUpdate(BaseModel):
    title: str | None = Field(default= None, min_length=3)
    priority: ServiceCallPriority | None = None
    status: ServiceCallStatus | None= None
    atm_id: int | None = None
    technician_id: int | None = None

class ServiceCallCreate(ServiceCallBase):
    """ Shape of base model """

class UpdateStatus(BaseModel):
    status: ServiceCallStatus = ServiceCallStatus.PENDING