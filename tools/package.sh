#!/usr/bin/env bash
# Usage:
#   chmod +x tools/package.sh
#     Grants execute permission so the script can be run directly.
#   ./tools/package.sh 0.1.0
#     Packages the latest build into a versioned ZIP archive.

# Exit on errors, unset variables, and failed pipes to avoid partial packaging.
set -euo pipefail

# Move to the project root so paths resolve consistently.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# App naming and version for the ZIP file.
APP_NAME="TimeSheetCalculator"
VERSION="${1:-0.1.0}"

# Dist folders and bundle names produced by PyInstaller.
DIST_DIR="dist"
DIST_APP_FILE="${DIST_DIR}/${APP_NAME}"
DIST_APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"

# Temporary staging area for the ZIP contents.
PACKAGE_ROOT="package_tmp"

# Output ZIP name.
ZIP_NAME="${APP_NAME}_v${VERSION}.zip"

# Pick the build output to package.
if [[ -d "$DIST_APP_BUNDLE" ]]; then
  SOURCE_PATH="$DIST_APP_BUNDLE"
elif [[ -f "$DIST_APP_FILE" ]]; then
  SOURCE_PATH="$DIST_APP_FILE"
else
  echo "Build output not found. Run tools/build.sh first." >&2
  exit 1
fi

# Remove previous staging folders and ZIP archives.
rm -rf "$PACKAGE_ROOT"
rm -f "$ZIP_NAME"

# Create a clean staging directory.
mkdir -p "$PACKAGE_ROOT"

echo "Copying PyInstaller build output..."
if [[ -d "$SOURCE_PATH" ]]; then
  cp -R "$SOURCE_PATH" "$PACKAGE_ROOT/"
else
  cp "$SOURCE_PATH" "$PACKAGE_ROOT/$APP_NAME"
fi

# Remove sensitive or generated files before packaging.
echo "Removing sensitive and generated files..."
find "$PACKAGE_ROOT" -name ".env" -type f -delete || true
find "$PACKAGE_ROOT" -name "*.xlsx" -type f -delete || true
find "$PACKAGE_ROOT" -name "logs" -type d -prune -exec rm -rf {} + || true
find "$PACKAGE_ROOT" -name ".DS_Store" -type f -delete || true

if find "$PACKAGE_ROOT" -name ".env" -type f | grep -q "."; then
  echo "ERROR: .env file still present in package. Aborting." >&2
  exit 1
fi

# Add About markdown to the package (required).
echo "Adding About markdown..."
if [[ -f "dist/ABOUT.md" ]]; then
  cp "dist/ABOUT.md" "$PACKAGE_ROOT/ABOUT.md"
elif [[ -f "src/ABOUT.md" ]]; then
  cp "src/ABOUT.md" "$PACKAGE_ROOT/ABOUT.md"
elif [[ -f "src/about.md" ]]; then
  cp "src/about.md" "$PACKAGE_ROOT/ABOUT.md"
else
  echo "ERROR: About markdown not found in src/. Aborting." >&2
  exit 1
fi

# Create the ZIP archive.
echo "Creating ZIP archive..."
(
  cd "$PACKAGE_ROOT"
  zip -r "../$ZIP_NAME" . >/dev/null
)

rm -rf "$PACKAGE_ROOT"

echo "ZIP created successfully: $ZIP_NAME"
