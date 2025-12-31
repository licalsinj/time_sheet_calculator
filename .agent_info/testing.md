- Negative and non numeric
# UI Testing Guide for Outstanding Items

## Stacked Message Areas (errors, warnings, successes)
1. Launch the app.
2. Enter an invalid start time (e.g., `25:00`) for Monday and click Calculate.
3. Confirm a red error area appears at the top and no yellow/green areas are shown.
4. Fix the invalid time, leave lunch blank for at least two days, and click Calculate.
5. Confirm a yellow warning area appears and is not overwritten.
6. Set Monday–Thursday to 8:00 AM–7:00 PM with lunch `60`, leave Friday start at `8:00 AM`, click Calculate.
7. Confirm a green success area appears at the bottom while warnings remain visible above it.

## Friday Clock-Out Handling
1. Enter Monday–Thursday as 8:00 AM–5:00 PM with lunch `60` (or blank).
2. Enter Friday start as `8:00 AM`, leave Friday end blank, click Calculate.
3. Confirm Friday Clock Out shows a time (e.g., `5:00 PM`) and warnings show for assumed lunch.
4. Clear Friday start time, click Calculate.
5. Confirm Friday Clock Out still appears and a warning indicates the default start time.
6. Set Monday–Thursday to 8:00 AM–7:00 PM with lunch `60`, keep Friday start `8:00 AM`, click Calculate.
7. Confirm Friday Clock Out equals the start time and the success message appears.

## About Dialog Markdown Rendering
1. Create a `readme.md` file with H1/H2 headings, bold/italic text, and a `-` list.
2. Launch the app and click About.
3. Confirm headings are styled differently, bold/italics render correctly, and bullet lists display.
4. Remove or rename `readme.md`, relaunch the app, and hover the disabled About button.
5. Confirm the tooltip explains the button is disabled because the file is missing.

## Normalize Time Strings After Calculation
1. Enter varied time formats without leaving the fields (e.g., `8`, `8a`, `16:35`).
2. Press Enter or click Calculate.
3. Confirm all time entries display normalized values in `h:mm AM/PM` format.
4. Verify per-day Hours and KPIs still update correctly after normalization.

## Pytest Unit Tests (not UI-driven)
1. After tests are added, run `pytest` from the project root.
2. Confirm all tests pass for time parsing, partial-day assumptions, lunch validation, Friday clock-out, and KPI calculations.
