from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, require_permission
from app.models import Role
from app.permissions import Permission

router = APIRouter(prefix='/roles', tags=['roles'])

@router.get('', dependencies=[Depends(require_permission(Permission.USER_MANAGE))])
async def list_roles(db: AsyncSession = Depends(get_db)):
    roles = (await db.scalars(select(Role).order_by(Role.name))).all()
    return [
        {'id': role.id, 'name': role.name,
         'permissions': sorted(permission.name for permission in role.permissions)}
        for role in roles
    ]