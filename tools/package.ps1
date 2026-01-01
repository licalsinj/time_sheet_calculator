# ==============================
# InspectorEmailTool ZIP Packager
# ==============================

$ErrorActionPreference = "Stop"

Write-Host "Packaging TimeSheetCalculator for distribution..."

# Version Number
$Version = "0.1.0"

# --- Paths (relative to repo root) ---
$distAppDir = "dist\TimeSheetCalculator"

$aboutPath = "src\ABOUT.md"

$packageRoot = "package_tmp"
$packageAppDir = Join-Path $packageRoot "TimeSheetCalculator"

$zipName = "TimeSheetCalculator_v$Version.zip"

# --- Validate required inputs ---
$requiredPaths = @(
    $distAppDir,
    $aboutPath
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
New-Item -ItemType Directory -Path $packageAppDir -Force | Out-Null

# --- Copy PyInstaller output (CONTENTS, not folder) ---
Write-Host "Copying PyInstaller build output..."
Copy-Item "$distAppDir\*" $packageAppDir -Recurse -Force

# --- Remove sensitive & generated files ---
Write-Host "Removing sensitive and generated files..."

# Remove .env anywhere
Get-ChildItem $packageAppDir -Recurse -Filter ".env" -ErrorAction SilentlyContinue |
    Remove-Item -Force

# Remove logs directory
$logsDir = Join-Path $packageAppDir "logs"
if (Test-Path $logsDir) {
    Remove-Item $logsDir -Recurse -Force
}

# --- Fail fast if .env still exists ---
$envLeak = Get-ChildItem $packageAppDir -Recurse -Filter ".env" -ErrorAction SilentlyContinue
if ($envLeak) {
    Write-Error "ERROR: .env file still present in package. Aborting."
    exit 1
}

# --- Add distribution files ---
Write-Host "Adding About file..."

Copy-Item $aboutPath $packageAppDir -Force

# --- Create ZIP ---
Write-Host "Creating ZIP archive..."
Compress-Archive -Path $packageAppDir -DestinationPath $zipName

Write-Host "ZIP created successfully: $zipName"

# --- Cleanup temp directory ---
Remove-Item $packageRoot -Recurse -Force

Write-Host "Packaging complete."
