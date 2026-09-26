# ARK recording runbook

## What this update actually implements

The Overview page now contains a persistent equipment investigation panel. It is a bounded deterministic workflow, not a new LangGraph/LLM agent implementation. Existing local-model, OCR, Office-drafting, sandbox and security tools are preserved.

New flow: retrieve evidence → engineer confirmation → thickness-trend calculation → Decimal arithmetic cross-check → separate reviewer approval → controlled HTML report export. Every action records an audit event. Reopening a case revokes confirmation, verification and approval. Changed uploaded source bytes or extracted pages block progress and export.

The application still uses FastAPI, SQLite, vanilla JavaScript and its existing model/OCR adapters. The proposed React/Vite, LangGraph, Qdrant/PostgreSQL and PaddleOCR migration is NOT part of this update. Do not claim those technologies in a prototype video.

## Preparation

1. Start ARK using `Start ARK.cmd` and open http://127.0.0.1:8765/login/user.
2. Use an existing User account and a different existing Supervisor/Administrator account. No passwords or elevated accounts are created by this update. An Administrator can assign roles through the existing user management screen.
3. Open a workspace. The new **Evidence to approved case** section appears first on Overview.
4. Keep the local models loaded before recording the separate Assistant/Office-generation portion. The new case flow needs no model warmup and never pretends to run a model.

## Main recording sequence (about 3 minutes)

1. Choose P-101 and **Synthetic demo: conflicting readings**. Click **Start investigation**. Say the records are fictional demonstration data, not MRPL plant records.
2. Open the retained baseline inspection and revision-2 inspection. Show 8.0 mm (2023-09-01) and 7.4 mm (2025-09-01).
3. Open the excluded sources: revision 1 is superseded and P-101A is a different asset. Show the conflicting field note (7.1 mm). No automatic conclusion is presented.
4. Select the baseline and revision-2 source checkboxes. Enter previous thickness **8**, current thickness **7.4**, interval **2** years.
5. Confirmation note: **Use the signed inspection revision 2 for this synthetic case; the 7.1 mm field transcription is unconfirmed. The baseline and current inspection dates are two years apart.** These are demonstrator-selected assumptions for the fixture, not an automatic proof that revision 2 is signed.
6. Click **Confirm evidence & calculate**. Show **0.3000 mm/year** and the formula. Explain this is a thickness trend only, not remaining life or a fitness-for-service assessment.
7. Click **Run arithmetic cross-check**. The independent Decimal arithmetic path checks the floating-point result. This checks arithmetic, not engineering validity or OCR correctness.
8. Show export is locked. Sign out and sign in through the Supervisor portal with a separate reviewer account. Open the same workspace, then Refresh cases.
9. Inspect sources and inputs. Enter **Reviewed the selected revisions, confirmed inputs and calculation for this synthetic demonstration.** Click **Approve exact version**.
10. Export the report. Show the evidence, calculation, reviewer, digest and audit trail. Existing plant systems remain the official record.
11. Optional: the owner reopens the case to demonstrate revocation. Export becomes locked and fresh confirmation/checks/approval are required.

## Other demonstrations

- Missing reading: start the missing-evidence fixture. Attempts to enter an unsupported current thickness are rejected. Obtain new evidence and create another case.
- Real uploaded material: upload/read supported files using Materials. Each retained page must contain standalone `Equipment: P-101` and `Revision: 2` lines. Reading values must appear with `mm` units. The engineer selects the applicable sources and manually confirms revision applicability and elapsed time. This parser is deliberately conservative; it is not a general P&ID/tag recognizer.
- Existing AI capabilities: show grounded Assistant sources, local model selection, Office review pack and WebAssembly utility checks separately. The case panel is deterministic and must not be narrated as an LLM-generated multi-agent trace.
- Existing Office review-pack downloads now require approved review snapshots. Unapproved or changed output is blocked at the server, not only by the UI.

## Limits to state honestly

No production certification, guaranteed OCR accuracy, claimed savings, prevention of accidents, full-host network proof or automatic engineering approval. Case reports are HTML (printable from the browser); existing Office workflows remain separate. No native integration/export into MRPL production systems is installed.
