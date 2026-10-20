
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.audited_writes import (
    create_record,
    update_record,
    set_active,
)


@pytest.fixture
def db():
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def record():
    return SimpleNamespace(
        id=1,
        is_active=True,
        deleted_at=None,
        deleted_by=None,
        status="Pending",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["atm", "service_call"])
async def test_soft_delete(db, record, kind):
    await set_active(db, record, kind, actor_id=5, active=False)

    assert record.is_active is False
    assert record.deleted_at is not None
    assert record.deleted_by == 5

    db.delete.assert_not_called()
    db.commit.assert_awaited_once()

    entry = db.add.call_args.args[0]
    assert entry.action == "delete"
    assert entry.record_type == kind
    assert entry.actor_id == 5


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["atm", "service_call"])
async def test_restore(db, record, kind):
    record.is_active = False
    record.deleted_at = "previous deletion"
    record.deleted_by = 5

    await set_active(db, record, kind, actor_id=2, active=True)

    assert record.is_active is True
    assert record.deleted_at is None
    assert record.deleted_by is None

    entry = db.add.call_args.args[0]
    assert entry.action == "restore"
    assert entry.actor_id == 2


@pytest.mark.asyncio
async def test_create_audit(db):
    record = SimpleNamespace(
        id=1,
        title="Fix ATM",
        __table__=SimpleNamespace(
            columns={"id": None, "title": None}
        ),
    )

    await create_record(db, record, "service_call", actor_id=5)

    db.flush.assert_awaited_once()
    db.commit.assert_awaited_once()

    entry = db.add.call_args.args[0]
    assert entry.action == "create"
    assert entry.record_id == 1
    assert entry.changes["title"]["after"] == "Fix ATM"


@pytest.mark.asyncio
async def test_status_change_audit(db, record):
    await update_record(
        db, record, "service_call", actor_id=5,
        values={"status": "Completed"},
        action="status_change",
    )

    assert record.status == "Completed"

    entry = db.add.call_args.args[0]
    assert entry.action == "status_change"
    assert entry.changes["status"] == {
        "before": "Pending",
        "after": "Completed",
    }


@pytest.mark.asyncio
async def test_no_audit_when_nothing_changes(db, record):
    await update_record(
        db, record, "service_call", actor_id=5,
        values={"status": "Pending"},
    )

    db.add.assert_not_called()
    db.commit.assert_not_awaited()
