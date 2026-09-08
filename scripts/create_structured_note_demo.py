from pathlib import Path

from backend.exports import build_exports
from backend.workflows import extractive_approval_note

evidence = [{
    'ref': 'S1',
    'filename': 'inspection-scan.pdf',
    'page': 1,
    'document_id': 'demo',
    'text': (
        'Inspection reference: DEMO-002\n'
        'Equipment: P-101\n'
        'Finding: identification label damaged\n'
        'Recommendation: replace the damaged label after review.\n'
        'Cost: not provided.'
    ),
}]

output = Path('docs/demo-output/structured-review-pack')
draft = extractive_approval_note(evidence)
build_exports(output, draft, evidence)
print(output / 'approval-note.docx')
