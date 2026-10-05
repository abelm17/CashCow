from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user, require_role
from app.models import Branch, UserRole
from app.schemas.branch import BranchCreate, BranchRead, BranchUpdate



router= APIRouter(prefix="/branches", tags=["branches"])

@router.get("", response_model=list[BranchRead], status_code=status.HTTP_200_OK)
async def list_branches(
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN,
        UserRole.AUDITOR
    ))
) -> list[Branch]:
    statement= select(Branch)
    result= await db.execute(statement)

    return list(result.scalars().all())


@router.get("/{branch_id}", response_model= BranchRead, status_code=status.HTTP_200_OK)
async def get_branch(
    branch_id: int,
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN,
        UserRole.AUDITOR
    ))
) -> Branch:
    statement= select(Branch).where(Branch.id == branch_id)
    result= await db.execute(statement)

    branch= result.scalar_one_or_none()

    if branch is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= f"Branch {branch_id} not found"
        )

    return branch


@router.patch("/{branch_id}", response_model=BranchRead, status_code= status.HTTP_202_ACCEPTED)
async def update_branch(
    branch_id: int,
    data: BranchUpdate,
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    ))
) -> Branch:
    statement= select(Branch).where(Branch.id == branch_id)
    result= await db.execute(statement)
    branch= result.scalar_one_or_none()

    if branch is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= f"Branch {branch_id} not found",
        )

    changes= data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(branch, field, value)

    await db.commit()
    await db.refresh(branch)
    return branch


@router.post("", response_model=BranchRead, status_code=status.HTTP_201_CREATED)
async def create_branch(
    payload: BranchCreate,
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    ))
) -> Branch:
    branch= Branch(**payload.model_dump())

    db.add(branch)
    await db.commit()
    await db.refresh(branch)

    return branch

@router.delete("/{branch_id}", status_code= status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: int,
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    ))
):
    statement= select(Branch).where(Branch.id == branch_id)
    result= await db.execute(statement)
    branch= result.scalar_one_or_none()

    if branch is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= f"Branch {branch_id} not found"
        )

    await db.delete(branch)
    await db.commit()
    