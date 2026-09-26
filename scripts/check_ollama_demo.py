"""Fail the public demo startup if its loopback-only local models are unavailable."""
import sys
import httpx

EXPECTED = {'ark-demo-general:latest', 'ark-demo-coding:latest', 'ark-demo-vision:latest'}

try:
    with httpx.Client(trust_env=False, timeout=5) as client:
        response = client.get('http://127.0.0.1:11434/api/tags')
        response.raise_for_status()
        installed = {item['name'] for item in response.json()['models']}
except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
    print(f'Ollama is not ready on this PC: {error}', file=sys.stderr)
    raise SystemExit(1)

missing = EXPECTED - installed
if missing:
    print('Missing local demo models: ' + ', '.join(sorted(missing)), file=sys.stderr)
    raise SystemExit(1)
print('Local general, coding, and vision models are ready.')
