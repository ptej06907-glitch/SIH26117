"""Import the supplied maintenance corpus into a local Aegis workspace.

This is intentionally local-only. It copies the three Markdown source files into
the application's upload store, records their metadata in SQLite, and extracts
their pages so Assistant source retrieval can use them. The test matrix and JSON
task list remain versioned fixtures in samples/test-fixtures rather than being
treated as operational evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sqlite3
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app import ROOT, create_app
from backend.documents import extract
from backend import vault


CORPUS = (
    ("sop_press_maintenance.md", "sop_press_maintenance.txt", "reference"),
    ("maintenance_log_hp800.md", "maintenance_log_hp800.txt", "reference"),
    ("incident_report_template.md", "incident_report_template.txt", "report"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import the local HP-800 maintenance corpus into Aegis.")
    parser.add_argument("username", help="Existing local Aegis username that will own the workspace")
    parser.add_argument("--workspace", default="HP-800 maintenance reference", help="Workspace name to create or reuse")
    parser.add_argument("--db", type=Path, default=ROOT / "data" / "workbench.sqlite3")
    args = parser.parse_args()
    db_path = args.db.resolve()
    source_dir = ROOT / "samples" / "maintenance-corpus"
    if not source_dir.is_dir():
        raise SystemExit(f"Corpus folder not found: {source_dir}")

    # Ensure migrations and the pages table exist without contacting any service.
    create_app(db_path, model_engine=None)
    upload_dir = db_path.parent / "uploads"
    preview_dir = db_path.parent / "previews"
    with (vault.database(db_path) if vault.enabled(db_path) else sqlite3.connect(db_path)) as con:
        con.row_factory = sqlite3.Row
        user = con.execute("SELECT id,username FROM users WHERE username=?", (args.username.lower(),)).fetchone()
        if not user:
            raise SystemExit(f"No local account named '{args.username}'. Create the account in the User portal first.")
        workspace = con.execute(
            "SELECT id FROM workspaces WHERE owner_id=? AND name=?", (user["id"], args.workspace)
        ).fetchone()
        if workspace:
            workspace_id = workspace["id"]
        else:
            workspace_id = str(uuid.uuid4())
            con.execute(
                "INSERT INTO workspaces VALUES (?,?,?,?,?)",
                (workspace_id, user["id"], args.workspace, "Reference corpus for HP-800 maintenance and incident testing.", int(time.time())),
            )
        imported = 0
        skipped = 0
        for source_name, stored_name, kind in CORPUS:
            source = source_dir / source_name
            if not source.is_file():
                raise SystemExit(f"Missing corpus file: {source}")
            content = source.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            duplicate = con.execute(
                "SELECT id FROM documents WHERE workspace_id=? AND sha256=?", (workspace_id, digest)
            ).fetchone()
            if duplicate:
                skipped += 1
                continue
            document_id = str(uuid.uuid4())
            destination = upload_dir / document_id
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            if vault.enabled(destination):vault.seal(destination)
            con.execute(
                "INSERT INTO documents VALUES (?,?,?,?,?,?)",
                (document_id, workspace_id, stored_name, len(content), digest, int(time.time())),
            )
            con.execute("INSERT INTO document_metadata(document_id,kind) VALUES (?,?)", (document_id, kind))
            pages = extract(destination, stored_name, preview_dir, document_id)
            for page in pages:
                import json
                con.execute(
                    "INSERT INTO pages VALUES (?,?,?,?)",
                    (document_id, page["page"], page["text"], json.dumps(page)),
                )
            con.execute(
                "INSERT INTO audit_events(user_id,action,created_at) VALUES (?,?,?)",
                (user["id"], "maintenance_corpus_imported", int(time.time())),
            )
            imported += 1
        con.commit()
    print(f"Workspace: {args.workspace} ({workspace_id})")
    print(f"Imported: {imported}; already present: {skipped}")
    print("Files are stored locally and extracted pages are ready for source-grounded questions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
