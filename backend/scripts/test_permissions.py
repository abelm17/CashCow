# Run with this: python -m pytest scripts/test_permissions.py -v
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.dependencies import require_permission
from app.permissions import Permission


@pytest.fixture
def db():
    session = MagicMock()
    session.execute = AsyncMock()
    return session


def mock_role(db, permissions):
    role = SimpleNamespace(
        permissions=[
            SimpleNamespace(name=name)
            for name in permissions
        ]
    )

    result = MagicMock()
    result.scalar_one_or_none.return_value = role
    db.execute.return_value = result


@pytest.mark.asyncio
async def test_permission_granted(db):
    user = SimpleNamespace(role=SimpleNamespace(value="Operations Admin"))
    mock_role(db, ["atm:read", "atm:write"])

    checker = require_permission(Permission.ATM_WRITE)
    result = await checker(current_user=user, db=db)

    assert result is user


@pytest.mark.asyncio
async def test_permission_denied(db):
    user = SimpleNamespace(role=SimpleNamespace(value="Auditor"))
    mock_role(db, ["atm:read"])

    checker = require_permission(Permission.ATM_WRITE)

    with pytest.raises(HTTPException) as error:
        await checker(current_user=user, db=db)

    assert error.value.status_code == 403
    assert "atm:write" in error.value.detail


@pytest.mark.asyncio
async def test_permission_granted_after_change(db):
    user = SimpleNamespace(role=SimpleNamespace(value="Auditor"))
    mock_role(db, ["atm:read", "atm:write"])

    checker = require_permission(Permission.ATM_WRITE)
    result = await checker(current_user=user, db=db)

    assert result is user


@pytest.mark.asyncio
async def test_role_not_found(db):
    user = SimpleNamespace(role=SimpleNamespace(value="Unknown Role"))

    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    checker = require_permission(Permission.ATM_READ)

    with pytest.raises(HTTPException) as error:
        await checker(current_user=user, db=db)

    assert error.value.status_code == 403
