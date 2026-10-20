from app.permissions import Permission
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_permission
from app.models import (
    Atm, Branch, ServiceCall, Technician, User, UserRole,
    AtmStatus, ServiceCallStatus,
)
from app.schemas.analytics import (
    LowCashAlert, CoLocationDiscrepancy, ReliabilityMetric,
    MaintenanceFlag, TechnicianActiveCalls, ReportingLineResult,
)

ATM_MAX_CASH = 50_000
LOW_CASH_THRESHOLD = ATM_MAX_CASH * 0.20

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[Depends(require_permission(Permission.ANALYTICS_READ))],
)


@router.get("/low-cash", response_model=list[LowCashAlert])
async def low_cash_alert(db: AsyncSession = Depends(get_db)):
    statement = (
        select(
            Atm.id.label("atm_id"),
            Atm.serial_number,
            Atm.model,
            Atm.cash_level,
            Branch.id.label("branch_id"),
            Branch.name.label("branch_name"),
        )
        .join(Branch, Branch.id == Atm.branch_id)
        .where(
            Atm.is_active.is_(True),
            Atm.status == AtmStatus.OPERATIONAL,
            Atm.cash_level < LOW_CASH_THRESHOLD,
        )
        .order_by(Atm.cash_level.asc())
    )

    result = await db.execute(statement)

    return [LowCashAlert(**row._mapping) for row in result]



@router.get("/co-location-discrepancy", response_model=list[CoLocationDiscrepancy])
async def co_location_discrepancy(db: AsyncSession = Depends(get_db)):
    statement = (
        select(
            ServiceCall.id.label("service_call_id"),
            ServiceCall.title,
            Atm.id.label("atm_id"),
            Atm.branch_id.label("atm_branch_id"),
            Technician.id.label("technician_id"),
            Technician.name.label("technician_name"),
            Technician.branch_id.label("technician_branch_id"),
        )
        .join(Atm, Atm.id == ServiceCall.atm_id)
        .join(Technician, Technician.id == ServiceCall.technician_id)
        .where(Atm.branch_id != Technician.branch_id, Atm.is_active.is_(True), ServiceCall.is_active.is_(True))
        .order_by(ServiceCall.id)
    )

    result = await db.execute(statement)

    return [CoLocationDiscrepancy(**row._mapping) for row in result]


@router.get("/reliability", response_model=list[ReliabilityMetric])
async def reliability_metrics(
    db: AsyncSession = Depends(get_db),
):
    statement = (
        select(
            Atm.model.label("model"),
            func.count(ServiceCall.id).label("total_service_calls"),
            func.sum(
                case(
                    (ServiceCall.status == ServiceCallStatus.COMPLETED, 1),
                    else_=0,
                )
            ).label("completed_count"),
            func.sum(
                case(
                    (ServiceCall.status == ServiceCallStatus.FAILED, 1),
                    else_=0,
                )
            ).label("failed_count"),
        )
        .join(ServiceCall, ServiceCall.atm_id == Atm.id)
        .where(Atm.is_active.is_(True), ServiceCall.is_active.is_(True))
        .group_by(Atm.model)
        .order_by(Atm.model)
    )

    result = await db.execute(statement)

    metrics = []

    for row in result:
        completed = int(row.completed_count or 0)
        failed = int(row.failed_count or 0)
        ratio = None if failed == 0 else completed / failed

        metrics.append(
            ReliabilityMetric(
                model=row.model,
                total_service_calls=int(row.total_service_calls or 0),
                completed_count=completed,
                failed_count=failed,
                completion_failure_ratio=ratio,
            )
        )

    return metrics

@router.get("/maintenance-flags", response_model=list[MaintenanceFlag])
async def maintenance_flags(
    db: AsyncSession = Depends(get_db),
):
    statement = (
        select(
            Branch.id.label("branch_id"),
            Branch.name.label("branch_name"),
            func.count(Atm.id).label("total_atms"),
            func.sum(
                case(
                    (Atm.status == AtmStatus.MAINTENANCE, 1),
                    else_=0,
                )
            ).label("maintenance_count"),
        )
        .join(Atm, Atm.branch_id == Branch.id)
        .where(Atm.is_active.is_(True))
        .group_by(Branch.id, Branch.name)
    )

    result = await db.execute(statement)

    flagged = []

    for row in result:
        total = int(row.total_atms or 0)
        maintenance = int(row.maintenance_count or 0)

        if total == 0:
            continue

        percentage = (maintenance / total) * 100

        if percentage > 30:
            flagged.append(
                MaintenanceFlag(
                    branch_id=row.branch_id,
                    branch_name=row.branch_name,
                    total_atms=total,
                    maintenance_count=maintenance,
                    maintenance_percentage=percentage,
                )
            )

    return flagged



@router.get("/supervisors")
async def get_supervisors(
    db: AsyncSession = Depends(get_db),
):
    statement = (
        select(User.id, User.name)
        .where(User.role == UserRole.OPERATIONS_ADMIN)
        .order_by(User.name)
    )

    result = await db.execute(statement)

    return [
        {
            "id": row.id,
            "name": row.name,
        }
        for row in result
    ]


@router.get("/reporting-lines/{supervisor_id}", response_model=ReportingLineResult)
async def reporting_lines(supervisor_id: int, db: AsyncSession = Depends(get_db)):
    supervisor_statement = select(User).where(
        User.id == supervisor_id,
        User.role == UserRole.OPERATIONS_ADMIN,
    )

    supervisor_result = await db.execute(supervisor_statement)
    supervisor = supervisor_result.scalar_one_or_none()

    if supervisor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Operations supervisor not found",
        )

    statement = (
        select(
            Technician.id.label("technician_id"),
            Technician.name.label("technician_name"),
            func.count(ServiceCall.id).label("active_service_call_count"),
        )
        .join(User, User.id == Technician.user_id)
        .join(ServiceCall, ServiceCall.technician_id == Technician.id)
        .join(Branch, Branch.id == Technician.branch_id)
        .where(
            Branch.supervisor_id == supervisor_id,
            ServiceCall.is_active.is_(True),
            ServiceCall.status.in_([
                ServiceCallStatus.PENDING,
                ServiceCallStatus.IN_PROGRESS,
            ]),
        )
        .group_by(Technician.id, Technician.name)
        .order_by(Technician.name)
    )

    result = await db.execute(statement)

    technicians = [
        TechnicianActiveCalls(
            technician_id=row.technician_id,
            technician_name=row.technician_name,
            active_service_call_count=int(row.active_service_call_count or 0),
        )
        for row in result
    ]

    return ReportingLineResult(
        supervisor_id=supervisor.id,
        supervisor_name=supervisor.name,
        technician_count=len(technicians),
        technicians=technicians,
    )