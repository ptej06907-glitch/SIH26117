from pathlib import Path
import sys,time,json,shutil,secrets,base64
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))
from backend.app import create_app
from fastapi.testclient import TestClient
result={}
app=create_app(ROOT/'data/e2e.sqlite3')
def wait(c,w):
 deadline=time.monotonic()+240
 while time.monotonic()<deadline:
  run=c.get(f'/api/workspaces/{w}/runs').json()['runs'][0]
  if run['status']!='running':return run
  time.sleep(.5)
 raise RuntimeError('Workflow timed out')
with TestClient(app,base_url='http://127.0.0.1',headers={'X-Workbench-Request':'1'}) as c:
 r=c.post('/api/auth/register',json={'username':'qa_'+secrets.token_hex(4),'display_name':'Local verification','password':secrets.token_urlsafe(24)});r.raise_for_status();c.headers['X-CSRF-Token']=r.json()['csrf_token']
 w=c.post('/api/workspaces',json={'name':'Fictional inspection verification'}).json()['id']
 ids=[]
 for name in ['inspection-scan.pdf','demo-sop.txt']:
  r=c.post(f'/api/workspaces/{w}/documents',params={'filename':name},content=(ROOT/'samples'/name).read_bytes());r.raise_for_status();ids.append(r.json()['id'])
  r=c.post(f'/api/documents/{ids[-1]}/extract');r.raise_for_status();result[name]=r.json()
 r=c.post(f'/api/workspaces/{w}/questions',json={'prompt':'What is damaged on P-101 and are costs supplied?'});r.raise_for_status();result['grounded_answer']=r.json();print('Grounded answer:',r.json()['answer'],flush=True)
 r=c.post(f'/api/documents/{ids[0]}/vision');result['vision_status']=r.status_code;result['vision']=r.json();print('Vision:',r.status_code,flush=True)
 r=c.post(f'/api/workspaces/{w}/runs',json={'document_id':ids[0]});r.raise_for_status();run=wait(c,w);result['review_run']=run;print('Review pack:',run['status'],flush=True)
 output=ROOT/'docs/demo-output';output.mkdir(exist_ok=True)
 for a in run['result'].get('artifacts',[]):
  response=c.get(f"/api/artifacts/{a['id']}/download");response.raise_for_status();(output/a['filename']).write_bytes(response.content)
 r=c.post(f'/api/workspaces/{w}/code-runs',json={'utility':'temperature'});r.raise_for_status();run=wait(c,w);result['code_run']=run;print('Coding:',run['status'],run['result'].get('checks'),flush=True)
 for a in run['result'].get('artifacts',[]):
  response=c.get(f"/api/artifacts/{a['id']}/download");(output/a['filename']).write_bytes(response.content)
 result['network']=c.get('/api/system/network').json()
(ROOT/'docs/END_TO_END_RESULTS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert result['review_run']['status']=='complete',result['review_run']
assert result['code_run']['result'].get('verified'),result['code_run']
assert result['vision_status']==201,result['vision']
print('All live workflow checks completed.',flush=True)
