# Run with this: python -m pytest scripts/test_pagination.py -v
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from app.routers.atms import list_atms
from app.models import UserRole


@pytest.fixture
def db():
    session = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def user():
    return SimpleNamespace(id=1, role=UserRole.OPERATIONS_ADMIN)


def mock_results(db, items=None, total=50):
    items = items if items is not None else []

    count_result = MagicMock()
    count_result.scalar_one.return_value = total

    rows_result = MagicMock()
    rows_result.scalars.return_value.all.return_value = items

    db.execute.side_effect = [count_result, rows_result]


async def run_list(db, user, **overrides):
    params = {
        "page": 1,
        "size": 25,
        "status_filter": None,
        "branch_id": None,
        "search": None,
        "sort_by": "id",
        "sort_dir": "asc",
        "db": db,
        "current_user": user,
    }
    params.update(overrides)
    return await list_atms(**params)


def sql_statements(db):
    return [
        str(call.args[0].compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        ))
        for call in db.execute.await_args_list
    ]


@pytest.mark.asyncio
async def test_first_page(db, user):
    mock_results(db, items=[1, 2, 3], total=50)

    result = await run_list(db, user)

    assert result["items"] == [1, 2, 3]
    assert result["total"] == 50
    assert db.execute.await_count == 2

    sql = sql_statements(db)[1]
    assert "LIMIT 25" in sql
    assert "OFFSET 0" in sql


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "page, offset",
    [(1, 0), (2, 10), (3, 20)],
)
async def test_page_boundaries(db, user, page, offset):
    mock_results(db, total=25)

    await run_list(db, user, page=page, size=10)

    sql = sql_statements(db)[1]
    assert "LIMIT 10" in sql
    assert f"OFFSET {offset}" in sql


@pytest.mark.asyncio
@pytest.mark.parametrize("direction", ["asc", "desc"])
async def test_sort_directions(db, user, direction):
    mock_results(db)

    await run_list(
        db, user, sort_by="cash_level", sort_dir=direction
    )

    sql = sql_statements(db)[1]
    assert f"cash_level {direction.upper()}" in sql


@pytest.mark.asyncio
async def test_status_filter(db, user):
    mock_results(db)

    await run_list(db, user, status_filter="active")

    count_sql, rows_sql = sql_statements(db)

    assert "status" in count_sql
    assert "status" in rows_sql


@pytest.mark.asyncio
async def test_branch_filter(db, user):
    mock_results(db)

    await run_list(db, user, branch_id=3)

    count_sql, rows_sql = sql_statements(db)

    assert "branch_id = 3" in count_sql
    assert "branch_id = 3" in rows_sql


@pytest.mark.asyncio
async def test_search_filter(db, user):
    mock_results(db)

    await run_list(db, user, search="NCR")

    count_sql, rows_sql = sql_statements(db)

    for sql in (count_sql, rows_sql):
        assert "ILIKE" in sql
        assert "model" in sql
        assert "serial_number" in sql


@pytest.mark.asyncio
async def test_combined_filters(db, user):
    mock_results(db)

    await run_list(
        db, user, branch_id=3, search="NCR"
    )

    count_sql, rows_sql = sql_statements(db)

    for sql in (count_sql, rows_sql):
        assert "branch_id = 3" in sql
        assert "ILIKE" in sql


@pytest.mark.asyncio
async def test_invalid_sort_field(db, user):
    with pytest.raises(HTTPException) as error:
        await run_list(db, user, sort_by="invalid_column")

    assert error.value.status_code == 422
    db.execute.assert_not_awaited()