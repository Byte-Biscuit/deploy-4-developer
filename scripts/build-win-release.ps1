<#
.SYNOPSIS
    Build and package deploy4dev for Windows x64 using PyInstaller and create a release zip with checksum.

.DESCRIPTION
    This script runs PyInstaller against the project spec, collects the produced executable and
    packaging assets (README, LICENSE, example config), zips them into a versioned release file,
    generates a SHA256 checksum, verifies the zip contains the expected executable, and optionally
    creates a GPG detached signature (.asc).

    It expects to be run from the repository root (where pyproject.toml and the spec live).

.PARAMETER Spec
    Path to the PyInstaller spec file. Default: build/deploy-4-developer.spec or deploy-4-developer.spec in repo root.

.PARAMETER ExeName
    The executable base name (without extension). Default: deploy4dev

.PARAMETER Arch
    Target architecture label used for filename (default win-x64)

.PARAMETER OutputDir
    Directory where release artifacts (zip, checksums) will be placed. Default: ./release

.PARAMETER Sign
    If provided, script will try to sign the zip with gpg and produce a .asc file.

.EXAMPLE
    .\scripts\build-win-release.ps1 -Spec deploy-4-developer.spec -ExeName deploy4dev

.NOTES
    - Requires PyInstaller available in PATH
    - For console logs visible, run from a terminal (don't double-click exe)
#>

param(
    [string]$Spec = 'deploy-4-developer.spec',
    [string]$ExeName = 'deploy4dev',
    [string]$Arch = 'win-x64',
    [string]$OutputDir = 'release',
    [switch]$Sign
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info { Write-Host "[INFO]    " -NoNewline; Write-Host $args -ForegroundColor Cyan }
function Write-Warn { Write-Host "[WARN]    " -NoNewline; Write-Host $args -ForegroundColor Yellow }
function Write-ErrorOut { Write-Host "[ERROR]   " -NoNewline; Write-Host $args -ForegroundColor Red }

# Helper: read version from pyproject.toml
function Get-VersionFromPyProject {
    $pyproject = Join-Path (Get-Location) 'pyproject.toml'
    if (-not (Test-Path $pyproject)) {
        throw "pyproject.toml not found in current directory: $PWD"
    }
    $content = Get-Content $pyproject -Raw
    # naive TOML parse for project.version
    if ($content -match 'version\s*=\s*"(?<ver>[0-9]+\.[0-9]+\.[0-9]+[0-9A-Za-z\.-]*)"') {
        return $Matches['ver']
    }
    throw 'Unable to find version string in pyproject.toml'
}

try {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $repoRoot = Resolve-Path (Join-Path $scriptDir '..')
    Push-Location $repoRoot.ProviderPath
    #Push-Location (Resolve-Path .).ProviderPath

    Write-Info "Using spec: $Spec"

    if (-not (Test-Path $Spec)) {
        Write-ErrorOut "Spec file not found: $Spec"
        exit 2
    }

    $version = Get-VersionFromPyProject
    Write-Info "Project version: $version"

    # Ensure build tools exist
    if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
        Write-ErrorOut "pyinstaller not found in PATH. Please install it in your build environment."
        exit 3
    }

    # Run PyInstaller
    Write-Info "Running PyInstaller..."
    pyinstaller $Spec
    Write-Info "PyInstaller finished."

    # Expect dist/<ExeName>.exe
    $distDir = Join-Path (Get-Location) 'dist'
    $exePath = Join-Path $distDir ($ExeName + '.exe')
    if (-not (Test-Path $exePath)) {
        Write-ErrorOut "Built executable not found at expected path: $exePath"
        Write-ErrorOut "List dist directory:"; Get-ChildItem $distDir | ForEach-Object { Write-Host $_.Name }
        exit 4
    }

    # Prepare release directory and package name
    $tag = "v$version"
    $releaseBase = "$ExeName-$tag-$Arch"
    $releaseDir = Join-Path (Get-Location) $releaseBase

    if (Test-Path $releaseDir) { Remove-Item -Recurse -Force $releaseDir }
    New-Item -ItemType Directory -Path $releaseDir | Out-Null

    # Files to include
    $filesToInclude = @()
    $filesToInclude += $exePath
    $readme = Join-Path (Get-Location) 'README.md'
    if (Test-Path $readme) { $filesToInclude += $readme }
    $license = Join-Path (Get-Location) 'LICENSE'
    if (Test-Path $license) { $filesToInclude += $license }
    $example = Join-Path (Get-Location) 'deploy.json'
    if (Test-Path $example) { $filesToInclude += $example } else {
        # if no deploy.json, try example name or include nothing
        $exampleSample = Join-Path (Get-Location) 'deploy.example.json'
        if (Test-Path $exampleSample) { $filesToInclude += $exampleSample }
    }

    # Copy files into release dir (flatten, keep file names)
    foreach ($f in $filesToInclude) {
        Copy-Item -Path $f -Destination $releaseDir -Force
    }

    # Create output path
    if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir | Out-Null }
    $zipName = "$releaseBase.zip"
    $zipPath = Join-Path (Get-Location).Path (Join-Path $OutputDir $zipName)

    # Remove existing zip if present
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

    Write-Info "Creating zip: $zipPath"
    Compress-Archive -Path (Join-Path $releaseDir '*') -DestinationPath $zipPath -Force

    # Compute SHA256 checksum
    Write-Info "Computing SHA256..."
    $hash = Get-FileHash -Algorithm SHA256 $zipPath
    $checksumsFile = Join-Path (Get-Location) $OutputDir 'CHECKSUMS.txt'
    "$($hash.Hash)  $zipName" | Out-File -FilePath $checksumsFile -Encoding utf8 -Force
    Write-Info "Wrote checksums to: $checksumsFile"

    # Validate zip contains exe
    Write-Info "Validating zip contents..."
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
    $entries = $zip.Entries | Select-Object -ExpandProperty FullName
    $zip.Dispose()

    $exeFound = $entries | Where-Object { $_ -eq ($ExeName + '.exe') }
    if (-not $exeFound) {
        Write-ErrorOut "Validation failed: $ExeName.exe not found inside $zipName"
        exit 5
    }

    Write-Info "Validation passed: $ExeName.exe present in zip"

    # Optional GPG signing
    if ($Sign) {
        if (-not (Get-Command gpg -ErrorAction SilentlyContinue)) {
            Write-Warn "gpg not found in PATH; skipping signature."
        }
        else {
            Write-Info "Creating detached ASCII-armored signature"
            & gpg --armor --detach-sign $zipPath
            if ($LASTEXITCODE -ne 0) {
                Write-Warn "gpg returned exit code $LASTEXITCODE"
            }
            else { Write-Info "Signature written: $zipPath.asc" }
        }
    }

    Write-Info "Release package created: $zipPath"
    Write-Info "Checksum: $($hash.Hash)"

    # Cleanup intermediate release dir
    Remove-Item -Recurse -Force $releaseDir

    Pop-Location
    exit 0
}
catch {
    Write-ErrorOut "Exception: $($_.Exception.Message)"
    Write-ErrorOut $_.Exception.StackTrace
    Pop-Location -ErrorAction SilentlyContinue
    exit 10
}