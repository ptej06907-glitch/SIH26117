"""Import ARK's bundled GGUF weights into an already-running local Ollama service.

Only the fixed loopback API is used. This script never pulls models from the cloud.
"""
from pathlib import Path
import hashlib
import json
import sys
import httpx

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / 'models'
API = 'http://127.0.0.1:11434'

def digest(path):
    with path.open('rb') as source:
        return 'sha256:' + hashlib.file_digest(source, 'sha256').hexdigest()

def main():
    registry = json.loads((MODELS / 'registry.json').read_text(encoding='utf-8-sig'))
    with httpx.Client(trust_env=False, timeout=httpx.Timeout(600, connect=5)) as client:
        response = client.get(API + '/api/tags')
        response.raise_for_status()
        installed = {item['name'] for item in response.json()['models']}
        for entry in registry:
            name = 'ark-demo-' + entry['id']
            if name + ':latest' in installed:
                print(name + ' already imported')
                continue
            files = {}
            for filename in (entry['file'], *([entry['projector']] if entry.get('projector') else [])):
                path = (MODELS / filename).resolve()
                if not path.is_relative_to(MODELS.resolve()) or not path.is_file():
                    raise FileNotFoundError(f'Missing local model component: {filename}')
                checksum = digest(path)
                check = client.head(API + '/api/blobs/' + checksum)
                if check.status_code == 404:
                    print('Importing ' + filename + ' from this PC...')
                    with path.open('rb') as source:
                        upload = client.post(API + '/api/blobs/' + checksum, content=source)
                    upload.raise_for_status()
                else:
                    check.raise_for_status()
                files[filename] = checksum
            result = client.post(API + '/api/create', json={'model':name,'files':files,'stream':False})
            result.raise_for_status()
            if result.json().get('status') != 'success':
                raise RuntimeError(f'Local import did not complete for {name}')
            print(name + ' ready')

if __name__ == '__main__':
    try:
        main()
    except (httpx.HTTPError, KeyError, ValueError, OSError, RuntimeError) as error:
        print(f'Local Ollama model import failed: {error}', file=sys.stderr)
        raise SystemExit(1)
