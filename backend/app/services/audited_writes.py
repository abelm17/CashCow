"""All ATM/service-call writes and audit entries share one transaction.

Call these functions instead of mutating audited models in route handlers.
The caller must not commit independently before these functions return.
"""
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_entry import AuditEntry


def serialize(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def audit(db: AsyncSession, kind: str, record_id: int, action: str, actor_id: int, changes: dict):
    db.add(AuditEntry(record_type=kind, record_id=record_id, action=action,
                      actor_id=actor_id, changes=changes))


async def create_record(db, obj, kind, actor_id):
    db.add(obj)
    await db.flush()
    changes = {key: {"before": None, "after": serialize(getattr(obj, key))}
               for key in obj.__table__.columns.keys()
               if key not in ("deleted_at", "deleted_by")}
    audit(db, kind, obj.id, "create", actor_id, changes)
    await db.commit()
    await db.refresh(obj)
    return obj


async def update_record(db, obj, kind, actor_id, values, action="update"):
    changes = {}
    for key, value in values.items():
        before = getattr(obj, key)
        if before != value:
            changes[key] = {"before": serialize(before), "after": serialize(value)}
            setattr(obj, key, value)
    if changes:
        audit(db, kind, obj.id, action, actor_id, changes)
        await db.commit()
        await db.refresh(obj)
    return obj


async def set_active(db, obj, kind, actor_id, active):
    if obj.is_active == active:
        return obj
    when = None if active else datetime.now(timezone.utc)
    values = {"is_active": active, "deleted_at": when,
              "deleted_by": None if active else actor_id}
    return await update_record(db, obj, kind, actor_id, values,
                               "restore" if active else "delete")