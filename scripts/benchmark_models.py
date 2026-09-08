from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from backend.local_models import LocalModels
engine=LocalModels(ROOT)
results=[]
try:
    for prompt,expected in [
        ('Write a two-sentence note requesting review of inspection report DEMO-001. No findings or costs have been supplied. Do not invent them.','general'),
        ('Write a short Python function celsius_to_fahrenheit(c) that converts Celsius to Fahrenheit. Include one example.','coding')]:
        result=engine.generate(prompt)
        assert result['capability']==expected
        assert result['answer'].strip()
        results.append({'prompt':prompt,**result})
        print(json.dumps(result),flush=True)
finally:
    engine.close()
    (ROOT/'docs/LOCAL_MODEL_BENCHMARK.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
