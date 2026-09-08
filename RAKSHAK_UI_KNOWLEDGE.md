# Existing Application UI Knowledge Specification

## Scope and source of truth

This document describes the application that currently exists in this project. It is a functional and visual specification for rebuilding the user experience while preserving the existing information architecture and behavior.

The visible product name is **Aegis · Local workbench**. “Rakshak AI” is the requested name of this specification, not a label currently shown by the application. The UI identifies the context as **MRPL · SMART AUTOMATION**, **SIH 26117**, and **ON-PREMISE AI**. The application is a local Windows prototype served from `http://127.0.0.1:8765`; it is not a hosted web product.

This document is based on the local HTML, CSS, JavaScript, backend behavior, sample files, and the running prototype. It records implemented behavior and explicitly marks requested concepts that are not present.

## 1. Product overview

Aegis is a local, on-premise AI workbench for confidential industrial knowledge work. It is intended for people who need to upload inspection reports, notes, drawings, photographs, structured readings, or internal text; extract and review their contents locally; ask a local language model questions; and create editable review deliverables. The application presents local processing as the central trust boundary: accounts, workspaces, source files, model inference, OCR, generated answers, and workflow artifacts remain on the computer.

The primary user task is:

1. Sign in through a local account portal.
2. Create or open a project workspace.
3. Add material and read it locally.
4. Ask a general or source-grounded question.
5. Inspect saved answers and source page references.
6. Run an inspection review-pack workflow or a verified utility workflow.
7. Review and download editable outputs.
8. Inspect the Offline status page for local-runtime observations.

Important product terms:

| Term | Meaning in the existing UI |
|---|---|
| Workspace | A project container for material, saved answers, workflow runs, and deliverables. |
| Material | An uploaded PDF, TXT, CSV, PNG, JPG, or JPEG file. |
| Read locally | Extract selectable text, render PDF pages, or run local OCR and retain page data. |
| Source-grounded answer | An answer produced with retrieved excerpts and source IDs such as `[S1]`. |
| General answer | A prompt answered by the local general model without workspace evidence. |
| Review pack | An inspection workflow that creates Word, Excel, and PowerPoint files. |
| Verified utility | A fixed-purpose coding workflow that generates a small function and tests it in WebAssembly. |
| Workflow run | A persisted task with status, progress events, result data, and downloadable artifacts. |
| Local model | A model loaded from the project’s local model files; no cloud fallback is presented. |
| Offline status | The UI’s view of loopback binding, local model files, WebAssembly isolation, and connection observations. |
| Supervisor review access | Read-only access to team workspaces owned by other users. |

The product is a prototype. Generated material is explicitly marked for human review. It does not claim that an output authorizes expenditure, maintenance, or an operational safety conclusion.

## 2. Application navigation

### Global navigation tree

```text
Aegis local workbench
├── Authentication
│   ├── User portal (/login/user)
│   ├── Supervisor portal (/login/supervisor)
│   └── Administrator portal (/login/administrator)
└── Signed-in shell
    ├── My workspaces / Team workspaces
    │   ├── Workspace cards
    │   ├── New workspace dialog
    │   └── Empty workspaces state
    ├── Current workspace
    │   ├── Overview
    │   ├── Assistant
    │   ├── Materials
    │   ├── Workflows
    │   └── Offline status
    ├── Manage users (Administrator only)
    ├── How to use Aegis dialog
    └── Account & display dialog
```

### Authentication navigation

The root route and all three login routes serve the same application file. The path determines the selected portal. A portal switcher has three options: **User / My work**, **Supervisor / Team review**, and **Administrator / Full control**. The selected portal changes the title, subtitle, color accent, and login payload. The server verifies that the account’s stored role matches the selected portal.

The User portal exposes a **Create account** tab. Supervisor and Administrator portals do not expose registration. New registrations always receive the User role.

### Signed-in shell

The desktop shell has a fixed dark left sidebar and a sticky white top bar. The sidebar contains the Aegis mark, a Local workbench status block, the main navigation, help links, and the signed-in profile. The top bar shows the current location, a green local-only indicator, and the current number/status of local models.

The sidebar’s **My workspaces** button returns to the workspace list. When a workspace is open, the sidebar reveals five current-workspace tabs: **Overview**, **Assistant**, **Materials**, **Workflows**, and **Offline status**. **Manage users** is hidden unless the signed-in role is Administrator. **How to use Aegis** and **Account & display** are always available after sign-in. The bottom profile includes initials, display name, username, role, and a sign-out icon.

## 3. Screens and pages

### 3.1 Boot screen

Purpose: brief application initialization state.

Layout and content: a centered Aegis “A” mark and the text **Opening Aegis…** on a white background. It has `role="status"` and is hidden after the authentication or workspace shell is initialized.

State: only a loading/opening state is implemented. There is no boot error page.

### 3.2 Authentication screen

Purpose: local sign-in or local User account creation.

Layout:

