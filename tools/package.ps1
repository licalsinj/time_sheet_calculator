# ==============================
# InspectorEmailTool ZIP Packager
# ==============================
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools\package.ps1
#     Uses version from pyproject.toml.
#   powershell -ExecutionPolicy Bypass -File tools\package.ps1 -Version 0.1.0
#     Uses the provided version for the ZIP name.

$ErrorActionPreference = "Stop"

Write-Host "Packaging TimeSheetCalculator for distribution..."

# Version Number (from CLI or pyproject.toml)
param (
    [string]$Version
)

if (-not $Version) {
    try {
        $tomlPath = Join-Path (Get-Location) "pyproject.toml"
        $tomlText = Get-Content -Raw -Path $tomlPath
        if ($tomlText -match 'version\\s*=\\s*"([^"]+)"') {
            $Version = $Matches[1]
        }
    }
    catch {
        $Version = $null
    }
}

if (-not $Version) {
    Write-Error "Version not provided and not found in pyproject.toml."
    exit 1
}

# --- Paths (relative to repo root) ---
$distAppDir = "dist\TimeSheetCalculator.exe"


$packageRoot = "package_tmp"

$zipName = "TimeSheetCalculator_windows_v$Version.zip"

# --- Validate required inputs ---
$requiredPaths = @(
    $distAppDir
)

foreach ($path in $requiredPaths) {
    if (-not (Test-Path $path)) {
        Write-Error "Required path missing: $path"
        exit 1
    }
}

# --- Clean previous artifacts ---
if (Test-Path $packageRoot) {
    Remove-Item $packageRoot -Recurse -Force
}

if (Test-Path $zipName) {
    Remove-Item $zipName -Force
}

# --- Create package root ---
New-Item -ItemType Directory -Path $packageRoot -Force | Out-Null

# --- Copy PyInstaller output (CONTENTS, not folder) ---
Write-Host "Copying PyInstaller build output..."
Copy-Item $distAppDir (Join-Path $packageRoot "TimeSheetCalculator.exe") -Force

# --- Remove sensitive & generated files ---
Write-Host "Removing sensitive and generated files..."

# Remove .env anywhere
Get-ChildItem $packageRoot -Recurse -Filter ".env" -ErrorAction SilentlyContinue |
    Remove-Item -Force

# Remove logs directory
$logsDir = Join-Path $packageRoot "logs"
if (Test-Path $logsDir) {
    Remove-Item $logsDir -Recurse -Force
}

# --- Fail fast if .env still exists ---
$envLeak = Get-ChildItem $packageRoot -Recurse -Filter ".env" -ErrorAction SilentlyContinue
if ($envLeak) {
    Write-Error "ERROR: .env file still present in package. Aborting."
    exit 1
}

# --- Add distribution files ---
Write-Host "Adding About file..."

$aboutCandidates = @("dist\ABOUT.md", "src\ABOUT.md", "src\about.md")
$aboutPath = $aboutCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($aboutPath) {
    Copy-Item $aboutPath (Join-Path $packageRoot "ABOUT.md") -Force
}
else {
    Write-Error "About markdown not found in src/. Aborting."
    exit 1
}

# --- Create ZIP ---
Write-Host "Creating ZIP archive..."
Compress-Archive -Path (Join-Path $packageRoot "*") -DestinationPath $zipName

Write-Host "ZIP created successfully: $zipName"

# --- Cleanup temp directory ---
Remove-Item $packageRoot -Recurse -Force

Write-Host "Packaging complete."
