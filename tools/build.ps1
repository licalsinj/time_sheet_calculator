# parameters to handle launch
param (
    [ValidateSet("y", "n")]
    [string]$Launch
)

# --- Function to safely remove a folder ---
function SafeRemove($path) {
    if (Test-Path $path) {
        try {
            Remove-Item -Recurse -Force $path -ErrorAction Stop
        }
        catch {
            Write-Warning "Could not delete $path (likely in use)."
        }
    }
    else {
        Write-Host "$path does not exist - skipping delete."
    }
}

# --- Function to wait for running EXE to close ---
function WaitForExeToClose($exeName) {
    while (Get-Process -Name $exeName -ErrorAction SilentlyContinue) {
        Write-Host "$exeName is running. Please close it..."
        Start-Sleep -Seconds 2
    }
}

# --- Function to attach to logging ---
function Tail-LogFile($logPath) {
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Get-Content `"$logPath`" -Tail 100 -Wait"
    )
}

# --- Ensure we're running from project root ---
$projectRoot = Get-Location

# --- Wait for any running TimeSheetCalculator.exe ---
WaitForExeToClose "TimeSheetCalculator"

# --- Clean build folders ---
SafeRemove "build"
SafeRemove "dist"

# --- Verify uv is available via python -m uv ---
try {
    python -m uv --version | Out-Null
}
catch {
    Write-Error "uv is not available. Make sure uv is installed for this Python interpreter."
    exit 1
}

# prints the python version and uv version just incase they're out of sync
python --version
python -m uv --version

Write-Host "Building application with PyInstaller..."

# --- Run PyInstaller using uv ---
# PyInstaller creates the executable
if (Test-Path "TimeSheetCalculator.spec") {
    python -m uv run pyinstaller TimeSheetCalculator.spec
}
else {
    python -m uv run pyinstaller --noconfirm --clean --windowed --name TimeSheetCalculator src\app.py
}

# --- Stop if build failed ---

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed. Aborting."
    exit 1
}

# --- Verify dist output exists ---
$distAppPath = "dist\TimeSheetCalculator"
if (-not (Test-Path $distAppPath)) {
    Write-Error "Build output not found at $distAppPath"
    exit 1
}

# --- Copy ABOUT.md into dist folder ---
$aboutSource = "src\ABOUT.md"
$aboutDestination = Join-Path $distAppPath "ABOUT.md"

if (-not (Test-Path $aboutSource)) {
    Write-Error "ABOUT.md not found at $aboutSource. Cannot continue."
    exit 1
}

Copy-Item $aboutSource $aboutDestination -Force
Write-Host "ABOUT.md copied to $aboutDestination"

# --- Launch behavior ---
$exePath = Join-Path $distAppPath "TimeSheetCalculator.exe"

if ($Launch -eq "y") {
    Write-Host "Auto-launch enabled. Starting app..."
    Start-Process $exePath
    if (Test-Path $logPath) {
        Tail-LogFile $logPath
    }
    else {
        Write-Warning "Log file not found yet: $logPath"
    }
}
elseif ($Launch -eq "n") {
    Write-Host "Auto-launch disabled. Build complete."
}
else {
    # No argument passed → prompt user
    $response = Read-Host "Build succeeded. Launch the app now? (y/n)"
    if ($response.ToLower() -eq "y") {
        Start-Process $exePath
    }
}
