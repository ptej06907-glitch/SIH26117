from pathlib import Path
from threading import Thread,Lock
import json,time,uuid,re,io,base64,ast
from fastapi import Request,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel,Field
from PIL import Image
from backend.documents import extract,retrieve,context_for
from backend.exports import build_exports
from backend.local_models import ModelUnavailable,ModelBusy
from backend.sandbox import run_isolated

class Question(BaseModel):
    prompt:str=Field(min_length=1,max_length=800)
    document_id:str|None=None
class RunInput(BaseModel):
    document_id:str
    goal:str=Field(default='Summarize the inspection findings and draft a review approval note.',min_length=1,max_length=500)
class CodeInput(BaseModel):
    utility:str=Field(pattern='^(temperature|sum_readings)$')

def extractive_approval_note(evidence):
    combined='\n'.join(e['text'] for e in evidence)
    def field(label):
        match=re.search(rf'(?im)^\s*{re.escape(label)}\s*:\s*(.+?)\s*$',combined)
        return match.group(1).strip().rstrip(',.') if match else None
    reference=field('Inspection reference')
    equipment=field('Equipment')
    finding=field('Finding')
    recommendation=field('Recommendation')
    cost=field('Cost')
    source=next((e for e in evidence if any(token and token in e['text'] for token in (reference,equipment,finding))),evidence[0])
    ref=f"[{source['ref']}]"
    subject=f"Review of inspection finding{f' for {equipment}' if equipment else ''}"
    background=(f"Inspection {reference} records a review of {equipment or 'the reported equipment'} {ref}." if reference
                else f"The supplied inspection material records a finding for {equipment or 'the reported equipment'} {ref}.")
    finding_text=(f"The report records {finding.lower()} {ref}." if finding else
                  f"The source excerpt should be checked for the exact recorded finding {ref}.")
    action=(f"The report recommends the following action: {recommendation[0].lower()+recommendation[1:]} {ref}." if recommendation else
            "No proposed action was identified in the extracted evidence. The reviewer should consult the original report.")
    if cost and cost.lower() not in {'not provided','not available','nil'}:
        finance=f"The extracted report states the cost as {cost} {ref}. This amount requires independent verification."
    else:
        finance=f"Cost information was not provided in the report {ref}. Financial approval cannot be completed until the responsible reviewer supplies and verifies it."
    references='\n'.join(f"[{e['ref']}] {e['filename']}, page {e['page']}" for e in evidence)
    observations='\n'.join(f"- {e['text'].replace(chr(10),' ').strip()} [{e['ref']}]" for e in evidence)
    return '\n'.join([
        f"Subject: {subject}",
        "Background",background,
        "Recorded finding",finding_text,
        "Proposed action",action,
        "Financial position",finance,
        "Decision requested",
        "Review the recorded finding and proposed action, confirm the responsible owner, and provide any required cost and authorization details. This draft does not authorize expenditure, maintenance or an operational conclusion.",
        "Immediate reviewer next steps",
        "1. Confirm the original report and the cited page evidence.\n2. Verify isolation, permit and site safety controls before any work.\n3. Assign an accountable owner and due date.\n4. Record cost, authorization and restart requirements before approval.",
        "Recorded source observations",observations,
        "Source references",references,
    ])

def grounded_evidence_brief(evidence, prompt):
    """Readable deterministic answer used when model citations cannot be trusted."""
    lines=[
        "Evidence-grounded brief",
        "The local model draft did not pass citation validation. The statements below are limited to the supplied source text and require human review.",
        "",
        "What the supplied sources state",
    ]
    for evidence_item in evidence:
        text=' '.join(evidence_item['text'].split())
        sentences=[part.strip() for part in re.split(r'(?<=[.!?])\s+',text) if part.strip()]
        selected=' '.join(sentences[:3])[:650]
        lines.append(f"- {selected} [{evidence_item['ref']}]")
    lines.extend([
        "",
        "Required verification before action",
        "- Confirm the original document, revision and page reference for each statement.",
        "- Check the applicable site permit, isolation, gas-testing and emergency procedures with the responsible supervisor.",
        "- Record the decision owner, due date, authorization and any missing measurements or cost information.",
        "",
        "Evidence limits",
        "The supplied excerpts do not by themselves establish that an incident occurred, identify a root cause, or authorize work. Review the original files and applicable site rules before making an operational decision.",
        "",
        "Sources",
        '\n'.join(f"[{item['ref']}] {item['filename']}, page {item['page']}" for item in evidence),
    ])
    return '\n'.join(lines)

