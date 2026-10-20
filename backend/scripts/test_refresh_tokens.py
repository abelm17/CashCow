# Run with this: python -m pytest scripts/test_refresh_tokens.py -v
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.refresh_tokens import (
    rotate_refresh_token,
    revoke_refresh_token,
)

@pytest.fixture
def db():
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    return session


def mock_results(db, *objects):
    db.execute.side_effect = [
        SimpleNamespace(scalar_one_or_none=lambda obj=obj: obj)
        for obj in objects
    ]


@pytest.fixture
def token_data():
    chain_id = uuid4()

    record = SimpleNamespace(
        user_id=1,
        chain_id=chain_id,
        revoked=False,
        rotated=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    session = SimpleNamespace(id=chain_id, revoked=False)
    user = SimpleNamespace(id=1)

    return record, session, user


@pytest.mark.asyncio
async def test_valid_refresh_token(db, token_data):
    record, session, user = token_data
    mock_results(db, record, session, user)

    with patch(
        "app.services.refresh_tokens.issue_refresh_token",
        new_callable=AsyncMock,
        return_value="new_refresh_token",
    ):
        result_user, new_token = await rotate_refresh_token(
            db, "old_refresh_token"
        )

    assert result_user is user
    assert new_token == "new_refresh_token"
    assert record.rotated is True
    assert record.revoked is True
    assert session.revoked is False
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_expired_refresh_token(db, token_data):
    record, session, user = token_data
    record.expires_at = datetime.now(timezone.utc) - timedelta(days=1)

    mock_results(db, record, session)

    with pytest.raises(HTTPException) as error:
        await rotate_refresh_token(db, "expired_token")

    assert error.value.status_code == 401
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_reused_refresh_token(db, token_data):
    record, session, user = token_data
    record.rotated = True

    mock_results(db, record, session, None)

    with pytest.raises(HTTPException) as error:
        await rotate_refresh_token(db, "reused_token")

    assert error.value.status_code == 401
    assert session.revoked is True
    db.commit.assert_awaited_once()
    assert db.execute.await_count == 3


@pytest.mark.asyncio
async def test_refresh_after_logout(db, token_data):
    record, session, user = token_data

    mock_results(db, record, session, None)
    await revoke_refresh_token(db, "refresh_token")

    assert session.revoked is True
    db.commit.assert_awaited_once()

    db.execute.reset_mock()
    mock_results(db, record, session)

    with pytest.raises(HTTPException) as error:
        await rotate_refresh_token(db, "refresh_token")

    assert error.value.status_code == 401
