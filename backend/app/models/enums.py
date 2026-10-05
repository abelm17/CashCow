from enum import Enum

class AtmStatus(str, Enum):
    OPERATIONAL= "Operational"
    IN_TRANSPORT= "In-Transport"
    MAINTENANCE= "Maintenance"
    OFFLINE= "Offline"

class ServiceCallPriority(str, Enum):
    LOW= "Low"
    MEDIUM= "Medium"
    CRITICAL= "Critical"

class ServiceCallStatus(str, Enum):
    PENDING= "Pending"
    IN_PROGRESS= "In-Progress"
    COMPLETED= "Completed"
    FAILED= "Failed"

class UserRole(str, Enum):
    OPERATIONS_ADMIN= "Operations Admin"
    FIELD_TECHNICIAN= "Field Technician"
    AUDITOR= "Auditor"