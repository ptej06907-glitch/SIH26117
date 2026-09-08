from pathlib import Path
import re

from backend.app import create_app
from tests.test_auth import client, register


class CorpusEngine:
    def close(self):
        pass

    def status(self):
        return [{'id': 'fixture', 'name': 'Corpus test model', 'capability': 'general', 'status': 'installed'}]

    def generate(self, prompt, **kwargs):
        return {
            'answer': 'The first vibration breach is 2026-08-25 at 4.8 mm/s RMS [S1].',
            'model_name': 'Corpus test model', 'capability': 'general',
            'routing_reason': 'Test fixture', 'duration_ms': 1, 'finish_reason': 'stop',
        }


def test_supplied_maintenance_corpus_supports_incident_reference_flow(tmp_path):
    app = create_app(tmp_path / 'db.sqlite3', CorpusEngine())
    corpus = Path(__file__).parents[1] / 'samples' / 'maintenance-corpus'
    with client(app) as c:
        register(c)
        workspace = c.post('/api/workspaces', json={'name': 'HP-800 incident test'}).json()['id']
        document_ids = []
        for source in sorted(corpus.glob('*.md')):
            uploaded = c.post(
                f'/api/workspaces/{workspace}/documents',
                params={'filename': source.stem + '.txt'},
                content=source.read_bytes(),
            )
            assert uploaded.status_code == 201, uploaded.text
            document_ids.append(uploaded.json()['id'])
            assert c.post(f"/api/documents/{document_ids[-1]}/extract").status_code == 200

        documents = c.get(f'/api/workspaces/{workspace}/documents').json()['documents']
        assert len(documents) == 3 and all(item['extracted'] for item in documents)
        pages = []
        for document_id in document_ids:
            pages.extend(c.get(f'/api/documents/{document_id}/pages').json()['pages'])
        corpus_text = '\n'.join(page['text'] for page in pages)
        assert corpus_text.count('HP-800-03') >= 3
        assert '4.8' in corpus_text and 'WO-4471' in corpus_text

        answer = c.post(
            f'/api/workspaces/{workspace}/questions',
            json={'prompt': 'Which maintenance log reading first crossed the vibration threshold?'}
        )
        assert answer.status_code == 201
        assert answer.json()['citation_format_valid']
        assert answer.json()['sources']

        work_orders = sorted(set(re.findall(r'WO-\d+', corpus_text)))
        assert work_orders == ['WO-4471']
