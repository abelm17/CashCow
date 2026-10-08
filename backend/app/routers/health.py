"""Database readiness and admin-only dependency diagnostics."""

import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_role
from app.models import UserRole
from app.storage import get_s3_bucket, get_s3_client

router = APIRouter(prefix="/health", tags=["health"])
DATABASE_CHECK_TIMEOUT = 2.0
S3_CHECK_TIMEOUT = 3.0


async def check_database(db: AsyncSession) -> dict[str, str]:
    try:
        result = await asyncio.wait_for(
            db.execute(text("SELECT 1")),
            timeout=DATABASE_CHECK_TIMEOUT,
        )
        if result.scalar() != 1:
            return {"status": "unavailable"}
        return {"status": "ok"}
    except Exception:
        return {"status": "unavailable"}


def _head_bucket(bucket: str) -> None:
    get_s3_client().head_bucket(Bucket=bucket)


async def check_s3() -> dict[str, str]:
    try:
        bucket = get_s3_bucket()
        if bucket is None:
            return {"status": "not_configured"}
        await asyncio.wait_for(
            asyncio.to_thread(_head_bucket, bucket),
            timeout=S3_CHECK_TIMEOUT,
        )
        return {"status": "ok"}
    except Exception:
        return {"status": "unavailable"}


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    database = await check_database(db)
    healthy = database["status"] == "ok"
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "not_ready"},
        headers={"Cache-Control": "no-store"},
    )


@router.get("/detail")
async def health_detail(
    current_user=Depends(require_role(UserRole.OPERATIONS_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    database, s3 = await asyncio.gather(check_database(db), check_s3())
    healthy = database["status"] == "ok" and s3["status"] == "ok"
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "ok" if healthy else "degraded",
            "dependencies": {"database": database, "s3": s3},
        },
        headers={"Cache-Control": "no-store"},
    )
