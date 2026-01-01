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
DIST_APP_DIR="${DIST_DIR}/${APP_NAME}"
DIST_APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"

# Temporary staging area for the ZIP contents.
PACKAGE_ROOT="package_tmp"
PACKAGE_APP_DIR="${PACKAGE_ROOT}/${APP_NAME}"

# Output ZIP name.
ZIP_NAME="${APP_NAME}_v${VERSION}.zip"

# Pick the build output to package.
if [[ -d "$DIST_APP_BUNDLE" ]]; then
  SOURCE_PATH="$DIST_APP_BUNDLE"
elif [[ -d "$DIST_APP_DIR" ]]; then
  SOURCE_PATH="$DIST_APP_DIR"
else
  echo "Build output not found. Run tools/build_mac.sh first." >&2
  exit 1
fi

# Remove previous staging folders and ZIP archives.
rm -rf "$PACKAGE_ROOT"
rm -f "$ZIP_NAME"

# Create a clean staging directory.
mkdir -p "$PACKAGE_APP_DIR"

echo "Copying PyInstaller build output..."
cp -R "$SOURCE_PATH" "$PACKAGE_APP_DIR/"

# Remove sensitive or generated files before packaging.
echo "Removing sensitive and generated files..."
find "$PACKAGE_APP_DIR" -name ".env" -type f -delete || true
find "$PACKAGE_APP_DIR" -name "*.xlsx" -type f -delete || true
find "$PACKAGE_APP_DIR" -name "logs" -type d -prune -exec rm -rf {} + || true
find "$PACKAGE_APP_DIR" -name ".DS_Store" -type f -delete || true

if find "$PACKAGE_APP_DIR" -name ".env" -type f | grep -q "."; then
  echo "ERROR: .env file still present in package. Aborting." >&2
  exit 1
fi

# Add extra distribution files if present.
echo "Adding distribution files..."
if [[ -f "README.md" ]]; then
  cp "README.md" "$PACKAGE_APP_DIR/"
fi
if [[ -f "src/ABOUT.md" ]]; then
  cp "src/ABOUT.md" "$PACKAGE_APP_DIR/"
elif [[ -f "src/about.md" ]]; then
  cp "src/about.md" "$PACKAGE_APP_DIR/ABOUT.md"
fi

# Create the ZIP archive.
echo "Creating ZIP archive..."
(
  cd "$PACKAGE_ROOT"
  zip -r "../$ZIP_NAME" "$APP_NAME" >/dev/null
)

rm -rf "$PACKAGE_ROOT"

echo "ZIP created successfully: $ZIP_NAME"
