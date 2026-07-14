[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$distRoot = Join-Path $projectRoot 'dist'
$packageRoot = Join-Path $projectRoot 'ptsites'
$pluginFiles = @(
    'auto_sign_in.py',
    'html_rss.py',
    'iyuu_auto_reseed.py',
    'qbittorrent_mod.py',
    'show_entry.py',
    'wecom.py'
)

$resolvedProjectRoot = [System.IO.Path]::GetFullPath($projectRoot).TrimEnd('\')
$resolvedDistRoot = [System.IO.Path]::GetFullPath($distRoot)
if (-not $resolvedDistRoot.StartsWith(
        "$resolvedProjectRoot\",
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
    throw "Refusing to rebuild a dist directory outside the project: $resolvedDistRoot"
}

# Recreate the output directory so removed source files cannot remain in dist.
if (Test-Path -LiteralPath $distRoot) {
    Remove-Item -LiteralPath $distRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $distRoot | Out-Null

$copiedFiles = 0

# Copy only supported FlexGet plugin entry points. Tests and local scripts must
# never become part of the deployable plugin directory.
$pluginFiles | ForEach-Object {
    $sourcePath = Join-Path $projectRoot $_
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        throw "Missing plugin entry point: $sourcePath"
    }
    Copy-Item -LiteralPath $sourcePath -Destination $distRoot
    $copiedFiles++
}

# Copy the package and its data files, excluding Python cache artifacts.
if (Test-Path -LiteralPath $packageRoot) {
    Get-ChildItem -LiteralPath $packageRoot -File -Recurse |
        Where-Object {
            $_.FullName -notmatch '[\\/]__pycache__([\\/]|$)' -and
            $_.Extension -notin @('.pyc', '.pyo')
        } |
        ForEach-Object {
            $relativePath = $_.FullName.Substring($projectRoot.Length + 1)
            $targetPath = Join-Path $distRoot $relativePath
            $targetDirectory = Split-Path -Parent $targetPath

            New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination $targetPath
            $copiedFiles++
        }
}

Write-Host "Built $distRoot ($copiedFiles files; Python caches excluded)."
