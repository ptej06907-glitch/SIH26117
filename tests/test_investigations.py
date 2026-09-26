import json
import sqlite3

from backend.app import create_app
from tests.test_auth import client, register


def test_case_lifecycle_and_permissions(tmp_path):
    path = tmp_path / 'cases.sqlite3'
    app = create_app(path)
    with client(app) as owner, client(app) as reviewer, client(app) as stranger:
        owner_id = register(owner).json()['user']['id']
        reviewer_id = register(reviewer, 'reviewer').json()['user']['id']
        register(stranger, 'stranger')
        with sqlite3.connect(path) as con:
            con.execute("UPDATE users SET role='supervisor' WHERE id=?", (reviewer_id,))
        workspace = owner.post('/api/workspaces', json={'name': 'Case tests'}).json()['id']
        case = owner.post(f'/api/workspaces/{workspace}/investigations', json={'scenario': 'conflict'}).json()
        ident = case['id']
        url = f'/api/investigations/{ident}/actions'
        export = f'/api/investigations/{ident}/export'
        assert len([s for s in case['sources'] if s['status'] == 'excluded']) == 2
        assert owner.get(export).status_code == 409
        assert stranger.get(export).status_code == 404
        assert stranger.post(url, json={'action': 'revise', 'version': 1}).status_code == 404
        assert owner.post(url, json={'action': 'verify', 'version': 1}).status_code == 409
        confirm = dict(action='confirm', version=1, previous_mm=8, current_mm=7.4, interval_years=2,
                       source_ids=['0', '1'], note='Use baseline rev 1 and 2025 inspection rev 2; field note is unconfirmed.')
        assert owner.post(url, json={**confirm, 'source_ids': ['2']}).status_code == 422
        assert reviewer.post(url, json=confirm).status_code == 404
        assert owner.post(url, json={**confirm, 'current_mm': 6}).status_code == 422
        response = owner.post(url, json=confirm)
        assert response.status_code == 200, response.text
        assert response.json()['status'] == 'awaiting_verification'
        assert owner.post(url, json=confirm).status_code == 409
        verified = owner.post(url, json={'action': 'verify', 'version': 2}).json()
        assert verified['result']['verification'] == 'passed'
        assert abs(verified['result']['rate_mm_per_year'] - .3) < 1e-10
        assert owner.post(url, json={'action': 'approve', 'version': 3, 'note': 'Reviewed'}).status_code == 403
        approved = reviewer.post(url, json={'action': 'approve', 'version': 3, 'note': 'Checked source revisions and arithmetic.'})
        assert approved.status_code == 200, approved.text
        assert 'SYNTHETIC DEMONSTRATION' in owner.get(export).text
        assert reviewer.get(export).status_code == 200
        assert owner.post(url, json={'action': 'revise', 'version': 4}).status_code == 200
        assert owner.get(export).status_code == 409
        assert owner.get(f'/api/workspaces/{workspace}/investigations').json()['cases'][0]['approval'] is None
        with sqlite3.connect(path) as con:
            actions = [r[0] for r in con.execute("SELECT action FROM audit_events WHERE action LIKE 'case_%'")]
        assert any('case_export' in a for a in actions)


def test_missing_evidence_and_self_approval(tmp_path):
    path = tmp_path / 'cases.sqlite3'
    app = create_app(path)
    with client(app) as c:
        uid = register(c).json()['user']['id']
        with sqlite3.connect(path) as con:
            con.execute("UPDATE users SET role='administrator' WHERE id=?", (uid,))
        wid = c.post('/api/workspaces', json={'name': 'Missing'}).json()['id']
        case = c.post(f'/api/workspaces/{wid}/investigations', json={'scenario': 'missing'}).json()
        assert c.post(f'/api/investigations/{case["id"]}/actions', json=dict(action='confirm', version=1,
            previous_mm=8, current_mm=7.4, interval_years=2, source_ids=['0'], note='Not in evidence')).status_code == 422
        case = c.post(f'/api/workspaces/{wid}/investigations', json={'scenario': 'ready'}).json()
        url = f'/api/investigations/{case["id"]}/actions'
        assert c.post(url, json=dict(action='confirm', version=1, previous_mm=8, current_mm=7.4,
            interval_years=2, source_ids=['0', '1'], note='Checked source revisions and dates')).status_code == 200
        assert c.post(url, json={'action': 'verify', 'version': 2}).status_code == 200
        assert c.post(url, json={'action': 'approve', 'version': 3, 'note': 'Self approve'}).status_code == 403


