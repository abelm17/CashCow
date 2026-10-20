from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from .base import Base
from .enums import ServiceCallPriority, ServiceCallStatus
from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .technician import Technician
    from .atm import Atm

class ServiceCall(Base):
    __tablename__= "service_calls"

    id: Mapped[int]= mapped_column(primary_key= True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title: Mapped[str]= mapped_column(String(75))
    priority: Mapped["ServiceCallPriority"]= mapped_column(
        SqlEnum(
            ServiceCallPriority,
            name= "service_call_priority",
            values_callable= lambda enum_cls: [member.value for member in enum_cls],
        ),
        default= ServiceCallPriority.LOW,
    )
    status: Mapped["ServiceCallStatus"]= mapped_column(
        SqlEnum(
            ServiceCallStatus,
            name= "service_call_status",
            values_callable= lambda enum_cls: [member.value for member in enum_cls],
        ),
        default= ServiceCallStatus.PENDING
    )

    atm_id: Mapped[int]= mapped_column(ForeignKey("atms.id"))
    atm: Mapped["Atm"]= relationship("Atm", back_populates="service_calls")
    technician_id: Mapped[int]= mapped_column(ForeignKey("technicians.id"))
    technician: Mapped["Technician"]= relationship("Technician", back_populates="service_calls")

    def __repr__(self) -> str:
        return (f"Service Call(id= {self.id}, title= {self.title!r}, priority= {self.priority.value!r}, "
                f"status= {self.status.value!r}, atm_id= {self.atm_id}, technician_id= {self.technician_id})")