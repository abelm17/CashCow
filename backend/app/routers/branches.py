from app.permissions import Permission
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db, get_current_user, require_permission
from app.models import Branch
from app.schemas.branch import BranchCreate, BranchRead, BranchUpdate
from app.schemas.pagination import Page


router= APIRouter(prefix="/branches", tags=["branches"])

@router.get("", response_model=Page[BranchRead],
            status_code=status.HTTP_200_OK)
async def list_branches(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
    name: str | None = Query(default=None, min_length=1),
    location_region: str | None = Query(default=None, min_length=1),
    supervisor_id: int | None = Query(default=None, ge=1),
    sort_by: str = Query(default="id"),
    sort_dir: str = Query(default="asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission(Permission.BRANCH_READ)),
):
    filters = []

    if name:
        filters.append(Branch.name.ilike(f"%{name.strip()}%"))

    if location_region:
        filters.append(
            Branch.location_region.ilike(
                f"%{location_region.strip()}%"
            )
        )

    if supervisor_id is not None:
        filters.append(Branch.supervisor_id == supervisor_id)

    sortable_columns = {
        "id": Branch.id,
        "name": Branch.name,
        "location_region": Branch.location_region,
        "capacity": Branch.capacity,
        "supervisor_id": Branch.supervisor_id,
    }

    sort_column = sortable_columns.get(sort_by)
    if sort_column is None:
        raise HTTPException(
            status_code=422,
            detail="Invalid sort field",
        )

    base_statement = select(Branch).where(*filters)

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
        .order_by(sort_expression, Branch.id.asc())
        .offset((page - 1) * size)
        .limit(size)
    )

    result = await db.execute(statement)

    return {
        "items": list(result.scalars().all()),
        "total": total,
    }


@router.get("/{branch_id}", response_model= BranchRead, status_code=status.HTTP_200_OK)
async def get_branch(
    branch_id: int,
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_permission(Permission.BRANCH_READ))
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
    current_user= Depends(require_permission(Permission.BRANCH_WRITE))
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
    current_user= Depends(require_permission(Permission.BRANCH_WRITE))
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
    current_user= Depends(require_permission(Permission.BRANCH_WRITE))
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