# Run from backend folder: python -m pytest scripts/test_health.py -q
import os
from unittest.mock import patch

import httpx
import pytest
import pytest_asyncio

from app.main import app
from app.dependencies import get_current_user, get_db
from app.models import UserRole
from app.routers import health


class FakeResult:
    def scalar(self):
        return 1


class FakeDatabase:
    def __init__(self):
        self.available = True
        self.calls = 0

    async def execute(self, statement):
        self.calls += 1
        assert str(statement) == "SELECT 1"
        if not self.available:
            raise ConnectionError("private-database-host")
        return FakeResult()


class FakeUser:
    def __init__(self, role):
        self.role = role


def use_role(role):
    async def fake_user():
        return FakeUser(role)

    app.dependency_overrides[get_current_user] = fake_user


@pytest_asyncio.fixture
async def client():
    database = FakeDatabase()
    original_overrides = app.dependency_overrides.copy()

    async def fake_db():
        yield database

    def fake_head_bucket(bucket):
        pass

    app.dependency_overrides[get_db] = fake_db
    transport = httpx.ASGITransport(app=app)
    try:
        with patch.dict(os.environ, {"S3_BUCKET": "test-bucket"}):
            with patch.object(health, "_head_bucket", fake_head_bucket):
                async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
                    yield http, database
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)


@pytest.mark.asyncio
async def test_health_does_not_use_database(client):
    http, database = client
    database.available = False

    response = await http.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert database.calls == 0


@pytest.mark.asyncio
async def test_ready_when_database_works(client):
    http, database = client

    response = await http.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert database.calls == 1


@pytest.mark.asyncio
async def test_ready_when_database_is_down(client):
    http, database = client
    database.available = False

    response = await http.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    assert "private-database-host" not in response.text


@pytest.mark.asyncio
async def test_admin_can_view_details(client):
    http, database = client
    use_role(UserRole.OPERATIONS_ADMIN)

    response = await http.get("/health/detail")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "dependencies": {
            "database": {"status": "ok"},
            "s3": {"status": "ok"},
        },
    }


@pytest.mark.asyncio
async def test_details_require_admin(client):
    http, database = client

    response = await http.get("/health/detail")
    assert response.status_code == 401

    for role in [UserRole.AUDITOR, UserRole.FIELD_TECHNICIAN]:
        use_role(role)
        response = await http.get("/health/detail")
        assert response.status_code == 403

    assert database.calls == 0


@pytest.mark.asyncio
async def test_details_report_s3_failure(client):
    http, database = client
    use_role(UserRole.OPERATIONS_ADMIN)

    def failing_head_bucket(bucket):
        raise ConnectionError("private-bucket-name")

    with patch.object(health, "_head_bucket", failing_head_bucket):
        response = await http.get("/health/detail")

    assert response.status_code == 503
    assert response.json()["dependencies"] == {
        "database": {"status": "ok"},
        "s3": {"status": "unavailable"},
    }
    assert "private-bucket-name" not in response.text
    assert (await http.get("/health/ready")).status_code == 200