- Two-column desktop layout. The left brand panel is dark navy; the right authentication panel is white.
- Brand panel contains the Aegis logo, **ON-PREMISE AI**, the eyebrow **SOVEREIGN INDUSTRIAL WORKBENCH**, headline **Confidential work stays on this machine.**, supporting text, three trust points, and footer text **Local service ready / SIH 26117**.
- Authentication panel top line shows **MRPL · SMART AUTOMATION** and a **PROTOTYPE** badge.
- Auth card contains the current portal title/subtitle, portal switcher, Sign in/Create account switch, form, local-account note, and footer.

User actions and results:

- Select a portal: changes the route and portal-specific copy. It does not change account permissions by itself.
- Select **Sign in**: submits username, password, and portal. Success opens the workspace shell. Wrong credentials show **Incorrect username or password.** Wrong portal shows a role-specific error.
- Select **Create account** in the User portal: reveals a name field and password guidance. Success signs the new User in and opens the workspace shell.
- Select **Show**: toggles password visibility.
- Select the Aegis home link: returns to the root route.

Implemented validation and errors:

- Username is required, 3–32 characters, normalized to lowercase, and limited to letters, digits, underscore, dot, and hyphen.
- Password is required and 12–128 characters.
- Display name is required for registration and limited to 60 characters.
- Duplicate usernames, invalid credentials, malformed input, and rate limiting appear in the inline red alert area.

States: default sign-in; registration; disabled submit while submitting; inline error; successful transition to the signed-in shell. There is no password recovery or external identity-provider flow.

### 3.3 Workspace list: User

Purpose: show the signed-in User’s private project workspaces and create a new one.

Content: heading **My workspaces**, supporting copy **Separate materials, conversations and deliverables by project.**, a **＋ New workspace** button, a workspace count, workspace cards, and an empty state when none exist.

Each card is a clickable button with a folder-like icon, workspace name, description, creation date, and **Private** metadata. Selecting it opens the workspace detail screen.

Empty state: **Create your first workspace**, explanatory text, and a **Create workspace** button. Both creation entry points open the same dialog.

### 3.4 Workspace list: Supervisor and Administrator

The heading changes to **Team workspaces** and the eyebrow to **HIERARCHICAL ACCESS**. Supervisors see all team workspaces for review; Administrators see all workspaces and can manage local account roles. Cards include the owner’s display name instead of “Private.” The Supervisor subtitle explains that other users’ records are read-only.

### 3.5 New/edit workspace dialog

The same dialog is used for creation and, in the current management implementation, editing workspace details.

Creation title: **New workspace**; eyebrow **NEW PROJECT SPACE**; copy explains that a project’s materials, conversations, and deliverables stay together. Inputs are **Workspace name** and optional **Description**. Buttons are **Cancel** and **Create workspace**.

Edit title: **Edit workspace details**; eyebrow **WORKSPACE SETTINGS**; copy explains that the name and description shown to people with access can be updated. The same inputs are prefilled and the submit button says **Save changes**.

Success closes the dialog and refreshes the relevant workspace view. Validation errors appear in the dialog’s red alert area. The dialog is a native HTML dialog; Escape closes it through browser dialog behavior.

### 3.6 Workspace Overview

Purpose: provide the first project-level surface and direct the user through the intended sequence.

Header: back link **← All workspaces**, eyebrow **PRIVATE WORKSPACE**, workspace name, description, and, for writable users, **Edit details** and **Delete workspace** controls. A Supervisor viewing another owner’s workspace sees an access banner saying changes are disabled, and the management controls are hidden.

Main content:

- Dark **WORKSPACE OVERVIEW** welcome card with **Continue your confidential work.**, explanation, **Add materials**, and **Ask Aegis** buttons.
- Four metric cards: Materials, Saved answers, Workflow runs, and Local models. The material card reports total and ready-to-question counts; workflow card reports total and completed counts.
- **GET STARTED / Recommended sequence** panel with four numbered steps: Add project material, Read it locally, Ask with sources, Create deliverables. Each has an Open button that switches to the relevant tab.
- **RECENT ACTIVITY / Latest workspace results** panel. It shows recent runs/answers when available, or **No activity yet. Add your first material to begin.**

States: empty metrics, populated metrics, recent activity empty/populated, writable controls, and Supervisor read-only access.

### 3.7 Assistant

Purpose: ask Aegis for general local answers or source-grounded answers.

Layout and content:

- Header eyebrow **LOCAL ASSISTANT**, title **Ask Aegis**, explanatory sentence, and model status badge.
- Three prompt suggestions: **Summarize the key findings**, **Draft an approval note**, and **Explain this calculation**. Clicking one fills the prompt; it does not submit automatically.
- Prompt form with label **Your request**, a five-row textarea, a source toggle labeled **Use workspace sources**, and **Generate answer**.
- Source toggle is disabled until at least one file has been read. Its helper text reports readiness or Supervisor read-only mode.
- Inline status and inline error areas.
- Saved answers area with count, newest-first text, filters **All**, **With sources**, and **General**.

