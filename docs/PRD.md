# Aegis — Local Industrial AI Workbench

Problem statement: SIH26117, MRPL. Updated: 2026-09-08.

## Product objective
Deliver an on-premise assistant for confidential knowledge work: automatic selection of local open-weight models, multi-step tool use, document grounding, multimodal inputs, real deliverables, and independently observable offline behavior.

## Current milestone
**User-facing dashboard and core end-to-end prototype complete; 37 automated tests passed.**

The prototype now covers the required demonstration path from local sign-in and material upload through OCR, source-grounded assistance, multimodal interpretation, agent workflow execution, editable deliverables, sandboxed code verification and visible connection observations. Packet-level capture, production hardening and engineering validation remain outside the completed prototype claim.

## Features currently present

| Area | Present capability | Demonstration state |
|---|---|---|
| Local identity | Account creation, Argon2id password hashing, expiring local sessions, CSRF checks, sign-out and authentication rate limiting | Complete for workstation prototype |
| Private workspaces | Per-user workspace creation, listing, persistence and ownership checks across materials, answers, runs and artifacts | Complete |
| Dashboard | Overview metrics, recent activity, desktop and mobile navigation, onboarding guide and browser-local compact mode | Complete |
| Material upload | PDF, TXT, CSV, PNG and JPEG upload by picker or drag and drop; 20 MB per file and 200 MB per workspace | Complete |
| Material explorer | Search by name, Ready and Unread filters, download, file-type labels and local-storage status | Complete |
| Document reading | Native text extraction, scanned PDF and image OCR, page images, extracted-text review and warning labels | Complete for supported formats |
| Local models | Local general, coding and vision roles with deterministic automatic selection and no cloud fallback | Complete |
| Source-grounded answers | Local retrieval from read materials, page-linked sources, citation validation and extractive fallback | Complete for prototype retrieval |
| Multimodal understanding | Local interpretation of uploaded images and the first page of a scanned PDF | Complete with small-model review warning |
| Agent workflow | Bounded inspection workflow that reads, retrieves, drafts, checks references, retries and creates outputs | Complete |
| Office deliverables | Editable approval note in DOCX, findings register in XLSX and briefing in PPTX | Complete |
| Verified utilities | Fixed-purpose utility generation, independent test cases, one repair attempt and downloadable Python source | Complete |
| Execution isolation | Python utility execution inside WebAssembly and WASI with time, fuel, memory and output limits and no host-directory or network grants | Complete |
| Workflow history | Live status, progress, event history, verification checks, filters and grouped downloads | Complete |
| Offline visibility | Loopback-only services, Python outbound guard and application plus child-process connection observations | Complete as observable prototype evidence |
| Audit and persistence | SQLite persistence for accounts, workspaces, materials, model answers, runs and local audit events | Complete |

### Current limitations

- Word, Excel and PowerPoint files are generated as outputs but are not accepted as source uploads yet.
- Material and workspace deletion controls are not present.
- Retrieval is lexical and designed for the demonstration collection rather than a large enterprise corpus.
- The database is not application-encrypted, and a Windows administrator can access workstation files.
- Password recovery, administrator provisioning, invitations and enterprise SSO are not included.
- Connection snapshots can miss short-lived traffic; the attempted host packet-capture proof is not yet complete.
- Generated text, OCR, vision output, calculations and engineering interpretations require human review.
- The workstation configuration supports one active generation request at a time.

## User decisions
- Start implementation now; prior planning-only restriction is superseded.
- Approximately 10 hours for the prototype.
- User-based authentication and separate workspaces.
- Deliver project work and documentation to Desktop/GiggaNigga.
- Build feature by feature, show each visible working feature, and verify backend/database behavior.
- Update this PRD after each completed step.

## Hardware evidence
- User screenshots: Windows 11 Home Single Language, Intel Core Ultra 5 125H, 24 GB installed RAM.
- Screenshot available RAM: approximately 6.85 GB; this is a point-in-time reading.
- Windows display-driver registry: Intel(R) Graphics. No dedicated NVIDIA GPU established.
- Python 3.14 and Node 24 available. Ollama and Docker not found on PATH at initiation.
- Plan CPU-first with small quantized models, one active generation task. Actual performance remains unmeasured.

## Official requirements versus proposed scope
Official: entirely local deployment; multiple open-weight models and automatic routing across at least two task types; extensibility; local agent tools; OCR and vision; local knowledge connector; Office/code/calculation deliverables; sandboxed verified coding; visible evidence of no external calls. Public demonstration data is acceptable.

Proposed MVP: English samples, local accounts, individual workspaces, local-folder knowledge import, small text/coding models, narrow scan-to-Word workflow, basic image interpretation and template exports. These are implementation choices, not added official requirements.

