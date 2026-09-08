import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def run_isolated(code):
    if len(code)>12000:raise ValueError('Code exceeds the prototype limit.')
    if not (ROOT/'runtime/python.wasm').is_file():raise ValueError('The isolated Python runtime is not installed.')
    try:
        process=subprocess.run([sys.executable,str(ROOT/'backend/wasm_runner.py')],input=json.dumps({'code':code}),text=True,capture_output=True,timeout=45,creationflags=0x08000000 if sys.platform=='win32' else 0)
    except subprocess.TimeoutExpired:return {'exit_code':1,'stdout':'','stderr':'Sandbox wall-time limit exceeded.','reason':'timeout','isolation':'WebAssembly/WASI'}
    if process.returncode:raise ValueError('Sandbox runtime failed to start: '+process.stderr[-500:])
    return json.loads(process.stdout)
