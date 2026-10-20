"""Run from backend: python -m scripts.seed_permissions

Seeds missing roles/permissions without overwriting subsequent administrator edits.
"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Role, PermissionModel, UserRole
from app.permissions import Permission

ROLE_DEFAULTS = {
    UserRole.OPERATIONS_ADMIN.value: {
        Permission.ATM_READ, Permission.ATM_WRITE,
        Permission.BRANCH_READ, Permission.BRANCH_WRITE,
        Permission.SERVICE_CALL_READ, Permission.SERVICE_CALL_WRITE,
        Permission.REPORT_READ, Permission.REPORT_UPLOAD,
        Permission.REPORT_WRITE, Permission.REPORT_DELETE,
        Permission.ANALYTICS_READ, Permission.USER_MANAGE,
        Permission.HEALTH_DETAIL,
    },
    UserRole.FIELD_TECHNICIAN.value: {
        Permission.ATM_READ, Permission.SERVICE_CALL_READ,
        Permission.SERVICE_CALL_STATUS, Permission.REPORT_READ,
        Permission.REPORT_UPLOAD, Permission.REPORT_WRITE,
    },
    UserRole.AUDITOR.value: {
        Permission.ATM_READ, Permission.BRANCH_READ,
        Permission.SERVICE_CALL_READ, Permission.REPORT_READ,
        Permission.ANALYTICS_READ,
    },
}

async def main():
    async with AsyncSessionLocal() as db:
        async with db.begin():
            existing = {p.name: p for p in (await db.scalars(select(PermissionModel))).all()}
            for permission in Permission:
                if permission.value not in existing:
                    row = PermissionModel(name=permission.value)
                    db.add(row)
                    existing[permission.value] = row
            await db.flush()
            roles = {r.name: r for r in (await db.scalars(select(Role))).all()}
            for name, permissions in ROLE_DEFAULTS.items():
                if name not in roles:
                    db.add(Role(name=name, permissions=[existing[p.value] for p in permissions]))
    print('Missing permission definitions and default roles seeded.')

if __name__ == '__main__':
    asyncio.run(main())