## Ten-hour timebox (planning estimates)
| Step | Time budget | Acceptance gate | State |
|---|---:|---|---|
| 1. Accounts, database, private workspaces | 1.25 h | Two-user isolation, persistence, sign-in/out, working preview | Complete |
| 2. Local model runtime and automatic routing | 1.50 h | Two real model routes, benchmark, no cloud fallback | Complete as Feature 3 |
| 3. Upload, extraction, local knowledge search | 1.50 h | Source/page-linked retrieval with access checks | Pending |
| 4. Agent workflow and Word deliverable | 1.75 h | Tool-result-driven iteration and usable cited DOCX | Pending |
| 5. Isolated coding and test verification | 1.25 h | Independent tests; no unrestricted host execution | Pending |
| 6. Multimodal and narrow Office exports | 1.25 h | Real image/scan result, valid XLSX/PPTX | Pending |
| 7. Offline proof, integration, demo package | 1.50 h | Clean cold start, network evidence, runbook | Pending |

Total: 10 h. Model downloads and Windows isolation support are schedule risks. If isolation cannot be established, coding must remain disabled and the requirement reported incomplete.

## Feature 1 requirements
- Create a local account with display name, unique normalized username, and a 12–128 character password.
- Hash passwords with Argon2id; never save plaintext passwords.
- Store only a hash of the browser session token in SQLite; expire sessions after eight hours.
- Use HttpOnly, SameSite=Strict cookies and origin/custom-header/CSRF checks for writes.
- Rate-limit authentication attempts.
- Bind the application to loopback only. HTTP cookies are intentionally not Secure on this localhost prototype; LAN use requires TLS and deployment review.
- Create, list, and open workspaces belonging to the signed-in user only.
- Persist accounts/workspaces across app instances.
- Sign-out revokes the current session.
- No default credentials, external identity, CDNs, fonts, analytics, or model APIs.
- Self-registration is a prototype facility, not enterprise account provisioning.

## Architecture decisions
FastAPI + SQLite + Argon2. The first interface uses locally served HTML/CSS/JavaScript to avoid frontend package/build overhead in a ten-hour prototype. Python remains the integration backend for OCR, inference adapters, and artifacts. React is deferred rather than required.

The Sites skill's hosted authentication/scaffold is unsuitable for the explicitly offline/local-account requirement; the local implementation follows the user's requirement. No Site is registered or published.

## Data model
Users → sessions; users → workspaces; users → local audit events. Foreign keys and workspace-owner index enabled. Sessions carry CSRF values and expiry. Passwords and session secrets are excluded from API responses/logs.

## Limitations and unresolved requirements
- Application-level separation does not protect data from the Windows account owner/administrator.
- Database is not encrypted by the application.
- Password recovery, administrator provisioning, invitations, and enterprise SSO are deferred.
- Exact concurrency meaning of 'multiple models at once' is unresolved.
- OCR/vision accuracy, acceptable latency, and engineering-drawing depth are unmeasured.
- Network capture is pending; local-only implementation is not yet proof of zero outbound activity across the entire host.
- Network downloads are permitted during preparation; final runtime must work with assets preloaded.

## Update history
- Step 0: reviewed supplied hardware and scope; created requested Desktop folder.
- Step 1 implementation: added accounts, sessions, ownership enforcement, workspace UI, and health reporting; 10 automated tests passed; live root and health endpoints returned success.

## Next step
Feature 3 preview is running at http://127.0.0.1:8765. Open a workspace to submit a local AI request. Next: extract text from uploaded documents and use cited source content. See TEST_REPORT.md for exact checks and limits.

## Feature 8 — Dashboard experience (in progress, 2026-09-08)
The user-facing workspace has been reorganized around the main task sequence: Overview, Assistant, Materials, Workflows and Offline status. The overview now reports material, answer, workflow and local-model counts, provides direct next actions, and summarizes recent runs. Navigation works from the desktop sidebar and a compact mobile tab row.

### Feature 8A — Materials explorer (complete)
Materials now supports drag-and-drop and file-picker upload, search by filename, All/Ready/Unread filters, local-storage status, readable file-type badges and clearer extraction state. Image description appears only for PDF and image inputs. Empty and no-match states explain the next action. Upload size and accepted-format limits remain enforced by the existing API.

Next visible slice: improve the Assistant results area with clearer source-grounded mode, response actions and citation presentation.

### Feature 8B — Assistant workspace (complete)
The source-grounded switch is disabled until at least one material has been read, then reports how many materials are available. Saved answers identify General versus Source-grounded mode, can be filtered by mode, retain page-reference buttons, and provide a copy action. Prompt suggestions fill the composer without submitting automatically.

### Feature 8C — Workflow and deliverable center (complete)
Workflow history now presents task type, status, start time, progress, event history, verification checks and grouped deliverable downloads. Users can filter all, running and complete jobs. Starting an inspection pack moves directly to its live workflow view; image interpretation moves to the saved Assistant result.

