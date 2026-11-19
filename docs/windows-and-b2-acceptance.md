# Next-stage acceptance: Windows and B2

Status: pending. The owner confirmed neither environment is ready. The local Linux tests are recorded separately; they do not satisfy these gates.

## 1. Build the practice environment

Use a supported Windows 11 VM with valid licensing on the existing server, isolated from client systems and production monitoring. Use synthetic business folders only. Make a clean VM checkpoint before installation. Prepare a second clean Windows VM for replacement-computer recovery; never rely on the original machine's credential store for that test.

Install a supported PowerShell 7 release and the approved Kopia CLI/UI from official releases, validating publisher signatures/checksums. Record versions. The current local test baseline is Kopia 0.23.1 and PowerShell 7.7.0. Revalidate if the Windows package version differs.

On the first VM, prepare `C:\ProgramData\VISI-Backup` as a protected local directory. Grant access only to SYSTEM and Administrators (use their SIDs to avoid localized-name issues); restrict inheritance and verify all child files, including logs/cache/credential files. Refuse an existing symlink/reparse destination. Confirm a standard Windows user cannot read secrets or modify the scripts/configuration. Keep Kopia and PowerShell binaries in administrator-controlled locations.

Copy the runner and an edited configuration there. Create its `state` subdirectory with the same protection. Set source paths, minimum file counts, required marker files, deadline, and the private ping URL. Do not put credentials in the JSON. Confirm the machine timezone is Central Time if its schedule is intended to follow America/Chicago, including daylight saving changes.

## 2. Establish an unattended local baseline first

Connect a synthetic local repository and apply the baseline policy. Verify effective policies on every source. Test missing/locked files, skipped paths, unsupported file types, unavailable VSS, sleep, shutdown, battery use, missed schedules, and long initial upload windows. Check mapped drives, UNC paths and OneDrive placeholders separately; they are not automatically covered by the current directory-based pilot.

Generate and inspect the disabled task XML. In the isolated VM only, register it and enable it for acceptance testing after prerequisites are satisfied. Run as SYSTEM after reboot with no user logged in. A successful administrator-terminal run does not prove SYSTEM can find/decrypt saved credentials. Record credential-storage paths and ACLs without recording their values. Do not fix failures by putting passwords in task arguments or readable scripts.

Required evidence: scheduled execution, actual VSS behavior, expected failure alerts, protected configuration, fresh-machine recovery, and the reviewer sign-off. Windows task XML has been parsed locally, not validated by the Windows Task Scheduler engine.

## 3. Add a dedicated B2 practice account/bucket

The owner creates/owns the practice account, enables MFA, and controls billing. Use a dedicated bucket containing only fake data and a bucket-restricted application key. Do not send any key or password through chat, git, tickets, or screenshots.

Before creating COMPLIANCE locks, agree a test budget and retention interval: locks cannot simply be undone, and storage remains billable. Use the reviewed plan and the installed CLI's help to establish the S3 repository, lock extension, maintenance owner, and restricted key. Record permission names and version numbers, not secret values. The toolkit deliberately does not automate account-wide key regeneration or bucket lifecycle deletion.

Keep all versions until cleanup has been tested. Never expire current repository objects based solely on their upload age. Record and independently inspect retain-until dates for real object versions. A green snapshot is not evidence that lock renewal succeeded.

## 4. Recovery and attack matrix

| Test | Required result |
|---|---|
| Restricted-key version deletion | Retained versions cannot be deleted; distinguish hidden/delete-marker operations from permanent deletion |
| Attempted COMPLIANCE lock shortening | Rejected while the lock is active |
| Metadata overwrite/hiding | Restore from a known pre-attack time using a clean recovery connection |
| Maintenance over time | Actual object lock dates renew before expiry; wrong owner/offline maintenance causes an actionable alert |
| Fresh Windows VM | Recover using the client recovery packet and newly issued access key, without the original machine |
| Lost/invalid repository password | Recovery fails; independent recovery-password custody is demonstrated |
| Revoked backup credential / cap / network outage | Job failure or missed-run alert; no false success |
| Lifecycle cleanup | Obsolete unlocked versions eventually removed, needed/current versions retained; test across the actual interval |
| Restore business exports | Synthetic exported database opens through its application-specific restore procedure |
| Monitor outage | Independent external alert reaches the owner; backups continue locally |
| Alert delivery | Real Healthchecks receives start/success/failure and missing-run conditions; emails reach the correct recipients |

Keep destructive attempts within the disposable practice bucket. These tests do not authorize deletion of other cloud resources. Do not publish practice account details or live ping URLs.

## 5. Release decision

Record OS/tool versions, dates, reviewer, expected/actual result, sanitized evidence, and remediation for each row. Keep Windows, B2, actual Healthchecks/SMTP, and real-time lifecycle gates marked pending until actually observed. After they pass, enroll two or three pilot businesses under the reviewed agreement; continue to record recovery and support workload before expanding.
