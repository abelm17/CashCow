from pydantic import BaseModel


class LowCashAlert(BaseModel):
    atm_id: int
    serial_number: str
    model: str
    cash_level: int
    branch_id: int
    branch_name: str


class CoLocationDiscrepancy(BaseModel):
    service_call_id: int
    title: str
    atm_id: int
    atm_branch_id: int
    technician_id: int
    technician_name: str
    technician_branch_id: int


class ReliabilityMetric(BaseModel):
    model: str
    total_service_calls: int
    completed_count: int
    failed_count: int
    completion_failure_ratio: float | None


class MaintenanceFlag(BaseModel):
    branch_id: int
    branch_name: str
    total_atms: int
    maintenance_count: int
    maintenance_percentage: float


class TechnicianActiveCalls(BaseModel):
    technician_id: int
    technician_name: str
    active_service_call_count: int


class ReportingLineResult(BaseModel):
    supervisor_id: int
    supervisor_name: str
    technician_count: int
    technicians: list[TechnicianActiveCalls]
