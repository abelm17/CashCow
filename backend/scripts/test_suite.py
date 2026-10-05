# Test Suite for CashCow
# Run using this command: python -m pytest scripts/test_suite.py -v --tb=short

from datetime import datetime, timedelta
from types import SimpleNamespace
import importlib
import os
from pathlib import Path
import sys

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pytestmark = pytest.mark.asyncio
PASSWORD = "RouterTestPassword123!"
ADMIN, TECH, AUDITOR = 'admin', 'technician', 'auditor'
ALL = (ADMIN, TECH, AUDITOR)
READ = (ADMIN, AUDITOR)


CASES = []
for resource, readers, writers, patch_code in [
    ('users', (ADMIN,), (ADMIN,), 200),
    ('branches', READ, (ADMIN,), 202),
    ('atms', ALL, (ADMIN,), 202),
    ('service_calls', ALL, (ADMIN,), 200),
    ('diagnostic_reports', ALL, (ADMIN, TECH), 200),
]:
    CASES.extend([
        ('GET', f'/{resource}', readers, 202 if resource == 'users' else 200, None),
        ('GET', f'/{resource}/{{{resource}}}', readers, 200, None),
        ('POST', f'/{resource}', writers, 201, resource + '_create'),
        ('PATCH', f'/{resource}/{{{resource}}}', writers, patch_code, resource + '_update'),
        ('DELETE', f'/{resource}/{{delete_{resource}}}', (ADMIN,), 204, None),
    ])
CASES.append(('PATCH', '/service_calls/{service_calls}/status', (TECH,), 200, 'status'))
for path in ('low-cash', 'co-location-discrepancy', 'reliability', 'maintenance-flags', 'supervisors', 'reporting-lines/{supervisor}'):
    CASES.append(('GET', '/analytics/' + path, READ, 200, None))


def case_id(case):
    return case[0] + '-' + case[1]


async def snapshot(h):
    """Compare rows, not just counts, after forbidden/invalid operations."""
    async with AsyncSession(bind=h.connection, join_transaction_mode='create_savepoint') as db:
        return {table.name: [tuple(row) for row in (await db.execute(select(table).order_by(table.c.id))).all()]
                for table in h.models.Base.metadata.sorted_tables}


