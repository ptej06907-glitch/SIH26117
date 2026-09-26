# ARK judge link through Tailscale Funnel

Use this route instead of the Azure VM. Funnel publishes a **separate synthetic-data ARK instance** from this Windows PC. It is not an MRPL deployment or an air-gapped system. The current private workbench on port 8765 and its `data/` folder must never be published.

## 1. Prepare the isolated demo while it is private

1. Install Tailscale for Windows from https://tailscale.com/download and sign in to a Personal account. Funnel is included on all plans, but check the Personal plan terms for your use.
2. Double-click `Start Demo Setup.cmd`. It uses `demo-data/` and listens only on `http://localhost:8767`. No Funnel should point to this port. Use `localhost` in the browser so its sign-in cookie stays separate from the private workbench at `127.0.0.1:8765`.
3. In that local setup site, create a dedicated Judge/User account and a separate Reviewer/Supervisor account. Use unique passwords unrelated to personal or MRPL accounts. Create a private Administrator account if needed. Never reuse accounts from `data/`.
4. Stop the setup server. Assign the reviewer role with `scripts/set_user_role.py`, pointing it at `demo-data/workbench.sqlite3`. For example:

   ```powershell
   .\.venv\Scripts\python.exe scripts/set_user_role.py ark_reviewer supervisor --database demo-data/workbench.sqlite3
   ```

5. Start `Start Demo Setup.cmd` again. Sign in as the Judge account and load **only labelled synthetic or public materials**. The repository's `samples/maintenance-corpus/` is a fictional sample; it can be imported with:

   ```powershell
   .\.venv\Scripts\python.exe scripts/import_maintenance_corpus.py ark_judge --db demo-data/workbench.sqlite3
   ```

6. Stop all ARK server windows. Encrypt the demo database, uploaded files and artifacts, and enable mandatory Defender scanning:

   ```powershell
   .\.venv\Scripts\python.exe scripts/encrypt_local_data.py --directory demo-data
   ```

   Run the import before encryption. Do not copy the private `data/` directory into `demo-data/`.

## 2. Obtain and enable the public URL

1. In PowerShell, run `tailscale funnel --bg 8766`. The Tailscale authorization page may ask you to enable Funnel. This exposes **only local port 8766**, not setup port 8767 or private port 8765.
2. Copy the exact `https://...ts.net` URL shown by Tailscale. In the project directory, launch the public server using that origin:

   ```powershell
   & '.\Start Public Demo.cmd' 'https://YOUR-HOST.YOUR-TAILNET.ts.net'
   ```

   The script refuses to start if the isolated demo database has not been created. Public mode requires the matching HTTPS origin, marks the site as synthetic, disables new-account registration, and uses Secure session cookies.
3. Test the URL from a phone with Wi-Fi **off**. Sign in as the Judge account, open the seeded sources, run a grounded question and the synthetic P-101 scenario, then complete a Supervisor review. Verify the public warning and that the local private workspace is absent.

## 3. Keep the link working

- Keep the PC powered on, awake, online, signed in to Tailscale, and running `Start Public Demo.cmd` through the evaluation window. If any of these stop, the link stops working. Funnel is currently a beta service with bandwidth limits, so test again immediately before submitting the PPT.
- Share the Judge credentials privately with evaluators; never publish the Administrator password. Use unique demo credentials and rotate or retire them after judging.
- Never run the private setup app through Funnel. Setup uses a different port by design. If you need to disable public access, run `tailscale funnel --https=443 off` and verify the URL no longer opens.
- Do not upload confidential, personal or MRPL plant files to the public demo. Keep the existing local instance for private work.

Tailscale references: https://tailscale.com/docs/features/tailscale-funnel and https://tailscale.com/docs/reference/tailscale-cli/funnel .