### Feature 8D — In-product guidance and offline status (complete)
A four-step guide is available from the main navigation. The Offline status view explains application binding, model locality and WebAssembly isolation, and converts live connection observations into a clear status badge while preserving the prototype evidence limitation.

### Feature 8E — Account and display preferences (complete)
The account panel shows the active local identity, provides sign-out, and offers a compact workspace layout. The layout preference is browser-local and does not alter server data.

The dashboard milestone passed 32 automated application tests, JavaScript syntax validation, interface-ID checks and a live HTTP check. It has been synchronized to Desktop/GiggaNigga without replacing the existing data directory.

### Feature 9 — Structured approval note fallback (complete, 2026-09-08)
When the small general model cannot produce reliable source references after one retry, the inspection workflow now builds a deterministic approval note instead of copying raw evidence into a generic paragraph. The fallback contains Subject, Background, Recorded finding, Proposed action, Financial position, Decision requested and Source references sections. Missing cost information remains explicit, every extracted factual statement retains a source ID, and the note does not authorize expenditure, maintenance or an operational conclusion. Automated validation increased to 33 passing tests.

### Feature 10 — Hierarchical role based access (complete, 2026-09-08)
Three login portals are provided for User, Supervisor and Administrator roles. New self-registered accounts always receive User access. Users can access only their own records. Supervisors can list and inspect all team workspaces, documents, answers, workflow history and artifacts, while modification controls and mutating APIs remain unavailable for workspaces they do not own. Administrators can access and modify every workspace and can change local account roles through the dashboard. An Administrator cannot demote their own active account. Portal selection is verified during credential login and does not grant a role by itself. The first Administrator is assigned locally with scripts/set_user_role.py.

### Feature 12 — Maintenance reference corpus and incident test data (complete, 2026-09-08)

The supplied artificial maintenance corpus is now versioned under `samples/maintenance-corpus` and can be imported into an existing local account’s workspace with `scripts/import_maintenance_corpus.py`. The importer creates or reuses `HP-800 maintenance reference`, stores the three operational documents as local Materials, records their metadata and SHA-256 values in SQLite, copies their bytes into the local upload store, and extracts their pages into the existing source-grounding tables. The seeded files are `sop_press_maintenance.txt`, `maintenance_log_hp800.txt`, and `incident_report_template.txt`.

The supplied `agentic_test_tasks.json` and `SIH26117_Test_Case_Matrix.xlsx` are retained as test fixtures under `samples/test-fixtures`; they are not inserted as maintenance evidence because JSON/XLSX are outside the current upload format allow-list. A corpus integration test exercises upload, extraction, Asset ID/Work Order retrieval, and an incident-threshold question through the existing Assistant API. T-01 through T-05 can now be exercised against the three seeded documents. Confidentiality-boundary refusal, packet-capture proof, latency SLA, drift testing, and the multimodal placeholder remain separate test work.

### Feature 13 — Assistant incident intake and same-page deliverables (complete, 2026-09-08)

The Assistant now provides a direct incident intake surface. Users can drop or choose a new incident report plus supporting SOPs, maintenance logs, PDFs, or images from the Assistant page. Each file is uploaded into the active workspace through the existing local Materials API and immediately read/extracted, so the source toggle becomes available without visiting Materials. Pressing Enter in the request box starts the source-grounded analysis; Shift+Enter remains available for a new line. The resulting incident analysis is saved in the same Assistant page with source links. A same-page Deliverables area appears after a completed workflow and provides artifact downloads; the review-pack action can be started from the Assistant page and remains human-review required.

### Feature 14 — Readable analysis rendering (complete, 2026-09-08)

Assistant answers and inspection workflow drafts no longer display Markdown as raw text. A safe local renderer presents headings, paragraphs, bullet/numbered lists, bold/code spans, pipe-delimited evidence tables, and `[S1]`-style citation badges as structured content. Source links remain separate interactive controls so users can open the cited page evidence. Coding artifacts continue to display as plain code text.

### Reference artifact — refinery process-safety SOP demonstration (complete, 2026-09-08)

Created `output/pdf/refinery_process_safety_sop_demo.pdf` and its source text at `samples/maintenance-corpus/refinery_process_safety_sop_demo.txt`. This is an original fictional demonstration reference, not an approved operating procedure. It covers permit-to-work, LOTO/stored energy, high-risk work, abnormal conditions, incident investigation, MOC/restart, AI evidence/citation rules, confidentiality boundaries, escalation and Aegis test scenarios. It cites public OSHA, HSE and CSB reference material and requires controlled site procedures and human approval to govern any real work.

### Feature 15 — Longer PDF reference manuals (complete, 2026-09-08)

PDF extraction now supports up to 100 pages per document instead of 20. The existing 20 MB per-file limit, 120,000-character text-file limit, OCR warnings, page rendering, and workspace storage cap remain in place so longer manuals can be read without removing local resource safeguards.


