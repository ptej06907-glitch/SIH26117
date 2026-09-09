import hashlib
import sqlite3
from tests.test_auth import client, register
from backend.app import create_app
import pytest

@pytest.fixture
def env(tmp_path):
    path=tmp_path/'db.sqlite3'
    app=create_app(path)
    with client(app) as c:
        register(c)
        workspace=c.post('/api/workspaces',json={'name':'Documents'}).json()['id']
        yield c,app,path,workspace

def upload(c,w,name='report.txt',data=b'Inspection report: all readings recorded.'):
    return c.post(f'/api/workspaces/{w}/documents',params={'filename':name},content=data,headers={'Content-Type':'application/octet-stream'})

def test_upload_list_download_persistence(env):
    c,app,path,w=env
    data=b'Equipment,Reading\nP-101,42\n'
    result=upload(c,w,'measurements.csv',data)
    assert result.status_code==201,result.text
    item=result.json()
    assert item['scan_status']=='clean'
    assert item['sha256']==hashlib.sha256(data).hexdigest()
    assert item['size']==len(data)
    assert c.get(f'/api/workspaces/{w}/documents').json()['documents'][0]['id']==item['id']
    assert c.get(f'/api/workspaces/{w}/documents').json()['documents'][0]['scan_status']=='clean'
    downloaded=c.get(f"/api/documents/{item['id']}/download")
    assert downloaded.content==data
    assert 'attachment' in downloaded.headers['content-disposition']
    with client(create_app(path)) as fresh:
        from tests.test_auth import PASSWORD
        fresh.post('/api/auth/login',json={'username':'alice','password':PASSWORD})
        assert fresh.get(f"/api/documents/{item['id']}/download").content==data

def test_document_ownership(env):
    c,app,path,w=env
    doc=upload(c,w).json()['id']
    with client(app) as bob:
        register(bob,'bob')
        assert upload(bob,w).status_code==404
        assert bob.get(f'/api/workspaces/{w}/documents').status_code==404
        assert bob.get(f'/api/documents/{doc}/download').status_code==404
    with client(app) as anonymous:
        assert anonymous.get(f'/api/documents/{doc}/download').status_code==401

@pytest.mark.parametrize('name,data,status',[
    ('empty.txt',b'',400),('../escape.txt',b'content',400),
    ('tool.exe',b'anything',415),('fake.pdf',b'not a pdf',415),
    ('fake.png',b'not an image',415),('invalid.txt',b'\x00binary',415),
    ('invalid.csv',b'\xff\xfe',415)])
def test_invalid_uploads_leave_no_files(env,name,data,status):
    c,app,path,w=env
    assert upload(c,w,name,data).status_code==status
    assert list((path.parent/'uploads').iterdir())==[]
    assert c.get(f'/api/workspaces/{w}/documents').json()['documents']==[]

def test_limits_and_csrf(env):
    c,app,path,w=env
    assert upload(c,w,data=b'x'*(20*1024*1024+1)).status_code==413
    assert c.post(f'/api/workspaces/{w}/documents',params={'filename':'report.txt'},content=b'hello',headers={'X-CSRF-Token':'bad'}).status_code==403
    with sqlite3.connect(path) as db:
        db.execute('INSERT INTO documents VALUES (?,?,?,?,?,?)',('fixture',w,'fixture.txt',200*1024*1024,'test',1))
    assert upload(c,w).status_code==413
    assert not list((path.parent/'uploads').iterdir())

def test_same_name_does_not_overwrite(env):
    c,app,path,w=env
    first=upload(c,w,data=b'First').json()['id']
    second=upload(c,w,data=b'Second').json()['id']
    assert first!=second
    assert c.get(f'/api/documents/{first}/download').content==b'First'
    assert c.get(f'/api/documents/{second}/download').content==b'Second'

def test_security_scan_blocks_signature_and_active_pdf(env,monkeypatch):
    c,app,path,w=env
    import backend.security as security
    monkeypatch.setattr(security,'EICAR_MARKER',b'HARMLESS-TEST-SIGNATURE')
    assert upload(c,w,'signature.txt',b'HARMLESS-TEST-SIGNATURE').status_code==422
    active_pdf=b'%PDF-1.4\n1 0 obj <</OpenAction 2 0 R /JavaScript (alert)>> endobj\n%%EOF'
    assert upload(c,w,'active.pdf',active_pdf).status_code==422
    assert not list((path.parent/'uploads').iterdir())
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM audit_events WHERE action LIKE 'upload_blocked:%'").fetchone()[0]==2

def test_remove_document_deletes_record_file_and_extracted_pages(env):
    c,app,path,w=env
    item=upload(c,w,'inspection.txt',b'Finding: damaged identification label').json()
    assert c.post(f"/api/documents/{item['id']}/extract").status_code==200
    assert (path.parent/'uploads'/item['id']).is_file()
    assert c.delete(f"/api/documents/{item['id']}").status_code==200
    assert not (path.parent/'uploads'/item['id']).exists()
    assert c.get(f'/api/workspaces/{w}/documents').json()['documents']==[]
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT COUNT(*) FROM pages WHERE document_id=?',(item['id'],)).fetchone()[0]==0
