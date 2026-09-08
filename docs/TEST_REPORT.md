# Feature 1 verification report

Date: 2026-09-08

## Result
10 automated tests passed in 7.97 seconds. Two upstream test-library deprecation warnings remain; no test failures.

## Tested behavior
1. Registration normalizes usernames; Argon2id password hashes and hashed session tokens are stored; browser cookie has HttpOnly and SameSite=Strict.
2. Two users cannot list or directly open each other's workspaces; ownership injection is rejected.
3. Logout revokes the old session; login creates a different session.
4. User/workspace data survives construction of a fresh application instance on the same database.
5. Expired sessions are denied.
6. Wrong CSRF token, foreign origin, and missing request header are rejected; same-origin valid requests succeed.
7. Duplicate username, short password, invalid login and blank workspace are handled.
8. Authentication attempts are rate-limited.
9. Anonymous workspace access and invalid Host are denied; response security headers are present.
10. SQL-like input is stored as data; SQLite integrity and foreign-key checks pass.

## Additional checks
- Python source compilation: passed.
- Browser JavaScript syntax check: passed.
- Live root endpoint: HTTP 200.
- Live health endpoint: status ok, database connected.
- Local browser preview requested through Codex.

## Limits
This is backend/integration and source validation, not an assertion of comprehensive browser, accessibility, penetration, or load testing. GPU inference, OCR, sandbox coding, generated artifacts and network capture are not implemented/tested in Feature 1. A successful health check is not a full-system reliability guarantee.

## Feature 2 verification — 2026-09-08
21 tests passed in 10.06 seconds (including the original 10). New cases cover upload/list/download and persistence, another user's read/write denial, anonymous denial, seven invalid-file cases, limits/CSRF, and duplicate-name preservation. File bytes and checksums are checked. No OCR, antivirus, full binary-format validation or browser automation claim is made.

## Feature 3 verification — 2026-09-08
29 automated tests passed in 15.51 seconds; two upstream deprecation warnings. New tests cover five routing prompts, per-workspace generation access/persistence, CSRF, missing-model refusal and concurrent-request rejection. API integration tests use labelled fixtures. Separately, benchmark_models.py ran both actual models through the local adapter: general 4.041s and coding 10.687s, including startup. Exact responses are in LOCAL_MODEL_BENCHMARK.json. General output missed a two-sentence formatting request; code was inspected but not executed. No full network-isolation or sandbox-execution claim is made.
## Dashboard milestone — 2026-09-08

- 32 automated application tests passed.
- JavaScript syntax validation passed.
- 95 HTML IDs checked: every JavaScript-referenced element exists and no duplicate IDs were found.
- Five workspace views are wired: Overview, Assistant, Materials, Workflows and Offline status.
- Live root request returned HTTP 200 and contained the Materials explorer, quick guide and workflow filters.
- Visual browser interaction testing was not performed in this automated check; the local preview is available at http://127.0.0.1:8765/.

## Hierarchical access milestone — 2026-09-08

- 34 automated application tests passed.
- User, Supervisor and Administrator portal values are validated during credential login.
- A wrong portal is rejected even when the username and password are correct.
- Standard Users remain isolated to their own workspaces.
- Supervisors can list and read team workspaces but mutating another user's workspace is rejected.
- Administrators can access all workspaces and change other account roles.
- An Administrator cannot demote their own active account.
- JavaScript syntax and interface element checks passed.

## Maintenance corpus milestone — 2026-09-08

- Copied the supplied SOP, maintenance log, and incident report into `samples/maintenance-corpus`.
- Imported all three documents into the Administrator’s `HP-800 maintenance reference` workspace; SQLite contains three document records and their extracted page records.
- Added a repeatable local importer at `scripts/import_maintenance_corpus.py`; repeated runs skip matching SHA-256 content.
- Kept the supplied JSON task list and XLSX test matrix under `samples/test-fixtures` because the current Materials allow-list accepts PDF, TXT, CSV, PNG, and JPEG only.
- Added an integration test covering all three corpus uploads, extraction, repeated Asset ID evidence, Work Order extraction, and an incident-threshold grounded question.
- Corpus integration test: 1 passed. Full functional behavior remains limited to the current local model/retrieval and source-grounding implementation; T-06 confidentiality refusal, T-07 packet-capture proof, T-08 image dataset, T-09 SLA, and T-10 drift checks are not claimed complete.

## Assistant incident intake milestone — 2026-09-08

- Added a direct Assistant drop zone/file picker for incident reports and supporting evidence.
- Attached files use the existing local upload and extraction path, then appear as ready chips in Assistant.
- Enter submits the analysis request; Shift+Enter remains available for multi-line prompts.
- Added same-page incident analysis wording and a Deliverables area with review-pack artifact links after completion.
- Existing Materials remains the persistent reference library; Assistant attachments are also stored in the active workspace and therefore remain available after reload.
- JavaScript syntax validation passed and the HTML interface contains 138 unique IDs.

## Analysis presentation milestone — 2026-09-08

- Added safe client-side rendering for headings, paragraphs, lists, inline emphasis/code, citation badges, and Markdown-style evidence tables.
- Applied the renderer to saved Assistant answers and inspection workflow drafts; generated code remains in a code-style block.
- JavaScript syntax validation passed after the rendering change.

## Reference SOP artifact milestone — 2026-09-08

- Created and rendered the original fictional refinery process-safety demonstration SOP.
- Final PDF: 6 A4 pages, with header/footer, revision/classification cover, structured procedures, AI analysis protocol, test scenarios, and public source references.
- Rendered page review passed after correcting cover line breaks and source-reference heading styling.
- Companion TXT source is available for direct ingestion into Aegis Materials.

## Longer PDF reference milestone — 2026-09-08

- Increased supported PDF length from 20 to 100 pages per document.
- Preserved the 20 MB file-size limit and existing OCR/page-rendering safeguards.
- Updated the extraction error message to state the 100-page limit.
