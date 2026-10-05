from __future__ import annotations
from typing import TYPE_CHECKING
from .base import Base
from .enums import UserRole
from sqlalchemy import Integer, String, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .branch import Branch
    from .technician import Technician

class User(Base):
    __tablename__= "users"
    id: Mapped[int]= mapped_column(primary_key= True)
    name: Mapped[str]= mapped_column(String(75))
    username: Mapped[str]= mapped_column(String(25), unique=True)
    hashed_password: Mapped[str]= mapped_column(String(255))
    role: Mapped["UserRole"]= mapped_column(
        SqlEnum(
            UserRole,
            name= "user_role",
            values_callable= lambda enum_cls: [member.value for member in enum_cls],
        ),
    )
    technician: Mapped["Technician | None"] = relationship(
        "Technician", back_populates="user"
    )

    branch: Mapped["Branch | None"]= relationship("Branch", back_populates="supervisor")

    def __repr__(self) -> str:
        return f"User(id= {self.id}, name= {self.name!r}, username= {self.username!r}, role= {self.role.value})"