## Feature 2 — Material uploads (2026-09-08)
Sequence adjustment: following the user's question about missing uploads and request to proceed, add the usable Materials section before model integration. The model milestone remains pending; this is an early portion of the original ingestion milestone.

Implemented: upload one or multiple PDF, TXT, CSV, PNG and JPEG files; list metadata; download original bytes. Files are scoped to workspace ownership on every API operation. Maximum 20 MB/file and 200 MB/workspace. Opaque server-generated filenames prevent path-based overwrites. SHA-256, size and original filename persist in SQLite. Duplicate names remain separate files. Text/CSV must be UTF-8. Binary signatures are checked; this is not antivirus scanning or full format validation. Files are served as attachments and never executed.

UI clearly marks files stored locally and not analyzed. OCR, extraction, Office-format uploads, deletion and AI processing are not part of this feature. The application still has no verified air-gap claim.

Acceptance: 21 tests passed (10 original + 11 upload cases), including original-byte retrieval, restart persistence, two-user denial, anonymous denial, invalid files, path traversal, CSRF, file/workspace limits and duplicate filenames. Existing Desktop data must be preserved during deployment.

## Feature 3 — Local models and automatic routing (complete)
Implementation: a workspace prompt form, local runtime adapter, model registry, deterministic task routing, private persisted request/answer history, and selected-model/duration display. Generated answers are rendered as text. No document context, previous conversation, tool calls or code execution is included yet.

Candidates: Qwen2.5-1.5B-Instruct-GGUF and Qwen2.5-Coder-1.5B-Instruct-GGUF, Q4_K_M, from Qwen's repositories. Runtime: llama.cpp b10809 Windows CPU build, referenced by stable v0.4.0. Source URLs and SHA-256 values are recorded in MODEL_ASSETS.json after download verification.

Runtime constraints: CPU, four generation threads, 2048-token context, 384-token answer limit, 2000-character prompt maximum, one request at a time. Models are started on demand and may both remain resident; actual resident-memory use is not yet measured. Runtime endpoints bind only to loopback and require process-specific credentials. Runtime offline mode is explicit; no cloud fallback, proxy inheritance or runtime downloads are allowed by this adapter.

Routing is a keyword-based MVP heuristic. General writing goes to the general model; programming-language/task indicators go to the coding model. Ambiguous or mixed tasks can route imperfectly. Registry changes require an application restart and a compatible GGUF file. This is not an agent loop yet.

Automated validation: 29 tests passed in 15.51 seconds, including original account/upload tests, five routing cases, generation ownership and persistence, CSRF, error handling, missing-model refusal and busy-request rejection. Generation API tests use an explicitly labelled fake engine; actual model quality/latency must be checked separately before completion.

### Feature 3 real validation
Both model assets and runtime were verified against published SHA-256 values. On this laptop, direct local-adapter tests including cold startup took 4.041 seconds for a short note and 10.687 seconds for Python code. Both routes selected the intended distinct model and returned nonempty output. These are two sample timings, not performance guarantees. The general model missed the requested two-sentence formatting; its response contained one sentence. Coding output contained the expected conversion formula on inspection, but was not executed or functionally verified. Full outputs are retained in LOCAL_MODEL_BENCHMARK.json. Document grounding, agent iteration, safe execution and network-monitor proof remain pending.

### Feature 16 — Separate reference library and incident report register (complete, 2026-09-08)
Materials is now divided into two visible collections. Reference materials contain approved SOPs, manuals and maintenance history; only Administrators can upload or remove them, while other roles can read and use them as evidence. Incident reports have their own upload area and register. Every report receives a stable `IR-XXXXXXXX` identifier, a Ready/Unread status and a progress bar reflecting extraction readiness. Report-only actions such as Describe image and Create review pack are not shown for reference materials. The API enforces the Administrator-only reference upload and deletion rule, and existing maintenance-corpus records have been classified accordingly.

### Feature 17 — Shared administrator reference grounding and complete review fallback (complete, 2026-09-08)
Administrator-owned reference documents are now visible as shared read-only references in User and Supervisor workspaces and are included in Assistant retrieval across those workspaces. Users and Supervisors may read, cite and download shared references, but cannot replace or remove them. If the local model cannot produce valid citations, the deterministic review fallback now includes recorded findings, source observations, explicit reviewer next steps, financial/authorization gaps and source references instead of returning only a short fragment.

### Feature 18 — Sentence-safe evidence output (complete, 2026-09-08)
Evidence retrieval now forms excerpts at sentence boundaries instead of cutting source text at arbitrary character offsets. The question-answer fallback presents a structured evidence brief with source-linked statements, verification steps and explicit limits. This prevents outputs such as fragments beginning mid-word or mid-sentence when a model response fails citation validation.

