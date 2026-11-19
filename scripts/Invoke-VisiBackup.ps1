#requires -Version 7.4
<#!
Lab candidate. Requires a preconnected repository and protected configuration/state
directories. Sends status only; detailed Kopia logs stay in the local state directory.
No cloud provisioning, credential rotation, policy changes, or restore is performed.
!#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ConfigFile,
    [switch]$AllowLocalTestEndpoint
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$lock = $null
$client = $null
$result = $null
$exitCode = 10
$reason = 'invalid-configuration'
$monitorFailed = $false
$runClock = [Diagnostics.Stopwatch]::StartNew()

function Assert-AbsolutePath([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path) -or -not [IO.Path]::IsPathFullyQualified($Path)) {
        throw 'An absolute path is required.'
    }
}

function Send-Status([string]$Suffix) {
    try {
        $response = $client.SendAsync([Net.Http.HttpRequestMessage]::new(
            [Net.Http.HttpMethod]::Head, "$($settings.pingUrl.TrimEnd('/'))/$Suffix`?rid=$runId"
        )).GetAwaiter().GetResult()
        try { return ([int]$response.StatusCode -eq 200) }
        finally { $response.Dispose() }
    } catch { return $false } # Never print a secret URL or exception from the HTTP client.
}

function Invoke-Kopia([string[]]$Arguments) {
    $remaining = [int][Math]::Floor($settings.maxRunSeconds - $runClock.Elapsed.TotalSeconds)
    if ($remaining -lt 1) { $script:reason = 'timeout'; throw 'Deadline reached.' }
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $settings.kopiaPath
    $info.UseShellExecute = $false
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.RedirectStandardInput = $true
    $info.CreateNoWindow = $true
    foreach ($argument in @(
        "--config-file=$($settings.repositoryConfig)", '--no-progress',
        "--log-dir=$($settings.stateDirectory)/kopia-logs"
    ) + $Arguments) { $info.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $info
    try {
        if (-not $process.Start()) { throw 'Process did not start.' }
        $process.StandardInput.Close() # Missing credentials must fail, never wait for a prompt.
        $outTask = $process.StandardOutput.ReadToEndAsync()
        $errTask = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($remaining * 1000)) {
            $script:reason = 'timeout'
            $process.Kill($true)
            $process.WaitForExit()
            throw 'Deadline reached.'
        }
        $stdout = $outTask.GetAwaiter().GetResult()
        $null = $errTask.GetAwaiter().GetResult()
        if ($process.ExitCode -ne 0) {
            $script:reason = 'kopia-failed'
            throw 'Kopia reported failure.'
        }
        return $stdout
    } finally { $process.Dispose() }
}

