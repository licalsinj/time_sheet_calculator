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

# Require About markdown so the build never ships without About content.
if [[ ! -f "src/ABOUT.md" && ! -f "src/about.md" ]]; then
  echo "ERROR: About markdown not found in src/. Aborting." >&2
  exit 1
fi

# Generate embedded About content for the executable.
python3 tools/generate_about_content.py

echo "Building application with PyInstaller..."

# Use a spec file if it exists, otherwise build from the entry point.
if [[ -f "$SPEC_FILE" ]]; then
  uv run pyinstaller "$SPEC_FILE"
else
  uv run pyinstaller --noconfirm --clean --onefile --windowed --name "$APP_NAME" "$ENTRY_POINT"
fi

# Determine whether the output is a single executable.
dist_app_file="dist/$APP_NAME"

if [[ ! -f "$dist_app_file" ]]; then
  echo "Build output not found in dist/." >&2
  exit 1
fi

# Build a minimal .app wrapper around the onefile binary.
dist_app_bundle="dist/${APP_NAME}.app"
bundle_contents="${dist_app_bundle}/Contents"
bundle_macos="${bundle_contents}/MacOS"
bundle_resources="${bundle_contents}/Resources"
launcher_path="${bundle_macos}/${APP_NAME}"
binary_path="${bundle_resources}/${APP_NAME}.bin"

rm -rf "$dist_app_bundle"
mkdir -p "$bundle_macos" "$bundle_resources"
mv "$dist_app_file" "$binary_path"

cat > "${bundle_contents}/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key>
  <string>${APP_NAME}</string>
  <key>CFBundleDisplayName</key>
  <string>${APP_NAME}</string>
  <key>CFBundleIdentifier</key>
  <string>com.example.${APP_NAME}</string>
  <key>CFBundleVersion</key>
  <string>1.0</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleExecutable</key>
  <string>${APP_NAME}</string>
  <key>LSUIElement</key>
  <false/>
</dict>
</plist>
EOF

cat > "$launcher_path" <<EOF
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="\$(cd "\${SCRIPT_DIR}/.." && pwd)"
BIN_PATH="\${APP_ROOT}/Resources/${APP_NAME}.bin"
exec "\$BIN_PATH"
EOF

chmod +x "$launcher_path" "$binary_path"

if [[ ! -s "$launcher_path" ]]; then
  echo "ERROR: Launcher script was not created correctly. Aborting." >&2
  exit 1
fi

# Copy About markdown into dist so packaging can include it.
if [[ -f "src/ABOUT.md" ]]; then
  cp "src/ABOUT.md" "dist/ABOUT.md"
elif [[ -f "src/about.md" ]]; then
  cp "src/about.md" "dist/ABOUT.md"
else
  echo "ERROR: About markdown not found in src/. Aborting." >&2
  exit 1
fi

# Optional launch behavior based on a single-letter flag.
launch="${1:-}"
if [[ "$launch" == "y" ]]; then
  echo "Auto-launch enabled. Starting app..."
  open "$dist_app_bundle"
elif [[ "$launch" == "n" ]]; then
  echo "Auto-launch disabled. Build complete."
else
  read -r -p "Build succeeded. Launch the app now? (y/n) " response
  if [[ "${response,,}" == "y" ]]; then
    open "$dist_app_bundle"
  fi
fi
