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