Answer behavior: a general prompt is routed to the local general/coding model heuristic. With workspace sources enabled, local extracted records are retrieved and passed to the general model with source IDs. Each saved answer shows the prompt, model/capability metadata, answer text, source-reference buttons when available, and a copy action. Clicking a source reference opens the source document dialog at the relevant page.

States: no answers, no answers matching a filter, submitting/loading status, model unavailable, busy model, generated answer, source-grounded answer, and error. Read-only Supervisor view disables the prompt, toggle, and Generate button.

### 3.8 Materials

Purpose: upload, inspect, search, filter, and locally read project material.

Layout:

- Header eyebrow **LOCAL KNOWLEDGE**, title **Materials**, copy describing reports, notes, drawings, photos, and structured readings.
- **Read all unread files** button.
- Large drop zone: **Drop files here or choose from this computer**, accepted types and 20 MB limit, **Choose files** action.
- Upload status and error areas.
- **Workspace files** summary and **Stored locally** privacy chip.
- Search input placeholder **Search materials**.
- Filters **All**, **Ready**, and **Unread**.
- Document rows with type badge, filename, file size, readiness label, Download link, Read locally/Read again, View sources, optional Describe image for PDF/image types, Create review pack, and Remove for writable users.

Accepted files: PDF, TXT, CSV, PNG, JPG, JPEG. Each file is limited to 20 MB and each workspace to 200 MB. Text and CSV must be UTF-8. Uploaded files are stored using opaque server IDs while the original filename is displayed.

Actions and results:

- Drop or choose files: uploads one or more files and refreshes the list. The status reports `n of n files uploaded`; individual failures appear in the error area.
- Read locally: extracts text from TXT/CSV, extracts PDF text and renders pages, OCRs image/scanned content, and changes the row to Ready.
- Read all unread files: processes every unread row sequentially and reports the number read.
- View sources: opens the Source document dialog with extracted page text and page image links/previews.
- Describe image: sends the rendered image to the local vision model and saves the result in Assistant.
- Download: returns the original uploaded bytes as an attachment.
- Create review pack: starts the inspection workflow and moves the user to the live workflow view.
- Remove: opens a confirmation dialog and deletes the material, extracted pages, upload file, and previews after confirmation.

Empty state: **No materials yet** with a prompt to choose files. Search/filter no-match state: **No matching materials**. Supervisor viewing another owner sees files and source actions but no mutation controls; unavailable unread actions are disabled.

### 3.9 Source document dialog

Purpose: let the user verify extracted evidence against the source.

The native dialog is titled **Source document** with eyebrow **EXTRACTED EVIDENCE**. It displays each extracted page’s page number, text, extraction method/warnings where available, and a rendered page image when present. The dialog has a close button and scrollable content.

OCR warnings state that measurements, identifiers, and handwriting may be misread and should be checked against the original. The UI does not represent OCR as authoritative.

### 3.10 Workflows and deliverables

Purpose: launch and monitor the two implemented workflow families and download their outputs.

Header: eyebrow **TASK AUTOMATION**, title **Workflows & deliverables**, and copy instructing the user to follow steps, review evidence, and download editable outputs.

Launchers:

- **Inspection review pack**: explains that a material’s **Create review pack** action starts a Word note, Excel register, and PowerPoint briefing. **Choose material** switches to Materials.
- **Verified utility**: a select with **Celsius to Fahrenheit** and **Sum numeric readings**, plus **Generate & verify**.

History area: **Workflow history** count, automatic-update copy, filters **All**, **Running**, and **Complete**, workflow cards, and empty/no-match states.

Workflow cards show kind, status badge, created time, a progress bar, chronological event messages, verification information, and artifact download buttons. Running cards update through polling. Completed inspection runs show draft text, evidence/source references, human-review status, and Word/Excel/PowerPoint artifacts. Completed coding runs show generated function code, independent checks, verification result, and `utility.py` download.

Workflow states actually represented: running, complete, failed, interrupted, empty, and filtered no-match. There is no approval button or human approval gate in the current UI; outputs are marked as requiring human review.

### 3.11 Offline status

Purpose: present the prototype’s local-processing evidence boundary.

Layout:

- Dark **SOVEREIGN RUNTIME / Offline status** hero with **Local mode / Loopback service** seal.
- Three security cards:
  - **Application binding — 127.0.0.1 only**.
  - **Model runtime — Local files**.
  - **Code isolation — WebAssembly**.
- **LIVE OBSERVATION / Connection monitor** panel with Watching or attention badge, summary, detail, and evidence boundary note.

The note explains that the monitor samples the Python application and child processes, short connections may be missed, and packet-capture evidence has not been collected. This page is an observation view, not a cryptographic sovereignty certificate.

### 3.12 Manage users dialog

