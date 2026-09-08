"""Local-only SIH workbench: identity and workspace foundation."""
from contextlib import contextmanager, asynccontextmanager
from pathlib import Path
from collections import defaultdict, deque
from threading import Lock
import hashlib
import secrets
import sqlite3
import time
import uuid
import os

from backend.local_models import LocalModels, ModelUnavailable, ModelBusy
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict, field_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware

ROOT = Path(__file__).resolve().parent.parent
COOKIE = 'aegis_session'
SESSION_SECONDS = 8 * 60 * 60


class Credentials(BaseModel):
    model_config = ConfigDict(extra='forbid')
    username: str = Field(min_length=3, max_length=32, pattern=r'^[A-Za-z0-9_.-]+$')
    password: str = Field(min_length=12, max_length=128)

    @field_validator('username')
    @classmethod
    def normalize(cls, value):
        return value.lower()


class Registration(Credentials):
    display_name: str = Field(min_length=1, max_length=60)

    @field_validator('display_name')
    @classmethod
    def clean(cls, value):
        if not value.strip():
            raise ValueError('Enter your name.')
        return value.strip()

class LoginCredentials(Credentials):
    portal: str = Field(default='user', pattern=r'^(user|supervisor|administrator)$')

class RoleInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role: str = Field(pattern=r'^(user|supervisor|administrator)$')


class WorkspaceInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default='', max_length=400)

    @field_validator('name')
    @classmethod
    def clean(cls, value):
        if not value.strip():
            raise ValueError('Enter a workspace name.')
        return value.strip()


class PromptInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1, max_length=2000)


