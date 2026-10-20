from app.services.audited_writes import create_record, update_record, set_active
from app.permissions import Permission
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import Atm, UserRole, ServiceCall, Technician
from app.dependencies import get_db, get_current_user, require_permission
from app.schemas.atm import AtmCreate, AtmRead, AtmStatus, AtmUpdate
from app.schemas.pagination import Page


router= APIRouter(prefix="/atms", tags=["atms"])


@router.get("", response_model=Page[AtmRead])
async def list_atms(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),

    status_filter: AtmStatus | None = Query(
        default=None, alias="status"
    ),
    branch_id: int | None = Query(default=None, ge=1),
    search: str | None = Query(default=None, min_length=1),

    sort_by: str = Query(default="id"),
    sort_dir: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
    ),

    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.ATM_READ)),
):
    filters = [Atm.is_active.is_(True)]

    if status_filter is not None:
        filters.append(Atm.status == status_filter)

    if branch_id is not None:
        filters.append(Atm.branch_id == branch_id)

    if search:
        term = search.strip()
        if term:
            filters.append(
                Atm.model.ilike(f"%{term}%")
                | Atm.serial_number.ilike(f"%{term}%")
            )

    if current_user.role == UserRole.FIELD_TECHNICIAN:
        filters.append(
            Atm.service_calls.any(
                ServiceCall.technician.has(
                    Technician.user_id == current_user.id
                )
            )
        )

    sortable_columns = {
        "id": Atm.id,
        "model": Atm.model,
        "serial_number": Atm.serial_number,
        "status": Atm.status,
        "cash_level": Atm.cash_level,
        "branch_id": Atm.branch_id,
    }

    sort_column = sortable_columns.get(sort_by)

    if sort_column is None:
        raise HTTPException(
            status_code=422,
            detail="Invalid sort field",
        )

    base_statement = select(Atm).where(*filters)

    count_statement = select(func.count()).select_from(
        base_statement.order_by(None).subquery()
    )

    total_result = await db.execute(count_statement)
    total = total_result.scalar_one()

    sort_expression = (
        sort_column.desc()
        if sort_dir == "desc"
        else sort_column.asc()
    )

    statement = (
        base_statement
        .order_by(sort_expression, Atm.id.asc())
        .offset((page - 1) * size)
        .limit(size)
    )

    result = await db.execute(statement)
    items = list(result.scalars().all())

    return {
        "items": items,
        "total": total,
    }





@router.get("/inactive", response_model=list[AtmRead])
async def inactive_records(db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.USER_MANAGE))):
    return list((await db.scalars(select(Atm).where(Atm.is_active.is_(False)).order_by(Atm.id))).all())


@router.post("/{atm_id}/restore", response_model=AtmRead)
async def restore_record(atm_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.USER_MANAGE))):
    obj = (await db.scalars(select(Atm).where(Atm.id == atm_id, Atm.is_active.is_(False)))).one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Inactive record not found")
    return await set_active(db, obj, "atm", current_user.id, True)


@router.get("/{atm_id}/history")
async def record_history(atm_id: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.ATM_READ))):
    from app.models.audit_entry import AuditEntry
    obj = (await db.scalars(select(Atm).where(Atm.id == atm_id, Atm.is_active.is_(True)))).one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Record not found")
    if current_user.role == UserRole.FIELD_TECHNICIAN:
        from app.models import Technician
        allowed = (await db.scalars(select(ServiceCall.id).join(Technician, Technician.id == ServiceCall.technician_id).where(ServiceCall.atm_id == obj.id, Technician.user_id == current_user.id, ServiceCall.is_active.is_(True)))).first() is not None
        if not allowed:
            raise HTTPException(status_code=404, detail="Record not found")
    rows = (await db.scalars(select(AuditEntry).where(AuditEntry.record_type == "atm", AuditEntry.record_id == atm_id).order_by(AuditEntry.created_at, AuditEntry.id))).all()
    return [{"id": row.id, "action": row.action, "actor_id": row.actor_id,
             "created_at": row.created_at, "changes": row.changes} for row in rows]


@router.get("/{atm_id}", response_model=AtmRead)
async def get_atm(
    atm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.ATM_READ)),
):
    if current_user.role == UserRole.FIELD_TECHNICIAN:
        statement = (
            select(Atm)
            .join(ServiceCall, ServiceCall.atm_id == Atm.id)
            .join(Technician, Technician.id == ServiceCall.technician_id)
            .where(
                Atm.id == atm_id,
                Atm.is_active.is_(True),
                Technician.user_id == current_user.id,
            )
        )

        result = await db.execute(statement)
        atm = result.scalars().unique().one_or_none()
    else:
        atm = (await db.execute(select(Atm).where(Atm.id == atm_id, Atm.is_active.is_(True)))).scalar_one_or_none()

    if atm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atm {atm_id} not found",
        )

    return atm

@router.post("", response_model= AtmRead, status_code=status.HTTP_201_CREATED)
async def create_atm(
    payload: AtmCreate,
    db: AsyncSession= Depends(get_db), 
    current_user= Depends(require_permission(Permission.ATM_WRITE))
):
    atm= Atm(**payload.model_dump())

    await create_record(db, atm, "atm", current_user.id)
    return atm

@router.patch("/{atm_id}", response_model=AtmRead, status_code=status.HTTP_202_ACCEPTED)
async def update_atm(
    atm_id: int,
    data: AtmUpdate,
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_permission(Permission.ATM_WRITE))
) -> Atm:
    statement= select(Atm).where(Atm.id == atm_id, Atm.is_active.is_(True))
    result= await db.execute(statement)
    atm= result.scalar_one_or_none()

    if atm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ATM {atm_id} not found",
        )

    await update_record(db, atm, "atm", current_user.id, data.model_dump(exclude_unset=True))

    return atm


@router.delete("/{atm_id}", status_code= status.HTTP_204_NO_CONTENT)
async def delete_atm(
    atm_id: int,
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_permission(Permission.ATM_WRITE))
):
    statement= select(Atm).where(Atm.id == atm_id, Atm.is_active.is_(True))
    result= await db.execute(statement)
    atm= result.scalar_one_or_none()

    if atm is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= f"Atm {atm_id} not found"
        )

    await set_active(db, atm, "atm", current_user.id, False)