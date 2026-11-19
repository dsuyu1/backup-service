# VISI backup service: script laboratory

This is an implementation starter for the reviewed nonprofit backup plan. **Lab candidate, not yet approved for client installation.** Tests use synthetic data only. No Windows VM, B2 bucket, client account, or production monitor was configured.

## Implemented

| File | Purpose |
|---|---|
| `scripts/Invoke-VisiBackup.ps1` | Back up each configured directory, validate the new manifest, send bodyless status pings, and write a local result |
| `scripts/Set-VisiKopiaPolicy.ps1` | Apply explicit snapshot retention/error-handling defaults to an already-connected repository; supports `-WhatIf` |
| `scripts/Export-VisiTaskXml.ps1` | Generate a disabled SYSTEM scheduled-task XML file for review; does not install it |
| `config/backup.example.json` | Placeholder configuration, with no real credentials |
| `tests/test_backup.py` | PowerShell process/fault tests plus real encrypted Kopia backup, verification, and restore |
| `tests/test_artifacts.py` | PowerShell syntax and generated task/config checks |
| `docs/windows-and-b2-acceptance.md` | Next-stage lab setup and acceptance evidence |
| `docs/test-results.md` | Recorded results and explicit limits |

## Run the tests on this Linux workstation

Python 3.12+ and the pinned local tools are required. The already-downloaded tools are under `.tools/` and are excluded from git. They were downloaded from the publishers' GitHub releases and checked against their SHA-256 asset digests. On another Linux x64 workstation, install them with:

```bash
python3 tests/bootstrap_tools.py
```

Then, from the project directory:

```bash
python3 -m unittest discover -s tests -v
```

The suite uses PowerShell 7.7.0 and Kopia 0.23.1. Scripts require PowerShell 7.4 or newer; only the recorded version has been tested. Windows PowerShell 5.1 (`powershell.exe`) is not supported. Override tool paths with `VISI_TEST_PWSH` and `VISI_TEST_KOPIA` if needed, but the version check intentionally rejects an unapproved Kopia release.

Tests create disposable temporary directories, a local loopback HTTP recorder, and synthetic repository credentials in child-process environments. Each test cleans up its own fixtures. No B2 credentials are required. The suite must run as an ordinary user for the unreadable-file test to be meaningful. Local filesystem tests do **not** emulate cloud immutability.

## Runner contract

Provide an absolute `-ConfigFile` path to a JSON file based on the example. Production ping URLs must use HTTPS; `-AllowLocalTestEndpoint` permits HTTP only on loopback for tests. Redirects are not followed. Keep the actual ping URL private: it can be used to forge status reports.

The repository must already be connected under the eventual task identity, with unattended credential access proven. The runner never creates repositories, embeds passwords, modifies cloud keys, or changes retention. Credentials must not be placed in the JSON or command line. Kopia handles its own protected credential storage; the Windows SYSTEM behavior remains an acceptance gate.

All paths are absolute. A source must be a directory, and `minimumFileCount` must be at least one. `requiredFiles` are relative names of files that must exist before the backup starts (a useful source/mount sanity check). This does not prove those files survived exclusion rules; inspect effective policies and confirm recovery during onboarding. Choose meaningful per-client minimum counts. Empty-directory-only workloads need a separate policy.

One state directory belongs to one repository/job. It must already exist, be on a local filesystem, and be writable only by administrators/the service identity. The config, runner, repository credential/config files, and executable must also be protected against ordinary-user modification. Do not place state, cache, repository contents, or logs inside a backed-up source directory. Reject reparse/symlink substitutions in the Windows acceptance review. This release does not automatically provision or audit Windows ACLs.

The runner checks every source before starting, runs snapshots one at a time, and validates each newly created manifest. Nonzero native exits, malformed output, incomplete snapshots, read errors (including ignored errors), too few files, and mismatched snapshot IDs all fail the run. Only complete runs send a success ping. A filesystem lock prevents overlapping processes from racing status or result writes.

Detailed Kopia logs remain in `stateDirectory/kopia-logs` and can contain client paths. Retain/rotate them according to the agreement; unattended log rotation has not been implemented. `last-result.json` contains job/run IDs, timing, reason codes, snapshot IDs, and counts, but no source paths or keys. It is the latest result, not an audit-history database. The wrapper suppresses raw exceptions so ping secrets and paths do not appear in its console summary.

| Exit | Meaning |
|---|---|
| 0 | Backup and manifest checks succeeded; status pings delivered |
| 2 | Backup succeeded but a monitoring ping failed; investigate monitoring |
| 3 | Lock unavailable: another run or a state-storage problem; no status ping sent |
| 10 | Invalid configuration; no job started or status sent |
| 20 | Backup/prerequisite/version/manifest validation failure |
| 22 | Overall backup deadline exceeded; child process tree terminated |
| 24 | Local result could not be persisted; investigate state storage |

The deadline includes startup and source processing; ping requests have their own bounded timeout. Set the scheduler's termination limit above the runner deadline. A killed machine, corrupted configuration, or unlaunchable PowerShell cannot send a failure ping: the external missed-run alert is still necessary. Success pings are not independent proof of recoverability and can be forged by a compromised endpoint.

## Policy and task artifacts

Apply the policy only to an approved practice repository initially. `-VssMode never` is for Linux/synthetic testing; select and test `always` on Windows when VSS is required. `when-available` allows fallback. VSS is not an application-consistency guarantee. Per-source overrides can override global settings: inspect them before acceptance. This script configures neither lock extension nor B2 lifecycle rules.

The exported task uses PowerShell 7, SYSTEM, a daily machine-local schedule, missed-run catch-up, and no overlapping instances. It is disabled, does not bypass execution policy, does not wake the device, and starts on AC power by default. Review laptop behavior with the client. `-MaxRunHours` must match the runner's configured deadline; the task allows an additional two minutes. Generate an artifact without registering anything:

```powershell
./scripts/Export-VisiTaskXml.ps1 -OutputPath ./practice-task.xml
```

Do not import/enable this task on client systems until the Windows and B2 acceptance checklist passes. Use the practice VM first.

## Reference documentation

- [Kopia snapshot creation](https://kopia.io/docs/reference/command-line/common/snapshot-create/) and [verification](https://kopia.io/docs/reference/command-line/common/snapshot-verify/).
- [Healthchecks ping API](https://healthchecks.io/docs/http_api/) for bodyless HEAD requests and run IDs.
- [Microsoft PowerShell installation](https://learn.microsoft.com/en-us/powershell/scripting/install/alternate-install-methods).
- Exact CLI flags and JSON fields were also checked against the downloaded Kopia 0.23.1 executable. Revalidate the parser before upgrading.
