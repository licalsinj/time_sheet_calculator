# Time Sheet Calculator – Design Summary

## Overview
This application is a desktop time sheet calculator built with Python 3.12 and CustomTkinter. It allows users to enter weekly work hours (Monday–Friday) and calculates total hours worked, remaining hours to reach 40, and an estimated Friday clock-out time.

The project is intentionally simple, with no data persistence, and is designed to be bundled as a single-file executable using PyInstaller.

---

## Architecture
The application is split into **two Python scripts**:

1. **Frontend (UI Layer)**
   - Implemented as a CustomTkinter `CTkFrame`
   - Responsible for layout, user input, validation display, and messaging
   - Contains a single `main()` entry point guarded by `if __name__ == "__main__"`

2. **Backend (Service Layer)**
   - Contains all business logic and calculations
   - Exposes a service object used by the UI
   - No UI dependencies

No controller layer is used at this stage.

---

## User Interface Design

### Input Grid
Each weekday (Monday–Friday) is represented by a row with the following columns:

- Day of Week (label)
- Start Time (text entry)
- End Time (text entry)
- Lunch Duration (minutes, text entry)
- Hours Worked (calculated label)

### Time Entry Behavior
- Accepts:
  - 12-hour time with optional AM/PM (e.g., `8`, `8a`, `8:35 PM`)
  - 24-hour time (e.g., `16:35`)
- Automatically inserts colons while typing
- Normalizes input on focus loss to `h:mm AM/PM`
- Tabs move left-to-right across fields
- Enter key triggers calculation

Assumptions:
- Start time defaults to AM
- End time defaults to PM
- These assumptions may be overridden by explicit user input

---

## Calculations & Rules

- Only completed days (with valid start and end times) are calculated directly
- Incomplete days are assumed to be 8-hour shifts
- Friday has special handling:
  - Blank start time defaults to 8:00 AM (with warning)
  - Blank lunch defaults to 60 minutes (with warning)
  - If 40 hours are reached before Friday, clock-out time equals clock-in time

All hour totals:
- Rounded to the nearest quarter hour
- Displayed with trimmed trailing zeros when possible

---

## Validation & Messaging

### Validation
- Invalid or missing time formats produce errors
- Negative time ranges (end before start) are not allowed
- Blank lunch duration is invalid (0 is allowed)

### Visual Feedback
- Invalid fields receive a red border
- Errors prevent calculations from running
- Multiple errors are shown together

### Messages
- Red: Errors (top)
- Yellow: Warnings (middle)
- Green: Informational/success messages (bottom)

---

## Output / KPIs
Displayed at the top of the UI after successful calculation:

- Total Hours Worked
- Hours to 40 (green if over, red if under)
- Friday Clock-Out Time

Values remain visible between runs unless the app is restarted.

---

## About Dialog
- Light gray "About" button next to Calculate
- Disabled if `readme.md` does not exist
- Displays `readme.md` in a popup
- Supports:
  - H1, H2
  - Bold, italics
  - Bullet lists using `-`

---

## Tooling & Environment
- Python 3.12
- CustomTkinter
- uv for dependency management
- PyInstaller for distribution

---

## Coding Standards
- Extensive inline comments written for non-programmers
- Full docstrings for all functions (args, returns, raises)
- No decorators used for documentation
- No first- or second-person language in comments
