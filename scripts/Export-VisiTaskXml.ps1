#requires -Version 7.4
<#! Generates a DISABLED Windows task for inspection. Does not register a task. !#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$OutputPath,
    [string]$TargetDirectory = 'C:\ProgramData\VISI-Backup',
    [string]$PowerShellPath = 'C:\Program Files\PowerShell\7\pwsh.exe',
    [ValidatePattern('^([01][0-9]|2[0-3]):[0-5][0-9]$')][string]$DailyAt = '21:00',
    [ValidateRange(1,168)][int]$MaxRunHours = 8
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
foreach ($path in @($TargetDirectory, $PowerShellPath)) {
    if ($path -notmatch '^[A-Za-z]:\\' -or $path -match '["\r\n]' -or $path.EndsWith('\')) {
        throw 'Use an absolute Windows path without quotes, newlines, or a trailing slash.'
    }
}
if (Test-Path -LiteralPath $OutputPath) { throw 'Refusing to overwrite an existing task artifact.' }
$command = [Security.SecurityElement]::Escape($PowerShellPath)
$arguments = [Security.SecurityElement]::Escape(
    "-NoLogo -NoProfile -NonInteractive -File `"$TargetDirectory\Invoke-VisiBackup.ps1`" -ConfigFile `"$TargetDirectory\backup.json`""
)
$working = [Security.SecurityElement]::Escape($TargetDirectory)
$xml = @"
<?xml version="1.0" encoding="utf-8"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>VISI backup lab candidate. Disabled until Windows and cloud acceptance tests pass. Schedule uses the Windows machine's local timezone.</Description></RegistrationInfo>
  <Triggers><CalendarTrigger><StartBoundary>2026-11-18T${DailyAt}:00</StartBoundary><Enabled>true</Enabled><ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger></Triggers>
  <Principals><Principal id="System"><UserId>S-1-5-18</UserId><LogonType>ServiceAccount</LogonType><RunLevel>HighestAvailable</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>true</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand><Enabled>false</Enabled>
    <Hidden>false</Hidden><WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT$($MaxRunHours * 3600 + 120)S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="System"><Exec><Command>$command</Command><Arguments>$arguments</Arguments><WorkingDirectory>$working</WorkingDirectory></Exec></Actions>
</Task>
"@
$null = [xml]$xml
[IO.File]::WriteAllText([IO.Path]::GetFullPath($OutputPath), $xml, [Text.UTF8Encoding]::new($false))
Write-Output 'Disabled task XML exported; no scheduled task was installed.'