def test_material_integrity_and_persistence(tmp_path):
    path = tmp_path / 'cases.sqlite3'
    app = create_app(path)
    with client(app) as c:
        register(c)
        wid = c.post('/api/workspaces', json={'name': 'Real sources'}).json()['id']
        raw = b'Equipment: P-101\nRevision: 2\nPrevious thickness: 8.0 mm\nCurrent thickness: 7.4 mm\nInterval: 2 years'
        upload = c.post(f'/api/workspaces/{wid}/documents?filename=inspection.txt', content=raw,
                        headers={'Content-Type': 'application/octet-stream'})
        assert upload.status_code == 201, upload.text
        did = upload.json()['id']
        assert c.post(f'/api/documents/{did}/extract').status_code == 200
        case = c.post(f'/api/workspaces/{wid}/investigations', json={'scenario': 'materials'}).json()
        assert not case['synthetic']
        assert case['sources'][0]['status'] == 'included'
        assert c.get(f'/api/workspaces/{wid}/investigations').json()['cases'][0]['id'] == case['id']
        with sqlite3.connect(path) as con:
            con.execute("UPDATE pages SET text='changed' WHERE document_id=?", (did,))
        assert c.post(f'/api/investigations/{case["id"]}/actions', json=dict(action='confirm', version=1,
            previous_mm=8, current_mm=7.4, interval_years=2, source_ids=['0'], note='Reviewed')).status_code == 409


def test_approved_result_tampering_blocks_export(tmp_path):
    path = tmp_path / 'cases.sqlite3'
    app = create_app(path)
    with client(app) as c:
        register(c)
        wid = c.post('/api/workspaces', json={'name': 'Integrity'}).json()['id']
        case = c.post(f'/api/workspaces/{wid}/investigations', json={}).json()
        # An approval-looking state with a wrong digest must never release a file.
        case.update(status='approved', approval={'digest': 'invalid'})
        with sqlite3.connect(path) as con:
            con.execute('UPDATE investigation_cases SET payload=? WHERE id=?', (json.dumps(case), case['id']))
        assert c.get(f'/api/investigations/{case["id"]}/export').status_code == 409


def test_encrypted_case_lifecycle(tmp_path):
    from backend import vault
    (tmp_path / '.encrypted-storage').touch()
    path = tmp_path / 'encrypted.sqlite3'
    app = create_app(path)
    with client(app) as c:
        register(c)
        wid = c.post('/api/workspaces', json={'name': 'Encrypted case'}).json()['id']
        case = c.post(f'/api/workspaces/{wid}/investigations', json={'scenario': 'ready'}).json()
        response = c.post(f'/api/investigations/{case["id"]}/actions', json=dict(action='confirm', version=1,
            previous_mm=8, current_mm=7.4, interval_years=2, source_ids=['0', '1'], note='Confirmed revisions and dates'))
        assert response.status_code == 200, response.text
        assert c.get(f'/api/workspaces/{wid}/investigations').json()['cases'][0]['inputs']['previous_mm'] == 8
        assert path.read_bytes().startswith(vault.MAGIC)


def test_existing_office_export_is_approval_gated(tmp_path):
    from backend.review_integrity import snapshot
    path = tmp_path / 'exports.sqlite3'
    app = create_app(path)
    with client(app) as c:
        uid = register(c).json()['user']['id']
        wid = c.post('/api/workspaces', json={'name': 'Office gate'}).json()['id']
        did = c.post(f'/api/workspaces/{wid}/documents?filename=report.txt', content=b'Inspection source').json()['id']
        artifact_dir = tmp_path / 'artifacts' / 'review-run'
        artifact_dir.mkdir(parents=True)
        artifact = artifact_dir / 'draft.docx'
        artifact.write_bytes(b'Test-only artifact bytes')
        with sqlite3.connect(path) as con:
            con.execute("INSERT INTO runs VALUES ('review-run',?,'inspection','complete','[]','{}',1)", (wid,))
            con.execute("INSERT INTO artifacts VALUES ('artifact',?,'review-run','draft.docx','artifacts/review-run/draft.docx')", (wid,))
            con.execute("INSERT INTO review_requests(id,run_id,workspace_id,document_id,requester_id,status,created_at) VALUES ('review','review-run',?,?,?,'pending_analysis',1)", (wid,did,uid))
        assert c.get('/api/artifacts/artifact/download').status_code == 409
        with sqlite3.connect(path) as con:
            con.row_factory = sqlite3.Row
            row = con.execute("SELECT * FROM review_requests WHERE id='review'").fetchone()
            digest, payload = snapshot(con, row, tmp_path)
            con.execute("INSERT INTO review_versions VALUES ('review',?,?,?,1)", (digest,payload,uid))
            con.execute("UPDATE review_requests SET status='approved' WHERE id='review'")
        assert c.get('/api/artifacts/artifact/download').status_code == 200
        artifact.write_bytes(b'Changed output')
        assert c.get('/api/artifacts/artifact/download').status_code == 409
