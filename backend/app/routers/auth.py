from fastapi import (APIRouter, Depends, HTTPException, Response, Cookie, status)
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.config import settings
from app.dependencies import get_db, get_current_user
from app.models import User, Role
from app.schemas.user import Token
from app.security import (create_access_token, verify_password)
from app.services.refresh_tokens import (issue_refresh_token, rotate_refresh_token, revoke_refresh_token)


router = APIRouter(prefix="/auth", tags=["Authentication"])


def generate_access_token(user: User) -> str:
    return create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value,
    })


def set_refresh_cookie(
    response: Response,
    token: str,
):
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=(
            settings.refresh_token_expire_days
            * 24 * 60 * 60
        ),
        path="/auth",
    )


def clear_refresh_cookie(response: Response):
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path="/auth",
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .where(
            User.username == form_data.username
        )
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = generate_access_token(user)

    refresh_token = await issue_refresh_token(
        db=db,
        user_id=user.id,
    )

    await db.commit()

    set_refresh_cookie(response, refresh_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(
        default=None,
        alias="refresh_token",
    ),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Refresh token missing",
        )

    user, replacement = await rotate_refresh_token(db, refresh_token)
    access_token = generate_access_token(user)

    set_refresh_cookie(response, replacement)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(
        default=None,
        alias="refresh_token",
    ),
    db: AsyncSession = Depends(get_db),
):
    if refresh_token:
        await revoke_refresh_token(db, refresh_token)

    clear_refresh_cookie(response)

    return {"message": "Logged out"}

@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Role).where(
            Role.name == current_user.role.value
        )
    )

    role = result.scalar_one_or_none()

    permissions = (
        sorted(permission.name for permission in role.permissions)
        if role
        else []
    )

    return {
        "id": current_user.id,
        "username": current_user.username,
        "name": current_user.name,
        "role": current_user.role.value,
        "permissions": permissions,
    }