### Feature 19 — Supervisor incident review and approval gate (complete, 2026-09-08)
Completed inspection workflows now create a persisted review request. Users see a coloured status in the workspace review panel: Supervisor yet to analyse, Supervisor yet to approve, Approved by supervisor, or Disapproved - needs revision. Supervisors see a review queue containing the incident filename, workspace, requester, AI summary and recent AI processing steps. A Supervisor can mark the AI analysis as analysed, which moves the request to approval, then Approve AI processing or Disapprove / return with a note. The decision, reviewer identity, timestamps and note are stored in SQLite and are visible to the submitting User. Administrator accounts can perform the same review actions. The API rejects invalid state transitions and prevents ordinary Users from changing review decisions.

### Feature 20 — Automatic queueing after Assistant incident analysis (complete, 2026-09-08)
When a User or Supervisor submits a source-grounded Assistant analysis tied to an incident report, the completed analysis now automatically creates a Supervisor review request. The request is inserted into the review queue without requiring a separate review-pack click. The Assistant status confirms that the analysis was sent to the Supervisor queue, while the workspace review panel polls for updated analysis, approval or disapproval state. Inspection review workflows continue to create requests as well, so both analysis entry paths share the same human approval gate.

---

# Judge-ready presentation dossier

This section is the authoritative presentation reference for the implemented SIH26117 prototype. It describes what can be demonstrated today, how information moves through the system, what technology is used, and which claims remain prototype limitations.

## 1. One-minute product explanation

Aegis is a self-hosted, local-first AI workbench for confidential industrial knowledge work. It is designed for refinery, PSU, defence-linked manufacturing and government environments where inspection reports, SOPs, drawings, maintenance logs and internal correspondence cannot be sent to public cloud assistants.

The user signs in locally, opens a project workspace, adds an incident report, and optionally asks the Assistant to use approved reference materials. Aegis reads text and scans on the workstation, retrieves page-linked evidence, routes the request to a local model, validates citations, and presents a reviewable answer. For an inspection task it can run a bounded workflow that creates a Word approval note, Excel evidence register and PowerPoint briefing. For a coding task it generates a small utility and verifies fixed test cases inside a WebAssembly/WASI sandbox.

The sovereign-processing claim is demonstrated by the architecture and by a visible Offline status page: the application binds to loopback, model runtimes are local files, Python outbound proxy inheritance is disabled, and application/child-process connection observations are shown in the UI. The prototype does not claim a full packet-capture certificate or protection from a Windows administrator who already controls the host.

## 2. Problem, users and value

Industrial teams repeatedly perform confidential work that is slow to complete manually: interpret a scanned inspection report, compare it with SOP limits and maintenance history, prepare an approval note, review calculations, and produce a board-ready briefing. Public AI tools create a confidentiality risk because the underlying P&IDs, financial information, vendor negotiations, unreleased designs and internal correspondence may leave the site.

The primary users are:

| Role | Main responsibility | Product value |
|---|---|---|
| User / Engineer | Submit incident reports, ask questions, inspect evidence and download drafts | Faster, source-linked first draft while retaining human control |
| Supervisor | Review team workspaces and evidence without changing another user’s records | Read-only oversight and review visibility |
| Administrator | Govern accounts and the approved reference library | Controls shared SOPs/manuals and full local access |
| Reviewer / Safety lead | Human decision-maker outside the software role model | Confirms evidence, authorization, costs, safety controls and final action |

Important terminology: **workspace** is a project container; **reference material** is Administrator-managed approved background knowledge; **incident report** is a case record submitted for analysis; **source/evidence** is a page-linked extracted passage; **Assistant** is the question-and-answer surface; **workflow** is the bounded multi-step inspection or coding run; **artifact/deliverable** is a generated DOCX, XLSX, PPTX or Python file; **Task Passport** is a future/extended provenance concept and is not a separate signed UI object in the current prototype.

## 3. Technology stack

| Layer | Implemented technology | Reason in the prototype |
|---|---|---|
| Operating environment | Windows 11, loopback workstation service | Matches the supplied laptop and on-premise demonstration constraint |
| Backend API | Python 3.14, FastAPI 0.141, Uvicorn | Small local API with typed request validation and static-file serving |
| Frontend | Local HTML, CSS and vanilla JavaScript | No package build, CDN, analytics or external font dependency |
| Storage | SQLite with WAL mode and foreign keys | Persistent local accounts, workspaces, documents, pages, answers, runs, artifacts and audit events |
| Authentication | Argon2id password hashing, HttpOnly SameSite cookies, CSRF token and request-boundary checks | Local account security appropriate for the prototype |
| PDF/document reading | PyMuPDF, Pillow, RapidOCR ONNX Runtime | Native PDF text, rendered page images, scanned PDF OCR and image OCR |
| Local inference | llama.cpp Windows CPU runtime, local GGUF files | No cloud model API or runtime download during use |
| Model selection | Deterministic capability router | Sends general requests to general model, code requests to coding model and image requests to vision model |
| Office generation | python-docx, openpyxl/XlsxWriter, python-pptx | Produces editable approval note, evidence register and briefing |
| Code isolation | wasmtime WebAssembly/WASI runner | Fixed utility generation and verification without host folders, environment variables or network grants |
| Network observation | psutil-based local monitor and observation JSON | Visible application/child-process connection status in Offline view |
| Testing | pytest, Python compilation, JavaScript syntax check, live HTTP health check | Regression coverage for core API and role behavior |