@pytest_asyncio.fixture
async def harness(monkeypatch):
    from app import database, dependencies, models, security
    
    module_name = 'app.main' if importlib.util.find_spec('app.main') else 'main'
    app = importlib.import_module(module_name).app
    assert database.engine.url.drivername == 'postgresql+asyncpg', 'This suite requires PostgreSQL/asyncpg.'
    old_overrides = app.dependency_overrides.copy()
    connection = await database.engine.connect()
    transaction = await connection.begin()

    def reject_extra_connection(dbapi_connection, connection_record, connection_proxy):
        raise RuntimeError('Test safety: application tried to open a connection outside the rollback transaction.')

    event.listen(database.engine.sync_engine, 'checkout', reject_extra_connection)
    factory = lambda: AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode='create_savepoint')
    monkeypatch.setattr(database, 'AsyncSessionLocal', factory)
    monkeypatch.setattr(dependencies, 'AsyncSessionLocal', factory)

    async def test_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[dependencies.get_db] = test_db
    h = SimpleNamespace(app=app, models=models, security=security, connection=connection, factory=factory)
    try:
        from uuid import uuid4
        prefix = 'rt' + uuid4().hex[:10]
        hashed = security.hash_password(PASSWORD)
        async with factory() as db:
            users = {}
            for key, role in [(ADMIN, models.UserRole.OPERATIONS_ADMIN), (TECH, models.UserRole.FIELD_TECHNICIAN),
                              (AUDITOR, models.UserRole.AUDITOR), ('other', models.UserRole.FIELD_TECHNICIAN),
                              ('supervisor2', models.UserRole.OPERATIONS_ADMIN), ('spare', models.UserRole.OPERATIONS_ADMIN),
                              ('delete', models.UserRole.AUDITOR)]:
                users[key] = models.User(name='Router Test ' + key, username=prefix + key[:8], hashed_password=hashed, role=role)
            db.add_all(users.values()); await db.flush()
            b1 = models.Branch(name='Router Test Branch', location_region='Test Region', capacity=10, supervisor_id=users[ADMIN].id)
            b2 = models.Branch(name='Other Test Branch', location_region='Test Region', capacity=10, supervisor_id=users['supervisor2'].id)
            bd = models.Branch(name='Delete Test Branch', location_region='Test Region', capacity=1, supervisor_id=users['delete'].id)
            db.add_all([b1, b2, bd]); await db.flush()
            t1 = models.Technician(name='Router Test Tech', user_id=users[TECH].id, branch_id=b1.id)
            t2 = models.Technician(name='Other Test Tech', user_id=users['other'].id, branch_id=b2.id)
            db.add_all([t1, t2]); await db.flush()
            a1 = models.Atm(serial_number=prefix+'a', model=prefix, status=models.AtmStatus.OPERATIONAL, cash_level=9999, branch_id=b1.id)
            a2 = models.Atm(serial_number=prefix+'b', model=prefix, status=models.AtmStatus.MAINTENANCE, cash_level=20000, branch_id=b1.id)
            ad = models.Atm(serial_number=prefix+'d', model=prefix, status=models.AtmStatus.OFFLINE, cash_level=0, branch_id=b2.id)
            db.add_all([a1, a2, ad]); await db.flush()
            calls = [models.ServiceCall(title='Router Test '+str(i), priority=models.ServiceCallPriority.LOW, status=s,
                                        atm_id=a.id, technician_id=t.id) for i, (a,t,s) in enumerate([
                (a1,t1,models.ServiceCallStatus.PENDING), (a2,t2,models.ServiceCallStatus.FAILED),
                (a1,t1,models.ServiceCallStatus.COMPLETED), (a1,t1,models.ServiceCallStatus.PENDING)])]
            db.add_all(calls); await db.flush()
            reports = [models.DiagnosticReport(file_url='https://example.com/test.pdf', notes='Router test report',
                        created_at=datetime(2026,1,1), service_call_id=calls[i].id, technician_id=t.id)
                       for i,t in [(0,t1),(1,t2)]]
            db.add_all(reports); await db.flush()
            h.ids = dict(users=users['delete'].id, branches=b1.id, atms=a1.id, service_calls=calls[0].id,
                         diagnostic_reports=reports[0].id, supervisor=users[ADMIN].id,
                         delete_users=users['spare'].id, delete_branches=bd.id, delete_atms=ad.id,
                         delete_service_calls=calls[3].id, delete_diagnostic_reports=reports[0].id)
            h.other_ids = {'atms': a2.id, 'service_calls': calls[1].id, 'diagnostic_reports': reports[1].id}
            h.prefix, h.branch, h.tech = prefix, b1.id, t1.id
            h.own_atms, h.own_calls, h.own_reports = {a1.id}, {calls[0].id,calls[2].id,calls[3].id}, {reports[0].id}
            h.usernames = {key:user.username for key,user in users.items()}
            h.user_ids = {key:user.id for key,user in users.items()}
            report = dict(file_url='https://example.com/new.pdf', notes='Updated test report', service_call_id=calls[0].id)
            h.payloads = {
                'users_create': dict(username=prefix+'new', password=PASSWORD, name='Created Test User', role='Auditor'),
                'users_update': dict(name='Updated Test User', username=prefix+'updated'),
                'branches_create': dict(name='Created Test Branch', location_region='Test Region', capacity=3, supervisor_id=users['spare'].id),
                'branches_update': dict(name='Updated Test Branch', capacity=20),
                'atms_create': dict(serial_number=prefix+'new', model=prefix, status='Offline', cash_level=20, branch_id=b1.id),
                'atms_update': dict(cash_level=12345, status='Offline'),
                'service_calls_create': dict(title='Created Test Call', priority='Low', status='Pending', atm_id=a1.id, technician_id=t1.id),
                'service_calls_update': dict(title='Updated Test Call', priority='Critical'),
                'diagnostic_reports_create': dict(**report, created_at='2026-01-01T00:00:00', technician_id=t1.id),
                'diagnostic_reports_update': report, 'status': dict(status='In-Progress'),
            }
            await db.commit()
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
            h.client = client
            h.headers = {}
            for role in ALL:
                response = await client.post('/auth/login', data={'username':h.usernames[role], 'password':PASSWORD})
                assert response.status_code == 200, f'Login for {role}: {response.status_code} {response.text}'
                assert response.json()['token_type'].lower() == 'bearer'
                h.headers[role] = {'Authorization':'Bearer '+response.json()['access_token']}
            yield h
    finally:
        app.dependency_overrides.clear(); app.dependency_overrides.update(old_overrides)
        try:
            await transaction.rollback()
        finally:
            event.remove(database.engine.sync_engine, 'checkout', reject_extra_connection)
            await connection.close()
            await database.engine.dispose()


