from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.security import hash_password


router= APIRouter(prefix= "/users", tags= ["users"])

@router.get("", response_model=list[UserRead], status_code=status.HTTP_202_ACCEPTED)
async def list_users(
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    ))
) -> list[User]:
    statement= select(User).order_by(User.id)
    result= await db.execute(statement)

    return list(result.scalars().all())


@router.get("/{user_id}", response_model= UserRead)
async def get_user(
    user_id: int,
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    ))
) -> User:
    statement= select(User).where(User.id == user_id)
    result= await db.execute(statement)
    user= result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= f"Service call {user_id} not found"
        )
    
    return user

@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    ))
) -> User:
    
    statement= select(User).where(User.id == user_id)
    result= await db.execute(statement)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    changes= data.model_dump(exclude_unset= True)

    for field, value in changes.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.post("", response_model= UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    ))
) -> User:
    values= payload.model_dump()
    plain_password= values.pop("password")
    user= User(
        **values, 
        hashed_password= hash_password(plain_password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user

@router.delete("/{user_id}", status_code= status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession= Depends(get_db),
    current_user= Depends(require_role(
        UserRole.OPERATIONS_ADMIN
    ))
):
    statement= select(User).where(User.id == user_id)
    result= await db.execute(statement)
    user= result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= f"User {user_id} not found"
        )

    await db.delete(user)
    await db.commit()
    