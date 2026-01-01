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

# --- Wait for any running InspectorEmailTool.exe ---
WaitForExeToClose "InspectorEmailTool"

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
python -m uv run pyinstaller InspectorEmailTool.spec

# --- Stop if build failed ---

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed. Aborting."
    exit 1
}

# --- Verify dist output exists ---
$distAppPath = "dist\InspectorEmailTool"
if (-not (Test-Path $distAppPath)) {
    Write-Error "Build output not found at $distAppPath"
    exit 1
}

$logPath = Join-Path $distAppPath "logs\_internal.log"

# --- Copy .env into dist folder ---
$envSource = ".env"
$envDestination = Join-Path $distAppPath ".env"

if (-not (Test-Path $envSource)) {
    Write-Error ".env file not found in project root. Cannot continue."
    exit 1
}

Copy-Item $envSource $envDestination -Force
Write-Host ".env copied to $envDestination"

# --- Launch behavior ---
$exePath = Join-Path $distAppPath "InspectorEmailTool.exe"

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
        
        if (Test-Path $logPath) {
            Tail-LogFile $logPath
        }
        else {
            Write-Warning "Log file not found yet: $logPath"
        }
    }
}
