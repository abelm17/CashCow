from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from .base import Base
from .enums import AtmStatus
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, String, Integer, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .branch import Branch
    from .service_call import ServiceCall
    
class Atm(Base):
    __tablename__= "atms"

    id: Mapped[int]= mapped_column(primary_key= True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    serial_number: Mapped[str]= mapped_column(String(50), unique= True)
    model: Mapped[str]= mapped_column(String(20))
    status: Mapped["AtmStatus"]= mapped_column(
        SqlEnum(
            AtmStatus,
            name= "atm_status",
            values_callable= lambda enum_cls: [member.value for member in enum_cls],
        ),
        default= AtmStatus.OPERATIONAL,
    )
    cash_level: Mapped[int]= mapped_column(Integer)

    # Relationship linking back to branch
    branch_id: Mapped[int]= mapped_column(Integer, ForeignKey("branches.id"))
    branch: Mapped["Branch"]= relationship("Branch", back_populates="atms")

    service_calls: Mapped[list["ServiceCall"]]= relationship("ServiceCall", back_populates="atm")

    def __repr__(self) -> str:
        return (f"ATM(id= {self.id}, serial_number= {self.serial_number}, model= {self.model!r}, " 
            f"status= {self.status.value!r}, cash_level= {self.cash_level}, branch_id= {self.branch_id})")