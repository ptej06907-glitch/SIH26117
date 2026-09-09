# Security implementation — 2026-09-09

## Encrypted storage

The Windows workstation can enable DPAPI storage by running `scripts/encrypt_local_data.py` with the application stopped. The migration verifies an encrypted recovery copy, encrypts the database and existing uploads/previews/artifacts, and creates the activation marker. DPAPI binds decryption to the Windows account; there is no plaintext application key file. Copying these files alone to another laptop does not make them readable. Preserve the Windows profile and its recovery arrangements before replacing the machine. This is not protection against code already running as the same Windows user or a compromised administrator.

For this small prototype, SQLite is deserialized into memory for each transaction and atomically persisted as encrypted bytes after writes. A process lock and file lock serialize access. Do not configure multiple Uvicorn workers. This approach is intentionally unsuitable for a large production database; use a supported encrypted database service for that deployment. Upload staging and Office generation can temporarily write plaintext before sealing. Model logs, browser downloads, OneDrive history, previous backups, memory and the Windows pagefile are outside this protection. Encryption does not retroactively erase prior copies.

Original downloads and page previews are decrypted only after the existing authorization checks. Existing local role and corpus scripts support the encrypted database. Database recovery file: `data/workbench.pre-encryption.dpapi`. To recover, stop the app and use `vault.read_bytes` to verify the backup before replacing the database through `vault.write_bytes`; never overwrite a live database.

## Antivirus

The `data/.require-antivirus` marker enables mandatory Windows Defender custom scans on new uploads. Existing format screening still runs. The adapter invokes the installed Microsoft engine with `-DisableRemediation`, never a shell command built from filenames. Nonzero exits, missing engines and a 60-second timeout reject the upload. No antivirus preferences or exclusions are modified. The scan follows Windows Defender's host policy: this application does not certify whether the host has cloud protection or sample submission enabled. The Python network guard does not constrain the Defender service. Air-gapped deployments must enforce host policy separately.

A scan passed on the fictional maintenance incident sample. Automated tests simulate detection and timeouts without placing live malware or an antivirus test file on disk. Existing uploads are not retrospectively certified clean by enabling this adapter.

## Document prompt injection

Unicode-normalized text pages matching selected instruction-override, role-spoofing or secret-exfiltration patterns are excluded from retrieval, including the inspection fallback search. Original documents remain available to humans. General and vision prompts explicitly treat document/image text as evidence and prohibit obeying embedded role or approval commands. These patterns are conservative: they can exclude harmless discussion of attacks and miss novel attacks. AI-generated text cannot call approval APIs; backend authentication remains authoritative. This is a risk-reduction control, not proof that every injection is detected.

## Approval versions

When a Supervisor marks a report analysed, `review_versions` persists a canonical snapshot and SHA-256 digest of the complete run result, report/source byte hashes and artifact hashes, together with reviewer identity and time. Approval or disapproval recomputes the snapshot in a serialized database transaction and rejects changed or missing evidence. The same reviewer must make the decision. Final decisions cannot be changed through the transition API; a new analysis creates a separate review request.

Pre-existing pending approvals lacking a snapshot return to pending analysis. Historical completed approvals are not retroactively version-certified. These hashes detect changes relative to the stored snapshot; they are not independently signed or tamper-proof against someone who can rewrite both the database and files. The frontend layout is unchanged.
