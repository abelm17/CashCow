from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, require_role
from app.models import (
    DiagnosticReport,
    ServiceCall,
    Technician,
    UserRole,
)
from app.schemas.diagnostic_report import (
    DiagnosticReportCreate,
    DiagnosticReportRead,
    DiagnosticReportUpdate,
)


router = APIRouter(
    prefix="/diagnostic_reports",
    tags=["diagnostic_reports"],
)


@router.get("", response_model=list[DiagnosticReportRead])
async def list_diagnostic_reports(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(
        UserRole.OPERATIONS_ADMIN,
        UserRole.AUDITOR,
        UserRole.FIELD_TECHNICIAN,
    )),
) -> list[DiagnosticReport]:

    if current_user.role == UserRole.FIELD_TECHNICIAN:
        statement = (
            select(DiagnosticReport)
            .join(
                ServiceCall,
                ServiceCall.id == DiagnosticReport.service_call_id,
            )
            .join(
                Technician,
                Technician.id == ServiceCall.technician_id,
            )
            .where(Technician.user_id == current_user.id)
            .order_by(DiagnosticReport.id)
        )
    else:
        statement = select(DiagnosticReport).order_by(
            DiagnosticReport.id
        )

    result = await db.execute(statement)

    return list(result.scalars().all())


@router.get("/{diagnostic_report_id}", response_model=DiagnosticReportRead)
async def get_diagnostic_report(
    diagnostic_report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(
        UserRole.OPERATIONS_ADMIN,
        UserRole.AUDITOR,
        UserRole.FIELD_TECHNICIAN,
    )),
) -> DiagnosticReport:

    if current_user.role == UserRole.FIELD_TECHNICIAN:
        statement = (
            select(DiagnosticReport)
            .join(
                ServiceCall,
                ServiceCall.id == DiagnosticReport.service_call_id,
            )
            .join(
                Technician,
                Technician.id == ServiceCall.technician_id,
            )
            .where(
                DiagnosticReport.id == diagnostic_report_id,
                Technician.user_id == current_user.id,
            )
        )
    else:
        statement = select(DiagnosticReport).where(
            DiagnosticReport.id == diagnostic_report_id
        )

    result = await db.execute(statement)
    diagnostic_report = result.scalar_one_or_none()

    if diagnostic_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic report {diagnostic_report_id} not found",
        )

    return diagnostic_report



@router.post(
    "",
    response_model=DiagnosticReportRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_diagnostic_report(
    payload: DiagnosticReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(
        UserRole.OPERATIONS_ADMIN,
        UserRole.FIELD_TECHNICIAN,
    )),
) -> DiagnosticReport:

    if current_user.role == UserRole.FIELD_TECHNICIAN:
        statement = (
            select(ServiceCall)
            .join(
                Technician,
                Technician.id == ServiceCall.technician_id,
            )
            .where(
                ServiceCall.id == payload.service_call_id,
                Technician.user_id == current_user.id,
            )
        )

        result = await db.execute(statement)
        service_call = result.scalar_one_or_none()

        if service_call is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only attach reports to your assigned service calls.",
            )

    values= payload.model_dump()
    if current_user.role == UserRole.FIELD_TECHNICIAN:
        values["technician_id"] = service_call.technician_id

    diagnostic_report = DiagnosticReport(**values)

    db.add(diagnostic_report)

    await db.commit()
    await db.refresh(diagnostic_report)

    return diagnostic_report



@router.patch(
    "/{diagnostic_report_id}",
    response_model=DiagnosticReportRead,
)
async def update_diagnostic_report(
    diagnostic_report_id: int,
    data: DiagnosticReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(
        UserRole.OPERATIONS_ADMIN,
        UserRole.FIELD_TECHNICIAN,
    )),
) -> DiagnosticReport:

    if current_user.role == UserRole.FIELD_TECHNICIAN:
        statement = (
            select(DiagnosticReport)
            .join(
                ServiceCall,
                ServiceCall.id == DiagnosticReport.service_call_id,
            )
            .join(
                Technician,
                Technician.id == ServiceCall.technician_id,
            )
            .where(
                DiagnosticReport.id == diagnostic_report_id,
                Technician.user_id == current_user.id,
            )
        )
    else:
        statement = select(DiagnosticReport).where(
            DiagnosticReport.id == diagnostic_report_id
        )

    result = await db.execute(statement)
    diagnostic_report = result.scalar_one_or_none()

    if diagnostic_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic report {diagnostic_report_id} not found",
        )

    changes = data.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(diagnostic_report, field, value)

    await db.commit()
    await db.refresh(diagnostic_report)

    return diagnostic_report



@router.delete(
    "/{diagnostic_report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_diagnostic_report(
    diagnostic_report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    )),
):
    statement = select(DiagnosticReport).where(
        DiagnosticReport.id == diagnostic_report_id
    )

    result = await db.execute(statement)
    diagnostic_report = result.scalar_one_or_none()

    if diagnostic_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic report {diagnostic_report_id} not found",
        )

    await db.delete(diagnostic_report)
    await db.commit()