Administrator-only entry in the sidebar. The dialog is titled **Users and roles** and explains that local account portals can be changed while the active Administrator role is protected. It lists display name, username, workspace count, and a role select with User, Supervisor, and Administrator options. An Administrator cannot demote their own active account. Success shows a toast; failure appears in the dialog alert.

### 3.13 How to use Aegis dialog

Title: **Complete a task in four steps**. It describes Create/open workspace, Add/read materials, Ask with workspace sources, and Run a workflow. A **Got it** button closes it. The dialog is informational and does not create data.

### 3.14 Account & display dialog

Title: **Account & display**. Shows local avatar, display name, username, and role. Contains a **Compact workspace layout** switch whose value is saved only in browser local storage. Buttons are **Sign out** and **Done**. Sign out revokes the local session and returns to authentication.

### 3.15 Delete confirmation dialog

Used for removing a material or deleting a whole workspace. Workspace deletion requires typing the exact workspace name; the dialog explains that materials, answers, workflow history, and generated files will be removed. Material deletion has a shorter confirmation. The destructive button remains disabled until the workspace confirmation matches. Errors such as an active workflow are shown inline.

## 4. Component inventory

| Component | Where | Interaction and states |
|---|---|---|
| Brand mark and brand panel | Authentication and sidebar | Static Aegis mark, local-product labeling, dark navy presentation. |
| Portal switcher | Authentication | Selects User, Supervisor, or Administrator portal; active accent and copy change. |
| Auth form | Authentication | Sign in/register fields, password reveal, validation, submit disabled state, inline errors. |
| Sidebar | Signed-in shell | Workspace navigation, help, account, role-sensitive Manage users, sign out. |
| Top bar | Signed-in shell | Current location, local-only indicator, model status badge. |
| Workspace card | Workspace list | Clickable project summary; owner metadata for elevated roles. |
| Workspace metrics | Overview | Counts materials, ready files, answers, runs, completions, and models. |
| Sequence list | Overview | Four numbered action steps with tab-jump buttons. |
| Activity list | Overview | Recent result summaries or empty copy. |
| Prompt suggestion | Assistant | Fills the prompt textarea without submitting. |
| Prompt composer | Assistant | Prompt textarea, source toggle, submit, status/error. |
| Answer card | Assistant | Saved prompt, model/capability metadata, answer text, source links, copy action. |
| Filter pills | Assistant, Materials, Workflows | Active filter changes visible cards/rows; no-match state appears when needed. |
| Drop zone/file picker | Materials | Multiple local file selection/drop, disabled in read-only mode, upload progress/error. |
| Material row | Materials | Type, name, size, readiness, download, read, source, vision, review-pack, remove actions. |
| Source dialog | Materials/Assistant | Page evidence and rendered preview; close control. |
| Workflow launcher | Workflows | Inspection pack entry and utility selector/action. |
| Workflow card | Workflows | Status, progress, events, checks, result, artifact links. |
| Security status cards | Offline status | Local binding, local model, WebAssembly descriptions. |
| Connection monitor | Offline status | Current observation summary, details, badge, limitations. |
| Native dialog | Workspace, guide, account, users, source, delete | Modal interaction, close buttons, Escape behavior, inline errors. |
| Toast | Global signed-in shell | Temporary success notification such as workspace created, role changed, or artifact ready. |
| Privacy chip | Materials and Offline status | Green local/storage/watch state; attention style for observed external activity. |

## 5. Roles and permissions

Only three roles are implemented: **User**, **Supervisor**, and **Administrator**. There are no implemented Viewer or Engineer roles. The requested “Supervisor/Admin” concept is split into the two actual roles.

### User

- Sees only workspaces they own.
- Can create, open, rename, and delete their own workspaces.
- Can upload, read, inspect, download, describe, and remove their own materials.
- Can ask general or source-grounded questions in their own workspace.
- Can launch inspection and coding workflows and download their artifacts.
- Can open Offline status, guide, and account settings.
- Cannot see or access another user’s workspaces, documents, answers, runs, or artifacts.
- Cannot access Manage users.

### Supervisor

- Logs in through the Supervisor portal.
- Can list and open all team workspaces.
- Can read documents, extracted pages, saved answers, workflow history, and artifacts in other users’ workspaces.
- In another owner’s workspace, mutation controls are hidden or disabled: upload, read/extract, generation, workflow start, code run, rename, workspace deletion, and material deletion.
- Can still work with a workspace they own using normal User-level controls.
- Cannot change account roles and has no Manage users screen.

### Administrator

- Logs in through the Administrator portal.
- Can list, read, modify, and delete every workspace and its material/data.
- Can run questions and workflows in every workspace.
- Can open Manage users and change other account roles.
- Cannot demote their own active account from Administrator.

Portal choice is not a privilege escalation mechanism: correct credentials with the wrong portal are rejected by the server.

## 6. Complete user workflows

### Sign-in workflow

