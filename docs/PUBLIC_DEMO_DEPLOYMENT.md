# ARK public judge demo

This is a **separate synthetic-data demonstration** of the working ARK application. It is not an MRPL installation or an air-gap demonstration. Never copy the development laptop's `data/` directory or any confidential document to the demo host.

## Chosen hosting layout

Use one Azure Windows VM with a public DNS name. Caddy accepts HTTPS on ports 80/443 and proxies to the ARK FastAPI process on `127.0.0.1:8765`. The local model runtime also binds to loopback. Do not expose port 8765 or model runtime ports. Keep one Uvicorn worker: encrypted SQLite storage and the workflow lock are single-process designs.

The public hostname must exactly match the value of `ARK_PUBLIC_DEMO_ORIGIN`. When set, ARK accepts that host, requires matching HTTPS `Origin` headers on writes, issues Secure session cookies, disables self-registration and identifies the site as a public synthetic-data demo. Leaving the variable unset preserves the original localhost mode.

## Prepare a clean demo VM

First, the team owner needs an Azure account with an active subscription: https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account . Complete Microsoft's identity and billing verification directly on Azure; do not share payment details or account passwords in chat. A free-account credit is not a promise that this Windows VM and its model workload will be free. Review the displayed VM price and set a budget alert before starting it.

1. Choose a Windows VM with at least the memory available on the tested 24 GB development laptop, then benchmark model loading before sharing the link. VM availability and pricing depend on the region and subscription.
2. Create a static public IP and DNS label. Record the final `https://<name>.<region>.cloudapp.azure.com` origin. Permit inbound HTTP/HTTPS for Caddy; restrict administrative access to the team. Do not permit inbound traffic to ARK's port 8765.
3. Copy a clean repository checkout. Install the pinned dependencies from `requirements.txt`, the verified `llama.cpp` Windows runtime and model assets. GitHub excludes `.venv/`, `runtime/`, `models/*.gguf` and `data/`.
4. Start ARK locally once **without** `ARK_PUBLIC_DEMO_ORIGIN`. Create separate User, Supervisor and Administrator accounts with unique passwords. Use `scripts/set_user_role.py` locally to assign the Supervisor and Administrator roles. Keep the Administrator password private.
5. Populate only synthetic cases and public demonstration reference files. Use the built-in P-101 synthetic cases and, if useful, the repository's labelled sample corpus. Check every file before upload.
6. Stop ARK. Enable the encrypted-storage and mandatory-antivirus markers using the documented `docs/SECURITY_IMPLEMENTATION.md` procedure. Confirm Defender is available and a harmless sample upload succeeds. Do not hand-create an encryption marker over an existing plaintext database: run the migration script if data already exists.

## Configure HTTPS and launch

Copy `deploy/Caddyfile.example` to a VM-local `Caddyfile` and replace the placeholder with the exact Azure DNS name. Caddy provisions a public certificate when DNS resolves and ports 80/443 reach it.

In the ARK process environment, set:

```powershell
$env:ARK_PUBLIC_DEMO_ORIGIN = 'https://ark-demo.YOUR_REGION.cloudapp.azure.com'
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8765 --workers 1
```

Run Caddy with the VM-local Caddyfile. Configure both processes to restart after reboot under the same dedicated Windows account. The account that encrypts the data must also run ARK thereafter; Windows DPAPI is bound to that account. Test restart and recovery before publishing the URL.

## Acceptance check before adding the PPT link

- Open the HTTPS site from a device outside the VM. Confirm the browser reports a valid certificate and the public synthetic-data label is visible.
- Confirm account creation is hidden and `/api/auth/register` rejects a request. Sign in with the assigned User account and verify the session cookie is Secure.
- Open a preloaded reference, ask a source-grounded question, and open the cited page. Exercise a local model route and a scanned-page OCR result.
- Run P-101's synthetic conflicting-reading case. Confirm the engineer inputs, arithmetic check and locked export. Sign in as a different Supervisor, approve the exact case, then export it.
- Run the Office review pack and the fixed-purpose coding utility. Confirm approvals and verification gates work through the public URL.
- Verify that a second browser/device can use the link. Restart the VM or services and repeat sign-in and the P-101 case listing.
- Check that no confidential files or local development accounts were copied to the VM. Keep the VM running through the evaluation period and monitor its availability.

The PPT should say **Interactive synthetic-data demo** and include the verified HTTPS URL plus the assigned demo credentials. Do not describe this public VM as air-gapped or on-premise MRPL infrastructure. MRPL's target installation remains a separate internal deployment.
