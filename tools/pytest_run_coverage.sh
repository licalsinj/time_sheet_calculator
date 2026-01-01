#!/usr/bin/env bash
# Usage:
#   chmod +x tools/pytest_run_coverage.sh
#     Grants execute permission so the script can be run directly.
#   ./tools/pytest_run_coverage.sh
#     Runs the full pytest suite without coverage output.
#   ./tools/pytest_run_coverage.sh coverage
#     Runs pytest with coverage for all modules under src and prints missing lines.
#   ./tools/pytest_run_coverage.sh service
#     Runs only TimeSheetService tests with coverage output for that module.
#   ./tools/pytest_run_coverage.sh ui
#     Runs only ui_view_model tests with coverage output for that module.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

usage() {
  cat <<'USAGE'
Usage: tools/pytest_run_coverage.sh [mode]

Modes:
  test      Run pytest without coverage (default)
  coverage  Run pytest with full coverage report
  service   Run service tests with coverage
  ui        Run UI view-model tests with coverage
USAGE
}

mode="${1:-test}"

case "$mode" in
  test|tests)
    uv run pytest
    ;;
  coverage|cov)
    uv run pytest --cov=src --cov-report=term-missing
    ;;
  service)
    uv run pytest --cov=timesheet_service --cov-report=term-missing tests/test_timesheet_service.py
    ;;
  ui)
    uv run pytest --cov=ui_view_model --cov-report=term-missing tests/test_ui_view_model.py
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage
    exit 1
    ;;
esac