def create_app(db_path=None, model_engine=None):
    db_path = Path(db_path or ROOT / 'data' / 'workbench.sqlite3')
    db_path.parent.mkdir(parents=True, exist_ok=True)
    upload_dir = db_path.parent / 'uploads'
    upload_dir.mkdir(exist_ok=True)

    @contextmanager
    def database():
        con = sqlite3.connect(db_path, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        try:
            with con:
                yield con
        finally:
            con.close()

    with database() as con:
        con.execute('PRAGMA journal_mode=WAL')
        con.executescript('''
        CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE,
          display_name TEXT NOT NULL, password_hash TEXT NOT NULL, created_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions (
          token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id),
          csrf_token TEXT NOT NULL, expires_at INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at);
        CREATE TABLE IF NOT EXISTS workspaces (
          id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id),
          name TEXT NOT NULL, description TEXT NOT NULL, created_at INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_workspaces_owner ON workspaces(owner_id, created_at);
        CREATE TABLE IF NOT EXISTS documents (
          id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id),
          filename TEXT NOT NULL, size INTEGER NOT NULL, sha256 TEXT NOT NULL,
          created_at INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_documents_workspace ON documents(workspace_id, created_at);
        CREATE TABLE IF NOT EXISTS generations (
          id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id),
          prompt TEXT NOT NULL, result TEXT NOT NULL, created_at INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_generations_workspace ON generations(workspace_id, created_at);
        CREATE TABLE IF NOT EXISTS audit_events (
          id INTEGER PRIMARY KEY, user_id TEXT REFERENCES users(id),
          action TEXT NOT NULL, created_at INTEGER NOT NULL);
        ''')
        user_columns={row['name'] for row in con.execute('PRAGMA table_info(users)').fetchall()}
        if 'role' not in user_columns:
            con.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")

    from backend.network import Monitor
    monitor=Monitor(db_path.parent/'network-observation.json')
    engine = model_engine or LocalModels(ROOT)
    @asynccontextmanager
    async def lifespan(application):
        monitor.start()
        try:
            yield
        finally:
            engine.close()
            monitor.close()
    app = FastAPI(title='Aegis Local Workbench', docs_url=None, redoc_url=None, lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost'])
    hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
    dummy_hash = hasher.hash(secrets.token_urlsafe(32))
    attempts = defaultdict(deque)
    attempt_lock = Lock()

    @app.middleware('http')
    async def browser_boundary(request, call_next):
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            origin = request.headers.get('origin')
            expected = str(request.base_url).rstrip('/')
            if (origin and origin != expected) or request.headers.get('sec-fetch-site') == 'cross-site':
                return JSONResponse({'detail': 'Cross-site requests are not allowed.'}, status_code=403)
            if request.headers.get('x-workbench-request') != '1':
                return JSONResponse({'detail': 'Missing local request header.'}, status_code=403)
            try:
                size = int(request.headers.get('content-length', '0'))
            except ValueError:
                return JSONResponse({'detail': 'Invalid request length.'}, status_code=400)
            if size > (20 * 1024 * 1024 if request.url.path.endswith('/documents') else 16384):
                return JSONResponse({'detail': 'Request is too large.'}, status_code=413)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        return response

    def limit_auth(request):
        key = request.client.host if request.client else 'local'
        now = time.monotonic()
        with attempt_lock:
            queue = attempts[key]
            while queue and now - queue[0] > 60:
                queue.popleft()
            if len(queue) >= 10:
                raise HTTPException(429, 'Too many attempts. Wait one minute and try again.')
            queue.append(now)

    def identity(request, mutating=False):
        token = request.cookies.get(COOKIE, '')
        digest = hashlib.sha256(token.encode()).hexdigest()
        with database() as con:
            row = con.execute('''SELECT users.id, username, display_name, role, csrf_token
                FROM sessions JOIN users ON users.id=sessions.user_id
                WHERE token_hash=? AND expires_at>?''', (digest, int(time.time()))).fetchone()
        if not row:
            raise HTTPException(401, 'Please sign in to continue.')
        if mutating and not secrets.compare_digest(request.headers.get('x-csrf-token', ''), row['csrf_token']):
            raise HTTPException(403, 'Your session could not be verified. Refresh and try again.')
        return dict(row)

    def session_response(user, old_token=''):
        token = secrets.token_urlsafe(48)
        csrf = secrets.token_urlsafe(32)
        with database() as con:
            con.execute('DELETE FROM sessions WHERE expires_at<=? OR token_hash=?',
                        (int(time.time()), hashlib.sha256(old_token.encode()).hexdigest()))
            con.execute('INSERT INTO sessions VALUES (?,?,?,?)',
                        (hashlib.sha256(token.encode()).hexdigest(), user['id'], csrf, int(time.time()) + SESSION_SECONDS))
            con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',
                        (user['id'], 'signed_in', int(time.time())))
        response = JSONResponse({'user': {k: user[k] for k in ('id', 'username', 'display_name', 'role')}, 'csrf_token': csrf})
        # HTTP is restricted to loopback for this prototype. LAN deployment requires TLS + Secure cookies.
        response.set_cookie(COOKIE, token, httponly=True, samesite='strict', max_age=SESSION_SECONDS, path='/')
        return response

    @app.get('/api/system/network')
    def network(request: Request):
        identity(request)
        return monitor.snapshot()

    @app.get('/api/health')
    def health():
        with database() as con:
            con.execute('SELECT 1').fetchone()
        return {'status': 'ok', 'database': 'connected', 'milestone': 'Local model routing and generation',
                'model_status': engine.status(), 'offline_proof': 'not_yet_verified'}

    @app.post('/api/auth/register', status_code=201)
    def register(data: Registration, request: Request):
        limit_auth(request)
        user = {'id': str(uuid.uuid4()), 'username': data.username, 'display_name': data.display_name, 'role':'user'}
        password_hash = hasher.hash(data.password)
        try:
            with database() as con:
                con.execute('INSERT INTO users(id,username,display_name,role,password_hash,created_at) VALUES (?,?,?,?,?,?)',
                            (user['id'],user['username'],user['display_name'],user['role'],password_hash,int(time.time())))
                con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',
                            (user['id'], 'account_created', int(time.time())))
        except sqlite3.IntegrityError:
            raise HTTPException(409, 'That username is already taken.')
        response = session_response(user, request.cookies.get(COOKIE, ''))
        response.status_code = 201
        return response

    @app.post('/api/auth/login')
    def login(data: LoginCredentials, request: Request):
        limit_auth(request)
        with database() as con:
            row = con.execute('SELECT * FROM users WHERE username=?', (data.username,)).fetchone()
        try:
            hasher.verify(row['password_hash'] if row else dummy_hash, data.password)
        except (VerificationError, InvalidHashError):
            raise HTTPException(401, 'Incorrect username or password.')
        if not row:
            raise HTTPException(401, 'Incorrect username or password.')
        if row['role'] != data.portal:
            raise HTTPException(403, f"This account uses the {row['role'].title()} portal.")
        return session_response(dict(row), request.cookies.get(COOKIE, ''))

    @app.get('/api/auth/me')
    def me(request: Request):
        user = identity(request)
        csrf = user.pop('csrf_token')
        return {'user': user, 'csrf_token': csrf}

    @app.post('/api/auth/logout')
    def logout(request: Request):
        user = identity(request, True)
        with database() as con:
            con.execute('DELETE FROM sessions WHERE token_hash=?',
                        (hashlib.sha256(request.cookies.get(COOKIE, '').encode()).hexdigest(),))
            con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',
                        (user['id'], 'signed_out', int(time.time())))
        response = JSONResponse({'ok': True})
        response.delete_cookie(COOKIE, path='/', httponly=True, samesite='strict')
        return response

    @app.get('/api/admin/users')
    def admin_users(request: Request):
        actor=identity(request)
        if actor['role']!='administrator':raise HTTPException(403,'Administrator access required.')
        with database() as con:
            rows=con.execute('''SELECT u.id,u.username,u.display_name,u.role,u.created_at,COUNT(w.id) AS workspace_count
                FROM users u LEFT JOIN workspaces w ON w.owner_id=u.id
                GROUP BY u.id ORDER BY u.created_at,u.username''').fetchall()
        return {'users':[dict(row) for row in rows]}

    @app.patch('/api/admin/users/{user_id}/role')
    def change_role(user_id: str, body: RoleInput, request: Request):
        actor=identity(request,True)
        if actor['role']!='administrator':raise HTTPException(403,'Administrator access required.')
        if user_id==actor['id'] and body.role!='administrator':
            raise HTTPException(409,'Administrators cannot change their own role.')
        with database() as con:
            target=con.execute('SELECT id,username,role FROM users WHERE id=?',(user_id,)).fetchone()
            if not target:raise HTTPException(404,'User not found.')
            con.execute('UPDATE users SET role=? WHERE id=?',(body.role,user_id))
            con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',
                        (actor['id'],f"role_changed:{target['username']}:{target['role']}:{body.role}",int(time.time())))
        return {'id':user_id,'role':body.role}

    @app.get('/api/workspaces')
    def workspaces(request: Request):
        user = identity(request)
        with database() as con:
            if user['role'] in ('supervisor','administrator'):
                rows = con.execute('''SELECT w.id,w.name,w.description,w.created_at,w.owner_id,u.display_name AS owner_name,u.username AS owner_username
                    FROM workspaces w JOIN users u ON u.id=w.owner_id ORDER BY w.created_at DESC,w.rowid DESC''').fetchall()
            else:
                rows = con.execute('''SELECT w.id,w.name,w.description,w.created_at,w.owner_id,u.display_name AS owner_name,u.username AS owner_username
                    FROM workspaces w JOIN users u ON u.id=w.owner_id WHERE w.owner_id=? ORDER BY w.created_at DESC,w.rowid DESC''',(user['id'],)).fetchall()
        return {'workspaces': [dict(row) for row in rows]}

    @app.post('/api/workspaces', status_code=201)
    def create_workspace(data: WorkspaceInput, request: Request):
        user = identity(request, True)
        item = {'id': str(uuid.uuid4()), 'name': data.name, 'description': data.description.strip(), 'created_at': int(time.time())}
        with database() as con:
            con.execute('INSERT INTO workspaces VALUES (?,?,?,?,?)',
                        (item['id'], user['id'], item['name'], item['description'], item['created_at']))
            con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',
                        (user['id'], 'workspace_created', int(time.time())))
        return item

    @app.get('/api/workspaces/{workspace_id}')
    def workspace(workspace_id: str, request: Request):
        user = identity(request)
        with database() as con:
            row = con.execute('''SELECT w.id,w.name,w.description,w.created_at,w.owner_id,u.display_name AS owner_name,u.username AS owner_username
                FROM workspaces w JOIN users u ON u.id=w.owner_id WHERE w.id=?''',(workspace_id,)).fetchone()
        if row and row['owner_id']!=user['id'] and user['role'] not in ('supervisor','administrator'):
            row=None
        if not row:
            raise HTTPException(404, 'Workspace not found.')
        return dict(row)

    def owned_workspace(workspace_id, user, write=False):
        with database() as con:
            row=con.execute('SELECT owner_id FROM workspaces WHERE id=?',(workspace_id,)).fetchone()
        allowed=row and (row['owner_id']==user['id'] or user['role']=='administrator' or (user['role']=='supervisor' and not write))
        if not allowed:raise HTTPException(404, 'Workspace not found.')

    @app.patch('/api/workspaces/{workspace_id}')
    def update_workspace(workspace_id: str, data: WorkspaceInput, request: Request):
        user = identity(request, True)
        owned_workspace(workspace_id, user, True)
        with database() as con:
            con.execute('UPDATE workspaces SET name=?,description=? WHERE id=?',
                        (data.name, data.description.strip(), workspace_id))
            con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',
                        (user['id'], 'workspace_updated', int(time.time())))
            row = con.execute('''SELECT w.id,w.name,w.description,w.created_at,w.owner_id,u.display_name AS owner_name,u.username AS owner_username
                FROM workspaces w JOIN users u ON u.id=w.owner_id WHERE w.id=?''',(workspace_id,)).fetchone()
        return dict(row)

    @app.delete('/api/workspaces/{workspace_id}')
    def delete_workspace(workspace_id: str, request: Request):
        user = identity(request, True)
        owned_workspace(workspace_id, user, True)
        with database() as con:
            if con.execute("SELECT 1 FROM runs WHERE workspace_id=? AND status='running' LIMIT 1",(workspace_id,)).fetchone():
                raise HTTPException(409, 'Wait for the active workflow to finish before deleting this workspace.')
            document_ids=[row['id'] for row in con.execute('SELECT id FROM documents WHERE workspace_id=?',(workspace_id,)).fetchall()]
            artifact_paths=[row['path'] for row in con.execute('SELECT path FROM artifacts WHERE workspace_id=?',(workspace_id,)).fetchall()]
            for document_id in document_ids:
                con.execute('DELETE FROM pages WHERE document_id=?',(document_id,))
            con.execute('DELETE FROM artifacts WHERE workspace_id=?',(workspace_id,))
            con.execute('DELETE FROM runs WHERE workspace_id=?',(workspace_id,))
            con.execute('DELETE FROM generations WHERE workspace_id=?',(workspace_id,))
            con.execute('DELETE FROM documents WHERE workspace_id=?',(workspace_id,))
            con.execute('DELETE FROM workspaces WHERE id=?',(workspace_id,))
            con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',
                        (user['id'], 'workspace_deleted', int(time.time())))
        preview_dir=db_path.parent/'previews';artifact_root=(db_path.parent/'artifacts').resolve()
        for document_id in document_ids:
            (upload_dir/document_id).unlink(missing_ok=True)
            for preview in preview_dir.glob(f'{document_id}-*.png'):
                preview.unlink(missing_ok=True)
        for stored in artifact_paths:
            candidate=(db_path.parent/stored).resolve()
            if candidate.is_relative_to(artifact_root) and candidate.is_file():
                candidate.unlink(missing_ok=True)
        return {'ok': True}

    @app.get('/api/workspaces/{workspace_id}/documents')
    def documents(workspace_id: str, request: Request):
        user = identity(request)
        owned_workspace(workspace_id, user)
        with database() as con:
            rows = con.execute('SELECT d.*, EXISTS(SELECT 1 FROM pages p WHERE p.document_id=d.id) AS extracted FROM documents d WHERE workspace_id=? ORDER BY created_at DESC, d.rowid DESC', (workspace_id,)).fetchall()
        return {'documents': [dict(row) for row in rows], 'limit_bytes': 200 * 1024 * 1024}

    @app.post('/api/workspaces/{workspace_id}/documents', status_code=201)
    async def upload(workspace_id: str, request: Request, filename: str):
        user = identity(request, True)
        owned_workspace(workspace_id, user, True)
        if not filename or len(filename) > 180 or any(ord(c) < 32 for c in filename) or '/' in filename or chr(92) in filename:
            raise HTTPException(400, 'Use a filename without folders or control characters (up to 180 characters).')
        suffix = Path(filename).suffix.lower()
        if suffix not in {'.pdf', '.txt', '.csv', '.png', '.jpg', '.jpeg'}:
            raise HTTPException(415, 'Choose a PDF, TXT, CSV, PNG or JPEG file.')
        document_id = str(uuid.uuid4())
        temporary = upload_dir / (document_id + '.part')
        destination = upload_dir / document_id
        size = 0
        digest = hashlib.sha256()
        try:
            with temporary.open('xb') as stream:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 20 * 1024 * 1024:
                        raise HTTPException(413, 'Each file must be 20 MB or smaller.')
                    digest.update(chunk)
                    stream.write(chunk)
            if not size:
                raise HTTPException(400, 'The file is empty.')
            with temporary.open('rb') as stream:
                head = stream.read(1024)
            valid = True
            if suffix == '.pdf': valid = head.startswith(b'%PDF-')
            elif suffix == '.png': valid = head.startswith(bytes.fromhex('89504e470d0a1a0a'))
            elif suffix in {'.jpg', '.jpeg'}: valid = head.startswith(bytes.fromhex('ffd8ff'))
            else:
                try:
                    text = temporary.read_bytes().decode('utf-8-sig')
                    valid = chr(0) not in text
                except UnicodeDecodeError:
                    valid = False
            if not valid:
                raise HTTPException(415, 'The contents do not match this file type. Text and CSV files must use UTF-8.')
            item = {'id':document_id,'workspace_id':workspace_id,'filename':filename,'size':size,'sha256':digest.hexdigest(),'created_at':int(time.time())}
            with database() as con:
                con.execute('BEGIN IMMEDIATE')
                total = con.execute('SELECT COALESCE(SUM(size),0) FROM documents WHERE workspace_id=?', (workspace_id,)).fetchone()[0]
                if total + size > 200 * 1024 * 1024:
                    raise HTTPException(413, 'This workspace has reached its 200 MB storage limit.')
                os.replace(temporary, destination)
                con.execute('INSERT INTO documents VALUES (?,?,?,?,?,?)', tuple(item.values()))
                con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)', (user['id'], 'document_uploaded', int(time.time())))
            return item
        except BaseException:
            temporary.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)
            raise

    @app.get('/api/documents/{document_id}/download')
    def download(document_id: str, request: Request):
        user = identity(request)
        with database() as con:
            row = con.execute('SELECT documents.*,workspaces.owner_id FROM documents JOIN workspaces ON documents.workspace_id=workspaces.id WHERE documents.id=?',(document_id,)).fetchone()
        if row and row['owner_id']!=user['id'] and user['role'] not in ('supervisor','administrator'):row=None
        if not row:
            raise HTTPException(404, 'Document not found.')
        path = upload_dir / row['id']
        if not path.is_file():
            raise HTTPException(404, 'The stored file is unavailable.')
        return FileResponse(path, media_type='application/octet-stream', filename=row['filename'])

    @app.delete('/api/documents/{document_id}')
    def delete_document(document_id: str, request: Request):
        user = identity(request, True)
        with database() as con:
            row = con.execute('''SELECT d.id,d.filename,d.workspace_id,w.owner_id
                FROM documents d JOIN workspaces w ON d.workspace_id=w.id WHERE d.id=?''',(document_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'Document not found.')
        owned_workspace(row['workspace_id'], user, True)
        with database() as con:
            referenced=con.execute("SELECT 1 FROM runs WHERE workspace_id=? AND status='running' LIMIT 1",(row['workspace_id'],)).fetchone()
            if referenced:
                raise HTTPException(409, 'Wait for the active workflow to finish before deleting this material.')
            con.execute('DELETE FROM pages WHERE document_id=?',(document_id,))
            con.execute('DELETE FROM documents WHERE id=?',(document_id,))
            con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',
                        (user['id'], 'document_deleted', int(time.time())))
        (upload_dir/document_id).unlink(missing_ok=True)
        for preview in (db_path.parent/'previews').glob(f'{document_id}-*.png'):
            preview.unlink(missing_ok=True)
        return {'ok': True}

    @app.get('/api/models')
    def models(request: Request):
        identity(request)
        return {'models': engine.status()}

    @app.get('/api/workspaces/{workspace_id}/generations')
    def generations(workspace_id: str, request: Request):
        user=identity(request)
        owned_workspace(workspace_id,user)
        with database() as con:
            rows=con.execute('SELECT * FROM generations WHERE workspace_id=? ORDER BY created_at DESC, rowid DESC LIMIT 20',(workspace_id,)).fetchall()
        import json
        return {'generations':[{'id':row['id'],'prompt':row['prompt'],'created_at':row['created_at'],**json.loads(row['result'])} for row in rows]}

    @app.post('/api/workspaces/{workspace_id}/generations',status_code=201)
    def generate(workspace_id: str, data: PromptInput, request: Request):
        user=identity(request,True)
        owned_workspace(workspace_id,user,True)
        prompt=data.prompt.strip()
        if not prompt:raise HTTPException(422,'Enter a request.')
        try:result=engine.generate(prompt)
        except ModelBusy as exc:raise HTTPException(429,str(exc))
        except ModelUnavailable as exc:raise HTTPException(503,str(exc))
        import json
        item={'id':str(uuid.uuid4()),'prompt':prompt,'created_at':int(time.time()),**result}
        with database() as con:
            con.execute('INSERT INTO generations VALUES (?,?,?,?,?)',(item['id'],workspace_id,prompt,json.dumps(result),item['created_at']))
            con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',(user['id'],'local_generation_completed',item['created_at']))
        return item

    from backend.workflows import install
    install(app,database,identity,owned_workspace,engine,db_path,upload_dir)

    @app.get('/')
    def index():
        return FileResponse(ROOT / 'frontend' / 'index.html')

    @app.get('/login/{portal}')
    def login_page(portal: str):
        if portal not in ('user','supervisor','administrator'):raise HTTPException(404,'Portal not found.')
        return FileResponse(ROOT / 'frontend' / 'index.html')

    app.mount('/assets', StaticFiles(directory=ROOT / 'frontend' / 'assets'), name='assets')
    return app


app = create_app()
