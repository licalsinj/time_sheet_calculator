#!/usr/bin/env bash
# Usage:
#   chmod +x tools/build.sh
#     Grants execute permission so the script can be run directly.
#   ./tools/build.sh
#     Builds the app with PyInstaller (no auto-launch).
#   ./tools/build.sh y
#     Builds the app and launches it after a successful build.
#   ./tools/build.sh n
#     Builds the app without launching it.

# Exit on errors, unset variables, and failed pipes to avoid partial builds.
set -euo pipefail

# Move to the project root so paths resolve consistently.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Application name and entry point for PyInstaller.
APP_NAME="TimeSheetCalculator"
ENTRY_POINT="src/app.py"
SPEC_FILE="${APP_NAME}.spec"

# Waits until any running app process is closed to avoid build conflicts.
wait_for_running_app() {
  local app_name="$1"
  while pgrep -f "$app_name" >/dev/null 2>&1; do
    echo "$app_name is running. Please close it..."
    sleep 2
  done
}

# Removes build artifacts from previous runs.
safe_remove() {
  local path="$1"
  if [[ -e "$path" ]]; then
    rm -rf "$path" || echo "Could not delete $path (likely in use)."
  else
    echo "$path does not exist - skipping delete."
  fi
}

# Ensure no previous app instance is running.
wait_for_running_app "$APP_NAME"

# Clean old build folders so the output is fresh.
safe_remove "build"
safe_remove "dist"

# Verify uv exists so PyInstaller can run in the virtual environment.
if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not available. Install uv or ensure it is on PATH." >&2
  exit 1
fi

# Print versions for troubleshooting.
python3 --version
uv --version

echo "Building application with PyInstaller..."

# Use a spec file if it exists, otherwise build from the entry point.
if [[ -f "$SPEC_FILE" ]]; then
  uv run pyinstaller "$SPEC_FILE"
else
  uv run pyinstaller --noconfirm --clean --windowed --name "$APP_NAME" "$ENTRY_POINT"
fi

# Determine whether the output is a .app bundle or a folder.
dist_app_dir="dist/$APP_NAME"
dist_app_bundle="dist/${APP_NAME}.app"

if [[ -d "$dist_app_bundle" ]]; then
  dist_target="$dist_app_bundle"
elif [[ -d "$dist_app_dir" ]]; then
  dist_target="$dist_app_dir"
else
  echo "Build output not found in dist/." >&2
  exit 1
fi

# Optional launch behavior based on a single-letter flag.
launch="${1:-}"
if [[ "$launch" == "y" ]]; then
  echo "Auto-launch enabled. Starting app..."
  if [[ -d "$dist_app_bundle" ]]; then
    open "$dist_app_bundle"
  else
    "$dist_app_dir/$APP_NAME" &
  fi
elif [[ "$launch" == "n" ]]; then
  echo "Auto-launch disabled. Build complete."
else
  read -r -p "Build succeeded. Launch the app now? (y/n) " response
  if [[ "${response,,}" == "y" ]]; then
    if [[ -d "$dist_app_bundle" ]]; then
      open "$dist_app_bundle"
    else
      "$dist_app_dir/$APP_NAME" &
    fi
  fi
fi