The application deliberately does not require React, Docker, Ollama, a cloud database, a cloud vector service, an external identity provider or a hosted site. The current UI is served by the FastAPI process from `frontend/`.

## 4. Models and runtime

The model registry currently defines three local capabilities:

| Capability | Model | File convention | Used for |
|---|---|---|---|
| General | Qwen2.5 1.5B Instruct, Q4_K_M GGUF | `models/general.gguf` | Explanations, source-grounded answers and review-note drafts |
| Coding | Qwen2.5 Coder 1.5B Instruct, Q4_K_M GGUF | `models/coding.gguf` | Small Python utility generation |
| Vision | SmolVLM 500M plus projector | `models/vision.gguf`, `models/vision-projector.gguf` | Image and scanned-page description |

The router is keyword/capability based and intentionally deterministic for the MVP. It is extensible through `models/registry.json`, where a future compatible local model can be added without changing the dashboard contract. Runtime constraints are 2,000 characters per request, a 2,048-token context, a 384-token answer limit, four CPU generation threads and one active application generation at a time. Initial requests include model startup time. Recorded sample cold-start timings were approximately 4.041 seconds for the general route and 10.687 seconds for the coding route on the supplied laptop; these are demonstrations, not SLAs.

The local adapter starts the selected runtime on demand, binds it to `127.0.0.1`, uses a process-specific key, disables the runtime web UI and MCP proxy, enables runtime offline mode, and does not provide a cloud fallback. Model quality, OCR quality and engineering interpretation still require human review.

## 5. End-to-end data flow

### 5.1 Reference material flow

1. Administrator signs in through the Administrator portal.
2. Administrator opens a workspace and uploads an approved SOP, manual, maintenance log, PDF, text, CSV or image through Materials → Reference materials.
3. FastAPI validates the filename, extension, content signature, size and workspace quota. The raw bytes are written to the local upload store; SHA-256, original filename, size, workspace and `kind=reference` are stored in SQLite.
4. The document is read on demand. PyMuPDF extracts native PDF text; pages with little text are rendered and passed through local OCR. Text files are read as UTF-8; images use local OCR.
5. Extracted page text, page number, method, warnings and preview metadata are stored in SQLite’s `pages` table. No page is sent to an external service.
6. The reference is listed as a shared read-only library item for User and Supervisor workspaces. Administrator-owned references participate in retrieval across those workspaces.

### 5.2 Incident analysis flow

1. User or Supervisor signs in through the matching role portal and opens an accessible workspace.
2. The user uploads an incident report from Materials → Incident reports or directly in Assistant → Incident intake. The report receives an `IR-XXXXXXXX` identifier and Ready/Unread extraction status.
3. The user selects source-grounded mode and submits a question with Enter. Shift+Enter inserts a new line.
4. The API loads extracted pages from the active workspace plus shared Administrator references. Retrieval tokenizes the request and ranks sentence-safe excerpts by lexical overlap.
5. The router selects the general model for the text task. The model receives the current prompt and selected source excerpts with `[S1]`-style IDs; it does not receive unrelated workspaces or a remote context.
6. The response is checked to confirm that cited IDs belong to the supplied evidence. If valid, the answer is saved with model metadata, sources and citation status.
7. If citations fail, Aegis creates a deterministic evidence brief containing source-linked statements, verification steps, limits and source references. It does not silently invent a conclusion.
8. The saved answer appears in Assistant with formatted headings, citation badges, source buttons, copy action and source-grounded/general status.

### 5.3 Inspection workflow flow

1. User selects an incident report and starts the review workflow.
2. The agent records a plan event, reads the selected report and retains page references.
3. It retrieves supporting evidence from the active workspace and shared Administrator references. If the initial query is sparse, it retries using text from the selected report.
4. The general model drafts a review note. A citation check runs; one revision is attempted if needed.
5. If the revised draft remains unreliable, the deterministic approval-note fallback creates a structured human-review draft.
6. The workflow records events and progress, then creates `approval-note.docx`, `findings-register.xlsx` and `inspection-briefing.pptx`.
7. The workflow card shows status, progress, events, evidence and download links. The Assistant deliverables section also exposes completed outputs.

### 5.4 Coding verification flow

