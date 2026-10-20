from app.services.audited_writes import create_record, update_record, set_active
from app.permissions import Permission
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db, require_permission
from app.models import ServiceCall, ServiceCallStatus, ServiceCallPriority, UserRole, Technician

from app.schemas.service_call import ServiceCallRead, ServiceCallUpdate, ServiceCallCreate, UpdateStatus
from app.schemas.pagination import Page

router = APIRouter(prefix="/service_calls", tags=["service_calls"])


@router.get("", response_model=Page[ServiceCallRead])
async def list_service_calls(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
    status_filter: ServiceCallStatus | None = Query(
        default=None, alias="status"
    ),
    priority: ServiceCallPriority | None = Query(default=None),
    atm_id: int | None = Query(default=None, ge=1),
    technician_id: int | None = Query(default=None, ge=1),
    search: str | None = Query(default=None, min_length=1),
    sort_by: str = Query(default="id"),
    sort_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.SERVICE_CALL_READ)),
):
    filters = [ServiceCall.is_active.is_(True)]

    if status_filter is not None:
        filters.append(ServiceCall.status == status_filter)

    if priority is not None:
        filters.append(ServiceCall.priority == priority)

    if atm_id is not None:
        filters.append(ServiceCall.atm_id == atm_id)

    if technician_id is not None:
        filters.append(ServiceCall.technician_id == technician_id)

    if search:
        filters.append(
            ServiceCall.title.ilike(f"%{search.strip()}%")
        )


    if current_user.role == UserRole.FIELD_TECHNICIAN:
        filters.append(
            ServiceCall.technician.has(
                Technician.user_id == current_user.id
            )
        )

    sortable_columns = {
        "id": ServiceCall.id,
        "title": ServiceCall.title,
        "status": ServiceCall.status,
        "priority": ServiceCall.priority,
        "atm_id": ServiceCall.atm_id,
        "technician_id": ServiceCall.technician_id,
    }

    sort_column = sortable_columns.get(sort_by)
    if sort_column is None:
        raise HTTPException(
            status_code=422,
            detail="Invalid sort field",
        )

    base_statement = select(ServiceCall).where(*filters)

    count_statement = select(func.count()).select_from(
        base_statement.order_by(None).subquery()
    )
    total_result = await db.execute(count_statement)
    total = total_result.scalar_one()

    sort_expression = (
        sort_column.desc() if sort_dir == "desc"
        else sort_column.asc()
    )

    statement = (
        base_statement
        .order_by(sort_expression, ServiceCall.id.asc())
        .offset((page - 1) * size)
        .limit(size)
    )

    result = await db.execute(statement)

    return {
        "items": list(result.scalars().all()),
        "total": total,
    }




@router.get("/inactive", response_model=list[ServiceCallRead])
async def inactive_records(db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.USER_MANAGE))):
    return list((await db.scalars(select(ServiceCall).where(ServiceCall.is_active.is_(False)).order_by(ServiceCall.id))).all())


@router.post("/{service_call_id}/restore", response_model=ServiceCallRead)
async def restore_record(service_call_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.USER_MANAGE))):
    obj = (await db.scalars(select(ServiceCall).where(ServiceCall.id == service_call_id, ServiceCall.is_active.is_(False)))).one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Inactive record not found")
    return await set_active(db, obj, "service_call", current_user.id, True)


@router.get("/{service_call_id}/history")
async def record_history(service_call_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.SERVICE_CALL_READ))):
    from app.models.audit_entry import AuditEntry
    obj = (await db.scalars(select(ServiceCall).where(ServiceCall.id == service_call_id, ServiceCall.is_active.is_(True)))).one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Record not found")
    if current_user.role == UserRole.FIELD_TECHNICIAN:
        if not (await db.scalars(select(Technician.id).where(Technician.id == obj.technician_id, Technician.user_id == current_user.id))).first():
            raise HTTPException(status_code=404, detail="Record not found")
    rows = (await db.scalars(select(AuditEntry).where(AuditEntry.record_type == "service_call", AuditEntry.record_id == service_call_id).order_by(AuditEntry.created_at, AuditEntry.id))).all()
    return [{"id": row.id, "action": row.action, "actor_id": row.actor_id,
             "created_at": row.created_at, "changes": row.changes} for row in rows]


@router.get("/{service_call_id}", response_model=ServiceCallRead)
async def get_service_call(
    service_call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_permission(Permission.SERVICE_CALL_READ))
) -> ServiceCall:

    statement = select(ServiceCall).where(ServiceCall.id == service_call_id, ServiceCall.is_active.is_(True))

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


@router.patch("/{service_call_id}", response_model=ServiceCallRead)
async def update_service_call(
    service_call_id: int,
    data: ServiceCallUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.SERVICE_CALL_WRITE)),
) -> ServiceCall:

    statement = select(ServiceCall).where(ServiceCall.id == service_call_id, ServiceCall.is_active.is_(True))
    result = await db.execute(statement)
    service_call = result.scalar_one_or_none()

    if service_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service call {service_call_id} not found",
        )

    await update_record(db, service_call, "service_call", current_user.id, data.model_dump(exclude_unset=True))

    return service_call


@router.patch("/{service_call_id}/status", response_model=ServiceCallRead)
async def update_service_call_status(
    service_call_id: int,
    data: UpdateStatus,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.SERVICE_CALL_STATUS)),
) -> ServiceCall:

    statement = (
        select(ServiceCall)
        .join(Technician, Technician.id == ServiceCall.technician_id)
        .where(
            ServiceCall.id == service_call_id,
            ServiceCall.is_active.is_(True),
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

    await update_record(db, service_call, "service_call", current_user.id, {"status": data.status}, "status_change")

    return service_call



@router.post("", response_model=ServiceCallRead, status_code=status.HTTP_201_CREATED)
async def create_service_call(
    payload: ServiceCallCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.SERVICE_CALL_WRITE)),
) -> ServiceCall:

    service_call = ServiceCall(**payload.model_dump())

    await create_record(db, service_call, "service_call", current_user.id)

    return service_call



@router.delete("/{service_call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_call(
    service_call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.SERVICE_CALL_WRITE)),
):
    statement = select(ServiceCall).where(
        ServiceCall.id == service_call_id, ServiceCall.is_active.is_(True)
    )

    result = await db.execute(statement)
    service_call = result.scalar_one_or_none()

    if service_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service call {service_call_id} not found",
        )

    await set_active(db, service_call, "service_call", current_user.id, False)