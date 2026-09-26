"""Bounded, auditable thickness-trend cases. No LLM or fitness-for-service claim."""
import hashlib
import json
import math
import re
import time
import uuid
from decimal import Decimal
from html import escape
from typing import Literal

from fastapi import HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from backend.injection import suspicious
from backend.vault import read_bytes


class NewCase(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tag: str = Field(default='P-101', pattern=r'^[A-Za-z0-9][A-Za-z0-9_-]{1,39}$')
    scenario: Literal['conflict', 'missing', 'ready', 'materials'] = 'conflict'


class CaseAction(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    action: Literal['confirm', 'verify', 'approve', 'reject', 'revise']
    version: int = Field(ge=1)
    previous_mm: float | None = Field(default=None, gt=0, le=1000)
    current_mm: float | None = Field(default=None, gt=0, le=1000)
    interval_years: float | None = Field(default=None, gt=0, le=100)
    source_ids: list[str] = Field(default_factory=list, max_length=30)
    note: str = Field(default='', max_length=1200)


def fingerprint(case):
    content = {k: case[k] for k in ('tag', 'sources', 'inputs', 'result', 'synthetic')}
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


def demo_sources(tag, scenario):
    rows = [
        ('inspection-2023', tag, 1, '2023 baseline inspection', 'Previous thickness: 8.0 mm. Inspection date: 2023-09-01.'),
        ('inspection-2025', tag, 2, '2025 inspection', 'Current thickness: 7.4 mm. Inspection date: 2025-09-01.'),
        ('inspection-2025', tag, 1, 'Superseded 2025 inspection', 'Current thickness: 7.6 mm. Superseded by revision 2.'),
        ('other-asset', tag + 'A', 1, 'Similar equipment tag', 'Current thickness: 9.1 mm.'),
    ]
    if scenario == 'conflict':
        rows.append(('field-note', tag, 1, 'Conflicting field note', 'Current thickness: 7.1 mm. Unconfirmed handwritten transcription.'))
    if scenario == 'missing':
        rows = [r for r in rows if r[0] != 'inspection-2025']
        rows.append(('incomplete-note', tag, 1, 'Incomplete inspection', 'Current thickness unreadable. Engineer must obtain a verified reading.'))
    latest = {key: max(r[2] for r in rows if r[0] == key) for key in {r[0] for r in rows}}
    return [dict(id=str(i), filename=name, page=1, text=text, revision=str(rev),
                 status='included' if asset == tag and rev == latest[key] else 'excluded',
                 reason='Exact equipment tag; latest fixture revision' if asset == tag and rev == latest[key]
                 else 'Different equipment tag' if asset != tag else 'Superseded fixture revision')
            for i, (key, asset, rev, name, text) in enumerate(rows)]


def install(app, database, identity, owned_workspace, upload_dir):
    with database() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS investigation_cases(
            id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            payload TEXT NOT NULL, updated_at INTEGER NOT NULL)''')

    def event(case, actor, message):
        case['events'].append({'at': int(time.time()), 'actor': actor, 'message': message})

    def persist(con, case, user, action):
        con.execute('UPDATE investigation_cases SET payload=?,updated_at=? WHERE id=?',
                    (json.dumps(case), int(time.time()), case['id']))
        con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',
                    (user['id'], f'case_{action}:{case["id"]}:v{case["version"]}', int(time.time())))

    def get_case(con, ident, user, write=False):
        row = con.execute('SELECT * FROM investigation_cases WHERE id=?', (ident,)).fetchone()
        if not row:
            raise HTTPException(404, 'Case not found.')
        owner = con.execute('SELECT owner_id FROM workspaces WHERE id=?', (row['workspace_id'],)).fetchone()
        if not owner or not (owner['owner_id'] == user['id'] or user['role'] == 'administrator' or (user['role'] == 'supervisor' and not write)):
            raise HTTPException(404, 'Case not found.')
        return json.loads(row['payload'])

    def source_check(con, case):
        for source in case['sources']:
            if source['status'] != 'included' or not source.get('document_id'):
                continue
            row = con.execute('SELECT sha256 FROM documents WHERE id=?', (source['document_id'],)).fetchone()
            page = con.execute('SELECT text FROM pages WHERE document_id=? AND page=?',
                               (source['document_id'], source['page'])).fetchone()
            try:
                digest = hashlib.sha256(read_bytes(upload_dir / source['document_id'])).hexdigest()
            except (OSError, ValueError):
                digest = None
            if not row or row['sha256'] != source['sha256'] or digest != source['sha256'] or not page or page['text'] != source['text']:
                raise HTTPException(409, 'Evidence changed or was removed. Create a new case from current materials; previous approval cannot be used.')

    @app.get('/api/workspaces/{workspace_id}/investigations')
    def list_cases(workspace_id: str, request: Request):
        user = identity(request)
        owned_workspace(workspace_id, user)
        with database() as con:
            return {'cases': [json.loads(r['payload']) for r in con.execute(
                'SELECT payload FROM investigation_cases WHERE workspace_id=? ORDER BY updated_at DESC,rowid DESC LIMIT 30', (workspace_id,))]}

    @app.post('/api/workspaces/{workspace_id}/investigations', status_code=201)
    def create_case(workspace_id: str, body: NewCase, request: Request):
        user = identity(request, True)
        owned_workspace(workspace_id, user, True)
        tag = body.tag.upper()
        sources = demo_sources(tag, body.scenario) if body.scenario != 'materials' else []
        if body.scenario == 'materials':
            # No guessing equipment identities or document revisions from similarity scores.
            with database() as con:
                rows = con.execute('''SELECT p.document_id,p.page,p.text,d.filename,d.sha256
                    FROM pages p JOIN documents d ON d.id=p.document_id
                    WHERE d.workspace_id=? ORDER BY d.created_at,p.page LIMIT 100''', (workspace_id,)).fetchall()
            for i, row in enumerate(rows):
                item = dict(row)
                tags = re.findall(r'(?im)^\s*Equipment\s*:\s*([A-Za-z0-9_-]+)\s*$', item['text'])
                revisions = re.findall(r'(?im)^\s*Revision\s*:\s*([^\r\n]+)', item['text'])
                included = len(tags) == 1 and tags[0].upper() == tag and len(revisions) == 1 and not suspicious(item['text'])
                item.update(id=str(i), revision=revisions[0].strip() if len(revisions) == 1 else 'Unconfirmed',
                            status='included' if included else 'excluded',
                            reason='Equipment matched; engineer must confirm applicable revision' if included
                            else 'Missing/ambiguous metadata, another tag, or suspicious instructions')
                sources.append(item)
        case = dict(id=str(uuid.uuid4()), workspace_id=workspace_id, tag=tag, synthetic=body.scenario != 'materials',
                    scenario=body.scenario, status='awaiting_confirmation', version=1, sources=sources,
                    inputs=None, result=None, approval=None, events=[], created_by=user['id'])
        event(case, 'Coordinator', 'Opened bounded thickness-trend investigation. No fitness-for-service decision.')
        event(case, 'Evidence', f'{sum(s["status"] == "included" for s in sources)} source pages retained. Review exclusions and revisions.')
        event(case, 'Human confirmation', 'Confirm both thicknesses, elapsed years and source revisions before calculating.')
        with database() as con:
            con.execute('INSERT INTO investigation_cases VALUES (?,?,?,?)',
                        (case['id'], workspace_id, json.dumps(case), int(time.time())))
            persist(con, case, user, 'created')
        return case

    @app.post('/api/investigations/{ident}/actions')
    def case_action(ident: str, body: CaseAction, request: Request):
        user = identity(request, True)
        with database() as con:
            # Serialize check + mutation so concurrent reviewers cannot approve a stale version.
            con.execute('BEGIN IMMEDIATE')
            case = get_case(con, ident, user, body.action not in ('approve', 'reject'))
            if body.version != case['version']:
                raise HTTPException(409, 'Case changed. Refresh before continuing.')
            source_check(con, case)
            if body.action == 'confirm':
                if case['status'] != 'awaiting_confirmation':
                    raise HTTPException(409, 'Reopen the case before changing confirmed inputs.')
                if any(v is None for v in (body.previous_mm, body.current_mm, body.interval_years)):
                    raise HTTPException(422, 'Both thicknesses and elapsed years are required.')
                included = {s['id'] for s in case['sources'] if s['status'] == 'included'}
                if not body.source_ids or not set(body.source_ids) <= included or not body.note.strip():
                    raise HTTPException(422, 'Select retained evidence and explain the confirmed values and applicable revisions.')
                selected = '\n'.join(s['text'] for s in case['sources'] if s['id'] in body.source_ids)
                readings = [float(v) for v in re.findall(r'(?<![\w.])(\d+(?:\.\d+)?)\s*mm\b', selected, re.I)]
                if body.previous_mm not in readings or body.current_mm not in readings:
                    raise HTTPException(422, 'Both thickness readings must appear in the selected evidence in mm. Obtain missing evidence and create a new case.')
                if body.current_mm >= body.previous_mm:
                    raise HTTPException(422, 'This bounded loss calculation requires current thickness below previous thickness. Investigate zero/negative loss separately.')
                case['inputs'] = dict(previous_mm=body.previous_mm, current_mm=body.current_mm,
                                      interval_years=body.interval_years, source_ids=body.source_ids,
                                      confirmation_note=body.note.strip(), confirmed_by=user['id'])
                rate = (body.previous_mm - body.current_mm) / body.interval_years
                case['result'] = dict(formula='(previous thickness - current thickness) / elapsed years',
                                      loss_mm=body.previous_mm - body.current_mm, rate_mm_per_year=rate,
                                      verification='pending', limitation='Thickness trend only. No remaining-life, safe-operation or fitness-for-service conclusion.')
                case['status'] = 'awaiting_verification'
                event(case, 'Engineer', 'Inputs and revisions confirmed: ' + body.note.strip())
                event(case, 'Calculation', f'Calculated {rate:.6g} mm/year from confirmed inputs.')
            elif body.action == 'verify':
                if case['status'] != 'awaiting_verification':
                    raise HTTPException(409, 'Confirm inputs before independent recalculation.')
                v = case['inputs']
                check = (Decimal(str(v['previous_mm'])) - Decimal(str(v['current_mm']))) / Decimal(str(v['interval_years']))
                passed = math.isclose(float(check), case['result']['rate_mm_per_year'], rel_tol=1e-9, abs_tol=1e-12)
                case['result']['verification'] = 'passed' if passed else 'failed'
                case['result']['decimal_check_mm_per_year'] = str(check)
                case['status'] = 'pending_approval' if passed else 'verification_failed'
                event(case, 'Verification', 'Decimal arithmetic cross-check ' + ('passed. Source validity still requires human review.' if passed else 'failed; export blocked.'))
            elif body.action in ('approve', 'reject'):
                if user['role'] not in ('supervisor', 'administrator'):
                    raise HTTPException(403, 'Supervisor or Administrator approval is required.')
                if user['id'] == case['created_by'] or user['id'] == (case['inputs'] or {}).get('confirmed_by'):
                    raise HTTPException(403, 'A separate reviewer must decide this case.')
                if case['status'] != 'pending_approval' or not body.note.strip():
                    raise HTTPException(409, 'A verified draft and reviewer note are required.')
                case['status'] = 'approved' if body.action == 'approve' else 'rejected'
                case['approval'] = dict(reviewer=user['display_name'], reviewer_id=user['id'], note=body.note.strip(),
                                        digest=fingerprint(case), at=int(time.time())) if body.action == 'approve' else None
                event(case, 'Human review', body.action + ': ' + body.note.strip())
            elif body.action == 'revise':
                case.update(status='awaiting_confirmation', inputs=None, result=None, approval=None)
                event(case, 'Coordinator', 'Reopened. Previous confirmation, verification and approval revoked.')
            case['version'] += 1
            persist(con, case, user, body.action)
        return case

    @app.get('/api/investigations/{ident}/export')
    def export_case(ident: str, request: Request):
        user = identity(request)
        with database() as con:
            con.execute('BEGIN IMMEDIATE')
            case = get_case(con, ident, user)
            source_check(con, case)
            if case['status'] != 'approved' or not case['approval'] or case['approval']['digest'] != fingerprint(case):
                raise HTTPException(409, 'Export blocked. The exact current version requires approval.')
            con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',
                        (user['id'], f'case_export:{ident}:v{case["version"]}', int(time.time())))
        title = f'ARK engineering case — {case["tag"]}'
        report = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>' + escape(title) + '</title>'
        report += '<style>body{font:16px/1.6 system-ui,sans-serif;color:#173e60;max-width:960px;margin:40px auto;padding:24px}h1,h2{line-height:1.2}section{border-top:1px solid #bccfd9;padding:18px 0}table{border-collapse:collapse;width:100%}td,th{text-align:left;border-bottom:1px solid #dbe4e9;padding:10px}pre{white-space:pre-wrap;overflow-wrap:anywhere}strong{color:#145e54}.digest{font-size:12px;overflow-wrap:anywhere}@media print{body{margin:0}}</style><body><h1>' + escape(title) + '</h1>'
        report += '<p>' + ('SYNTHETIC DEMONSTRATION DATA. Not a plant assessment.' if case['synthetic'] else 'Engineer-reviewed thickness trend. Not a fitness-for-service assessment.') + '</p>'
        values, result, approval = case['inputs'], case['result'], case['approval']
        report += '<section><h2>Confirmed inputs</h2><table><tr><th>Input</th><th>Value</th></tr>'
        for label, value in [('Previous thickness', f'{values["previous_mm"]} mm'), ('Current thickness', f'{values["current_mm"]} mm'), ('Elapsed time', f'{values["interval_years"]} years')]:
            report += '<tr><td>' + escape(label) + '</td><td>' + escape(value) + '</td></tr>'
        report += '</table><p>' + escape(values['confirmation_note']) + '</p></section>'
        report += '<section><h2>Calculation and arithmetic check</h2><p>' + escape(result['formula']) + '</p><strong>' + f'{result["rate_mm_per_year"]:.6g} mm/year' + '</strong><p>Decimal recalculation: ' + escape(result['decimal_check_mm_per_year']) + ' mm/year. Check: ' + escape(result['verification']) + '.</p><p>' + escape(result['limitation']) + '</p></section>'
        report += '<section><h2>Evidence reviewed</h2>'
        for source in case['sources']:
            used = source['id'] in values['source_ids']
            report += '<h3>' + escape(source['filename']) + '</h3><p>' + escape(f'Page {source["page"]}; revision {source["revision"]}; {"selected for calculation" if used else source["status"]}. {source["reason"]}') + '</p><pre>' + escape(source['text']) + '</pre>'
        report += '</section><section><h2>Human approval</h2><p>Reviewer: ' + escape(approval['reviewer']) + '</p><p>' + escape(approval['note']) + '</p><p class="digest">Approved content SHA-256: ' + escape(approval['digest']) + '</p></section><section><h2>Audit trail</h2><ol>'
        for entry in case['events']:
            report += '<li>' + escape(time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(entry['at'])) + ' — ' + entry['actor'] + ': ' + entry['message']) + '</li>'
        report += '</ol></section><p>Existing plant systems remain the official record. This case does not authorize equipment operation.</p></body></html>'
        return Response(report, media_type='text/html', headers={'Content-Disposition': f'attachment; filename="ARK-{case["tag"]}-approved.html"'})
