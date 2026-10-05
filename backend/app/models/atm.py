from __future__ import annotations
from typing import TYPE_CHECKING
from .base import Base
from .enums import AtmStatus
from decimal import Decimal

from sqlalchemy import String, Integer, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .branch import Branch
    from .service_call import ServiceCall
    
class Atm(Base):
    __tablename__= "atms"

    id: Mapped[int]= mapped_column(primary_key= True)
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