Open root or a portal URL → choose portal → enter username/password → submit → server verifies credentials and role/portal match → workspace list opens. For a new User: choose Create account → enter display name, username, and 12–128 character password → submit → User account is created and signed in.

### Workspace workflow

Workspace list → New workspace → enter name and optional description → Create workspace → card appears. Select card → workspace detail opens at Overview. Use Edit details → change fields → Save changes → title/description refresh. Use Delete workspace → type exact name → Delete workspace → records/files are removed and list refreshes. Deletion is refused while a workflow is running.

### Material and evidence workflow

Open Materials → drop/choose files → upload status appears → rows show Stored locally and Unread → select Read locally or Read all unread files → extraction/OCR/rendering runs → row becomes Ready → View sources → source dialog shows page text and image → source toggle becomes available in Assistant.

### Grounded question workflow

Open Assistant → type a request or select suggestion → enable Use workspace sources → submit Generate answer → local retrieval selects up to three matching excerpts → general local model answers with source IDs → saved answer card appears → select source ID/page button to inspect evidence → copy answer if needed. If there is no matching evidence, the UI stores a message saying supporting evidence could not be found. If the model cannot run, an error is shown and no cloud fallback occurs.

### Inspection review-pack workflow

Materials → choose a read or unread material → Create review pack → Workflows opens and polls a Running card → system reads the report, retrieves evidence, drafts/revises or uses a structured extractive fallback, builds Office files, and marks the run Complete → user reviews event log, draft, evidence, and human-review warning → downloads approval-note DOCX, findings-register XLSX, and inspection-briefing PPTX/PDF where generated.

### Verified utility workflow

Workflows → select Celsius to Fahrenheit or Sum numeric readings → Generate & verify → Running card appears → local coding model generates a fixed function → WebAssembly runtime executes three independent cases → card records checks and verification → Complete if all pass or Failed if not → user downloads `utility.py` and reviews checks.

### Offline-status workflow

Open Offline status → view local binding/model/runtime cards → connection monitor loads a current snapshot → badge communicates observed local/external connections → evidence note explains scope and packet-capture limitation.

## 7. Agent/workflow representation

The UI does not expose named Planner, Retriever, Vision Inspector, Analyst, Verifier, or Human Approval agents as separate cards. Their implemented behavior is represented through workflow event messages and result fields.

Inspection run stages shown in the event history are equivalent to:

1. Plan: read the selected report, retrieve evidence, draft, check references, and create Office files.
2. Read selected report and retain page references.
3. Retrieve excerpts from the local collection.
4. Generate a draft using the general local model.
5. Optionally revise when source references are invalid.
6. Produce an explicitly extractive structured review note if references remain unreliable.
7. Create editable Word, Excel, and PowerPoint files; mark human review required.

Coding run event history shows planning, attempt 1/2, verification failures or successes, and completion in a WebAssembly runtime with no host filesystem/network grants.

Vision is available from a material row’s Describe image action and saves a cautious local vision result in Assistant. There is no separate Vision Inspector screen.

There is no interactive approval gate, signing gate, passport viewer, or reject/approve control in the current UI. Human review is a warning/status field, not a required button-driven state.

## 8. Evidence/RAG UI

The Materials section is the implemented knowledge collection surface. Files are stored locally and converted into page records. PDFs can use embedded text or OCR; images use OCR; text/CSV files use direct text extraction. Source records include document ID, filename, page, text, extraction method, warnings, OCR lines, and optional rendered page image.

Retrieval is deterministic token-overlap chunk selection. The Assistant displays source-grounded answers with `[S1]`, `[S2]`, and `[S3]` references and source buttons. The Source document dialog lets users compare the extracted excerpt with page content. There are no visible confidence scores, semantic-vector scores, relevance percentages, or standalone Knowledge Vault route.

## 9. Security and sovereignty UI

Visible security language includes **ON-PREMISE AI**, **Local workbench**, **Running on this computer**, **Local only**, **Stored locally**, **Local mode**, and **Loopback service**. Offline status cards explain loopback binding, local model files, and WebAssembly isolation.

The model status badge reports installed/running local model availability. The model adapter uses local llama.cpp model files and no cloud fallback. The connection monitor samples the Python app and child processes and records blocked Python-level non-loopback attempts. Its own text clearly states that snapshots are not packet capture and short connections may be missed.

There is no Ollama screen, TEE indicator, hardware panel, policy editor, cryptographic audit ledger, or enterprise security dashboard implemented in this UI.

## 10. Task Passport and audit UI

No Task Passport, signing workflow, hash viewer, audit ledger, provenance viewer, or verification passport screen is implemented. The closest visible equivalents are workflow event history, source references, artifact downloads, verification checks for utilities, and human-review status on inspection runs. A replacement UI must preserve those existing user-visible outputs unless a later implementation adds a real passport feature.

## 11. Forms and inputs

