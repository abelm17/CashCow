from __future__ import annotations
from typing import TYPE_CHECKING
from .base import Base
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


if TYPE_CHECKING:
    from .atm import Atm
    from .user import User
    from .technician import Technician

class Branch(Base):
    __tablename__= "branches"

    id: Mapped[int]= mapped_column(primary_key= True)
    name: Mapped[str]= mapped_column(String(40))
    location_region: Mapped[str]= mapped_column(String(30))
    capacity: Mapped[int]= mapped_column(Integer)


    # Add a relationship for supervisor id
    supervisor_id: Mapped[int]= mapped_column(Integer, ForeignKey("users.id"), unique= True)
    supervisor: Mapped["User"]= relationship("User", back_populates="branch")

    technicians: Mapped[list["Technician"]]= relationship("Technician", back_populates="branch")
    # Add a relationship for atms within a branch
    atms: Mapped[list["Atm"]]= relationship("Atm", back_populates="branch")

    def __repr__(self) -> str:
        return (f"Branch(id= {self.id}, name= {self.name!r}, location_region= {self.location_region!r}, "
            f"capacity= {self.capacity}, supervisor_id= {self.supervisor_id})")