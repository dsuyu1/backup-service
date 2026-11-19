#requires -Version 7.4
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)][string]$KopiaPath,
    [Parameter(Mandatory)][string]$RepositoryConfig,
    [Parameter(Mandatory)][ValidateSet('never','always','when-available')][string]$VssMode
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
foreach ($path in @($KopiaPath, $RepositoryConfig)) {
    if (-not [IO.Path]::IsPathFullyQualified($path) -or -not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw 'Executable and connected repository config must exist at absolute paths.'
    }
}
if ($PSCmdlet.ShouldProcess('the connected repository', 'Set VISI baseline snapshot policy')) {
    & $KopiaPath "--config-file=$RepositoryConfig" policy set --global `
        --keep-latest=10 --keep-hourly=0 --keep-daily=30 --keep-weekly=8 `
        --keep-monthly=12 --keep-annual=0 --compression=zstd `
        --ignore-file-errors=false --ignore-dir-errors=false --ignore-unknown-types=false `
        --ignore-identical-snapshots=false "--enable-volume-shadow-copy=$VssMode"
    if ($LASTEXITCODE -ne 0) { throw 'Policy update failed.' }
    Write-Output 'Baseline policy set. Check effective per-source policies; this does not configure Object Lock or lifecycle cleanup.'
}
