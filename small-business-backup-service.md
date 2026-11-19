# Small Business Backup Service: Client Owned Cloud Backups with Ransomware Protection

- **Scope:** a free VISI clinic service that sets up automatic, encrypted, ransomware resistant backups for local businesses and nonprofits. The backups go straight from the client's computers to a cloud account the client owns. **VISI does not host client backup contents or retain client encryption secrets. It does retain limited service records and monitoring metadata. Staff may see files during authorized support; do not promise zero access.**
- **Written:** November 18, 2026
- **Reviewed:** November 18, 2026. Revised for a nonprofit led by the owner and trained student professionals.
- **Status:** implementation and lab-validation draft; not an approved production runbook. Initial PowerShell scripts and 28 local tests are implemented (see `README.md` and `docs/test-results.md`). Windows/SYSTEM/VSS, B2 Object Lock/lifecycle, and live monitoring tests remain pending before the first client
- **Why this service:** most small businesses either have no backup or have one nobody has tested. What they can't do alone is pick the tools, set up immutability so ransomware can't delete the backups, notice when backups quietly stop, and practice a restore. That follow-through is the service, same idea as the DMARC rollout
- **Assumptions:** VISI branding, free clinic service, JSM, domain names, Proxmox/LXC, Keycloak, and companion documents come from the supplied draft; their availability was not verified. The existing server can host monitoring in an isolated VM using any supported hypervisor. Confirm branding and fees before publishing.
- **Companion docs (not supplied or reviewed):** `partner-email-security-service.md` (intake, "client drives, VISI guides" rule, agreement), `support-center.md` (the intake form), `contact-portal-and-help-center.md` (privacy and Discord rules), `master-timeline.md` section 4 (licenses), `backup-runbook.md` and `automated-backups.md` (VISI's own range backups, a different thing)

---

## 1. Ground rules

| Rule | Why |
|---|---|
| **The client owns the cloud account and pays the bill** | If VISI disappears tomorrow, the client still has every backup and full control |
| **The client types the encryption password and keeps it** | VISI can't leak what it never had. If the client loses it, nobody can recover the backups, including VISI. The agreement says this in plain words |
| **VISI never keeps a cloud key** | Same rule as the email service. Keys are created on the client's screen and pasted straight into the client's backup software |
| **The client clicks, the student guides** | In person or on a screen share. No remote access tools left behind |
| **No backup counts until a restore works** | Every setup ends with a test restore, and every client gets quarterly restore drills |
| **Minimize monitoring data** | Send status only; no filenames or backup logs. IP addresses, timestamps, check IDs, and contact records are still client metadata and must be protected |

---

## 2. What we offer, by client type

| Package | For | What gets set up | Client's running cost |
|---|---|---|---|
| **1. Files to cloud** (default) | 1 to 5 supported Windows computers in the pilot; expand toward 10 after measuring workload | Kopia on each machine, backing up to the client's Backblaze B2 bucket with Object Lock. Health pings to VISI's monitor | B2 storage, usually a few dollars a month (section 10) |
| **2. Files to cloud plus local image** | Same, when a dead laptop would stop the business for days | Package 1, plus a separately approved and properly licensed image-backup tool to a USB drive or NAS (section 8) | Drive/NAS plus any software license |
| **3. Office with a Synology NAS** | Offices that already have one, or are buying one | Synology Hyper Backup from the NAS to B2, immutable snapshots on the NAS, Active Backup for the PCs | B2 storage plus the NAS |
| **4. Simpler managed product** | Owners who will never look at a dashboard | Backblaze Business Backup on each computer, set up with a private encryption key. VISI only does setup and restore drills | $99 per computer per year |
| **SaaS add on** | Anyone whose files and email live in Microsoft 365 or Google Workspace | Advice and setup for Microsoft 365 Backup, or Synology Active Backup for M365 / Google Workspace if they have a NAS | See section 3.4 |

Package 1 is the launch. Package 2 is deferred until licensing and bare-metal recovery are validated; package 4 requires its own exclusion and recovery checklist. Package 3 waits until a client actually has a Synology. The SaaS add on is advice first, hands on later.

**Ask about Microsoft 365 and Google Workspace in the first meeting.** Many small businesses keep most of their files and all their email there. Packages 1 to 4 don't cover that data, and the client needs to hear it on day one, not after a deleted mailbox.

---

## 3. Tool selection and limits

Checked against the sources below on November 18, 2026. Record exact versions and license terms in the pilot evidence; recheck prices before quoting.

| Component | Decision and limits |
|---|---|
| Kopia + client-owned B2 | Keep as the package 1 candidate. Validate Windows unattended operation, restores, and retention before offering it. Use separate bucket, repository password, and restricted key per computer in the pilot; never share repositories or credentials between businesses |
| Healthchecks | Suitable for self-hosted status monitoring. A success ping is a job report, not proof that important files can be recovered |
| Veeam Agent Free | **Remove from the client-service default.** Veeam's licensing policy restricts Free/Community use for third-party services, including support and consulting. A client's own commercial use does not establish permission for VISI's service. Obtain written vendor permission or an appropriate service license before offering it; nonprofit status alone is not an exception. [Policy](https://www.veeam.com/legal/licensing-policy.html) |
| Backblaze Business Backup | Simpler alternative, currently listed at $99/computer/year. Validate supported drives, exclusions, version-history settings, billing, and restore workflow. Do not describe version history as equivalent to package 1's Object Lock. Explain the provider's passphrase/restore handling instead of promising provider-blind encryption. [Pricing](https://www.backblaze.com/cloud-backup/pricing), [encryption](https://www.backblaze.com/computer-backup/docs/data-encryption-and-passphrases) |
| Synology | Optional client-owned appliance. Confirm model, filesystem, DSM/package support, encryption and snapshot capabilities. Prove recovery after total NAS loss: restore the offsite data, relink Active Backup, then recover a workstation. Hyper Backup alone is not evidence that this whole chain works. Do not assume its B2 target supports the same lock workflow as Kopia. [Recovery procedure](https://kb.synology.com/en-me/DSM/tutorial/How_to_backup_and_relink_Active_Backup_for_Business_with_DSM_backup_packages) |
| Microsoft 365 Backup | Separate SaaS scope. Published price is $0.15/GiB/month of protected content, including applicable retained/deleted content; current mailbox size alone can understate charges. Map covered Exchange, OneDrive, and SharePoint data; do not imply full tenant/Teams/configuration coverage. [Pricing](https://learn.microsoft.com/en-us/microsoft-365/backup/backup-pricing) |
| Google Workspace / Synology SaaS backups | Design separately after inventorying mail, shared drives, permissions, and restore needs. A synced desktop folder is not a substitute for a SaaS backup |
| Other engines and storage providers | Keep restic/Backrest, Duplicati, UrBackup, Wasabi, S3, and IDrive as future evaluations. No second supported stack until the first has passed the pilot; do not make blanket unsupported-feature or licensing claims without checking the specific version |

B2 currently lists $6.95/TB/month, first 10 GB free, and free egress up to 3× average monthly storage; excess egress and applicable transactions can add cost. [B2 pricing](https://www.backblaze.com/cloud-storage/pricing)

---

## 4. How the pieces fit

| Where | What runs there | Holds client data? |
|---|---|---|
| Client computer | Kopia CLI, a scheduled task, the repo config and saved password | Yes, it's their machine |
| Client's B2 account | The encrypted backup repository, Object Lock on every file | Yes, encrypted with a password only the client has |
| VISI range: Healthchecks VM/container | One check per client job. Receives "started", "succeeded", or "failed" | **Metadata:** check IDs/names, timestamps, source IPs, alert recipients; no backup contents |
| VISI range: practice targets | Windows VM with fake business files, VISI's own practice B2 bucket | Fake data only |
| VISI JSM | Intake ticket, agreement, setup notes (no keys, no passwords) | Contact details, consent, scope, configuration metadata, incidents and test results; no secrets or copied client files |

Name checks with a client code (`c014-frontdesk-pc`), not the business name. This reduces obvious identification; IPs, alert addresses, and the separate client-code mapping may still identify a business.

---

### 4.1 Use of the existing server

Host the monitoring service and synthetic practice environment on the owner's server. Put production monitoring in a dedicated VM/network segment separate from student attack labs; a container alone is not a complete security boundary. Restrict administration to named staff accounts with MFA, patch regularly, and keep encrypted configuration/database backups off that server. The owner and a designated backup supervisor must both be able to recover it.

Do not host client backup contents on this server at launch. That would introduce tenant isolation, storage growth, bandwidth, physical security, incident response, and offsite recovery responsibilities. If added later, make it an optional additional encrypted copy with separate agreements and per-client isolation, while retaining independent offsite backups. A single self-hosted server is not a replacement for them.

### 4.2 Recovery objectives and eligibility

Before setup, document each critical workload, its business owner, acceptable data loss (RPO), acceptable recovery time (RTO), size, change rate, and dependencies. Proposed pilot target: daily file backup with up to 24 hours of data loss **only while daily jobs succeed**. Measure restore time before agreeing to an RTO; include replacement hardware, internet transfer, app installation, and staff availability.

Package 1 contains the original plus one offsite backup, not a complete three-copy strategy. Offer a separately tested local/offline copy where appropriate and document any declined protection. Database servers, production VMs, unsupported operating systems, regulated/sensitive workloads, and clients needing around-the-clock recovery require owner review and a specialist scope before acceptance. Identify sensitive data without collecting example records.

## 5. Lab components

### 5.1 Healthchecks behind the Cloudflare tunnel

**Placement:** a dedicated production VM is preferred on the existing server. An LXC with Docker is acceptable only after validating isolation and support. Allocate resources from measured usage; do not assume a sub-1-GB memory budget for the app and database. The example below requires the stated tunnel/identity infrastructure and lab validation.

**Two hostnames, so only the ping path is public:**

| Hostname | Serves | Protection |
|---|---|---|
| `ping.visiutrgv.org` | Only `/ping/...` | Public. Client machines have to reach it without logging in |
| `hc.visiutrgv.org` | The dashboard | Cloudflare Access with Keycloak, same as the other range apps |

`/opt/healthchecks/compose.yaml`:

```yaml
services:
  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_DB: hc
      POSTGRES_USER: hc
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data

  web:
    image: healthchecks/healthchecks:${HC_VERSION} # set to a tested published version; record digest
    restart: unless-stopped
    depends_on: [db]
    ports:
      - "<lxc-ip>:8000:8000"
    environment:
      DB: postgres
      DB_HOST: db
      DB_NAME: hc
      DB_USER: hc
      DB_PASSWORD: ${DB_PASSWORD}
      SECRET_KEY: ${SECRET_KEY}
      SITE_ROOT: https://hc.visiutrgv.org
      SITE_NAME: VISI Backup Monitor
      PING_ENDPOINT: https://ping.visiutrgv.org/ping/
      ALLOWED_HOSTS: hc.visiutrgv.org,ping.visiutrgv.org
      REGISTRATION_OPEN: "False"
      DEBUG: "False"
      PING_BODY_LIMIT: "0"
      EMAIL_HOST: ${EMAIL_HOST}
      EMAIL_PORT: "587"
      EMAIL_HOST_USER: ${EMAIL_USER}
      EMAIL_HOST_PASSWORD: ${EMAIL_PASSWORD}
      EMAIL_USE_TLS: "True"
      DEFAULT_FROM_EMAIL: backups@visiutrgv.org

volumes:
  db_data:
```

What each setting does:

- `postgres:16` with a named volume: the check history survives container rebuilds. A separate small Postgres keeps this off the shared database host, so a Healthchecks problem can't touch other apps
- `healthchecks/healthchecks:${HC_VERSION}`: the official image with a tested version selected before deployment. It runs the web app and the alert sender in one container and applies database migrations on start. Pinning a version means an upstream change can't break it on a random restart
- `ports: "<lxc-ip>:8000:8000"`: listens only on the LXC's own address, for `cloudflared` to reach. This binding does not block other network clients; firewall port 8000 so only the tunnel connector can reach it
- `SITE_ROOT`: the dashboard URL, used in alert emails
- `PING_ENDPOINT`: only changes how ping URLs are **displayed** in the dashboard. It does not change routing, which is why the tunnel rule below matters
- `ALLOWED_HOSTS`: Django refuses requests for any other hostname
- `REGISTRATION_OPEN: "False"`: nobody can sign up. Officers invite members to projects
- `EMAIL_*`: the SMTP relay for alerts. Which relay is an open decision (section 12)
- `HC_VERSION`, `SECRET_KEY`, and `DB_PASSWORD` live in a `.env` file next to the compose file, `chmod 600`, never in git

Start it and create the first admin:

```bash
cd /opt/healthchecks
docker compose up -d
docker compose exec web /opt/healthchecks/manage.py createsuperuser
```

- `up -d` starts both containers in the background
- `createsuperuser` makes the first login. Use an officer email; everyone else gets invited

**Tunnel rules** (locally managed `cloudflared` config; the dashboard managed version has the same fields under Public Hostnames):

```yaml
ingress:
  - hostname: ping.visiutrgv.org
    path: ^/ping/
    service: http://<lxc-ip>:8000
  - hostname: ping.visiutrgv.org
    service: http_status:404
  - hostname: hc.visiutrgv.org
    service: http://<lxc-ip>:8000
  - service: http_status:404
```

- Rules are checked top to bottom. The first rule sends `ping.visiutrgv.org/ping/...` to Healthchecks
- The second catches everything else on the ping hostname and returns 404, so the login page and admin pages are never reachable from the public name
- `hc.visiutrgv.org` gets the full app, and the Cloudflare Access policy in front of it requires a Keycloak login

**Per client setup in Healthchecks:**

- One **project per client** (named by client code). Members can be scoped per project
- One **check per backup job** (per computer). Schedule matches the task, for example daily at 21:00 America/Chicago with a 4 hour grace period
- Integrations: email to the VISI backup team and, with consent, the client backup contact by default. Complete any recipient confirmation and test both destinations

**Operational acceptance:** verify database startup readiness and recovery after reboot; `depends_on` alone does not ensure Postgres is ready. Validate HTTPS/proxy behavior, login/CSRF, application project permissions, and access denial through both the public hostname and origin IP. Disable public badges and unused integrations. Treat ping URLs as secrets: anyone who gets one can forge a success. Redact them from proxy logs and tickets; rotate after exposure. Set `PING_BODY_LIMIT=0` and verify metadata/log retention in the deployed version. See [configuration](https://healthchecks.io/docs/self_hosted_configuration/) and [official image](https://hub.docker.com/r/healthchecks/healthchecks).

Use an external monitor outside this server/power/internet connection to detect monitoring outages. Send a scheduled synthetic failure through the full alert path weekly; endpoint availability alone does not test the alert sender or email delivery. Back up the monitor daily and test recovery quarterly.

### 5.2 Practice range

Build this before the first client. It's where every command in this guide gets proven.

| Piece | Purpose |
|---|---|
| Windows 11 VM, "front desk PC" | Fake business files: a `Shared` folder, invoices, a fake QuickBooks style company file, a large PST |
| Second Windows VM | Restore target, playing a replacement laptop |
| VISI's own B2 account, practice bucket with Object Lock | Fake data only, a few cents a month. Uses the exact client steps |
| Healthchecks project `practice` | Check that pings, missed runs, and failures alert correctly |

**The ransomware drill** (the demo for every client meeting):

1. Back up the practice VM to the locked bucket
2. Acting as the attacker on the VM, use the same restricted key the backup uses and try to destroy the backups: delete snapshots through Kopia, then delete objects directly with the AWS CLI pointed at the B2 S3 endpoint
3. Record what happens. Expected: deletes of locked object versions fail. Some operations may only hide files (a delete marker) instead of removing them
4. Recover: connect to the repository as it was before the attack with `--point-in-time` (section 7.3) and restore a file
5. Also test overwritten repository metadata, rejected lock shortening, disabled jobs, absent sources, revoked keys, loss of the original PC, and maintenance/lock renewal over time. Use synthetic data and time-bounded disposable test buckets; do not incur long compliance locks unnecessarily.
6. Write up the synthetic-data result for the VISI blog. "We tried to delete our own backups and here's what stopped us" is a portfolio piece

### 5.3 Kit builder (later)

A small form where a student enters a client's setup (code, folders, schedule, retention) and gets a filled in checklist and the `Invoke-VisiBackup.ps1` configuration from section 6.6, with no secrets in it. A baseline runner and configuration example now exist; build the client form after two or three clients, when the checklist has settled. Until then, the checklist in this doc is the kit.

---

## 6. Client setup runbook: package 1 (Kopia + B2)

Plan about 90 minutes per office for the first computer, 20 to 30 for each additional one. The client sits at the keyboard for every step that involves a password or key.

### 6.1 Before the visit

- Signed agreement (section 9) and an intake ticket in JSM
- List of computers, and which folders matter on each. Ask: "If this computer burned tonight, what would you need tomorrow?"
- Microsoft 365 / Google Workspace question asked and answered (section 2)
- Check supported Windows version, free disk space, upload bandwidth, device sleep patterns, and the person responsible for leaving it online
- Record RPO/RTO, folder inclusions/exclusions, recovery order, application exports, cloud-only files, and client approval. OneDrive placeholders and mapped drives may be unavailable under SYSTEM; test actual sources under the task identity. Network sources need a separately scoped credential design
- Confirm two authorized client recovery custodians where feasible; keep MFA recovery codes and the repository password off the protected PC
- Do not mark onboarding complete until the initial upload and independent restore have passed; the first appointment may finish before that

### 6.2 The client's B2 account and bucket

1. The client creates a Backblaze account with **their business email**, and turns on two factor authentication
2. The client adds their card and sets a **cap and alert** in B2 billing, and learns which cap can stop uploads/downloads. Caps can break backups and cannot erase locked-storage charges; set warning thresholds before limits and test the resulting alerts
3. For each computer, create a separate **private** bucket, name it with no business name in it (for example `bk-` plus random characters), and **enable Object Lock when creating it**. Kopia needs the bucket created with Object Lock on. No default retention is needed; Kopia sets the lock on each file
4. Write down the bucket's **S3 endpoint** from the bucket page (looks like `s3.us-west-004.backblazeb2.com`)

### 6.3 The restricted key

Backblaze's website can't create a key with exactly the permissions Kopia needs, so this uses the B2 command line tool, on the client's machine, during the visit.

1. Inventory existing integrations before changing account credentials. In the B2 web console, the client generates the account master application key for this setup only; do not describe it as an independently disposable extra master key
2. Install the B2 CLI, set `B2_APPLICATION_KEY_ID` and `B2_APPLICATION_KEY` to the master key for this one terminal session
3. Create the restricted key (this is the command from Kopia's ransomware protection docs):

```
b2 create-key --bucket <bucket-name> <key-name> listBuckets,readBuckets,listFiles,readFiles,writeFiles,readBucketEncryption,readBucketReplications,readBucketRetentions,readFileRetentions,writeFileRetentions,readFileLegalHolds
```

- `--bucket <bucket-name>`: the key only works on this one bucket
- `listBuckets,readBuckets`: lets Kopia find the bucket
- `listFiles,readFiles`: lets Kopia read the repository, which it needs for deduplication and for restores
- `writeFiles`: lets Kopia upload new backup data
- `readBucketEncryption,readBucketReplications,readBucketRetentions`: read only views of bucket settings
- `readFileRetentions,writeFileRetentions`: lets Kopia set the lock date on each file and push it further out over time
- `readFileLegalHolds`: read only
- **What's missing on purpose:** `deleteFiles`, and anything that changes bucket settings or other keys. Software running on the client's computer, including ransomware, can't use this key to delete what's already there

Newer B2 CLI versions renamed several commands. If the CLI says `create-key` is deprecated, use the replacement it names; the capability list stays the same.

4. The output shows the new key ID and secret **once**. The client pastes them straight into the Kopia step below. Nobody writes them in the ticket
5. Revoke the setup master credential by regenerating it after reviewing dependencies. Clear environment variables, CLI credential caches, clipboard, and any shell history/transcripts containing secrets; closing a window alone is not sufficient. Review other keys for excessive access, but do not revoke unrelated production integrations without an approved migration. Use the pinned CLI version's documented logout/cache-removal procedure

### 6.4 Create the Kopia repository

Install the Kopia CLI from the official GitHub releases into `C:\Program Files\Kopia\`. Install KopiaUI too; it's what the client uses for restores later.

Make a folder for the config and lock it down, from an **elevated** PowerShell:

```powershell
New-Item -ItemType Directory -Path C:\ProgramData\VISI-Backup
icacls C:\ProgramData\VISI-Backup /inheritance:r /grant:r "Administrators:(OI)(CI)F" "SYSTEM:(OI)(CI)F"
```

- `/inheritance:r` removes permissions inherited from `C:\ProgramData`, where every user can read
- `/grant:r ... (OI)(CI)F` gives Administrators and SYSTEM full control, applied to files (`OI`) and subfolders (`CI`). Standard users get nothing, so they can't read the saved repository password

Create the repository (the client types the password when prompted). The example illustrates arguments, not a safe method for entering real secrets: use the installed version's supported environment/credential-input mechanism, clear it afterward, and avoid secrets in command history, transcripts, screenshots, or tickets. Verify both ACLs and unattended password access in the lab before using client data:

```powershell
& "C:\Program Files\Kopia\kopia.exe" repository create s3 `
  --config-file=C:\ProgramData\VISI-Backup\repository.config `
  --bucket=<bucket-name> `
  --endpoint=<s3-endpoint> `
  --access-key=<restricted-key-id> `
  --secret-access-key=<restricted-key-secret> `
  --retention-mode=COMPLIANCE `
  --retention-period=30d `
  --override-username=backup `
  --override-hostname=<client-code>-<pc-name>
```

- `repository create s3`: uses Kopia's S3 engine against B2's S3 endpoint. This is the only way to get Object Lock with B2; Kopia's native `b2` engine doesn't support it
- `--config-file`: puts the connection settings in the locked folder instead of one user's profile, so the scheduled task (running as SYSTEM) can use them
- `--endpoint`: the S3 endpoint from 6.2, without `https://`
- `--retention-mode=COMPLIANCE`: once a file is written, **nobody** can delete it before its lock date, not even the client's own master key. Kopia's docs recommend COMPLIANCE. The cost: data stays billed until its lock expires, even if you'd like it gone
- `--retention-period=30d`: each file is locked for 30 days, extended over time (6.5). This is the window to notice an attack. Thirty days balances protection against paying for extra storage
- `--override-username` and `--override-hostname`: give snapshots and maintenance a fixed identity, so it doesn't matter whether the admin or SYSTEM runs the command. Without this, maintenance silently never runs under the scheduled task (6.5)
- The password prompt: the client types a long passphrase. It encrypts everything before it leaves the machine. **The student looks away**

Then the client writes the passphrase on the **recovery card** (section 9) and it goes wherever they keep important papers.

**Check where the password was saved.** Kopia saves it so scheduled runs don't prompt. List `C:\ProgramData\VISI-Backup\`; validate in the practice range exactly which files appear next to the config. If the password went to a per user store instead, a SYSTEM task can't read it, and the setup has to change before going live.

**About the saved password:** anyone with admin rights on this PC can read it and decrypt the backups. Treat compromise as exposure of historical backup contents too, including files no longer on the PC. Unattended encryption does not protect against an administrator-level attacker on the endpoint. Object Lock protects retained versions from deletion while the locks remain valid; it does not prevent theft, forged success reports, upload abuse, or interruption of future backups.

### 6.5 Lock extension, maintenance, and policies

**Three separate controls:** snapshot retention selects restore points; Object Lock protects object versions temporarily; bucket lifecycle rules clean up obsolete versions. None substitutes for the others. Pilot defaults: 30-day locks and 60 days before deleting hidden/noncurrent versions. The extra lifecycle margin is a proposed operating choice, not a guaranteed recovery window. Preserve current versions indefinitely—never expire them solely by upload age. Start with keep-all-versions until cleanup is tested; then validate the exact B2 rule on synthetic data before applying it. Otherwise storage may grow indefinitely or recovery history may be destroyed. [Lifecycle rules](https://www.backblaze.com/docs/cloud-storage-lifecycle-rules), [lock behavior](https://www.backblaze.com/blog/digging-deeper-into-object-lock/)

Record successful full maintenance and check actual object retain-until dates weekly during the pilot, then at a documented interval safely inside the lock window. Missing renewals are urgent even when snapshots report success. An offline laptop cannot renew indefinitely; prolonged-offline clients need a separate maintenance design before acceptance. Do not put broader cloud credentials on the endpoint to solve cleanup failures.


```powershell
$k = "C:\Program Files\Kopia\kopia.exe"
$c = "--config-file=C:\ProgramData\VISI-Backup\repository.config"

& $k $c maintenance set --extend-object-locks true
& $k $c maintenance info
```

- `--extend-object-locks true`: by default Kopia doesn't renew lock dates, so after 30 days old data would be unprotected. This makes maintenance push lock dates forward on everything still in use
- Kopia requires the full maintenance interval to be at least 1 day shorter than the retention period, or it won't allow lock extension. The default full interval is short (check it in `maintenance info`), so 30 days leaves plenty of room
- `maintenance info`: confirm the **owner** is `backup@<client-code>-<pc-name>`. Kopia runs maintenance automatically after other commands, but only when the current identity is the owner. If the owner shows something else, run `maintenance set --owner=me` with the same `--config-file`

Policies:

```powershell
& $k $c policy set --global --keep-latest=10 --keep-hourly=0 --keep-daily=30 --keep-weekly=8 --keep-monthly=12 --keep-annual=0 --compression=zstd
& $k $c policy set --global --enable-volume-shadow-copy=when-available
```

- `--keep-hourly=0` and `--keep-annual=0` explicitly disable those inherited defaults. The tested policy script also disables ignored file/directory errors and identical-snapshot suppression. Inspect effective per-source overrides.
- `--keep-*`: how many snapshots to keep: the last 10, one a day for 30 days, one a week for 8 weeks, one a month for a year. Retention makes snapshots eligible for removal; their data remains billed while still referenced, locked, or waiting for lifecycle cleanup. Lock expiry does not itself delete objects
- `--compression=zstd`: compresses before upload. Documents and spreadsheets shrink a lot; photos and PDFs barely change
- `--enable-volume-shadow-copy=when-available`: requests Windows shadow copies, but allows fallback if unavailable. It does not by itself establish application-consistent recovery for an open database or PST. Needs admin rights, which SYSTEM has. Confirm the flag name with `kopia policy set --help` on the installed version

**QuickBooks Desktop and other databases:** use vendor-supported backup/export procedures, protect those outputs, and test opening/restoring them in the application. Do not promise recoverability from a live file copy. If VSS is required, fail the job when VSS is unavailable using the validated policy, rather than silently accepting fallback. [VSS consistency](https://learn.microsoft.com/en-us/windows/win32/vss/shadow-copies-and-shadow-copy-sets)

Add exclusions for junk that wastes storage (temp folders, `node_modules`, game installs) with `policy set <path> --add-ignore <pattern>`.

### 6.6 First snapshot, then the scheduled task

Run the first snapshot by hand and watch it finish (the first upload can take hours on a slow connection; start it during the visit and let it run overnight):

```powershell
& $k $c snapshot create "D:\Shared" "C:\Users\FrontDesk\Documents"
```

Create the check in Healthchecks (5.1), then configure the version-controlled `scripts/Invoke-VisiBackup.ps1` using `config/backup.example.json`. This supersedes the original inline wrapper. It requires PowerShell 7.4+ (tested on 7.7.0), a preconnected repository, and protected config/state directories. Read `README.md` for invocation, configuration, exit codes, and deployment prerequisites.

The runner tests source availability, backs up each source separately, validates new snapshot manifests including read-error counts, enforces a deadline, prevents overlapping runs, and writes a sanitized local result. It sends bodyless start/success/failure pings with a run ID; errors in monitoring do not stop the backup. A monitoring failure produces a distinct exit code even when backup succeeds. Local tests use synthetic files and a loopback HTTP recorder; real Healthchecks delivery still needs testing.

Do not copy the Linux test credentials or `-AllowLocalTestEndpoint` switch into a client setup. Detailed instructions for the pending Windows and B2 gates are in `docs/windows-and-b2-acceptance.md`.

Kopia keeps its own detailed logs on the machine. When a run fails, a student reads them **with the client present**, on the client's screen.

**Task Scheduler** (Create Task, not Create Basic Task):

| Setting | Value | Why |
|---|---|---|
| Run as | `SYSTEM` | Reads every user's files, has the rights for shadow copies, and doesn't need a stored Windows password |
| Run whether user is logged on or not | Checked | Backups happen overnight with nobody logged in |
| Run with highest privileges | Checked | Needed for shadow copies |
| Trigger | Daily, after closing time | Files are idle |
| Action | `"C:\Program Files\PowerShell\7\pwsh.exe" -NoLogo -NoProfile -NonInteractive -File C:\ProgramData\VISI-Backup\Invoke-VisiBackup.ps1 -ConfigFile C:\ProgramData\VISI-Backup\backup.json` | Use PowerShell 7 and the tested wrapper; respect the machine execution policy. `Export-VisiTaskXml.ps1` generates a disabled task for review |
| Run task as soon as possible after a scheduled start is missed | Checked | A laptop that was off at 9 pm backs up when it's next on |
| Stop the task if it runs longer than | Measured steady-state limit; 8 hours is only a starting estimate | Give initial uploads a separate window; alert on hangs |
| If task is already running | Do not start a new instance | Avoid overlapping backup/maintenance jobs |
| Restart after failure | Bounded retries within the recovery objective | Do not hide repeated failures with endless retries |

Laptops: also check "Wake the computer to run this task" only if the client agrees, and uncheck "Start the task only if the computer is on AC power" for machines that live on battery.

### 6.7 Verify before leaving

```powershell
& $k $c snapshot list
& $k $c snapshot verify --verify-files-percent=10
```

- `snapshot list`: shows each snapshot with its time and size
- `snapshot verify --verify-files-percent=10`: checks that the repository's structure is intact and fully downloads and decrypts a random 10% of files. It proves the data in B2 is readable, not just present

A sampled verification is useful evidence, not proof of full recoverability. Inspect warnings, source coverage, snapshot age, and application export results locally.

Then:

1. **Test restore with the client driving** (section 7.1): pick one real file, restore it to the desktop, open it
2. Run the scheduled task once by hand from Task Scheduler and watch the check turn green in Healthchecks
3. From a clean second machine, use only the recovery packet and newly issued credentials to restore representative critical data; do not depend on the original PC
4. Fill in and hand over the recovery card (section 9). Reviewer signs acceptance only after the upload, task-identity test, lock inspection, and restore pass

---

## 7. Restores

### 7.1 Single file (most common)

KopiaUI → connect to the existing repository using the same bucket, endpoint, key and password (or point it at the existing config) → Snapshots → pick the folder and time → browse → restore the file to a new location. Restore to a new location, never on top of the original, so a wrong pick doesn't overwrite good data.

Command line equivalent (use the snapshot root object ID from `snapshot list --json`, field `rootEntry.obj`; restore into a new destination):

```powershell
& $k $c snapshot list "D:\Shared"
& $k $c snapshot restore <root-object-id>/<path-inside-snapshot> C:\Restore\
```

### 7.2 Lost or dead computer

On the replacement computer: install Kopia, connect to the same bucket with the restricted key and the passphrase from the recovery card, restore the folders. This is why the recovery card matters: without the passphrase and the bucket details, there is nothing to connect to.

### 7.3 After ransomware

1. **Isolate the infected device and notify the owner/supervisor.** Preserve evidence and seek incident-response help as appropriate. Do not wipe the only evidence or connect to backups from that machine. Use a known-clean recovery environment
2. Get a time from before the attack started
3. Connect to the repository **as it was at that time**:

```powershell
kopia repository connect s3 --bucket=<bucket> --endpoint=<s3-endpoint> --access-key=<key-id> --secret-access-key=<secret> --point-in-time=2026-11-01T00:00:00Z
```

- `--point-in-time`: Kopia reads the object versions that existed at that moment, ignoring anything the attacker added or "deleted" (hid) later. Recovery depends on the required versions still being retained and intact; Object Lock is time limited, not a guarantee of every historical restore point
4. From a clean device, secure the cloud account and revoke compromised credentials promptly; issue a restricted recovery credential before restoring. Keep the recovery connection separate and avoid maintenance on the incident repository. Validate restored data before reconnecting production
5. Treat the repository password as exposed if the endpoint was compromised. A password change does not undo prior access or historical exposure. Establish a fresh repository with fresh secrets for ongoing backups and preserve the old one for incident/recovery needs; involve the supervisor in retention decisions

This is the drill from section 5.2. Students run it in the range until it's routine.

### 7.4 Quarterly restore drill (the recurring service)

- Every quarter, a student schedules a restore drill with the client; allow enough time for the workload, not a fixed 15-minute promise
- The client restores one file chosen on the spot, opens it, and confirms it's right
- The student checks Healthchecks history for the quarter and B2 storage use
- Record date, asset code, test category, restore-point age, elapsed time, outcome, and attendees. Keep filenames/content in the client's own record; VISI records a sanitized test ID. This contributes evidence toward CIS Safeguard 11.5, not certification
- Rotate through critical data classes and application exports. At least annually and after major changes, repeat clean-machine recovery; test image boot and SaaS recovery where included

---

## 8. Package 2 add on: local recovery copy

Deferred until a tool is approved for this third-party service and a full recovery is demonstrated. Veeam Free is not the default (section 3). A paid product also needs appropriate service rights; price alone does not establish permission.

- Agree whether the client needs file recovery or a full system image. Do not promise an hour to rebuild a computer without measuring the entire recovery.
- Encrypt removable backup media and keep the recovery secret off the computer. Verify the installed edition supports the chosen encryption and restore workflow.
- For offline protection, assign a named client custodian to rotate/disconnect media and keep a copy away from the office. A permanently attached drive or writable NAS share is exposed to endpoint compromise.
- Create recovery media, record required drivers and application licenses, and test boot and restoration on a spare device/VM suited to the test. Revalidate after significant OS/hardware changes.
- Monitor local-copy freshness separately from the cloud job. Document who checks that the client actually connects and rotates the drive.

---

## 9. Paperwork

### Agreement (add to the clinic agreement, attorney review before launch)

- The client owns the cloud account, backup contents, and passphrase. VISI retains only the service records and monitoring metadata described here; authorized support may expose content on screen
- If the client loses the passphrase, the backups can't be recovered by anyone
- Define covered systems, exclusions, support hours, response targets, client duties, student supervision, permission to view data during support, and incident escalation. No 24/7 response or guaranteed recovery is offered in the pilot; a disclaimer does not replace operating procedures
- The client is responsible for the cloud bill
- The monitoring wrapper sends start/success/failure pings; VISI retains check identifiers, timing, source IP, and the separately disclosed service records. Native exit codes stay on the client machine
- Either side can end the service. First test independent client access and transfer monitoring responsibility; remove VISI alerts/access and ping URLs while keeping backup jobs running. Do not delete repositories or revoke backup credentials merely because service ends. Explain continuing cloud charges and non-cancellable lock periods
- Specify incident/privacy notification handling, record retention/deletion, third-party providers, and any insurance or special contractual requirements with counsel before launch. Do not claim regulatory compliance based on encryption alone

### Recovery card (the client keeps it; VISI keeps no copy)

- B2 account email and where the login is stored
- Bucket name and S3 endpoint
- Restricted key ID (the secret is in the repository config on each PC; if every PC is lost, the client creates a new key from their B2 account)
- **The Kopia passphrase for each repository**, with a second protected copy in a separate location or client-controlled password manager accessible after device loss
- MFA recovery codes and authorized backup custodian; avoid keeping every recovery factor only in the same account or office
- Which folders on which computers are backed up
- VISI contact for help: `contact@visiutrgv.org`

### Handoff packet

- One page "how to restore a file" in English and Spanish, with screenshots of KopiaUI
- The recovery card
- The restore drill log, started with the setup day test

### CIS Controls v8 mapping (feeds the Checkup report)

| Safeguard | Covered by |
|---|---|
| 11.1 Data recovery process | The handoff packet plus this runbook |
| 11.2 Automated backups | Scheduled task, monitored by Healthchecks |
| 11.3 Protect recovery data | Encryption before upload, restricted key, locked down config folder |
| 11.4 Isolated instance of recovery data | Object Lock in a separate cloud account; the unplugged USB image in package 2 |
| 11.5 Test data recovery | Quarterly restore drill log |

This is a supporting evidence map, not automatic closure of safeguards or a compliance certification. Assess the client's whole in-scope environment, coverage gaps, and measured recovery results. [CIS Control 11](https://www.cisecurity.org/controls/data-recovery)

---

## 10. Costs, worked example

A 4 person office, 3 PCs, about 200 GB of files that matter.

| Item | Cost |
|---|---|
| B2 storage, 200 GB plus versions kept by the 30 day lock (estimate 1.5x) ≈ 300 GB | ≈ $2 a month ($6.95 per TB, first 10 GB free) |
| Kopia and Healthchecks software | No license fee; administration and hosting still cost staff time |
| Image-backup software | Quote only after service licensing is approved |
| USB drive for package 2 | One time, about the price of a 1 to 2 TB external drive |
| Same office on package 4 (Backblaze Business Backup) | $99 × 3 = $297 a year |
| Microsoft 365 Backup for 60 GiB of billable protected content | 60 × $0.15 = $9 a month |

The 1.5× storage multiplier is an illustration, not a sizing rule. Yearly snapshots, changed/deleted data, noncurrent versions, compression, and cleanup lag determine actual usage. Measure after 30 and 90 days; test a high-change scenario and agree on alert thresholds.

Budget nonprofit costs separately: owner review, student training and supervision, recurring triage/drills, server power/storage, offsite monitor backups, SMTP/external monitoring, and legal/insurance administration. Track hours per client during the pilot before setting enrollment limits or sponsorship/fee levels. A free service is a funding choice, not a zero-cost operation.

---

## 11. Student roles

| Role | Does |
|---|---|
| Setup lead | Runs the visit from 6.1 to 6.7 with the client driving |
| Shadow | Takes setup notes (no keys, no passwords), learns the runbook |
| Monitoring analyst | Watches Healthchecks alerts, contacts the client when a check goes red |
| Drill lead | Runs the quarterly restore drills |
| Reviewer | A different person checks each setup against the checklist before the case is marked done |

The owner is the accountable service lead, approves scope and exceptions, and handles incidents. Trained students can execute approved runbooks; credential, retention, deletion, and recovery changes require supervisor review. Students use individual accounts, least privilege, confidentiality training, and no personal storage/screenshots of client material. Remove access promptly at graduation or role changes.

New students demonstrate setup, clean-machine restore, and the ransomware drill before client work. Keep a skills sign-off and a second-person review. Provide coverage over exams, holidays, and turnover; an unattended mailbox is not monitoring.

### 11.1 Pilot operating commitments

These are proposed internal targets to confirm with the owner before enrollment, not an advertised SLA:

| Event | Owner and action |
|---|---|
| Every business day | Assigned analyst reviews failed/missing jobs; backup supervisor covers absence |
| Failed/missed job | Acknowledge by the next business day, notify the client, and track until a successful backup or documented pause |
| No good backup for 48 hours, suspected attack, or lock-renewal risk | Escalate to owner immediately when discovered; agree a recovery/protection action with client |
| Evenings/weekends/breaks | Client receives direct alerts and written self-help/escalation instructions; staff response only during agreed hours unless separately arranged |
| Monthly | Review recurring failures, storage/billing, coverage changes, and maintenance/lock evidence; report unresolved protection gaps |
| Quarterly | Restore drill, permissions review, and monitoring recovery test |

Send alerts to the owner/backup contact and client by default, with consent; test delivery and avoid sensitive details in messages. Record alert ownership and next action, not just a green dashboard. Pilot with two or three businesses; expand only when staffing can sustain the measured workload and holiday coverage.

Proposed privacy schedule: retain raw monitoring metadata for 90 days and sanitized service/drill records through the service term plus 12 months, subject to the final agreement and applicable obligations. Limit access by client assignment; document when backup copies of these records age out. Client data and real incident details never go into teaching materials or portfolios without separate informed authorization.

---

## 12. Open decisions

- **SMTP relay** for Healthchecks alert email
- **Confirm support hours and coverage roster;** default to client and VISI alerts with consent (11.1)
- **LXC ID and IP** for Healthchecks
- **Uptime Kuma or Healthchecks** for the hub's uptime page: if "uptimechecker" is Uptime Kuma, decide whether to keep both
- **Retention period:** 30 days COMPLIANCE is the starting point; revisit after the first few clients' bills
- **Legal review** of the agreement additions, same reviewer as the email service
- **Mac clients:** defer until a separate runbook covers launchd, permissions/Full Disk Access, sleep behavior, secrets, and clean-machine restores; validate before accepting the first Mac

---

## 13. Build order

1. Practice range: VMs, VISI practice bucket, Kopia setup per section 6, the ransomware drill. Fix this guide wherever reality differs
2. Healthchecks LXC and the two tunnel hostnames
3. Bilingual handoff packet and recovery card template
4. Agreement additions, legal review
5. First client, package 1, with a reviewer present
6. Package 2 only after licensing approval and measured bare-metal recovery
7. Kit builder after three clients

---

## 14. Launch acceptance checklist

- [ ] Owner names the primary and backup supervisors, service hours, client limit, and break coverage.
- [ ] Agreement, privacy terms, recovery objectives, cost responsibility, and escalation contacts are finalized.
- [ ] Approved versions and licenses are recorded; scripts tested under the actual scheduled identity after reboot with no user logged in.
- [ ] Missing sources, partial reads, VSS failures, network loss, credential revocation, and stopped monitor/SMTP all produce actionable failures.
- [ ] Initial backup and clean-machine restore pass; client can recover without VISI or the original PC.
- [ ] Actual object locks and renewal are verified; synthetic attack and point-in-time recovery pass.
- [ ] Lifecycle cleanup is validated across its real retention interval; until then retain all versions and disclose the extra cost.
- [ ] Monitoring is isolated from the lab, externally watched, backed up, and restored successfully.
- [ ] Reviewer signs the client scope, recovery packet, alert delivery, and outstanding exceptions.

No client deployment or command execution against live infrastructure was performed during this document review. Windows, cloud, and NAS behavior remains subject to the lab acceptance tests above.

---

## Sources and verification notes

Primary references checked for this revision; links describe upstream behavior, not proof that VISI's deployment works:

- [Kopia ransomware protection](https://kopia.io/docs/advanced/ransomware-protection/) — S3/B2 access restrictions, locks, maintenance, and historical recovery. Original command examples retained as lab candidates.
- [Kopia policy flags](https://kopia.io/docs/reference/command-line/common/policy-set/) — snapshot policy and VSS options.
- [Backblaze lifecycle rules](https://www.backblaze.com/docs/cloud-storage-lifecycle-rules) and [Object Lock](https://www.backblaze.com/docs/en/cloud-storage-object-lock) — retention and cleanup are separate controls.
- [B2 pricing](https://www.backblaze.com/cloud-storage/pricing), [Computer Backup pricing](https://www.backblaze.com/cloud-backup/pricing), and [passphrase handling](https://www.backblaze.com/computer-backup/docs/data-encryption-and-passphrases).
- [Veeam licensing policy](https://www.veeam.com/legal/licensing-policy.html) and [EULA](https://www.veeam.com/legal/eula.html) — third-party service restrictions.
- [Synology Active Backup backup/relink procedure](https://kb.synology.com/en-me/DSM/tutorial/How_to_backup_and_relink_Active_Backup_for_Business_with_DSM_backup_packages).
- [Microsoft 365 Backup billing](https://learn.microsoft.com/en-us/microsoft-365/backup/backup-pricing) and [VSS consistency](https://learn.microsoft.com/en-us/windows/win32/vss/shadow-copies-and-shadow-copy-sets).
- [Healthchecks configuration](https://healthchecks.io/docs/self_hosted_configuration/), [ping API](https://healthchecks.io/docs/http_api/), and [official Docker image](https://hub.docker.com/r/healthchecks/healthchecks).
- [CIS Control 11](https://www.cisecurity.org/controls/data-recovery).