1. User opens Workflows and selects a fixed utility: Celsius-to-Fahrenheit or numeric-reading sum.
2. The coding model receives a constrained function-generation prompt.
3. The generated source is sent to the local WebAssembly/WASI runner, not unrestricted host Python.
4. Three independent inputs are checked against expected values. A single repair attempt is available.
5. The result shows PASS/FAIL checks and provides a downloadable Python artifact. The sandbox has wall-time, fuel, memory and output constraints and no host-folder or network grants.

## 6. Product screens and user-visible behavior

| Screen | Purpose | Main visible elements |
|---|---|---|
| Role login | Authenticate into the correct portal | User, Supervisor and Administrator portal switch; sign in/create account; validation and rate-limit errors |
| Workspace home | Choose a project | Workspace cards, ownership, role banner, create/open controls and recent activity |
| Overview | Orient the user | Counts for materials, answers, workflows and models; next actions; recent runs; incident intake entry point |
| Assistant | Ask questions and analyse incidents | Prompt composer, source toggle, incident file drop zone, suggestions, analysis cards, citations, source links and deliverables |
| Materials | Manage local evidence | Separate Reference materials and Incident reports sections, upload/drop zones, search, filters, report IDs, readiness/progress, download/read/source actions |
| Workflows | Monitor agent and coding jobs | Inspection review-pack launcher, coding utility launcher, running/complete filters, event timeline, checks and artifact downloads |
| Offline status | Explain sovereignty evidence | Loopback binding, local model status, WebAssembly isolation, connection observations, warning when observation is incomplete |
| Account dialog | Manage local session/display | Identity, role, compact layout, sign-out |
| Administrator users dialog | Manage roles | Account list and role selector; administrator self-demotion is disabled |
| Source dialog | Inspect provenance | Per-page method, OCR warnings, page image where available and extracted text |

## 7. Role and permission matrix

| Action | User | Supervisor | Administrator |
|---|---:|---:|---:|
| Create own workspace | Yes | Yes | Yes |
| View own workspace | Yes | Yes | Yes |
| View another user’s workspace | No | Yes, read-only | Yes |
| Upload incident report to owned workspace | Yes | Yes | Yes |
| Upload reference material | No | No | Yes |
| Read shared Administrator reference | Yes | Yes | Yes |
| Remove reference material | No | No | Yes |
| Modify another user’s workspace | No | No | Yes |
| Ask Assistant / retrieve evidence | Own workspace + shared references | Accessible workspace + shared references | Any accessible workspace + shared references |
| Start workflow in another user’s workspace | No | No | Yes |
| Change account roles | No | No | Yes |
| Demote own Administrator account | Not applicable | Not applicable | No |

Portal selection is an access check, not a privilege grant. A correct username/password combination is rejected if it is used with the wrong portal.

## 8. Data model and persistence

SQLite tables currently include `users`, `sessions`, `workspaces`, `documents`, `document_metadata`, `pages`, `generations`, `runs`, `artifacts` and `audit_events`. Documents retain original filename, size, SHA-256, workspace, creation time and reference/report classification. Pages retain extracted text, page number, extraction method, warnings and serialized page details. Generated answers retain prompt, result JSON, timestamp and source metadata. Runs retain kind, status, event history and result JSON. Artifacts retain local path, filename, workspace and run relationship.

Raw files live in the local `data/uploads` directory; previews live in `data/previews`; generated files live under `data/artifacts`; model logs live under `data/model-logs`; network observations live in `data/network-observation.json`. The database is persistent across application restarts. The prototype does not encrypt the SQLite file at the application layer.

## 9. Security and sovereignty story

- Service host is restricted to `127.0.0.1`/`localhost` by Uvicorn and TrustedHostMiddleware.
- The browser requires a local request header and same-origin checks for writes.
- Mutating requests require a per-session CSRF token.
- Passwords use Argon2id; session cookies are HttpOnly and SameSite=Strict; sessions expire after eight hours.
- Authentication attempts are rate-limited.
- Content Security Policy disallows external scripts, frames, connections and form destinations.
- Uploads validate supported types, signatures, UTF-8 text, filename safety and quotas; uploaded bytes are never executed.
- Source retrieval applies workspace and role checks, with shared references limited to Administrator-owned `reference` documents.
- Coding execution uses WebAssembly/WASI limits and receives no host directory, environment-variable or network grant.
- Model processes are local and configured without cloud fallback, proxy inheritance or runtime downloads.
- Offline status surfaces observed external connections and observation limitations.

The honest boundary for judges: this is a local prototype, not a certified air gap. A Windows administrator can read the files, packet-level capture is not yet a complete certificate, and generated content/OCR/vision must be reviewed by an authorized human.

## 10. Recommended live judging demonstration

