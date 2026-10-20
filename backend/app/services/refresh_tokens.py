
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RefreshToken, RefreshSession, User
from app.security import (
    create_refresh_token,
    hash_refresh_token,
    refresh_expiry,
)


def unauthorized():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )


async def issue_refresh_token(
    db: AsyncSession,
    user_id: int,
    chain_id: uuid.UUID | None = None,
) -> str:
    raw_token = create_refresh_token()

    if chain_id is None:
        session = RefreshSession()
        db.add(session)
        await db.flush()
        chain_id = session.id

    record = RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(raw_token),
        chain_id=chain_id,
        expires_at=refresh_expiry(),
        revoked=False,
        rotated=False,
    )

    db.add(record)
    await db.flush()

    return raw_token


async def rotate_refresh_token(
    db: AsyncSession,
    raw_token: str,
) -> tuple[User, str]:
    token_hash = hash_refresh_token(raw_token)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )
    )
    record = result.scalar_one_or_none()

    if record is None:
        unauthorized()

    # Lock the session to serialize rotation/revocation.
    result = await db.execute(
        select(RefreshSession)
        .where(RefreshSession.id == record.chain_id)
        .with_for_update()
    )
    session = result.scalar_one_or_none()

    if session is None or session.revoked:
        unauthorized()

    if record.rotated:
        session.revoked = True

        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.chain_id == record.chain_id)
            .values(revoked=True)
        )

        await db.commit()
        unauthorized()

    if record.revoked:
        unauthorized()

    if record.expires_at <= datetime.now(timezone.utc):
        unauthorized()

    result = await db.execute(
        select(User).where(User.id == record.user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        session.revoked = True
        await db.commit()
        unauthorized()

    record.rotated = True
    record.revoked = True

    replacement = await issue_refresh_token(
        db=db,
        user_id=user.id,
        chain_id=record.chain_id,
    )

    await db.commit()

    return user, replacement


async def revoke_refresh_token(
    db: AsyncSession,
    raw_token: str,
) -> None:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash
            == hash_refresh_token(raw_token)
        )
    )
    record = result.scalar_one_or_none()

    if record is None:
        return

    result = await db.execute(
        select(RefreshSession)
        .where(RefreshSession.id == record.chain_id)
        .with_for_update()
    )
    session = result.scalar_one_or_none()

    if session is not None:
        session.revoked = True

        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.chain_id == record.chain_id)
            .values(revoked=True)
        )

        await db.commit()