@pytest.mark.parametrize('role', ALL)
@pytest.mark.parametrize('case', CASES, ids=case_id)
async def test_role_matrix(harness, role, case):
    h = harness
    method, template, allowed, success, payload_key = case
    path = template.format(**h.ids)
    payload = h.payloads.get(payload_key)
    before = await snapshot(h)
    response = await h.client.request(method, path, json=payload, headers=h.headers[role])
    expected = success if role in allowed else 403
    assert response.status_code == expected, f'{role} {method} {path}: expected {expected}, got {response.status_code}: {response.text}'
    after = await snapshot(h)
    if role not in allowed or method == 'GET':
        assert after == before, 'Forbidden/read request changed database rows.'
        return
    resource = path.split('/')[1]
    if method == 'DELETE':
        target = int(path.split('/')[2])
        assert response.content == b''
        assert after[resource] == [row for row in before[resource] if row[0] != target]
    else:
        body = response.json()
        assert isinstance(body, dict) and isinstance(body['id'], int)
        target = body['id']
        table = h.models.Base.metadata.tables[resource]
        async with h.factory() as db:
            saved = (await db.execute(select(table).where(table.c.id == target))).mappings().one()
        for key,value in payload.items():
            if key == 'password':
                assert h.security.verify_password(value, saved['hashed_password'])
                assert 'password' not in body and 'hashed_password' not in body
            elif key == 'created_at':
                assert saved[key] == datetime.fromisoformat(value)
            elif key in saved:
                assert saved[key] == value, f'{key} was not persisted'
        if method == 'POST':
            assert len(after[resource]) == len(before[resource]) + 1
        else:
            assert len(after[resource]) == len(before[resource])
    
    for name in before:
        if name != resource:
            assert after[name] == before[name], f'Unexpected change to {name}'
    assert [r for r in after[resource] if r[0] != target] == [r for r in before[resource] if r[0] != target]


@pytest.mark.parametrize('case', CASES, ids=case_id)
async def test_unauthenticated(harness, case):
    h = harness
    before = await snapshot(h)
    method,template,_,_,key = case
    r = await h.client.request(method, template.format(**h.ids), json=h.payloads.get(key))
    assert r.status_code == 401, r.text
    assert r.headers.get('www-authenticate') == 'Bearer'
    assert await snapshot(h) == before


@pytest.mark.parametrize('resource', ['atms','service_calls','diagnostic_reports'])
async def test_technician_list_is_scoped(harness, resource):
    h = harness
    r = await h.client.get('/'+resource, headers=h.headers[TECH])
    assert r.status_code == 200, r.text
    expected = getattr(h, {'atms':'own_atms','service_calls':'own_calls','diagnostic_reports':'own_reports'}[resource])
    assert {row['id'] for row in r.json()} == expected


@pytest.mark.parametrize('method,resource,suffix,key,expected', [
    ('GET','atms','',None,404), ('GET','service_calls','',None,404),
    ('GET','diagnostic_reports','',None,404),
    ('PATCH','service_calls','/status','status',404),
    ('PATCH','diagnostic_reports','','diagnostic_reports_update',404),
    ('POST','diagnostic_reports','', 'diagnostic_reports_create',403),
])
async def test_other_technician_records_are_blocked(harness, method,resource,suffix,key,expected):
    h = harness
    before = await snapshot(h)
    payload = dict(h.payloads[key]) if key else None
    if method == 'POST':
        path = '/'+resource
        payload['service_call_id'] = h.other_ids['service_calls']
    else:
        path = f'/{resource}/{h.other_ids[resource]}{suffix}'
    r = await h.client.request(method,path,json=payload,headers=h.headers[TECH])
    assert r.status_code == expected, r.text
    assert await snapshot(h) == before


@pytest.mark.parametrize('case', [c for c in CASES if '{' in c[1] and c[0] in ('GET','PATCH','DELETE')], ids=case_id)
async def test_missing_record(harness, case):
    h = harness
    method,template,allowed,_,key = case
    missing = {key: -2147483648 for key in h.ids}
    role = TECH if template.endswith('/status') else ADMIN
    before = await snapshot(h)
    r = await h.client.request(method, template.format(**missing), json=h.payloads.get(key), headers=h.headers[role])
    assert r.status_code == 404, r.text
    assert await snapshot(h) == before


@pytest.mark.parametrize('case', [c for c in CASES if c[0] in ('POST','PATCH')], ids=case_id)
async def test_invalid_body(harness, case):
    h = harness
    method,template,allowed,_,key = case
    before = await snapshot(h)
    r = await h.client.request(method,template.format(**h.ids),json=[],headers=h.headers[allowed[0]])
    assert r.status_code == 422, r.text
    assert await snapshot(h) == before


