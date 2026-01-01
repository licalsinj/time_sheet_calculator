# Time Sheet Calculator

Welcome! This app helps you track weekly hours, see time remaining to reach 40, and estimate your Friday clock-out based on what you enter.

## Quick start (happy path)
1. Enter start and end times for Monday–Thursday (e.g., `8:00 AM`, `5:00 PM`).
2. Enter lunch minutes (e.g., `60`). Leave blank to auto-assume 60 minutes (you will see a yellow warning).
3. Enter Friday start (or leave blank to assume `8:00 AM`).
4. Click **Calculate** or press **Enter** to update totals, hours-to-40, and Friday clock-out.

## Assumptions & defaults
- Friday start defaults to **8:00 AM** if you leave it blank.
- Lunch defaults to **60 minutes** if blank. You will see a yellow highlight and warning.
- Times are normalized as you move between fields (e.g., `8` becomes `8:00 AM`).
- Rounding is to quarter hours for totals.

## Errors & warnings
- **Red** borders and messages: invalid time formats (e.g., `25:00`, `asdf`), end before start, or negative/non-numeric lunch.
- **Yellow** borders and messages: assumed lunch defaults.
- Errors and warnings stack; fix inputs and press **Calculate** again to clear them.

## Handy shortcuts
- **Tab** to move between fields quickly.
- **Enter** triggers Calculate.
- Clear a field to remove its value; Friday will still estimate if enough data is present.

## Need help?
- Check the project README for install/build guidance.
- Open an issue on the project’s GitHub to report problems or request support.