try {
    Assert-AbsolutePath $ConfigFile
    $settings = Get-Content -LiteralPath $ConfigFile -Raw | ConvertFrom-Json -AsHashtable
    $keys = @('schemaVersion', 'jobId', 'kopiaPath', 'expectedKopiaVersion',
        'repositoryConfig', 'stateDirectory', 'pingUrl', 'pingTimeoutSeconds', 'maxRunSeconds', 'sources')
    if (@($settings.Keys | Where-Object { $_ -notin $keys }).Count -or
        @($keys | Where-Object { -not $settings.ContainsKey($_) }).Count) { throw 'Invalid fields.' }
    if ($settings.schemaVersion -ne 1 -or $settings.jobId -notmatch '^[a-z0-9][a-z0-9-]{0,63}$' -or
        $settings.expectedKopiaVersion -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid schema.' }
    foreach ($field in @('kopiaPath', 'repositoryConfig', 'stateDirectory')) { Assert-AbsolutePath $settings[$field] }
    foreach ($field in @('pingTimeoutSeconds', 'maxRunSeconds')) {
        if ($settings[$field] -isnot [long] -and $settings[$field] -isnot [int]) { throw 'Integer required.' }
    }
    if ($settings.pingTimeoutSeconds -lt 1 -or $settings.pingTimeoutSeconds -gt 30 -or
        $settings.maxRunSeconds -lt 1 -or $settings.maxRunSeconds -gt 604800) { throw 'Invalid timeout.' }
    $uri = [Uri]$settings.pingUrl
    if (-not $uri.IsAbsoluteUri -or $uri.Query -or $uri.Fragment -or $uri.UserInfo -or
        ($uri.Scheme -ne 'https' -and -not ($AllowLocalTestEndpoint -and $uri.IsLoopback -and $uri.Scheme -eq 'http'))) {
        throw 'HTTPS required except explicit loopback tests.'
    }
    if ($settings.sources -isnot [array] -or $settings.sources.Count -lt 1) { throw 'Sources required.' }
    $unique = [Collections.Generic.HashSet[string]]::new(
        $(if ($IsWindows) { [StringComparer]::OrdinalIgnoreCase } else { [StringComparer]::Ordinal }))
    foreach ($source in $settings.sources) {
        if (@($source.Keys | Where-Object { $_ -notin @('path', 'minimumFileCount', 'requiredFiles') }).Count -or
            -not $source.ContainsKey('path') -or -not $source.ContainsKey('minimumFileCount') -or
            -not $source.ContainsKey('requiredFiles')) { throw 'Invalid source fields.' }
        Assert-AbsolutePath $source.path
        if (-not $unique.Add([IO.Path]::GetFullPath($source.path).TrimEnd([IO.Path]::DirectorySeparatorChar))) {
            throw 'Duplicate source.'
        }
        if (($source.minimumFileCount -isnot [long] -and $source.minimumFileCount -isnot [int]) -or
            $source.minimumFileCount -lt 1 -or $source.requiredFiles -isnot [array]) { throw 'Invalid source policy.' }
        foreach ($relative in $source.requiredFiles) {
            if ([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative) -or
                $relative -match '(^|[\\/])\.\.([\\/]|$)') { throw 'Invalid required file.' }
        }
    }
    if (-not (Test-Path -LiteralPath $settings.stateDirectory -PathType Container)) { throw 'State directory missing.' }
    # One state directory per repository/job. File lock is released by the OS after crashes.
    try {
        $lock = [IO.File]::Open((Join-Path $settings.stateDirectory 'run.lock'),
            [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    } catch [IO.IOException] {
        # Do not race the active run's pings or replace its result.
        [Console]::Error.WriteLine('Run skipped: lock unavailable (active run or storage error).')
        exit 3
    }
    $runId = [Guid]::NewGuid().ToString()
    $result = [ordered]@{
        schemaVersion = 1; jobId = $settings.jobId; runId = $runId
        startedUtc = [DateTime]::UtcNow.ToString('o'); finishedUtc = $null
        backupStatus = 'failed'; reason = 'not-started'; monitoringDelivered = $false
        snapshots = @()
    }
    $handler = [Net.Http.HttpClientHandler]::new()
    $handler.AllowAutoRedirect = $false
    $client = [Net.Http.HttpClient]::new($handler)
    $client.Timeout = [TimeSpan]::FromSeconds($settings.pingTimeoutSeconds)
    $monitorFailed = -not (Send-Status 'start')
    $reason = 'missing-executable-or-config'
    if (-not (Test-Path -LiteralPath $settings.kopiaPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $settings.repositoryConfig -PathType Leaf)) { throw 'Missing prerequisite.' }
    $reason = 'missing-source'
    foreach ($source in $settings.sources) {
        if (-not (Test-Path -LiteralPath $source.path -PathType Container)) { throw 'Missing source.' }
        foreach ($relative in $source.requiredFiles) {
            if (-not (Test-Path -LiteralPath (Join-Path $source.path $relative) -PathType Leaf)) { throw 'Missing required file.' }
        }
    }
    $reason = 'unsupported-version'
    $version = Invoke-Kopia @('--version')
    if ($version.Trim() -notmatch ('^' + [Regex]::Escape($settings.expectedKopiaVersion) + '(\s|$)')) {
        throw 'Version differs from approved version.'
    }
    foreach ($source in $settings.sources) {
        $reason = 'invalid-snapshot-result'
        $created = Invoke-Kopia @('snapshot', 'create', $source.path, '--json') | ConvertFrom-Json -AsHashtable
        if (-not $created.id -or $created['incompleteReason'] -or $created.rootEntry.summ.numFailed -ne 0) {
            throw 'Snapshot incomplete.'
        }
        # create --json omits stats in the pinned version. Inspect the stored manifest too.
        $listed = @(Invoke-Kopia @('snapshot', 'list', $source.path, '--json', '--show-identical',
            '--incomplete', '--max-results=1') | ConvertFrom-Json -AsHashtable)
        $snapshot = @($listed | Where-Object { $_.id -eq $created.id })
        if ($snapshot.Count -ne 1) { throw 'New manifest not found.' }
        $manifest = $snapshot[0]
        if (-not $manifest.stats -or $manifest['incompleteReason'] -or
            $manifest.stats.errorCount -ne 0 -or $manifest.stats.ignoredErrorCount -ne 0 -or
            $manifest.rootEntry.summ.numFailed -ne 0 -or
            $manifest.stats.fileCount -lt $source.minimumFileCount) { throw 'Snapshot coverage failed.' }
        $result.snapshots += [ordered]@{
            id = $manifest.id; rootObjectId = $manifest.rootEntry.obj
            fileCount = $manifest.stats.fileCount; bytes = $manifest.stats.totalSize
        }
    }
    $result.backupStatus = 'succeeded'
    $reason = 'complete'
    $exitCode = 0
} catch {
    # Exceptions may contain client paths, URLs, or native output. Emit only our reason code.
    $exitCode = if ($reason -eq 'invalid-configuration') { 10 } elseif ($reason -eq 'timeout') { 22 } else { 20 }
} finally {
    if ($null -ne $result) {
        $result.reason = $reason
        $result.finishedUtc = [DateTime]::UtcNow.ToString('o')
        try {
            # Persist before reporting success. A local state-write failure must not send green.
            $temp = Join-Path $settings.stateDirectory "result-$runId.tmp"
            $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $temp -Encoding utf8
            [IO.File]::Move($temp, (Join-Path $settings.stateDirectory 'last-result.json'), $true)
        } catch { $exitCode = 24; $result.reason = 'state-write-failed' }
        if ($null -ne $client) {
            $suffix = if ($exitCode -eq 0) { '0' } else { 'fail' }
            if (-not (Send-Status $suffix)) { $monitorFailed = $true }
            $result.monitoringDelivered = -not $monitorFailed
        }
        if ($exitCode -eq 0 -and $monitorFailed) { $exitCode = 2 }
        try {
            $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $temp -Encoding utf8
            [IO.File]::Move($temp, (Join-Path $settings.stateDirectory 'last-result.json'), $true)
        } catch { $exitCode = 24 }
        $result | ConvertTo-Json -Depth 8 -Compress
    } else { [Console]::Error.WriteLine("Backup did not start: $reason") }
    if ($null -ne $client) { $client.Dispose() }
    if ($null -ne $lock) { $lock.Dispose() }
}
exit $exitCode
