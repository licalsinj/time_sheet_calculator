# Project Plan

## Bug Fixes
- Propagate field-level errors from `src/timesheet_service.py` (extend `CalculationResult` and `_process_day` signature) so `src/app.py` can highlight invalid start/end/lunch entries as intended.
- Align lunch validation with spec: non-Friday blank lunch should error (0 allowed), Friday defaults to 60 minutes with warning, and invalid/non-numeric values should not crash `_calculate_friday_clock_out`.
- Normalize partial-day handling: treat any day missing a start or end time as an incomplete day that assumes an 8-hour shift, while Friday specifically defaults a missing start to 8:00 AM with a warning instead of throwing an error.
- Correct "hours to 40" math and presentation: avoid absolute value so under/over status is clear, apply quarter-hour rounding, trim trailing zeros, and color the label red when under/green when over.
- Fix message flow so warnings are not overwritten by successes and follow the red/yellow/green layering required by the spec.
- Rework Friday clock-out math to rely on pre-Friday totals (so "40 hours reached before Friday" is accurate) and handle scenarios where Friday is blank without inflating weekly totals.

## Feature Implementation
- Populate the per-day "Hours Worked" column by surfacing daily totals from `TimeSheetService` and wiring them into the UI labels.
- Add stacked error/warning/info message areas in `src/app.py` with the specified coloring instead of the single `message_label`.
- Implement simple markdown rendering for the About dialog (H1/H2, bold, italics, bullet lists) rather than showing raw `readme.md` text.
- Use normalized time strings returned from the service to update entry fields after calculation so all inputs display consistently.
