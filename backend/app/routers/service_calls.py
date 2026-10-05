from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, require_role
from app.models import ServiceCall, ServiceCallStatus, ServiceCallPriority, UserRole, Technician

from app.schemas.service_call import ServiceCallRead, ServiceCallUpdate, ServiceCallCreate, UpdateStatus

router = APIRouter(prefix="/service_calls", tags=["service_calls"])


# GET ALL SERVICE CALLS
# Admins and Auditors see everything.
# Technicians see only their assigned calls.
@router.get("", response_model=list[ServiceCallRead])
async def list_service_calls(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(
        UserRole.OPERATIONS_ADMIN,
        UserRole.AUDITOR,
        UserRole.FIELD_TECHNICIAN
    ))
) -> list[ServiceCall]:

    statement = select(ServiceCall)

    if current_user.role == UserRole.FIELD_TECHNICIAN:
        statement = (
            statement
            .join(ServiceCall.technician)
            .where(Technician.user_id == current_user.id)
        )

    statement = statement.order_by(ServiceCall.id)

    result = await db.execute(statement)
    return list(result.scalars().all())


# GET ONE SERVICE CALL
@router.get("/{service_call_id}", response_model=ServiceCallRead)
async def get_service_call(
    service_call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(
        UserRole.OPERATIONS_ADMIN,
        UserRole.AUDITOR,
        UserRole.FIELD_TECHNICIAN
    ))
) -> ServiceCall:

    statement = select(ServiceCall).where(ServiceCall.id == service_call_id)

    if current_user.role == UserRole.FIELD_TECHNICIAN:
        statement = (
            statement
            .join(ServiceCall.technician)
            .where(Technician.user_id == current_user.id)
        )

    result = await db.execute(statement)
    service_call = result.scalar_one_or_none()

    if service_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service call {service_call_id} not found"
        )

    return service_call



# UPDATE SERVICE CALL
# Admin can update anything allowed by ServiceCallUpdate.
# Technician can only update the status of their own call.
@router.patch("/{service_call_id}", response_model=ServiceCallRead)
async def update_service_call(
    service_call_id: int,
    data: ServiceCallUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    )),
) -> ServiceCall:

    statement = select(ServiceCall).where(ServiceCall.id == service_call_id)
    result = await db.execute(statement)
    service_call = result.scalar_one_or_none()

    if service_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service call {service_call_id} not found",
        )

    changes = data.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(service_call, field, value)

    await db.commit()
    await db.refresh(service_call)

    return service_call


@router.patch("/{service_call_id}/status", response_model=ServiceCallRead)
async def update_service_call_status(
    service_call_id: int,
    data: UpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(
        UserRole.FIELD_TECHNICIAN
    )),
) -> ServiceCall:

    statement = (
        select(ServiceCall)
        .join(Technician, Technician.id == ServiceCall.technician_id)
        .where(
            ServiceCall.id == service_call_id,
            Technician.user_id == current_user.id,
        )
    )

    result = await db.execute(statement)
    service_call = result.scalar_one_or_none()

    if service_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service call {service_call_id} not found",
        )

    service_call.status = data.status

    await db.commit()
    await db.refresh(service_call)

    return service_call



@router.post("", response_model=ServiceCallRead, status_code=status.HTTP_201_CREATED)
async def create_service_call(
    payload: ServiceCallCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    )),
) -> ServiceCall:

    service_call = ServiceCall(**payload.model_dump())

    db.add(service_call)
    await db.commit()
    await db.refresh(service_call)

    return service_call



@router.delete("/{service_call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_call(
    service_call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    )),
):
    statement = select(ServiceCall).where(
        ServiceCall.id == service_call_id
    )

    result = await db.execute(statement)
    service_call = result.scalar_one_or_none()

    if service_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service call {service_call_id} not found",
        )

    await db.delete(service_call)
    await db.commit()