@pytest.mark.parametrize('kind', ['malformed','expired','missing_user','missing_sub'])
async def test_invalid_token(harness, kind):
    h = harness
    if kind == 'missing_user':
        async with h.factory() as db:
            user = await db.get(h.models.User, h.user_ids['spare'])
            await db.delete(user)
            await db.commit()
    if kind == 'malformed':
        token = 'not-a-jwt'
    else:
        data = {} if kind == 'missing_sub' else {'sub':str(h.user_ids['spare'] if kind == 'missing_user' else h.user_ids[ADMIN])}
        token = h.security.create_access_token(data, expires_delta=timedelta(seconds=-1) if kind == 'expired' else None)
    before = await snapshot(h)
    r = await h.client.get('/users',headers={'Authorization':'Bearer '+token})
    assert r.status_code == 401, r.text
    assert await snapshot(h) == before


@pytest.mark.parametrize('username,password', [('unknown','wrong'), (ADMIN,'wrong')])
async def test_bad_login(harness, username,password):
    h = harness
    before = await snapshot(h)
    r = await h.client.post('/auth/login',data={'username':h.usernames.get(username,h.prefix+'absent'),'password':password})
    assert r.status_code == 401, r.text
    assert await snapshot(h) == before


async def test_user_response_hides_password(harness):
    h = harness
    r = await h.client.get('/users',headers=h.headers[ADMIN])
    assert r.status_code == 202, r.text
    assert all('password' not in row and 'hashed_password' not in row for row in r.json())


async def test_atm_with_multiple_assigned_calls(harness):
    h = harness
    r = await h.client.get(f'/atms/{h.ids["atms"]}',headers=h.headers[TECH])
    assert r.status_code == 200, r.text
    assert r.json()['id'] == h.ids['atms']


@pytest.mark.parametrize('role', READ)
async def test_analytics_values(harness, role):
    h = harness
    async def get(path):
        r = await h.client.get('/analytics/'+path,headers=h.headers[role])
        assert r.status_code == 200, r.text
        return r.json()
    low = await get('low-cash')
    assert any(r['atm_id']==h.ids['atms'] and r['cash_level']==9999 for r in low)
    assert not any(r['atm_id']==h.other_ids['atms'] for r in low)
    discrepancies = await get('co-location-discrepancy')
    assert any(r['service_call_id']==h.other_ids['service_calls'] for r in discrepancies)
    assert not any(r['service_call_id']==h.ids['service_calls'] for r in discrepancies)
    metric = next(r for r in await get('reliability') if r['model']==h.prefix)
    assert metric == dict(model=h.prefix,total_service_calls=4,completed_count=1,failed_count=1,completion_failure_ratio=1.0)
    flag = next(r for r in await get('maintenance-flags') if r['branch_id']==h.branch)
    assert flag['total_atms']==2 and flag['maintenance_count']==1 and flag['maintenance_percentage']==50
    supervisors = await get('supervisors')
    assert h.ids['supervisor'] in {r['id'] for r in supervisors}
    assert not set(h.user_ids[k] for k in (TECH,AUDITOR,'other')) & {r['id'] for r in supervisors}
    lines = await get(f'reporting-lines/{h.ids["supervisor"]}')
    assert lines['technician_count']==1
    assert lines['technicians']==[dict(technician_id=h.tech,technician_name='Router Test Tech',active_service_call_count=2)]


@pytest.mark.parametrize('path', ['/health','/version'])
async def test_public_routes(harness,path):
    r = await harness.client.get(path)
    assert r.status_code == 200, r.text
    assert r.json() == ({'status':'ok'} if path=='/health' else {'version':harness.app.version})


async def test_endpoint_inventory(harness):
    """Check that all documented endpoints have test coverage."""
    schema = harness.app.openapi()

    actual = {
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method in operations
        if method.lower() in ("get", "post", "patch", "delete")
    }

    mapping = {
        "users": "user_id",
        "branches": "branch_id",
        "atms": "atm_id",
        "service_calls": "service_call_id",
        "diagnostic_reports": "diagnostic_report_id",
        "supervisor": "supervisor_id",
    }

    covered = set()

    for method, path, *_ in CASES:
        for key, value in mapping.items():
            path = path.replace(
                "{" + key + "}",
                "{" + value + "}",
            )
            path = path.replace(
                "{delete_" + key + "}",
                "{" + value + "}",
            )

        covered.add((method, path))

    covered.update({
        ("POST", "/auth/login"),
        ("GET", "/health"),
        ("GET", "/version"),
    })

    assert actual == covered, (
        f"Uncovered: {actual - covered}; "
        f"obsolete: {covered - actual}"
    )