| Input | Screen | Default/placeholder | Validation/result |
|---|---|---|---|
| Portal selector | Authentication | User selected initially | Selects login portal and route. |
| Display name | User registration | `Pranav` placeholder | Required, 1–60 nonblank characters. |
| Username | Authentication | `e.g. pranav` | Required, 3–32 allowed characters; normalized lowercase. |
| Password | Authentication | `Your password` | Required, 12–128 characters; show/hide toggle. |
| Workspace name | New/edit dialog | `e.g. Pump P-101 inspection` | Required, 1–80 nonblank characters. |
| Workspace description | New/edit dialog | Project description | Optional, max 400 characters. |
| File picker | Materials | PDF/TXT/CSV/PNG/JPG/JPEG | Multiple files, max 20 MB each and 200 MB workspace. |
| Material search | Materials | `Search materials` | Client-side filename filtering. |
| Material readiness filter | Materials | All | All/Ready/Unread. |
| Prompt | Assistant | `Ask a question or describe the draft you need…` | Required, max 2,000 characters. |
| Source toggle | Assistant | Disabled until a file is read | Enables grounded retrieval. |
| Answer filter | Assistant | All | All/With sources/General. |
| Utility select | Workflows | Celsius to Fahrenheit | Celsius conversion or sum readings. |
| Run filter | Workflows | All | All/Running/Complete. |
| Compact layout switch | Account & display | Browser-stored value | Toggles compact spacing locally. |
| Role select | Manage users | Current stored role | Administrator changes another account’s role. |
| Workspace delete confirmation | Delete dialog | Empty | Exact workspace name required. |

## 12. Modals, dialogs, and overlays

Implemented dialogs are native HTML `<dialog>` elements: workspace create/edit, Source document, How to use Aegis, Account & display, Users and roles, and Delete confirmation. Each has an explicit close icon. The guide, account, user, source, and delete dialogs also expose action buttons. Escape is supported by the browser dialog behavior; no custom outside-click behavior is defined in the application script. Inline red alert areas are used for errors. Toasts are temporary global success messages.

There are no drawers, side sheets, approval modals, passport viewers, or confirmation dialogs for starting ordinary questions.

## 13. Visual design language

The visual language is a dense industrial workbench rather than a marketing page.

- Typeface: system UI stack headed by `Segoe UI Variable`, then `Segoe UI`, Arial, sans-serif.
- Main background: pale blue-gray `#f3f6f9`; surfaces are white; sidebar and hero panels use deep navy around `#0b1724` and `#132538`.
- Primary action: blue around `#245edb`; Supervisor accent uses teal; Administrator accent uses purple.
- Secure/local accent: mint/green, including status dots and privacy chips.
- Error/destructive accent: muted red, pale red backgrounds, red borders.
- Text: dark navy/ink for headings, muted blue-gray for secondary text, small uppercase letter-spaced eyebrows.
- Cards and panels: white surfaces, thin light borders, rounded corners generally 7–11px, restrained shadows on dialogs and selected/hovered elements.
- Buttons: compact rounded rectangles; primary filled, secondary white with border, destructive pale red with red border, text buttons borderless.
- Inputs: white background, light border, 7px radius, blue focus ring/border.
- Icons: simple text glyphs such as `▦`, `⌂`, `✦`, `▤`, `↻`, `◇`, `?`, `○`, and `↪`; no external icon library is used in the HTML.
- Status representation: green dot/local chip for secure/local; blue/purple/teal accents for action and role; pale blue for processing or informational; pale red for error/restricted/destructive.

## 14. Responsive behavior

Desktop uses a fixed 248px sidebar and content area with up to 1380px width. Workspace cards use three columns, reducing to two around 1100px. Overview columns and workflow launcher grids collapse around 1100px.

At widths below 760px, the sidebar becomes a horizontal top strip; its product block and navigation links hide, while the profile collapses to the avatar/action area. The top bar becomes shorter, content padding reduces, workspace cards become one column, the current-workspace nav becomes a horizontally scrollable mobile tab row, and file action buttons become a grid. Overview metrics may use two columns, then one column below 430px. Dialogs remain width-limited with viewport-based margins. Long filenames and answer text wrap.

## 15. Data displayed

The UI displays identity (display name, username, role, initials), portal, workspace name/description/owner/created date, material filename/type/size/readiness/storage state, extracted page number/text/method/warnings, source IDs and citations, prompt text, answer text, model name/capability/routing reason/duration, model availability, workflow kind/status/created time/events/progress, verification inputs/expected/actual/pass values, artifact filename and download, local binding/runtime/isolation state, connection observations, and temporary success/error messages.

Interactive data includes workspace cards, tab buttons, source-reference links, download links, workflow filters, material search/filter, role selectors, and artifact buttons. Workspace identity and source page references are important for traceability; model/status metadata explains local processing; owner/role metadata explains permissions.

## 16. API behavior relevant to the UI

The UI uses same-origin `/api` calls with session cookies and CSRF headers. The main mappings are:

