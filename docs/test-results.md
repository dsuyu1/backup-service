# Initial script test results

Date: November 18, 2026 (America/Chicago).

**Result: 28 tests passed in 47.032 seconds.** These are local laboratory results, not approval for production/client deployment.

Environment: Linux x86_64, ordinary user, Python 3.14.8, PowerShell 7.7.0, Kopia 0.23.1. Publisher release URLs and verified SHA-256 hashes are in `tool-versions.json`. Script/test/config hashes are in `tested-files.sha256`. The final complete test output is in `test-output.txt`.

Command run from the project directory:

```bash
python3 -m unittest discover -s tests -v
```

| Area | Observed result |
|---|---|
| Real encrypted filesystem repository | Created, policy applied through the PowerShell policy script, and snapshot created by the runner |
| Content verification | Kopia verification with 100% file sampling completed successfully on the synthetic snapshot |
| Historical restore | Synthetic files were overwritten/deleted, another snapshot made, and the earlier root restored through a fresh repository connection to a new directory |
| Restored integrity | All restored files matched the original set and SHA-256 hashes, including a 1 MiB binary file and nested Unicode filename |
| Wrong password | A fresh connection using an incorrect password was rejected |
| Real unreadable source file | Wrapper reported failure rather than success |
| Failure injection | Missing executable/source/required file, native exit failure, malformed output, incomplete/partial snapshots, empty snapshots, mismatched snapshot ID, and unsupported version were rejected |
| Multiple sources | A second-source failure could not be masked by first-source success |
| Deadline | Hung child process was terminated and failure reported |
| Overlap | Second process did not run a backup, overwrite the active result, or send conflicting pings |
| Status transport | Local recorder observed HEAD requests without bodies, matching run IDs, and the expected start/success/failure sequence |
| Monitor errors | HTTP 503 and redirect responses did not prevent backup; redirects were not followed and degraded monitoring was reflected in the exit/result |
| Configuration/state | Unknown fields, duplicate sources, unsafe relative required-file paths, non-test HTTP, and result-write failure were rejected |
| PowerShell/task artifacts | All scripts parsed; exported XML was disabled, used SYSTEM/PowerShell 7, prevented overlaps, and refused to overwrite an existing artifact |

Issues found and corrected during implementation:

- The actual Kopia `snapshot create --json` response does not include full statistics; the runner also inspects the saved snapshot manifest.
- Successful manifests can omit `incompleteReason`; optional fields must be accessed safely under PowerShell strict mode.
- Kopia's hourly/annual default retention must be explicitly set to zero to match the intended policy.
- Result replacement uses a file-specific operation so an unexpected directory named `last-result.json` cannot be mistaken for a successful write.
- The task XML generator's argument quoting was corrected and its parser/export checks now pass.

## Not yet tested

- Windows Task Scheduler import/execution, SYSTEM credentials, ACLs/reparse protection, VSS, reboot/sleep/battery behavior, and Windows file semantics.
- B2 authentication/permissions, Object Lock, retention renewal, version-hiding attacks, point-in-time cloud recovery, billing caps, and lifecycle cleanup over real time.
- Actual Healthchecks routing/authentication, email delivery, external outage monitoring, and monitor backup/restore. A local HTTP recorder only validates the runner's requests.
- Application-consistent QuickBooks/database restore, SaaS backup, NAS recovery, and bare-metal images.
- Large-client performance, very large snapshot output, log rotation, automatic maintenance/lock-freshness monitoring, and prolonged outages.

Neither a Windows practice VM nor a B2 practice account is ready yet. Follow `windows-and-b2-acceptance.md` next. No real client data, cloud secrets, or billable cloud resources were used in these tests.
