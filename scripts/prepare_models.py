from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request, hashlib, zipfile, json
ROOT=Path(__file__).resolve().parent.parent
ASSETS=[
 ('runtime/llama.zip','https://github.com/ggml-org/llama.cpp/releases/download/b10809/llama-b10809-bin-win-cpu-x64.zip','9df3158ed228a641a4b127942d7f459f24c9e13f04682659d05c00c80099b6b5'),
 ('models/general.gguf','https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf?download=true','6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e'),
 ('models/coding.gguf','https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf?download=true','cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046')]
def digest(path):
 with path.open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()
def download(asset):
 relative,url,expected=asset;path=ROOT/relative;path.parent.mkdir(exist_ok=True)
 if path.exists() and digest(path)==expected:return relative+' already verified'
 temporary=path.with_suffix('.part')
 with urllib.request.urlopen(url,timeout=120) as response, temporary.open('wb') as target:
  while chunk:=response.read(1024*1024):target.write(chunk)
 if digest(temporary)!=expected:raise RuntimeError('Checksum mismatch: '+relative)
 temporary.replace(path)
 return relative+' downloaded and verified'
with ThreadPoolExecutor(max_workers=3) as pool:
 for result in pool.map(download,ASSETS):print(result,flush=True)
with zipfile.ZipFile(ROOT/'runtime/llama.zip') as archive:
 target=(ROOT/'runtime/llama').resolve()
 for entry in archive.infolist():
  if not (target/entry.filename).resolve().is_relative_to(target):raise RuntimeError('Unsafe archive member')
 archive.extractall(target)
(ROOT/'docs/MODEL_ASSETS.json').write_text(json.dumps([{'file':p,'source':u,'sha256':h} for p,u,h in ASSETS],indent=2))
print('Runtime extracted; all assets ready.',flush=True)
