# Aegis — SIH26117 local workbench

The current prototype includes local accounts, private workspaces, material uploads and OCR, source-grounded answers, automatic local model selection, multimodal interpretation, agent workflows, editable Office deliverables, verified WebAssembly utilities, and visible local-connection observations.

## Run on this Windows computer
Double-click `Start Aegis.cmd`, then open http://127.0.0.1:8765 in your browser.
Create your own account using **Create account**. There is no default password.

## Role portals

- User: http://127.0.0.1:8765/login/user
- Supervisor: http://127.0.0.1:8765/login/supervisor
- Administrator: http://127.0.0.1:8765/login/administrator

Self-registration always creates a User account. Assign the first elevated role locally with `python scripts/set_user_role.py USERNAME administrator`; Administrators can then manage other roles from the dashboard. Supervisors can review team workspaces but cannot change another user's workspace. Administrators have full workspace access.

Alternatively, from this project directory:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8765
```

The server deliberately listens only on this computer. Do not change the host to expose it to a network without adapting deployment security.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

See `docs/PRD.md`, `docs/IMPLEMENTATION_LOG.md`, and `docs/TEST_REPORT.md` for scope, progress, and results.

## Files
- `backend/`: API, identity, SQLite storage and ownership checks.
- `frontend/`: local HTML, CSS and JavaScript; no CDN/build step.
- `data/workbench.sqlite3`: created automatically; contains local accounts and workspace metadata.
- `tests/`: isolated automated tests, independent of your live database.
- `requirements.txt`: frozen Python dependencies.

## Dashboard sequence
Open a workspace and follow Overview → Materials → Assistant → Workflows → Offline status. The dashboard includes desktop sidebar navigation and compact mobile tabs.

- Materials: drag and drop PDF, TXT, CSV, PNG or JPEG files; 20 MB per file and 200 MB per workspace. Read files locally, inspect extracted sources, search and filter the collection.
- Assistant: ask general questions or enable workspace sources for grounded answers with page links.
- Workflows: create an inspection review pack as DOCX/XLSX/PPTX or generate and verify a fixed-purpose utility in WebAssembly.
- Offline status: view current application and child-process connection observations.

## Maintenance corpus test data

The supplied HP-800 maintenance corpus is available in `samples/maintenance-corpus`. After creating or selecting a local account, import it into that account's workspace with:

```powershell
.\.venv\Scripts\python.exe scripts/import_maintenance_corpus.py pranav_tej
```

This creates or reuses `HP-800 maintenance reference`, stores the SOP, maintenance log, and incident report as local Materials, and extracts their pages for source-grounded questions. The JSON task list and XLSX test matrix are kept in `samples/test-fixtures` because the current Materials uploader accepts PDF, TXT, CSV, PNG, and JPEG.

This remains a workstation prototype. Windows administrators can access its data; password recovery and enterprise account provisioning are not implemented. Generated output requires human review. Connection snapshots are useful evidence but are not a packet-capture certificate.
