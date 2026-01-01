# Time Sheet Calculator

Desktop app to track weekly hours, see time remaining to reach 40, and estimate a Friday clock-out time.

## What to look at
- Suggested screenshots to capture:
  - Clean “happy path” entry with totals and Hours to 40.
  - Warning state for assumed lunch (yellow highlights).
  - Error state for invalid time/lunch (red highlights).
  - Overtime view with Hours to 40 shown in green.
  - About dialog rendering markdown.

## Get the app (non-technical)
- Download the appropriate ZIP:
  - macOS: `TimeSheetCalculator_macos_vX.Y.Z.zip`
  - Windows: `TimeSheetCalculator_windows_vX.Y.Z.zip`
- Unzip and run:
  - macOS: double-click `TimeSheetCalculator.app` (use right-click → Open on first run if Gatekeeper warns).
  - Windows: double-click `TimeSheetCalculator.exe` (you may need “Run anyway” if SmartScreen prompts).
- Open `ABOUT.md` in the ZIP for usage guidance.

## Using the app
- Enter start/end times for Monday–Thursday; add lunch minutes or leave blank to assume 60 minutes.
- Enter Friday start (or leave blank to assume 8:00 AM).
- Click **Calculate** or press **Enter** to update totals, Hours to 40, and Friday clock-out.
- Red = errors (invalid time, end before start, bad lunch). Yellow = assumed lunch.
- See `src/ABOUT.md` for the full usage guide.

## For developers
- Prerequisites: Python 3.12+, `uv` installed.
- Setup: `uv sync`
- Run tests with coverage:
  - `uv run pytest --cov=timesheet_service --cov-report=term-missing`
  - `uv run pytest --cov=ui_view_model --cov-report=term-missing tests/test_ui_view_model.py`
  - `uv run pytest --cov=app --cov-report=term-missing tests/test_app_ui.py`
  - Or use the helper script: `./tools/pytest_run_coverage.sh`
- Build (mac): `./tools/build.sh` (produces `.app` bundle wrapping a onefile binary)
- Package (mac): `./tools/package.sh` (produces `TimeSheetCalculator_macos_vX.Y.Z.zip`)
- Build (Windows): `powershell -ExecutionPolicy Bypass -File tools\build.ps1`
- Package (Windows): `powershell -ExecutionPolicy Bypass -File tools\package.ps1`

## Contributing
- Fork the repo, create a feature branch, and open a PR.
- File issues for bugs or feature requests on GitHub.

## License
- GPLv3 — see `LICENSE`.
