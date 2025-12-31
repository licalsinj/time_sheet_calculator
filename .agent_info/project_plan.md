# Project Plan

## Bug Fixes
- [x] Propagate field-level errors from `src/timesheet_service.py` so `src/app.py` can highlight invalid start/end/lunch entries.
- [x] Align lunch validation with the spec: non-Friday blank lunch should be an warning (0 allowed), Friday defaults to 60 minutes with a warning, and invalid/negative/non-numeric lunch must not crash the flow.
- [x] Correct "Hours to 40" behavior: signed math is already in place; restore spec coloring (green when over only) while keeping quarter-hour rounding and trimmed trailing zeros.
- [ ] Fix message flow to stack red/yellow/green areas instead of a single label so warnings are not overwritten by successes.
- [x] Refine Friday handling: keep using pre-Friday totals, but ensure Friday defaults/warnings are surfaced and clock-out always displays when available.
- [x] Errors Don't Propogate
    If I enter an invalid time (25:00 or asdf) for monday's start time and tuesday's start time. It only shows an error for Monday.
    It should check all fields that have an input and highlight them red red and show an error message
- [ ] 24 hour date in End Time rolls over to AM
    - If I type 16:00 into end time it is normalized into 4:00 AM
    - I would expect it to be 4:00 PM

## Feature Implementation
- [x] Populate the per-day "Hours Worked" column by surfacing daily totals from `TimeSheetService` and wiring them into the UI labels.
- [x] Add stacked error/warning/info message areas in `src/app.py` with the specified coloring instead of the single `message_label`.
- [x] Implement simple markdown rendering for the About dialog (H1/H2, bold, italics, bullet lists) rather than showing raw `readme.md` text.
- [x] Use normalized time strings returned from the service to update entry fields after calculation so all inputs display consistently.
- [ ] Add pytest-based unit tests covering time parsing/normalization, partial-day assumptions, lunch validation (including negative/blank cases), Friday clock-out scenarios, and KPI calculations.
