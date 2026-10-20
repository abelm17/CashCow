from enum import StrEnum

class Permission(StrEnum):
    ATM_READ = 'atm:read'
    ATM_WRITE = 'atm:write'
    BRANCH_READ = 'branch:read'
    BRANCH_WRITE = 'branch:write'
    SERVICE_CALL_READ = 'service_call:read'
    SERVICE_CALL_WRITE = 'service_call:write'
    SERVICE_CALL_STATUS = 'service_call:status'
    REPORT_READ = 'report:read'
    REPORT_UPLOAD = 'report:upload'
    REPORT_WRITE = 'report:write'
    REPORT_DELETE = 'report:delete'
    ANALYTICS_READ = 'analytics:read'
    AUDIT_READ = 'audit:read'
    USER_MANAGE = 'user:manage'
    HEALTH_DETAIL = 'health:detail'
