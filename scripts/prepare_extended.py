from pathlib import Path
import urllib.request,hashlib,json
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parent.parent
base='https://github.com/vmware-labs/webassembly-language-runtimes/releases/download/python/3.12.0%2B20231211-040d5a6/'
checksum=urllib.request.urlopen(base+'python-3.12.0.wasm.sha256sum').read().decode().split()[0]
assets=[('runtime/python.wasm',base+'python-3.12.0.wasm',checksum),('models/vision.gguf','https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF/resolve/main/SmolVLM-500M-Instruct-Q8_0.gguf?download=true','9d4612de6a42214499e301494a3ecc2be0abdd9de44e663bda63f1152fad1bf4'),('models/vision-projector.gguf','https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF/resolve/main/mmproj-SmolVLM-500M-Instruct-Q8_0.gguf?download=true','d1eb8b6b23979205fdf63703ed10f788131a3f812c7b1f72e0119d5d81295150')]
def fetch(asset):
 name,url,sha=asset;p=ROOT/name;part=p.with_suffix('.part')
 if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==sha:return name
 with urllib.request.urlopen(url,timeout=120) as source,part.open('wb') as dest:
  while chunk:=source.read(1024*1024):dest.write(chunk)
 if hashlib.sha256(part.read_bytes()).hexdigest()!=sha:raise RuntimeError('Checksum mismatch')
 part.replace(p);return name
with ThreadPoolExecutor(max_workers=3) as pool:
 for item in pool.map(fetch,assets):print('Verified '+item,flush=True)
(ROOT/'docs/EXTENDED_ASSETS.json').write_text(json.dumps(assets,indent=2))
