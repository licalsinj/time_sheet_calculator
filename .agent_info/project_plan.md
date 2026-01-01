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
- [x] 24 hour date in End Time rolls over to AM
    - If I type 16:00 into end time it is normalized into 4:00 AM
    - I would expect it to be 4:00 PM
- [ ] If there's an error on the start time or end time then the lunch doesn't warn you that it's assumed to be 60 minutes

## Feature Implementation
- [x] Populate the per-day "Hours Worked" column by surfacing daily totals from `TimeSheetService` and wiring them into the UI labels.
- [x] Add stacked error/warning/info message areas in `src/app.py` with the specified coloring instead of the single `message_label`.
- [x] Implement simple markdown rendering for the About dialog (H1/H2, bold, italics, bullet lists) rather than showing raw `readme.md` text.
- [x] Use normalized time strings returned from the service to update entry fields after calculation so all inputs display consistently.
- [x] Add pytest-based unit tests covering time parsing/normalization, partial-day assumptions, lunch validation (including negative/blank cases), Friday clock-out scenarios, and KPI calculations.
    - [x] Implement pytest smoke tests to verify the runner is wired up.
    - [x] Implement initial TimeSheetService tests based on the documented rules.
    - [x] Reach full TimeSheetService coverage by filling in any missing edge cases.
    - [x] Extract UI-adjacent logic into pure helpers to make frontend rules unit-testable.
    - [x] Add a lightweight view-model layer for app state mapping and test it with pytest.
    - [x] Implement helper unit tests over GUI automation for most UI behavior.
    - [x] If minimal UI coverage is needed, add a local-only smoke test that instantiates the app and calls `_calculate` with prefilled entries.
- [ ] if the hours column is calculated/assumed to be 8 because no start or end time is given then make the font the number in the Hours column yellow

## Documentation

- [ ] Write the about.md file that will introduce users to the project
    - This will focus on what to do when you're inside the app
    - How to use it the happy path
    - What assumptions the program makes (8am start on friday, 60 min lunch, etc)
    - What to look out for with errors
    - How to contact for support (use github or something)
- [ ] Write the README.md file that will introduce users to the project
    - High level: I'd like this to have a check it out section with cool stuff to look at, a non-technical user section, a technical user section. Don't call them that come up with something more professional but that's the idea. 
    - Check it out:
        - A short intro to the project with screen shots of it running
            - give me a list of screenshots to take should be happy path, errors, neat features like overtime
    - Non technical user info
        - An explaination for non technical users on how to download/install the app
        - A link to the about to understand how to use it 
        - How to run it
        - How to support (using github support thing)
    - Technical User info
        - How to build from source for technical users
        - How to contribute (fork and create a PR)
        - A link to the license file (TBD either MIT or GNU) 
- [ ] Add a license file not sure which kind