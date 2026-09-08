import hashlib
import sqlite3
import time

import pytest
from fastapi.testclient import TestClient
from backend.app import create_app, COOKIE

PASSWORD = 'A reference passphrase 2026!'
HEADERS = {'X-Workbench-Request': '1'}


@pytest.fixture
def setup(tmp_path):
    path = tmp_path / 'test.sqlite3'
    app = create_app(path)
    return app, path


def client(app):
    return TestClient(app, base_url='http://127.0.0.1', headers=HEADERS)


def register(c, username='alice'):
    response = c.post('/api/auth/register', json={'username': username, 'display_name': username.title(), 'password': PASSWORD})
    assert response.status_code == 201, response.text
    c.headers['X-CSRF-Token'] = response.json()['csrf_token']
    return response


def test_registration_hash_and_cookie(setup):
    app, path = setup
    with client(app) as c:
        response = register(c, 'ALICE')
        assert response.json()['user']['username'] == 'alice'
        assert 'password' not in response.text
        cookie = response.headers['set-cookie'].lower()
        assert 'httponly' in cookie and 'samesite=strict' in cookie
        token = c.cookies.get(COOKIE)
        with sqlite3.connect(path) as db:
            saved = db.execute('SELECT password_hash FROM users').fetchone()[0]
            session = db.execute('SELECT token_hash FROM sessions').fetchone()[0]
        assert saved.startswith('$argon2id$') and PASSWORD not in saved
        assert session == hashlib.sha256(token.encode()).hexdigest()
        assert c.get('/api/auth/me').status_code == 200


def test_two_users_cannot_access_each_others_workspaces(setup):
    app, _ = setup
    with client(app) as alice, client(app) as bob:
        register(alice)
        item = alice.post('/api/workspaces', json={'name':'Inspection review','description':'Private notes'})
        assert item.status_code == 201
        workspace_id = item.json()['id']
        register(bob, 'bob')
        assert bob.get('/api/workspaces').json() == {'workspaces': []}
        assert bob.get(f'/api/workspaces/{workspace_id}').status_code == 404
        assert alice.get(f'/api/workspaces/{workspace_id}').json()['name'] == 'Inspection review'
        spoof = bob.post('/api/workspaces', json={'name':'Spoof', 'owner_id':item.json()['id']})
        assert spoof.status_code == 422


def test_logout_revokes_session_and_relogin(setup):
    app, _ = setup
    with client(app) as c:
        register(c)
        old = c.cookies.get(COOKIE)
        assert c.post('/api/auth/logout').status_code == 200
        assert c.get('/api/auth/me').status_code == 401
        c.cookies.set(COOKIE, old)
        assert c.get('/api/auth/me').status_code == 401
        c.cookies.clear()
        response = c.post('/api/auth/login',json={'username':'alice','password':PASSWORD})
        assert response.status_code == 200
        assert c.cookies.get(COOKIE) != old


def test_persistence_across_app_instances(setup):
    app, path = setup
    with client(app) as c:
        register(c)
        assert c.post('/api/workspaces',json={'name':'Persistent workspace'}).status_code == 201
    with client(create_app(path)) as fresh:
        assert fresh.post('/api/auth/login',json={'username':'alice','password':PASSWORD}).status_code == 200
        assert fresh.get('/api/workspaces').json()['workspaces'][0]['name'] == 'Persistent workspace'


def test_expired_session(setup):
    app, path = setup
    with client(app) as c:
        register(c)
        with sqlite3.connect(path) as db:
            db.execute('UPDATE sessions SET expires_at=?', (int(time.time())-1,))
        assert c.get('/api/auth/me').status_code == 401


def test_csrf_origin_and_missing_header(setup):
    app, _ = setup
    with client(app) as c:
        register(c)
        assert c.post('/api/workspaces',json={'name':'Rejected'},headers={'X-CSRF-Token':'bad'}).status_code == 403
        assert c.post('/api/workspaces',json={'name':'Rejected'},headers={'Origin':'https://evil.example'}).status_code == 403
        assert c.post('/api/workspaces',json={'name':'Rejected'},headers={'X-Workbench-Request':''}).status_code == 403
        assert c.post('/api/workspaces',json={'name':'Accepted'},headers={'Origin':'http://127.0.0.1'}).status_code == 201


def test_validation_duplicates_wrong_password(setup):
    app, _ = setup
    with client(app) as c:
        register(c)
        assert c.post('/api/auth/register',json={'username':'ALICE','display_name':'Other','password':PASSWORD}).status_code == 409
        assert c.post('/api/auth/register',json={'username':'short','display_name':'Short','password':'short'}).status_code == 422
        assert c.post('/api/auth/login',json={'username':'alice','password':'wrong-password-123'}).status_code == 401
        assert c.post('/api/auth/login',json={'username':'nobody','password':PASSWORD}).status_code == 401
        assert c.post('/api/workspaces',json={'name':'   '}).status_code == 422


