import json
from pathlib import Path
from backend.sandbox import run_isolated
cases={
 'arithmetic':'print(2+3)',
 'host_file':'open("C:/Windows/win.ini").read()',
 'network':'import socket; socket.create_connection(("example.com",443),timeout=1)',
 'loop':'while True: pass',
 'memory':'x=bytearray(500*1024*1024)'}
results={name:run_isolated(code) for name,code in cases.items()}
assert results['arithmetic']['stdout'].strip()=='5'
assert all(results[name]['exit_code']!=0 for name in ['host_file','network','loop','memory'])
Path('docs/SANDBOX_CHECKS.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
