# Small Business Backup Service: Client Owned Cloud Backups with Ransomware Protection

- **Scope:** a free VISI clinic service that sets up automatic, encrypted, ransomware resistant backups for local businesses and nonprofits. The backups go straight from the client's computers to a cloud account the client owns. **VISI stores no client data, holds no client keys, and never sees the encryption password**
- **Written:** November 18, 2026
- **Status:** plan only. Nothing built. Every command in sections 6 to 8 gets validated in the practice range (section 5.2) before the first client
- **Why this service:** most small businesses either have no backup or have one nobody has tested. What they can't do alone is pick the tools, set up immutability so ransomware can't delete the backups, notice when backups quietly stop, and practice a restore. That follow-through is the service, same idea as the DMARC rollout
- **Companion docs:** `partner-email-security-service.md` (intake, "client drives, VISI guides" rule, agreement), `support-center.md` (the intake form), `contact-portal-and-help-center.md` (privacy and Discord rules), `master-timeline.md` section 4 (licenses), `backup-runbook.md` and `automated-backups.md` (VISI's own range backups, a different thing)

---

## 1. Ground rules

| Rule | Why |
|---|---|
| **The client owns the cloud account and pays the bill** | If VISI disappears tomorrow, the client still has every backup and full control |
| **The client types the encryption password and keeps it** | VISI can't leak what it never had. If the client loses it, nobody can recover the backups, including VISI. The agreement says this in plain words |
| **VISI never keeps a cloud key** | Same rule as the email service. Keys are created on the client's screen and pasted straight into the client's backup software |
| **The client clicks, the student guides** | In person or on a screen share. No remote access tools left behind |
| **No backup counts until a restore works** | Every setup ends with a test restore, and every client gets quarterly restore drills |
| **The only thing VISI's lab sees is "job ran" or "job failed"** | Health pings carry a check ID and an exit code. No file names, no logs, no data |

---

## 2. What we offer, by client type

| Package | For | What gets set up | Client's running cost |
|---|---|---|---|
| **1. Files to cloud** (default) | 1 to 10 Windows or Mac computers, maybe one shared folder | Kopia on each machine, backing up to the client's Backblaze B2 bucket with Object Lock. Health pings to VISI's monitor | B2 storage, usually a few dollars a month (section 10) |
| **2. Files to cloud plus local image** | Same, when a dead laptop would stop the business for days | Package 1, plus Veeam Agent for Windows Free making a full system image to a USB drive or NAS | One USB drive or NAS share |
| **3. Office with a Synology NAS** | Offices that already have one, or are buying one | Synology Hyper Backup from the NAS to B2, immutable snapshots on the NAS, Active Backup for the PCs | B2 storage plus the NAS |
| **4. Hands off** | Owners who will never look at a dashboard | Backblaze Business Backup on each computer, set up with a private encryption key. VISI only does setup and restore drills | $99 per computer per year |
| **SaaS add on** | Anyone whose files and email live in Microsoft 365 or Google Workspace | Advice and setup for Microsoft 365 Backup, or Synology Active Backup for M365 / Google Workspace if they have a NAS | See section 3.4 |

Package 1 is the launch. Packages 2 and 4 are small additions. Package 3 waits until a client actually has a Synology. The SaaS add on is advice first, hands on later.

**Ask about Microsoft 365 and Google Workspace in the first meeting.** Many small businesses keep most of their files and all their email there. Packages 1 to 4 don't cover that data, and the client needs to hear it on day one, not after a deleted mailbox.

---

## 3. Tool comparison

Researched November 18, 2026. Prices change; recheck before quoting a client.

### 3.1 File backup engines (computer to cloud)

| Tool | License | Immutability with B2 | Unattended on Windows | Verdict |
|---|---|---|---|---|
| **Kopia** | Open source (Apache 2.0) | Yes, through Object Lock using its S3 engine. The native B2 engine does not support locks | CLI plus Windows Task Scheduler. KopiaUI only runs schedules while it is open and the user is logged in | **Pick.** Encrypted, deduplicated, real lock support, GUI for restores |
| **restic** (with Backrest web UI) | Open source (BSD 2; Backrest GPL 3) | **No.** restic does not support Object Lock. Its append only option needs a rest server, which means someone hosts storage | Backrest schedules backups and can ping Healthchecks. An earlier Backrest README warned Windows gets less testing than Linux and macOS | Good for Linux servers. Not for this service, because the client machine's key could delete the backups |
| **Duplicati 2.3** | Open source core | Yes, remote file locking for B2 and S3 (`--b2-lock-mode`) | Yes, runs as a service with a web UI | **Fallback** for clients who want a friendlier GUI. Newer builds ship some proprietary modules that need a license in production, so check which features you depend on |
| **UrBackup** | Open source (AGPL 3) | Not a cloud tool; backs up to its own server | Yes | Only if the client has a box in the office to run the server. Then that server goes to B2. Too much to maintain for a 3 person office |
| **Backblaze Business Backup** | Commercial, $99 per computer per year | Managed by Backblaze; one year of version history | Yes, install and forget | **Package 4.** Simplest option. Costs more per machine and the client depends on one vendor's app |

### 3.2 Full system images (bare metal restore)

| Tool | Notes | Verdict |
|---|---|---|
| **Veeam Agent for Windows Free** | Free edition allows one backup job, to a local drive, network share, or Veeam repository. **No object storage targets.** Veeam's editions page also lists some schedule options as Server edition only, so check what Free offers on the installed version. A Veeam product manager confirmed on Veeam's forum that the free license can be used for your own company | **Pick for the local copy** in package 2. Not a cloud tool |
| **Macrium Reflect Free** | Retired January 1, 2024, and it was licensed for non commercial use only | Don't use |
| **Rescuezilla** | Open source, boots from USB, manual only | Good for a one time image before a risky change. Not a backup system |

### 3.3 NAS based (package 3)

| Tool | Notes |
|---|---|
| **Synology Hyper Backup** | Backs up NAS folders to B2 through the S3 compatible API. Backblaze documents the setup |
| **Synology immutable snapshots** | Point in time WORM snapshots on Btrfs volumes; not even an admin can remove them during the protection period. Requires a WORM capable model, so check the model before promising it |
| **Synology Active Backup for Business** | Backs up the office PCs to the NAS, then Hyper Backup sends that to B2 |

### 3.4 Microsoft 365 and Google Workspace

| Tool | Cost | Notes |
|---|---|---|
| **Microsoft 365 Backup** (Microsoft's own) | $0.15 per GB per month of protected content, billed through an Azure subscription | Covers OneDrive, SharePoint, Exchange. Simple, but per GB pricing adds up for large mailboxes |
| **Synology Active Backup for Microsoft 365 / Google Workspace** | License free on a Synology NAS | Best value if the client has or buys a NAS. Data lands on their NAS, then Hyper Backup sends it to B2 |
| **Corso** (open source M365 backup) | n/a | **Archived October 2024, no longer maintained.** Don't use |
| **Paid per user services** (Veeam, CrashPlan, others) | Roughly $2.50 to $4 per user per month | Mention as options; VISI doesn't resell anything |

### 3.5 Cloud storage

| Provider | Price | Catch | Verdict |
|---|---|---|---|
| **Backblaze B2** | $6.95 per TB per month, first 10 GB free, downloads free up to 3x what you store | Locks only through the S3 API with Kopia | **Pick** |
| **Wasabi** | $7.99 per TB per month | Bills at least 1 TB a month and at least 90 days per object. A client with 100 GB pays for 1 TB | Bad fit for small clients |
| **AWS S3 Standard** | About $23 per TB per month | Price, and AWS console complexity for a non technical owner | Only if the client already lives in AWS |
| **IDrive e2** | Annual plan listed at $29.75 for the first year per TB, $59.50 a year after | The first year price is a promo | Recheck terms and Object Lock support before recommending |

### 3.6 Monitoring

| Tool | Notes | Verdict |
|---|---|---|
| **Healthchecks** (self hosted) | Open source (BSD 3). Each job pings a URL; a missing or failed ping triggers an alert | **Pick.** It was built for exactly this |
| **Uptime Kuma push monitors** | Same idea, if the hub's "uptimechecker" turns out to be Uptime Kuma | Possible, but Healthchecks handles start/fail/exit codes and per client projects better |

---

## 4. How the pieces fit

| Where | What runs there | Holds client data? |
|---|---|---|
| Client computer | Kopia CLI, a scheduled task, the repo config and saved password | Yes, it's their machine |
| Client's B2 account | The encrypted backup repository, Object Lock on every file | Yes, encrypted with a password only the client has |
| VISI range: Healthchecks LXC | One check per client job. Receives "started", "succeeded", or "failed with exit code N" | **No.** Check names, timestamps, the client's public IP from the ping |
| VISI range: practice targets | Windows VM with fake business files, VISI's own practice B2 bucket | Fake data only |
| VISI JSM | Intake ticket, agreement, setup notes (no keys, no passwords) | Contact details only |

Name checks with a client code (`c014-frontdesk-pc`), not the business name. That way a leaked Healthchecks database doesn't reveal which local businesses VISI works with.

---

## 5. Lab components

### 5.1 Healthchecks behind the Cloudflare tunnel

**Placement:** a small LXC with Docker, same pattern as the other web apps. Pick a free ID with `pct list`. It needs well under 1 GB of RAM.

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
    image: healthchecks/healthchecks:v4.4   # pin a version; check Docker Hub for the newest
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
- `healthchecks/healthchecks:v4.4`: the official image. It runs the web app and the alert sender in one container and applies database migrations on start. Pinning a version means an upstream change can't break it on a random restart
- `ports: "<lxc-ip>:8000:8000"`: listens only on the LXC's own address, for `cloudflared` to reach. Nothing is exposed to the range network beyond that
- `SITE_ROOT`: the dashboard URL, used in alert emails
- `PING_ENDPOINT`: only changes how ping URLs are **displayed** in the dashboard. It does not change routing, which is why the tunnel rule below matters
- `ALLOWED_HOSTS`: Django refuses requests for any other hostname
- `REGISTRATION_OPEN: "False"`: nobody can sign up. Officers invite members to projects
- `EMAIL_*`: the SMTP relay for alerts. Which relay is an open decision (section 12)
- `SECRET_KEY` and `DB_PASSWORD` live in a `.env` file next to the compose file, `chmod 600`, never in git

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
- Integrations: email to the VISI backup team. Ask the client whether they want alerts too; if yes, add their email (Healthchecks sends a confirmation link first)

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
5. Write up the result for the VISI blog. "We tried to delete our own backups and here's what stopped us" is a portfolio piece

### 5.3 Kit builder (later)

A small form where a student enters a client's setup (code, folders, schedule, retention) and gets a filled in checklist and the `run-backup.ps1` from section 6.6, with no secrets in it. Build it after two or three clients, when the checklist has settled. Until then, the checklist in this doc is the kit.

---

## 6. Client setup runbook: package 1 (Kopia + B2)

Plan about 90 minutes per office for the first computer, 20 to 30 for each additional one. The client sits at the keyboard for every step that involves a password or key.

### 6.1 Before the visit

- Signed agreement (section 9) and an intake ticket in JSM
- List of computers, and which folders matter on each. Ask: "If this computer burned tonight, what would you need tomorrow?"
- Microsoft 365 / Google Workspace question asked and answered (section 2)
- Check Windows version and free disk space on each machine

### 6.2 The client's B2 account and bucket

1. The client creates a Backblaze account with **their business email**, and turns on two factor authentication
2. The client adds their card and sets a **cap and alert** in B2 billing, so a mistake can't run up a surprise bill
3. Create a **private** bucket, name it with no business name in it (for example `bk-` plus random characters), and **enable Object Lock when creating it**. Kopia needs the bucket created with Object Lock on. No default retention is needed; Kopia sets the lock on each file
4. Write down the bucket's **S3 endpoint** from the bucket page (looks like `s3.us-west-004.backblazeb2.com`)

### 6.3 The restricted key

Backblaze's website can't create a key with exactly the permissions Kopia needs, so this uses the B2 command line tool, on the client's machine, during the visit.

1. In the B2 web console, the client creates a temporary master application key
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
5. Clear the master key from the CLI session (close the terminal), then in the web console the client **deletes the temporary master key and regenerates the account master key**. Kopia's docs also say to delete any other application keys that don't have restricted access

### 6.4 Create the Kopia repository

Install the Kopia CLI from the official GitHub releases into `C:\Program Files\Kopia\`. Install KopiaUI too; it's what the client uses for restores later.

Make a folder for the config and lock it down, from an **elevated** PowerShell:

```powershell
New-Item -ItemType Directory -Path C:\ProgramData\VISI-Backup
icacls C:\ProgramData\VISI-Backup /inheritance:r /grant:r "Administrators:(OI)(CI)F" "SYSTEM:(OI)(CI)F"
```

- `/inheritance:r` removes permissions inherited from `C:\ProgramData`, where every user can read
- `/grant:r ... (OI)(CI)F` gives Administrators and SYSTEM full control, applied to files (`OI`) and subfolders (`CI`). Standard users get nothing, so they can't read the saved repository password

Create the repository (the client types the password when prompted):

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

- `repository create s3`: uses Kopia's S3 engine against B2's S3 endpoint. This is the only way to get Object Lock with B2; Kopia's native `b2` engine doesn't support it and is deprecated
- `--config-file`: puts the connection settings in the locked folder instead of one user's profile, so the scheduled task (running as SYSTEM) can use them
- `--endpoint`: the S3 endpoint from 6.2, without `https://`
- `--retention-mode=COMPLIANCE`: once a file is written, **nobody** can delete it before its lock date, not even the client's own master key. Kopia's docs recommend COMPLIANCE. The cost: data stays billed until its lock expires, even if you'd like it gone
- `--retention-period=30d`: each file is locked for 30 days, extended over time (6.5). This is the window to notice an attack. Thirty days balances protection against paying for extra storage
- `--override-username` and `--override-hostname`: give snapshots and maintenance a fixed identity, so it doesn't matter whether the admin or SYSTEM runs the command. Without this, maintenance silently never runs under the scheduled task (6.5)
- The password prompt: the client types a long passphrase. It encrypts everything before it leaves the machine. **The student looks away**

Then the client writes the passphrase on the **recovery card** (section 9) and it goes wherever they keep important papers.

**Check where the password was saved.** Kopia saves it so scheduled runs don't prompt. List `C:\ProgramData\VISI-Backup\`; validate in the practice range exactly which files appear next to the config. If the password went to a per user store instead, a SYSTEM task can't read it, and the setup has to change before going live.

**About the saved password:** anyone with admin rights on this PC can read it and decrypt the backups. That's unavoidable for unattended backups, and it's acceptable here because an attacker with admin rights already has the original files. What the attacker can't do is delete the locked backups, which is the point.

### 6.5 Lock extension, maintenance, and policies

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
& $k $c policy set --global --keep-latest=10 --keep-daily=30 --keep-weekly=8 --keep-monthly=12 --compression=zstd
& $k $c policy set --global --enable-volume-shadow-copy=when-available
```

- `--keep-*`: how many snapshots to keep: the last 10, one a day for 30 days, one a week for 8 weeks, one a month for a year. Old snapshots are removed by maintenance, and their data stays (and is billed) until its lock expires
- `--compression=zstd`: compresses before upload. Documents and spreadsheets shrink a lot; photos and PDFs barely change
- `--enable-volume-shadow-copy=when-available`: uses Windows shadow copies so open files (Outlook PSTs, a QuickBooks file left open) are copied in a consistent state. Needs admin rights, which SYSTEM has. Confirm the flag name with `kopia policy set --help` on the installed version

**QuickBooks Desktop:** even with shadow copies, the safest copy of a company file is one taken while it's closed. Schedule the backup after closing time, or also back up the backup file QuickBooks makes itself.

Add exclusions for junk that wastes storage (temp folders, `node_modules`, game installs) with `policy set <path> --add-ignore <pattern>`.

### 6.6 First snapshot, then the scheduled task

Run the first snapshot by hand and watch it finish (the first upload can take hours on a slow connection; start it during the visit and let it run overnight):

```powershell
& $k $c snapshot create "D:\Shared" "C:\Users\FrontDesk\Documents"
```

Create the check in Healthchecks (5.1) and copy its UUID. Then save this as `C:\ProgramData\VISI-Backup\run-backup.ps1`:

```powershell
$Kopia   = "C:\Program Files\Kopia\kopia.exe"
$Config  = "--config-file=C:\ProgramData\VISI-Backup\repository.config"
$Ping    = "https://ping.visiutrgv.org/ping/<check-uuid>"
$Sources = @("D:\Shared", "C:\Users\FrontDesk\Documents")

try { Invoke-WebRequest -Uri "$Ping/start" -Method Head -TimeoutSec 10 -UseBasicParsing | Out-Null } catch {}

& $Kopia $Config snapshot create @Sources --no-progress
$code = $LASTEXITCODE

try { Invoke-WebRequest -Uri "$Ping/$code" -Method Head -TimeoutSec 10 -UseBasicParsing | Out-Null } catch {}
exit $code
```

Line by line:

- `$Ping/start`: tells Healthchecks the job began, so it can measure run time and alert if a run hangs
- `try { ... } catch {}`: if the internet or VISI's monitor is down, the backup still runs. Monitoring must never block a backup
- `-Method Head`: sends no body. **No log or file names ever go to VISI**, only the fact that a ping happened
- `snapshot create @Sources --no-progress`: backs up each folder; `--no-progress` keeps the output clean for a non interactive run
- `$LASTEXITCODE`: Kopia's exit code. 0 means success
- `$Ping/$code`: Healthchecks reads 0 as success and anything else as a failure, so a failed backup alerts right away instead of waiting for a missed ping
- `exit $code`: Task Scheduler's history shows the same result

Kopia keeps its own detailed logs on the machine. When a run fails, a student reads them **with the client present**, on the client's screen.

**Task Scheduler** (Create Task, not Create Basic Task):

| Setting | Value | Why |
|---|---|---|
| Run as | `SYSTEM` | Reads every user's files, has the rights for shadow copies, and doesn't need a stored Windows password |
| Run whether user is logged on or not | Checked | Backups happen overnight with nobody logged in |
| Run with highest privileges | Checked | Needed for shadow copies |
| Trigger | Daily, after closing time | Files are idle |
| Action | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\ProgramData\VISI-Backup\run-backup.ps1` | `-NoProfile` skips profile scripts; `Bypass` applies only to this run of this script |
| Run task as soon as possible after a scheduled start is missed | Checked | A laptop that was off at 9 pm backs up when it's next on |
| Stop the task if it runs longer than | 8 hours | A hung run ends, and the missing success ping triggers an alert |

Laptops: also check "Wake the computer to run this task" only if the client agrees, and uncheck "Start the task only if the computer is on AC power" for machines that live on battery.

### 6.7 Verify before leaving

```powershell
& $k $c snapshot list
& $k $c snapshot verify --verify-files-percent=10
```

- `snapshot list`: shows each snapshot with its time and size
- `snapshot verify --verify-files-percent=10`: checks that the repository's structure is intact and fully downloads and decrypts a random 10% of files. It proves the data in B2 is readable, not just present

Then:

1. **Test restore with the client driving** (section 7.1): pick one real file, restore it to the desktop, open it
2. Run the scheduled task once by hand from Task Scheduler and watch the check turn green in Healthchecks
3. Fill in and hand over the recovery card (section 9)

---

## 7. Restores

### 7.1 Single file (most common)

KopiaUI → connect to the existing repository using the same bucket, endpoint, key and password (or point it at the existing config) → Snapshots → pick the folder and time → browse → restore the file to a new location. Restore to a new location, never on top of the original, so a wrong pick doesn't overwrite good data.

Command line equivalent:

```powershell
& $k $c snapshot list "D:\Shared"
& $k $c snapshot restore <snapshot-id>\<path-inside-snapshot> C:\Restore\
```

### 7.2 Lost or dead computer

On the replacement computer: install Kopia, connect to the same bucket with the restricted key and the passphrase from the recovery card, restore the folders. This is why the recovery card matters: without the passphrase and the bucket details, there is nothing to connect to.

### 7.3 After ransomware

1. **Don't reconnect from the infected machine.** Clean or rebuild it first
2. Get a time from before the attack started
3. Connect to the repository **as it was at that time**:

```powershell
kopia repository connect s3 --bucket=<bucket> --endpoint=<s3-endpoint> --access-key=<key-id> --secret-access-key=<secret> --point-in-time=2026-11-01T00:00:00Z
```

- `--point-in-time`: Kopia reads the object versions that existed at that moment, ignoring anything the attacker added or "deleted" (hid) later. Object Lock guarantees those older versions still exist
4. Restore, then rotate the B2 key (the attacker may have it) and set up a fresh connection

This is the drill from section 5.2. Students run it in the range until it's routine.

### 7.4 Quarterly restore drill (the recurring service)

- Every quarter, a student schedules 15 minutes with the client
- The client restores one file chosen on the spot, opens it, and confirms it's right
- The student checks Healthchecks history for the quarter and B2 storage use
- Record date, file, result, and who was present. **This log is the client's evidence for CIS Safeguard 11.5** (section 9)

---

## 8. Package 2 add on: local image with Veeam Agent Free

The cloud copy protects files. A local image gets a dead laptop back to working, with apps and settings, in an hour instead of a day.

- Install Veeam Agent for Microsoft Windows; with no license installed it runs as the Free edition
- One backup job: **entire computer**, to a USB drive or a NAS share
- Free edition limits: one job, local or network targets only, no object storage. Veeam's editions page lists some schedule options as Server only, so set the job on whatever schedule Free offers on the installed version, or run it when the backup target is connected for a USB drive
- **Create the recovery media** (bootable USB) during setup and label it. Veeam reminds you to recreate it after major Windows updates
- A USB drive that stays plugged in can be encrypted by ransomware like any other drive. Tell the client to unplug it after the backup and keep it somewhere else. That makes it the offline copy
- The image is the client's data on the client's drive. VISI touches none of it

---

## 9. Paperwork

### Agreement (add to the clinic agreement, attorney review before launch)

- The client owns the cloud account, the data, and the passphrase. VISI keeps no copies of any of them
- If the client loses the passphrase, the backups can't be recovered by anyone
- VISI provides setup help and monitoring on a best effort basis, with no guarantee that backups or restores will succeed
- The client is responsible for the cloud bill
- VISI receives only job status pings (start, success, failure, exit code, and the source IP of the ping)
- Either side can end the service; at closeout VISI deletes the client's Healthchecks project and the client removes the scheduled task's ping URL

### Recovery card (the client keeps it; VISI keeps no copy)

- B2 account email and where the login is stored
- Bucket name and S3 endpoint
- Restricted key ID (the secret is in the repository config on each PC; if every PC is lost, the client creates a new key from their B2 account)
- **The Kopia passphrase**
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

Four of these five are IG1 safeguards. If the Checkup flags missing backups, this service closes them and leaves documentation behind.

---

## 10. Costs, worked example

A 4 person office, 3 PCs, about 200 GB of files that matter.

| Item | Cost |
|---|---|
| B2 storage, 200 GB plus versions kept by the 30 day lock (estimate 1.5x) ≈ 300 GB | ≈ $2 a month ($6.95 per TB, first 10 GB free) |
| Kopia, Veeam Agent Free, Healthchecks | $0 |
| USB drive for package 2 | One time, about the price of a 1 to 2 TB external drive |
| Same office on package 4 (Backblaze Business Backup) | $99 × 3 = $297 a year |
| Microsoft 365 Backup for 60 GB of mail and OneDrive | 60 × $0.15 = $9 a month |

Run the B2 number again after the first month using the client's actual bill; versions and the lock window change it.

---

## 11. Student roles

| Role | Does |
|---|---|
| Setup lead | Runs the visit from 6.1 to 6.7 with the client driving |
| Shadow | Takes setup notes (no keys, no passwords), learns the runbook |
| Monitoring analyst | Watches Healthchecks alerts, contacts the client when a check goes red |
| Drill lead | Runs the quarterly restore drills |
| Reviewer | A different person checks each setup against the checklist before the case is marked done |

New students practice the full runbook and the ransomware drill in the range before shadowing a real client.

---

## 12. Open decisions

- **SMTP relay** for Healthchecks alert email
- **Do clients get alerts directly,** or only VISI, who then calls them?
- **LXC ID and IP** for Healthchecks
- **Uptime Kuma or Healthchecks** for the hub's uptime page: if "uptimechecker" is Uptime Kuma, decide whether to keep both
- **Retention period:** 30 days COMPLIANCE is the starting point; revisit after the first few clients' bills
- **Legal review** of the agreement additions, same reviewer as the email service
- **Mac clients:** Kopia works on macOS, but this runbook is Windows only. Write the macOS scheduling section (launchd) when the first Mac client shows up

---

## 13. Build order

1. Practice range: VMs, VISI practice bucket, Kopia setup per section 6, the ransomware drill. Fix this guide wherever reality differs
2. Healthchecks LXC and the two tunnel hostnames
3. Bilingual handoff packet and recovery card template
4. Agreement additions, legal review
5. First client, package 1, with a reviewer present
6. Package 2 (Veeam) on the second or third client
7. Kit builder after three clients

---

## Sources

- Kopia ransomware protection (Object Lock, restricted B2 key, lock extension): https://kopia.io/docs/advanced/ransomware-protection
- Kopia actions and policy flags: https://kopia.io/docs/advanced/actions/ , https://kopia.io/docs/reference/command-line/common/policy-set/
- Kopia scheduling on Windows (KopiaUI only schedules while running): Kopia forum threads, kopia.discourse.group
- restic and Object Lock: restic forum, "Backblaze Object Lock / Ransomware protection"
- Backrest: https://github.com/garethgeorge/backrest
- Duplicati remote file locking: https://docs.duplicati.com/detailed-descriptions/using-remote-file-locking ; 2.3.0.0 stable release notes on forum.duplicati.com
- Veeam Agent Free limits: https://helpcenter.veeam.com/docs/agentforwindows/userguide/license_editions.html ; commercial use answer on forums.veeam.com
- Macrium Reflect Free retirement: ghacks.net, 2023
- Synology Active Backup for Google Workspace / Microsoft 365: synology.com ; Hyper Backup with B2: https://www.backblaze.com/docs/cloud-storage-integrate-synology-hyper-backup-with-backblaze-b2
- Microsoft 365 Backup pricing: https://learn.microsoft.com/microsoft-365/backup/backup-pricing
- Corso archived: github.com/alcionai/corso
- Backblaze B2 and Computer Backup pricing: backblaze.com pricing pages (B2 $6.95 per TB since 2026; Business Backup $99 per computer per year)
- Wasabi minimum storage duration: https://docs.wasabi.com/docs/how-does-wasabis-minimum-storage-duration-policy-work
- Healthchecks configuration and Pinging API: healthchecks.io docs (self hosted configuration, HTTP API)
- CIS Controls v8, Control 11: cisecurity.org