def test_rate_limit(setup):
    app, _ = setup
    with client(app) as c:
        for _ in range(10):
            assert c.post('/api/auth/login',json={'username':'nobody','password':PASSWORD}).status_code == 401
        assert c.post('/api/auth/login',json={'username':'nobody','password':PASSWORD}).status_code == 429


def test_anonymous_protection_and_headers(setup):
    app, _ = setup
    with client(app) as c:
        assert c.get('/api/workspaces').status_code == 401
        assert c.post('/api/workspaces',json={'name':'Anonymous'}).status_code == 401
        response = c.get('/')
        assert response.status_code == 200
        assert "connect-src 'self'" in response.headers['content-security-policy']
        assert response.headers['cache-control'] == 'no-store'
        assert c.get('/api/health').json()['database'] == 'connected'
        assert c.get('/',headers={'Host':'evil.example'}).status_code == 400


def test_sql_payload_is_data(setup):
    app, path = setup
    with client(app) as c:
        register(c)
        name = "Robert'); DROP TABLE users;--"
        assert c.post('/api/workspaces',json={'name':name}).status_code == 201
        assert c.get('/api/workspaces').json()['workspaces'][0]['name'] == name
        with sqlite3.connect(path) as db:
            assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            assert db.execute('PRAGMA foreign_key_check').fetchall() == []


def test_role_portals_and_hierarchical_access(setup):
    app,path=setup
    with client(app) as owner,client(app) as supervisor,client(app) as administrator:
        register(owner,'alice')
        workspace=owner.post('/api/workspaces',json={'name':'Operator inspection'}).json()['id']

        register(supervisor,'sue')
        supervisor.post('/api/auth/logout')
        register(administrator,'admin')
        administrator.post('/api/auth/logout')
        with sqlite3.connect(path) as db:
            db.execute("UPDATE users SET role='supervisor' WHERE username='sue'")
            db.execute("UPDATE users SET role='administrator' WHERE username='admin'")

        assert supervisor.post('/api/auth/login',json={'username':'sue','password':PASSWORD,'portal':'user'}).status_code==403
        login=supervisor.post('/api/auth/login',json={'username':'sue','password':PASSWORD,'portal':'supervisor'})
        supervisor.headers['X-CSRF-Token']=login.json()['csrf_token']
        assert login.json()['user']['role']=='supervisor'
        assert supervisor.get('/api/workspaces').json()['workspaces'][0]['name']=='Operator inspection'
        assert supervisor.get(f'/api/workspaces/{workspace}').status_code==200
        assert supervisor.patch(f'/api/workspaces/{workspace}',json={'name':'Changed by supervisor'}).status_code==404
        assert supervisor.delete(f'/api/workspaces/{workspace}').status_code==404
        assert supervisor.post(f'/api/workspaces/{workspace}/documents',params={'filename':'review.txt'},content=b'review').status_code==404

        login=administrator.post('/api/auth/login',json={'username':'admin','password':PASSWORD,'portal':'administrator'})
        administrator.headers['X-CSRF-Token']=login.json()['csrf_token']
        users=administrator.get('/api/admin/users')
        assert users.status_code==200 and len(users.json()['users'])==3
        alice=next(item for item in users.json()['users'] if item['username']=='alice')
        assert administrator.patch(f"/api/admin/users/{alice['id']}/role",json={'role':'supervisor'}).status_code==200
        assert administrator.patch(f"/api/admin/users/{login.json()['user']['id']}/role",json={'role':'user'}).status_code==409
        assert administrator.get(f'/api/workspaces/{workspace}').status_code==200
        updated=administrator.patch(f'/api/workspaces/{workspace}',json={'name':'Administrator review','description':'Updated by admin'})
        assert updated.status_code==200 and updated.json()['name']=='Administrator review'
        assert administrator.delete(f'/api/workspaces/{workspace}').status_code==200
        assert administrator.get(f'/api/workspaces/{workspace}').status_code==404

def test_owner_can_edit_and_delete_workspace_with_records(setup):
    app,path=setup
    with client(app) as c:
        register(c)
        workspace=c.post('/api/workspaces',json={'name':'Old name'}).json()['id']
        changed=c.patch(f'/api/workspaces/{workspace}',json={'name':'Pump review','description':'P-101 records'})
        assert changed.status_code==200 and changed.json()['description']=='P-101 records'
        document=c.post(f'/api/workspaces/{workspace}/documents',params={'filename':'record.txt'},content=b'local evidence').json()['id']
        assert c.delete(f'/api/workspaces/{workspace}').status_code==200
        assert c.get(f'/api/workspaces/{workspace}').status_code==404
        assert not (path.parent/'uploads'/document).exists()
        with sqlite3.connect(path) as db:
            assert db.execute('SELECT COUNT(*) FROM documents WHERE workspace_id=?',(workspace,)).fetchone()[0]==0
