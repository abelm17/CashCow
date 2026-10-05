from __future__ import annotations
from typing import TYPE_CHECKING

from .base import Base
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .service_call import ServiceCall
    from .diagnostic_report import DiagnosticReport
    from .branch import Branch
    from .user import User


class Technician(Base):
    __tablename__ = "technicians"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"))

    user: Mapped["User"] = relationship("User", back_populates="technician")
    branch: Mapped["Branch"] = relationship("Branch", back_populates="technicians")

    service_calls: Mapped[list["ServiceCall"]] = relationship(
        "ServiceCall", back_populates="technician"
    )
    diagnostic_reports: Mapped[list["DiagnosticReport"]] = relationship(
        "DiagnosticReport"
    )