1. Open `http://127.0.0.1:8765/login/administrator` and sign in as Administrator.
2. Open the maintenance workspace and show Reference materials containing the SOP and maintenance log. Explain that only Administrator can change this library.
3. Open a User or Supervisor portal in another browser tab, open a workspace and show the same Administrator reference files available for reading and grounding.
4. In Assistant, upload one generated incident PDF, such as the hydraulic-leak or confined-space demo report.
5. Ask: “Summarize the incident, identify the evidence-backed hazards, state which SOP controls apply, and list the next verification steps. Cite every claim.”
6. Show the formatted answer, citation badges and page-linked source dialog. If the model cannot validate citations, show the structured evidence brief and explain that it refuses to invent a conclusion.
7. Start the inspection review workflow. Show Planner/read, retrieval, drafting, reference-check and artifact events.
8. Download the generated Word approval note, Excel evidence register and PowerPoint briefing. Point out the human-review disclaimer and source evidence appendix.
9. Run the coding utility from Workflows and show independent PASS checks from the sandbox.
10. Open Offline status and show loopback binding, local model state, WebAssembly isolation and connection observations.

## 11. Judge claims and evidence

| Claim | Demonstrable evidence | Qualification |
|---|---|---|
| Local accounts and hierarchy | Three role portals, role checks, read-only Supervisor behavior and Administrator role management | Prototype local identity, not enterprise SSO |
| Shared controlled knowledge | Administrator reference library appears in User/Supervisor retrieval and source links | Shared through local SQLite/file store |
| Multimodal handling | OCR text, page preview, image description and scanned-PDF path | Vision result is preliminary and requires review |
| Agentic behavior | Workflow events, retrieval, retry, citation check and artifact creation | Bounded workflow, not an unrestricted autonomous agent |
| Useful deliverables | DOCX, XLSX, PPTX and verified Python output | Drafts require human approval |
| Sovereign/local runtime | Loopback, local model files, no cloud fallback, Offline status | Full host packet-capture certification is not claimed |
| Extensibility | Registry-based capability entries and separated runtime adapter | Routing is deterministic MVP heuristics |

## 12. Validation snapshot

The current regression suite passes **37 tests**. It covers authentication, session expiry, Argon2id storage, CSRF and origin checks, workspace isolation, upload validation and limits, persistence, role hierarchy, maintenance corpus extraction, model routing behavior, workflow access and related API behavior. JavaScript syntax validation, Python compilation and a live health request also pass. The server currently returns HTTP 200 from `/api/health`.

The supplied demo data includes the HP-800 maintenance corpus, a fictional process-safety SOP PDF/TXT reference, three fictional incident-report PDFs, the incident template, the test-task JSON and the SIH test matrix. The JSON and XLSX remain test fixtures because the current operational uploader accepts PDF, TXT, CSV, PNG and JPEG.

## 13. Known gaps before production

Production deployment would require encrypted storage, enterprise identity/SSO, administrator provisioning and recovery, formal retention/deletion policy, malware scanning, immutable audit export, stronger semantic/vector retrieval, larger and better-validated models, GPU performance testing, engineering-domain evaluation, signed provenance/Task Passport implementation, full packet capture, accessibility/browser automation, concurrency testing, and formal safety/security review. These are deliberately separated from the hackathon prototype claim.

## 14. Repository map for handoff

| Path | Purpose |
|---|---|
| `frontend/index.html` | All local screens, dialogs and semantic UI structure |
| `frontend/assets/app.js` | Navigation, uploads, retrieval requests, rendering, role-aware controls and workflow polling |
| `frontend/assets/style.css` | Existing visual language and responsive layout |
| `backend/app.py` | FastAPI application, authentication, workspace/document APIs, role enforcement and database schema |
| `backend/workflows.py` | Extraction, questions, retrieval orchestration, inspection workflow, artifacts and coding workflow |
| `backend/documents.py` | PDF/text/image extraction, OCR and sentence-safe retrieval |
| `backend/local_models.py` | Local model registry, routing and llama.cpp adapter |
| `backend/exports.py` | DOCX/XLSX/PPTX generation |
| `backend/sandbox.py`, `backend/wasm_runner.py` | WebAssembly/WASI utility execution |
| `models/registry.json` | Local model capability mapping |
| `scripts/import_maintenance_corpus.py` | Local seeded maintenance-data importer |
| `scripts/generate_demo_incident_reports.py` | Fictional incident-PDF generator |
| `data/workbench.sqlite3` | Persistent local runtime database |
| `tests/` | Automated regression suite |

## 15. Presentation closing statement

Aegis demonstrates that a useful industrial AI assistant can be assembled around local open-weight models without sending confidential material to a public assistant. Its strongest prototype proof is the complete local path: role-controlled sign-in, shared Administrator references, incident upload, OCR, page-linked retrieval, bounded agent workflow, human-review deliverables, isolated code verification and visible local-runtime evidence. The remaining gaps are stated explicitly so the demonstration is credible rather than overstated.
