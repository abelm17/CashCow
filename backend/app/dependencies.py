"""Shared FastAPI dependencies."""

from collections.abc import AsyncGenerator

import jwt
import asyncio
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.database import AsyncSessionLocal
from app.models import User, UserRole
from app.security import decode_access_token


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception

        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise credentials_exception

        user_id = int(subject)
        # User.id is a PostgreSQL INTEGER; reject out-of-range values before SQL.
        if not 1 <= user_id <= 2_147_483_647:
            raise credentials_exception
    except (jwt.InvalidTokenError, ValueError):
        raise credentials_exception

    try:
        result = await asyncio.wait_for(
            db.execute(select(User).where(User.id == user_id)),
            timeout=2.0,
        )
    except (SQLAlchemyError, OSError, TimeoutError):
        raise HTTPException(
            status_code= status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from None
    
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


def require_role(*allowed_roles: UserRole):
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{current_user.role.value}' "
                    "is not permitted to perform this action"
                ),
            )
        return current_user

    return role_checker
