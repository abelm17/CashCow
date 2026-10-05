from __future__ import annotations
from typing import TYPE_CHECKING
from .base import Base
from sqlalchemy import Integer, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime

if TYPE_CHECKING:
    from .service_call import ServiceCall
    from .technician import Technician

class DiagnosticReport(Base):
    __tablename__= "diagnostic_reports"

    id: Mapped[int]= mapped_column(primary_key= True)
    file_url: Mapped[str]= mapped_column(Text)
    notes: Mapped[str | None]= mapped_column(Text, nullable= True)
    created_at: Mapped[datetime]= mapped_column(DateTime, server_default=func.now())

    service_call_id: Mapped[int]= mapped_column(Integer, ForeignKey("service_calls.id"))
    technician_id: Mapped[int]= mapped_column(Integer, ForeignKey("technicians.id"))

    def __repr__(self) -> str:
        return (f"Diagnostic Report(id= {self.id}, file_url= {self.file_url!r}, "
                f"service_call= {self.service_call_id})")