| UI action | Server operation | UI result |
|---|---|---|
| Sign in/register | `/api/auth/login` or `/api/auth/register` | Session and user/role returned; workspace shell opens. |
| Load identity | `/api/auth/me` | Restores session or returns to auth. |
| Load workspaces | `GET /api/workspaces` | User-owned or elevated team list renders. |
| Create/edit/delete workspace | `POST`, `PATCH`, `DELETE /api/workspaces...` | Dialog closes, title/list refreshes, errors inline. |
| Upload material | `POST /api/workspaces/{id}/documents` | File row and upload status update. |
| Download material | `GET /api/documents/{id}/download` | Original attachment downloads. |
| Read/extract | `POST /api/documents/{id}/extract` | Page records and Ready state appear. |
| Read source | `GET /api/documents/{id}/pages` and page image | Source dialog fills with evidence. |
| Ask general/grounded | `POST /api/workspaces/{id}/questions` or generation route | Saved answer card appears. |
| Describe image | `POST /api/documents/{id}/vision` | Vision answer saved in Assistant. |
| Start inspection | `POST /api/workspaces/{id}/runs` | Running workflow is created and polled. |
| Start coding | `POST /api/workspaces/{id}/code-runs` | Running utility workflow is created and polled. |
| Load runs | `GET /api/workspaces/{id}/runs` | History/progress/events refresh. |
| Download artifact | `GET /api/artifacts/{id}/download` | Generated file downloads. |
| Load local status | `GET /api/models` and `/api/system/network` | Model badges and Offline status update. |
| Change role | `PATCH /api/admin/users/{id}/role` | Role select updates and toast appears. |

Every server-side read/write checks the session and workspace ownership/role. Unauthorized cross-workspace access appears as a permission/not-found error in the UI.

## 17. Loading, error, empty, and success states

Loading text includes **Opening Aegis…**, **Checking models**, **Loading local accounts…**, **Uploading n of n files**, **Reading filename…**, **Reading the image with the local vision model…**, **Working locally…**, and **Loading observations…**. Buttons are disabled while relevant submissions or reads run.

Empty states include no workspaces, no materials, no answers, no workflows, no matching materials, and no workflows in the selected filter. Empty copy always directs the next action.

Errors appear as inline pale-red alerts for authentication, workspace loading, uploads, extraction, generation, workflow launch, user role changes, and delete confirmation. Common messages include invalid credentials, wrong portal, model unavailable, model busy, unsupported/invalid file, storage limit, read-before-grounding requirement, active workflow deletion refusal, and permission denial.

Success feedback includes workspace-created/updated/deleted toasts, material removal toast, role-change toast, visual-description-ready toast, and status text for saved answers/read files. Workflow cards use status badges and event history rather than a spinner-only state.

Offline/model-unavailable behavior is explicit: the model badge reports unavailable, the API returns a local error, and no cloud fallback is used. The Offline status page may show attention if external connection observations exist, while retaining the packet-capture limitation.

## 18. GT-07 demo flow

No GT-07-specific route, label, seeded investigation, or demo wizard exists in the current UI. The closest reproducible demonstration is the inspection review-pack flow:

1. Sign in as a User or Administrator.
2. Create a workspace such as an inspection review.
3. Open Materials and upload a sample PDF/TXT/image.
4. Read locally and inspect the Source document dialog.
5. Choose Create review pack.
6. Watch Workflows update from Running through evidence retrieval, draft generation, reference checking, and Office export.
7. Review the draft, source references, review-required warning, event history, and downloadable DOCX/XLSX/PPTX artifacts.

The available sample assets include an inspection scan PDF/PNG, a demonstration inspection TXT, and a demo SOP. No separate GT-07 agent storyboard or human approval UI can be verified.

## 19. Visual references

No new screenshots are included in this specification because the request is documentation-only and the existing project already contains a live local preview. A rebuild should reproduce these major visual contexts: split authentication page; dark-sidebar workspace list; Overview with dark welcome card and metric cards; Assistant prompt/results; Materials uploader and document rows; Workflows launcher/history; Offline status security cards/monitor; and the native dialogs described above.

## 20. Final screen map

