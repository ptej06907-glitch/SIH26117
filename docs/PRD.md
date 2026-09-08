# Aegis — Local Industrial AI Workbench

Problem statement: SIH26117, MRPL. Updated: 2026-09-08.

## Product objective
Deliver an on-premise assistant for confidential knowledge work: automatic selection of local open-weight models, multi-step tool use, document grounding, multimodal inputs, real deliverables, and independently observable offline behavior.

## Current milestone
**User-facing dashboard and core end-to-end prototype complete; 32 automated tests passed.**

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