def install(app,database,identity,owned_workspace,engine,db_path,upload_dir):
    data=Path(db_path).parent;previews=data/'previews';artifacts=data/'artifacts';jobs_lock=Lock();extract_lock=Lock()
    with database() as con:
        con.executescript('''CREATE TABLE IF NOT EXISTS pages(document_id TEXT NOT NULL REFERENCES documents(id),page INTEGER NOT NULL,text TEXT NOT NULL,details TEXT NOT NULL,PRIMARY KEY(document_id,page));
        CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,workspace_id TEXT NOT NULL REFERENCES workspaces(id),kind TEXT NOT NULL,status TEXT NOT NULL,events TEXT NOT NULL,result TEXT NOT NULL,created_at INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_runs_workspace ON runs(workspace_id,created_at);
        CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY,workspace_id TEXT NOT NULL REFERENCES workspaces(id),run_id TEXT NOT NULL REFERENCES runs(id),filename TEXT NOT NULL,path TEXT NOT NULL);''')
    with database() as con:
        con.execute("UPDATE runs SET status='interrupted' WHERE status='running'")
    def owned_doc(document_id,user,write=False):
        with database() as con:
            row=con.execute('''SELECT d.*,w.owner_id,COALESCE(m.kind,'report') AS kind,u.role AS owner_role
                FROM documents d JOIN workspaces w ON d.workspace_id=w.id JOIN users u ON u.id=w.owner_id
                LEFT JOIN document_metadata m ON m.document_id=d.id WHERE d.id=?''',(document_id,)).fetchone()
        shared_reference=row and row['kind']=='reference' and row['owner_role']=='administrator'
        if row and row['owner_id']!=user['id'] and not shared_reference and user['role']!='administrator' and not (user['role']=='supervisor' and not write):row=None
        if not row:raise HTTPException(404,'Document not found.')
        return dict(row)
    def read_doc(doc):
        with extract_lock:
            try:pages=extract(upload_dir/doc['id'],doc['filename'],previews,doc['id'])
            except Exception as exc:raise ValueError('Could not read this file: '+str(exc)[:200])
            with database() as con:
                con.execute('DELETE FROM pages WHERE document_id=?',(doc['id'],))
                for page in pages:con.execute('INSERT INTO pages VALUES (?,?,?,?)',(doc['id'],page['page'],page['text'],json.dumps(page)))
        return pages
    def records(workspace):
        with database() as con:
            return [dict(r) for r in con.execute('''SELECT p.document_id,p.page,p.text,d.filename
                FROM pages p JOIN documents d ON p.document_id=d.id
                JOIN workspaces w ON w.id=d.workspace_id LEFT JOIN document_metadata m ON m.document_id=d.id
                WHERE d.workspace_id=? OR COALESCE(m.kind,'report')='reference' AND w.owner_id IN (SELECT id FROM users WHERE role='administrator')
                ORDER BY CASE WHEN COALESCE(m.kind,'report')='reference' THEN 0 ELSE 1 END,d.created_at DESC,p.page LIMIT 600''',(workspace,)).fetchall()]
    def save_answer(workspace,prompt,result):
        ident=str(uuid.uuid4());now=int(time.time())
        with database() as con:con.execute('INSERT INTO generations VALUES (?,?,?,?,?)',(ident,workspace,prompt,json.dumps(result),now))
        return {'id':ident,'prompt':prompt,'created_at':now,**result}
    def evidence_check(answer,evidence):
        allowed={e['ref'] for e in evidence};cited=set(re.findall(r'\[(S\d+)\]',answer))
        return bool(cited) and cited.issubset(allowed)
    def update(run,event=None,status=None,result=None):
        with database() as con:
            row=con.execute('SELECT events,status,result FROM runs WHERE id=?',(run,)).fetchone();events=json.loads(row['events'])
            if event:events.append({'time':int(time.time()),'message':event})
            con.execute('UPDATE runs SET events=?,status=?,result=? WHERE id=?',(json.dumps(events),status or row['status'],json.dumps(result) if result is not None else row['result'],run))
    def attach(run,workspace,path):
        ident=str(uuid.uuid4())
        with database() as con:con.execute('INSERT INTO artifacts VALUES (?,?,?,?,?)',(ident,workspace,run,path.name,str(path.relative_to(data))))
        return {'id':ident,'filename':path.name}
    def create_run(workspace,kind,work):
        if not jobs_lock.acquire(False):raise HTTPException(429,'An agent workflow is already running. Wait for it to finish.')
        ident=str(uuid.uuid4())
        with database() as con:con.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)',(ident,workspace,kind,'running','[]','{}',int(time.time())))
        def wrapped():
            try:work(ident)
            except Exception as exc:update(ident,'Stopped: '+str(exc)[:250],'failed',{'error':str(exc)[:250]})
            finally:jobs_lock.release()
        Thread(target=wrapped,daemon=True).start();return {'id':ident,'status':'running'}

    @app.post('/api/documents/{document_id}/extract')
    def read(document_id:str,request:Request):
        doc=owned_doc(document_id,identity(request,True),True)
        try:return {'pages':read_doc(doc)}
        except ValueError as exc:raise HTTPException(422,str(exc))

    @app.get('/api/documents/{document_id}/pages')
    def pages(document_id:str,request:Request):
        owned_doc(document_id,identity(request))
        with database() as con:rows=con.execute('SELECT details FROM pages WHERE document_id=? ORDER BY page',(document_id,)).fetchall()
        return {'pages':[json.loads(r['details']) for r in rows]}

    @app.get('/api/documents/{document_id}/pages/{page}/image')
    def page_image(document_id:str,page:int,request:Request):
        owned_doc(document_id,identity(request));path=previews/f'{document_id}-{page}.png'
        if not path.is_file():raise HTTPException(404,'Page image unavailable. Read the document first.')
        return FileResponse(path,media_type='image/png')

    @app.post('/api/workspaces/{workspace_id}/questions',status_code=201)
    def question(workspace_id:str,body:Question,request:Request):
        identity_user=identity(request,True);owned_workspace(workspace_id,identity_user,True)
        available=records(workspace_id)
        if not available:raise HTTPException(422,'Read at least one material first to build the local knowledge collection.')
        evidence=retrieve(available,body.prompt)
        if not evidence:return save_answer(workspace_id,body.prompt,{'answer':'I could not find supporting evidence in the extracted documents. Try a more specific term or read another document.','model_name':'Local evidence search','capability':'retrieval','routing_reason':'No matching evidence; generation was skipped.','duration_ms':0,'finish_reason':'stop','sources':[]})
        try:result=engine.generate(body.prompt,context=context_for(evidence))
        except (ModelUnavailable,ModelBusy) as exc:raise HTTPException(503,str(exc))
        if not evidence_check(result['answer'],evidence):
            result['answer']=grounded_evidence_brief(evidence,body.prompt)
            result['finish_reason']='stop'
            result['extractive_fallback']=True
        result['sources']=evidence;result['citation_format_valid']=evidence_check(result['answer'],evidence)
        result['review_note']='Source links identify retrieved evidence; review whether each claim is supported.'
        saved=save_answer(workspace_id,body.prompt,result)
        report_id=None
        with database() as con:
            candidates=dict.fromkeys(([body.document_id] if body.document_id else [])+[item['document_id'] for item in evidence if item.get('document_id')])
            for candidate in candidates:
                kind=con.execute("SELECT COALESCE(m.kind,'report') FROM documents d LEFT JOIN document_metadata m ON m.document_id=d.id WHERE d.id=? AND d.workspace_id=?",(candidate,workspace_id)).fetchone()
                if kind and kind[0]=='report':report_id=candidate;break
        if report_id:
            with database() as con:
                report=con.execute('''SELECT d.id,d.workspace_id,COALESCE(m.kind,'report') AS kind
                    FROM documents d LEFT JOIN document_metadata m ON m.document_id=d.id WHERE d.id=?''',(report_id,)).fetchone()
                if report and report['workspace_id']==workspace_id and report['kind']=='report':
                    run_id=str(uuid.uuid4());now=int(time.time());events=[{'time':now,'message':'Incident analysis completed in Assistant.'},{'time':now,'message':'Queued for Supervisor analysis and approval.'}]
                    con.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)',(run_id,workspace_id,'analysis','complete',json.dumps(events),json.dumps(result),now))
                    review_id=str(uuid.uuid4());con.execute('''INSERT INTO review_requests
                        (id,run_id,workspace_id,document_id,requester_id,status,reviewer_note,created_at)
                        VALUES (?,?,?,?,?,'pending_analysis','',?)''',(review_id,run_id,workspace_id,report_id,identity_user['id'],now))
                    con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',(identity_user['id'],'incident_analysis_queued_for_supervisor',now))
                    saved['review_request_id']=review_id;saved['review_status']='pending_analysis'
        return saved

    @app.post('/api/documents/{document_id}/vision',status_code=201)
    def vision(document_id:str,request:Request):
        doc=owned_doc(document_id,identity(request,True),True);path=previews/f'{document_id}-1.png'
        if not path.exists():read_doc(doc)
        if not path.exists():raise HTTPException(422,'Vision requires an image or PDF page.')
        with Image.open(path) as image:
            image.thumbnail((768,768));buffer=io.BytesIO();image.convert('RGB').save(buffer,format='JPEG')
        prompt='Describe the visible content in this image. Do not infer safety, hidden connections or unreadable measurements.'
        try:result=engine.generate(prompt,image='data:image/jpeg;base64,'+base64.b64encode(buffer.getvalue()).decode())
        except (ModelUnavailable,ModelBusy) as exc:raise HTTPException(503,str(exc))
        result['sources']=[{'ref':'Image','document_id':document_id,'filename':doc['filename'],'page':1,'text':'Visual interpretation of page 1; may be inaccurate. Check the original.'}]
        result['review_note']='Small vision model output is preliminary. No engineering validation was performed.'
        return save_answer(doc['workspace_id'],prompt,result)

    @app.post('/api/workspaces/{workspace_id}/runs',status_code=202)
    def agent(workspace_id:str,body:RunInput,request:Request):
        user=identity(request,True);owned_workspace(workspace_id,user,True);primary=owned_doc(body.document_id,user,True)
        if primary['workspace_id']!=workspace_id:raise HTTPException(404,'Document not found in this workspace.')
        def work(run):
            update(run,'Plan: read the selected report, retrieve evidence, draft, check references and create Office files.')
            read_doc(primary);update(run,'Read selected report and retained page references.')
            available=records(workspace_id);evidence=retrieve(available,body.goal)
            if not evidence:
                update(run,'Search returned no match. Refined the search using text from the selected report.')
                first=next((r for r in available if r['document_id']==primary['id'] and r['text'].strip()),None)
                if not first:raise ValueError('No readable text. Review the scan before drafting.')
                evidence=retrieve(available,first['text'][:300])
            if not evidence:raise ValueError('No supporting source evidence found.')
            if not any(e['document_id']==primary['id'] for e in evidence):
                first=next(r for r in available if r['document_id']==primary['id'] and r['text'].strip())
                evidence=evidence[:2]+[{'ref':'S3','document_id':primary['id'],'filename':primary['filename'],'page':first['page'],'text':first['text'][:600]}]
            update(run,f'Retrieved {len(evidence)} excerpts from the local collection.')
            prompt=body.goal+' Use source IDs like [S1]. Mark missing costs or authorizations as not provided. Draft for human review only.'
            result=engine.generate(prompt,context=context_for(evidence));draft=result['answer']
            update(run,'Generated a draft using the general local model.')
            if not evidence_check(draft,evidence):
                update(run,'Reference check failed. Requesting one revision with valid source IDs.')
                result=engine.generate(prompt+' Every factual sentence needs a supplied source ID.',context=context_for(evidence));draft=result['answer']
            if not evidence_check(draft,evidence):
                update(run,'Model references remained unreliable. Producing an explicitly extractive review note.')
                draft=extractive_approval_note(evidence)
            directory=artifacts/run;names=build_exports(directory,draft,evidence)
            links=[attach(run,workspace_id,directory/name) for name in names]
            update(run,'Created editable Word, Excel and PowerPoint files; human review remains required.','complete',{'draft':draft,'sources':evidence,'artifacts':links,'review_required':True})
            with database() as con:
                con.execute('''INSERT OR IGNORE INTO review_requests
                    (id,run_id,workspace_id,document_id,requester_id,status,reviewer_note,created_at)
                    VALUES (?,?,?,?,?,'pending_analysis','',?)''',
                    (str(uuid.uuid4()),run,workspace_id,primary['id'],user['id'],int(time.time())))
                con.execute('INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)',(user['id'],'review_request_created',int(time.time())))
        return create_run(workspace_id,'inspection',work)

    @app.post('/api/workspaces/{workspace_id}/code-runs',status_code=202)
    def coding(workspace_id:str,body:CodeInput,request:Request):
        owned_workspace(workspace_id,identity(request,True),True)
        def work(run):
            if body.utility=='temperature':name='celsius_to_fahrenheit';inputs=[-40,0,100];expected=[-40,32,212];description='Convert Celsius to Fahrenheit using c * 9 / 5 + 32.'
            else:name='sum_readings';inputs=[[],[1,2,3],[-2,2,5]];expected=[0,6,5];description='Return the sum of a list of numeric readings. An empty list returns zero.'
            prompt=f'Write only Python code defining {name}(value). {description} Do not call input or print.'
            update(run,'Plan: generate the function, run it in WebAssembly, compare independent cases and repair at most once.')
            passed=False;code='';checks=[]
            for attempt in range(2):
                result=engine.generate(prompt);text=result['answer'];match=re.search(r'```(?:python)?\s*(.*?)```',text,re.S);code=match.group(1) if match else text
                try:
                    parsed=ast.parse(code)
                    functions=[node for node in parsed.body if isinstance(node,ast.FunctionDef)]
                    if not any(node.name==name for node in functions):raise ValueError('Required function missing.')
                    code='\n\n'.join(ast.unparse(node) for node in functions)
                    harness=code+'\nimport json\nprint("AEGIS_RESULTS="+json.dumps(['+','.join(f'{name}({value!r})' for value in inputs)+']))'
                    execution=run_isolated(harness)
                    marker=next((line.split('=',1)[1] for line in execution['stdout'].splitlines() if line.startswith('AEGIS_RESULTS=')),None)
                    actual=json.loads(marker) if marker else []
                    checks=[{'input':value,'expected':expect,'actual':actual[i] if i<len(actual) else None,'passed':i<len(actual) and type(actual[i]) in (int,float) and abs(actual[i]-expect)<1e-8} for i,(value,expect) in enumerate(zip(inputs,expected))]
                    passed=execution['exit_code']==0 and all(c['passed'] for c in checks)
                except Exception as exc:execution={'exit_code':1,'stderr':str(exc),'stdout':''};checks=[]
                update(run,f'Attempt {attempt+1}: '+('all three independent cases passed.' if passed else 'verification failed.'))
                if passed:break
                prompt=f'Fix this Python function. Required name: {name}. {description} Previous code: {code[:1200]}. Failed checks: {json.dumps(checks)[:800]}. Return only code.'
            directory=artifacts/run;directory.mkdir(parents=True,exist_ok=True);path=directory/'utility.py';path.write_text(code,encoding='utf-8')
            links=[attach(run,workspace_id,path)]
            update(run,'Verification finished in a WebAssembly runtime with no host filesystem or network grants.','complete' if passed else 'failed',{'code':code,'checks':checks,'execution':execution,'artifacts':links,'verified':passed})
        return create_run(workspace_id,'coding',work)

    @app.get('/api/workspaces/{workspace_id}/runs')
    def list_runs(workspace_id:str,request:Request):
        owned_workspace(workspace_id,identity(request))
        with database() as con:rows=con.execute('SELECT * FROM runs WHERE workspace_id=? ORDER BY created_at DESC,rowid DESC LIMIT 20',(workspace_id,)).fetchall()
        return {'runs':[{**dict(r),'events':json.loads(r['events']),'result':json.loads(r['result'])} for r in rows]}

    @app.get('/api/artifacts/{artifact_id}/download')
    def artifact(artifact_id:str,request:Request):
        user=identity(request)
        with database() as con:row=con.execute('SELECT a.*,w.owner_id FROM artifacts a JOIN workspaces w ON a.workspace_id=w.id WHERE a.id=?',(artifact_id,)).fetchone()
        if row and row['owner_id']!=user['id'] and user['role'] not in ('supervisor','administrator'):row=None
        if not row:raise HTTPException(404,'Artifact not found.')
        path=(data/row['path']).resolve()
        if not path.is_relative_to(artifacts.resolve()) or not path.is_file():raise HTTPException(404,'Artifact unavailable.')
        return FileResponse(path,filename=row['filename'],media_type='application/octet-stream')