| Screen | Purpose | Main components | Main actions | Roles |
|---|---|---|---|---|
| User portal | User sign-in/registration | Brand panel, portal switcher, auth form | Sign in, register | User |
| Supervisor portal | Team review sign-in | Same auth surface, Supervisor copy | Sign in | Supervisor |
| Administrator portal | Full-control sign-in | Same auth surface, Administrator copy | Sign in | Administrator |
| Workspace list | Select/create project | Cards, count, empty state | Open/create | All |
| Overview | Project orientation | Welcome, metrics, sequence, activity | Jump tabs, edit/delete | Owner/Admin; read-only Supervisor for others |
| Assistant | Local Q&A | Prompt, suggestions, source toggle, answer cards | Ask, filter, inspect/copy | Owner/Admin; read-only Supervisor for others |
| Materials | Local evidence collection | Drop zone, search/filter, rows | Upload, read, source, vision, download, review pack, remove | Owner/Admin; read-only Supervisor for others |
| Source document dialog | Evidence verification | Page text/images, warnings | Close, inspect source | All with access |
| Workflows | Automation/artifacts | Launchers, history, cards | Start, filter, inspect, download | Owner/Admin; read-only Supervisor for others |
| Offline status | Sovereignty observation | Security cards, monitor | Refresh/view status | All signed-in roles |
| Manage users dialog | Role management | User list, role selects | Change role | Administrator |
| How to use dialog | Product guidance | Four-step guide | Close | All signed-in roles |
| Account & display dialog | Identity/preferences | Profile summary, compact switch | Toggle, sign out, close | All signed-in roles |
| Delete confirmation | Destructive action safety | Confirmation text/input | Keep or delete | Writable owner/Admin |

## 21. Final interaction map

| Feature | Entry point | User action | System response | Next state |
|---|---|---|---|---|
| Sign in | Portal form | Submit credentials | Session created if portal matches role | Workspace list |
| Register | User portal | Submit name/username/password | User account created and signed in | Workspace list |
| Create workspace | Workspace list | Fill dialog and submit | Workspace persisted | Refreshed list |
| Open workspace | Workspace card | Select card | Workspace data and panels load | Overview |
| Upload material | Materials drop zone | Choose/drop files | Bytes stored and rows added | Unread material rows |
| Read material | Material row | Read locally | Text/OCR/pages/previews retained | Ready row/source dialog |
| Ask grounded question | Assistant | Enable source mode and submit | Retrieve excerpts and generate cited response | Saved source-grounded answer |
| Ask general question | Assistant | Submit prompt with source mode off | Route to local general/coding model | Saved general answer |
| Create review pack | Material row | Select Create review pack | Async inspection run and exports | Running then Complete workflow |
| Verify utility | Workflows | Choose utility and Generate & verify | Generate and execute isolated checks | Complete/Failed workflow |
| Inspect evidence | Answer/material | Select source/page action | Source dialog opens | Evidence review |
| Download artifact | Workflow card | Select artifact | File attachment returned | Local downloaded file |
| View security | Sidebar tab | Select Offline status | Model/network snapshot loads | Status view |
| Manage role | Admin sidebar | Change role select | Server updates account role | Updated user row/toast |
| Delete material | Material row | Confirm removal | DB/file/page/previews removed | Refreshed list |
| Delete workspace | Workspace header | Type exact name and confirm | Workspace records/files removed | Workspace list |
| Sign out | Profile | Select sign-out | Session revoked | Authentication screen |

## 22. Product knowledge summary

### What must remain functionally identical

- Local portal authentication with User, Supervisor, and Administrator role matching.
- User-owned workspace separation and Supervisor read-only team access.
- Administrator-wide access and role management with self-demotion protection.
- Workspace creation, editing, deletion, and project-scoped material/answer/workflow data.
- PDF/TXT/CSV/PNG/JPG/JPEG upload limits, local storage, download, extraction/OCR, page previews, and source review.
- General and source-grounded local assistant behavior, saved answers, citations, and source inspection.
- Local model status and deterministic task routing behavior.
- Inspection review-pack workflow, evidence references, human-review warning, and editable artifact downloads.
- Verified utility workflow with isolated execution, independent checks, and verification output.
- Offline status information, loopback/local-runtime messaging, and observation limitation.
- Empty, loading, processing, success, error, disabled, read-only, and completed states.

### What is purely visual

The exact color values, typography scale, glyph choices, card geometry, sidebar width, spacing, responsive arrangement, illustration/decorative treatment, and visual styling can change in a new UI if the same information and interactions remain available. The current labels, terminology, status meanings, and role restrictions should remain recognizable.

### Critical workflows

Authentication → workspace → upload → read/OCR → source inspection → grounded question; and material → inspection review pack → event/progress review → evidence/draft review → artifact download. The verified utility flow is the second critical workflow.

### Role restrictions

Users are private owners; Supervisors can read team records but cannot mutate another owner’s records; Administrators can manage all records and roles but cannot demote themselves. Server-side authorization must remain authoritative even if a new UI hides controls.

### Important terminology

Aegis, Local workbench, On-premise AI, local-only, workspace, material, read locally, source-grounded, stored locally, review pack, verified utility, workflow history, artifact, Offline status, Supervisor review access, Administrator, human review required, and source IDs `[S1]`/`[S2]`/`[S3]`.

### Important data

Preserve workspace ownership and description; material filename/type/size/readiness; page text, page number, OCR method/warnings and source references; prompt/answer/model/duration/capability; workflow status/events/checks/artifacts; user identity/role; local model status; and the Offline status evidence boundary. These are the information a replacement UI must continue to expose for the existing functionality to remain understandable and reviewable.

