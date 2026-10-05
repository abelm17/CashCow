from pydantic import BaseModel, ConfigDict
from datetime import datetime

class DiagnosticReportBase(BaseModel):
    file_url: str
    notes: str
    service_call_id: int

class DiagnosticReportRead(DiagnosticReportBase):
    id: int
    created_at: datetime
    model_config= ConfigDict(from_attributes=True)

class DiagnosticReportCreate(DiagnosticReportBase):
    created_at: datetime
    technician_id: int


class DiagnosticReportUpdate(DiagnosticReportBase):
    """ Shape of base model """
