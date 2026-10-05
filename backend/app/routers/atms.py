from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Atm, UserRole, ServiceCall, Technician
from app.dependencies import get_db, get_current_user, require_role
from app.schemas.atm import AtmCreate, AtmRead, AtmStatus, AtmUpdate


router= APIRouter(prefix="/atms", tags=["atms"])


@router.get("", response_model=list[AtmRead])
async def list_atms(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(
        UserRole.OPERATIONS_ADMIN,
        UserRole.FIELD_TECHNICIAN,
        UserRole.AUDITOR,
    )),
):
    if current_user.role == UserRole.FIELD_TECHNICIAN:
        statement = (
            select(Atm)
            .join(ServiceCall, ServiceCall.atm_id == Atm.id)
            .join(Technician, Technician.id == ServiceCall.technician_id)
            .where(Technician.user_id == current_user.id)
            .distinct()
            .order_by(Atm.id)
        )
    else:
        statement = select(Atm).order_by(Atm.id)

    result = await db.execute(statement)
    return list(result.scalars().all())


@router.get("/{atm_id}", response_model=AtmRead)
async def get_atm(
    atm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(
        UserRole.OPERATIONS_ADMIN,
        UserRole.FIELD_TECHNICIAN,
        UserRole.AUDITOR,
    )),
):
    if current_user.role == UserRole.FIELD_TECHNICIAN:
        statement = (
            select(Atm)
            .join(ServiceCall, ServiceCall.atm_id == Atm.id)
            .join(Technician, Technician.id == ServiceCall.technician_id)
            .where(
                Atm.id == atm_id,
                Technician.user_id == current_user.id,
            )
        )

        result = await db.execute(statement)
        atm = result.scalars().unique().one_or_none()
    else:
        atm = await db.get(Atm, atm_id)

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
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    ))
):
    atm= Atm(**payload.model_dump())

    db.add(atm)
    await db.commit()
    await db.refresh(atm)
    return atm

@router.patch("/{atm_id}", response_model=AtmRead, status_code=status.HTTP_202_ACCEPTED)
async def update_atm(
    atm_id: int,
    data: AtmUpdate,
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    ))
) -> Atm:
    statement= select(Atm).where(Atm.id == atm_id)
    result= await db.execute(statement)
    atm= result.scalar_one_or_none()

    if atm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ATM {atm_id} not found",
        )

    changes= data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(atm, field, value)

    await db.commit()
    await db.refresh(atm)

    return atm


@router.delete("/{atm_id}", status_code= status.HTTP_204_NO_CONTENT)
async def delete_atm(
    atm_id: int,
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    ))
):
    statement= select(Atm).where(Atm.id == atm_id)
    result= await db.execute(statement)
    atm= result.scalar_one_or_none()

    if atm is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= f"Atm {atm_id} not found"
        )

    await db.delete(atm)
    await db.commit()
    

