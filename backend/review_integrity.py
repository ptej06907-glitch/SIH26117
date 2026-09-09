import hashlib
import json
from pathlib import Path
from backend.vault import read_bytes

def snapshot(con, review, data_root):
    run=con.execute('SELECT result FROM runs WHERE id=?',(review['run_id'],)).fetchone()
    result=json.loads(run['result'])
    document_ids={review['document_id']} | {s['document_id'] for s in result.get('sources',[]) if s.get('document_id')}
    documents={}
    for ident in sorted(document_ids):
        row=con.execute('SELECT sha256 FROM documents WHERE id=?',(ident,)).fetchone()
        path=Path(data_root)/'uploads'/ident
        if not row or not path.is_file():raise ValueError('A reviewed source is missing.')
        digest=hashlib.sha256(read_bytes(path)).hexdigest()
        if digest!=row['sha256']:raise ValueError('A source file has changed since upload.')
        documents[ident]=digest
    artifacts={}
    for row in con.execute('SELECT id,path FROM artifacts WHERE run_id=?',(review['run_id'],)):
        artifacts[row['id']]=hashlib.sha256(read_bytes(Path(data_root)/row['path'])).hexdigest()
    payload=json.dumps({'result':result,'documents':documents,'artifacts':artifacts},sort_keys=True,separators=(',',':'))
    return hashlib.sha256(payload.encode()).hexdigest(),payload
