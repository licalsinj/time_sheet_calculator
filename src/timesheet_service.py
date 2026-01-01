"""
timesheet_service.py

This module contains all business logic for the time sheet calculator.
No UI framework is imported here so the logic can be tested independently.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
import re
import math


@dataclass
class DayInput:
    """
    Represents raw user input for a single work day.

    Attributes:
        day_name: Name of the weekday (e.g. Monday)
        start_time: Raw start time string
        end_time: Raw end time string
        lunch_minutes: Raw lunch duration string
    """
    day_name: str
    start_time: str
    end_time: str
    lunch_minutes: str


@dataclass
class CalculationResult:
    """
    Represents the result of a full weekly calculation.

    Attributes:
        total_hours: Total hours worked so far
        hours_to_40: Absolute difference from 40 hours
        friday_clock_out: Calculated Friday clock out time string
        daily_hours: Mapping of day name to worked hours
        field_errors: Mapping of field identifiers to error messages
        errors: List of blocking error messages
        warnings: List of non-blocking warning messages
        successes: List of informational success messages
        normalized_times: Mapping of field identifiers to normalized display values
    """
    total_hours: Optional[float]
    hours_to_40: Optional[float]
    friday_clock_out: Optional[str]
    daily_hours: Dict[str, float]
    field_errors: Dict[str, str]
    errors: List[str]
    warnings: List[str]
    successes: List[str]
    normalized_times: Dict[str, str]

class TimeSheetService:
    """
    Service object responsible for parsing, validating, and calculating time sheet data.
    """

    def __init__(self) -> None:
        """
        Initializes the service defaults.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        self.minutes_per_day_assumption = 8 * 60

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate_week(self, days: List[DayInput]) -> CalculationResult:
        """
        Performs full validation and calculation for the work week.

        Args:
            days: List of DayInput objects for Monday through Friday.

        Returns:
            CalculationResult containing totals, messages, per-day hours, and normalized values.

        Raises:
            None.
        """
        errors: List[str] = []
        warnings: List[str] = []
        successes: List[str] = []
        normalized: Dict[str, str] = {}
        field_errors: Dict[str, str] = {}
        daily_minutes: Dict[str, int] = {}

        # First pass: validate and compute daily minutes
        for day in days:
            minutes, day_errors, day_warnings, day_normalized, day_field_errors = self._process_day(day)
            field_errors.update(day_field_errors)
            normalized.update(day_normalized)

            if day_errors:
                errors.extend(day_errors)
            if day_warnings:
                warnings.extend(day_warnings)

            if minutes is not None:
                daily_minutes[day.day_name] = minutes

        # Block all calculations if errors exist
        if errors:
            return CalculationResult(
                total_hours=None,
                hours_to_40=None,
                friday_clock_out=None,
                daily_hours={},
                field_errors=field_errors,
                errors=errors,
                warnings=warnings,
                successes=successes,
                normalized_times=normalized,
            )

        daily_hours = {
            day: self._round_to_quarter(minutes / 60)
            for day, minutes in daily_minutes.items()
        }

        total_minutes = sum(daily_minutes.values())
        total_hours = self._round_to_quarter(total_minutes / 60)

        hours_to_40 = self._round_to_quarter((40 * 60 - total_minutes) / 60)

        friday_clock_out = self._calculate_friday_clock_out(
            days,
            pre_friday_minutes=sum(
                minutes for name, minutes in daily_minutes.items() if name.lower() != "friday"
            ),
            friday_minutes=daily_minutes.get("Friday"),
            warnings=warnings,
            successes=successes,
            normalized=normalized,
        )

        return CalculationResult(
            total_hours=total_hours,
            hours_to_40=hours_to_40,
            friday_clock_out=friday_clock_out,
            daily_hours=daily_hours,
            field_errors=field_errors,
            errors=errors,
            warnings=warnings,
            successes=successes,
            normalized_times=normalized,
        )

    # ------------------------------------------------------------------
    # Day Processing
    # ------------------------------------------------------------------

    def _process_day(
        self, day: DayInput
    ) -> Tuple[Optional[int], List[str], List[str], Dict[str, str], Dict[str, str]]:
        """
        Validates and calculates worked minutes for a single day.

        Args:
            day: DayInput object representing one weekday.

        Returns:
            Tuple of:
                - minutes worked (or None).
                - list of error messages.
                - list of warning messages.
                - normalized display values.
                - field-level error metadata.

        Raises:
            None.
        """
        errors: List[str] = []
        warnings: List[str] = []
        normalized: Dict[str, str] = {}
        field_errors: Dict[str, str] = {}

        start_raw = day.start_time.strip()
        end_raw = day.end_time.strip()
        lunch_raw = day.lunch_minutes.strip()
        has_start = bool(start_raw)
        has_end = bool(end_raw)
        has_lunch = bool(lunch_raw)

        # Incomplete day logic
        if not has_start and not has_end:
            if has_lunch:
                try:
                    lunch_minutes = int(lunch_raw)
                    if lunch_minutes < 0:
                        raise ValueError
                except ValueError:
                    errors.append(f"{day.day_name}: invalid lunch duration")
                    field_errors[f"{day.day_name}_lunch"] = "Invalid lunch duration"
                    return None, errors, warnings, normalized, field_errors
            return self.minutes_per_day_assumption, errors, warnings, normalized, field_errors

        if has_start and not has_end:
            if day.day_name.lower() != "friday":
                start_minutes, start_display, start_error = self._parse_time(
                    start_raw, assume_am=True
                )
                if start_display:
                    normalized[f"{day.day_name}_start"] = start_display
                if start_error:
                    errors.append(f"{day.day_name}: invalid start time")
                    field_errors[f"{day.day_name}_start"] = "Invalid start time"
                    return None, errors, warnings, normalized, field_errors
                if has_lunch:
                    try:
                        lunch_minutes = int(lunch_raw)
                        if lunch_minutes < 0:
                            raise ValueError
                    except ValueError:
                        errors.append(f"{day.day_name}: invalid lunch duration")
                        field_errors[f"{day.day_name}_lunch"] = "Invalid lunch duration"
                        return None, errors, warnings, normalized, field_errors
                return self.minutes_per_day_assumption, errors, warnings, normalized, field_errors
            # Friday: allow estimating clock-out without an end time; no minutes added
            start_minutes, start_display, start_error = self._parse_time(
                start_raw, assume_am=True
            )
            if start_display:
                normalized[f"{day.day_name}_start"] = start_display
            if start_error:
                errors.append(f"{day.day_name}: invalid start time")
                field_errors[f"{day.day_name}_start"] = "Invalid start time"
                return None, errors, warnings, normalized, field_errors

            # Lunch handling for Friday partial entry
            if not lunch_raw:
                lunch_minutes = 60
                warnings.append(f"{day.day_name}: lunch assumed to be 60 minutes")
            else:
                try:
                    lunch_minutes = int(lunch_raw)
                    if lunch_minutes < 0:
                        raise ValueError
                except ValueError:
                    errors.append(f"{day.day_name}: invalid lunch duration")
                    field_errors[f"{day.day_name}_lunch"] = "Invalid lunch duration"
                    return None, errors, warnings, normalized, field_errors

            return None, errors, warnings, normalized, field_errors

        if not has_start and has_end:
            end_minutes, end_display, end_error = self._parse_time(
                end_raw, assume_am=False
            )
            if end_display:
                normalized[f"{day.day_name}_end"] = end_display
            if end_error:
                errors.append(f"{day.day_name}: invalid end time")
                field_errors[f"{day.day_name}_end"] = "Invalid end time"
                return None, errors, warnings, normalized, field_errors
            if has_lunch:
                try:
                    lunch_minutes = int(lunch_raw)
                    if lunch_minutes < 0:
                        raise ValueError
                except ValueError:
                    errors.append(f"{day.day_name}: invalid lunch duration")
                    field_errors[f"{day.day_name}_lunch"] = "Invalid lunch duration"
                    return None, errors, warnings, normalized, field_errors
            return self.minutes_per_day_assumption, errors, warnings, normalized, field_errors

        # Parse start and end times
        start_minutes, start_display, start_error = self._parse_time(
            start_raw, assume_am=True
        )
        end_minutes, end_display, end_error = self._parse_time(
            end_raw, assume_am=False
        )

        if start_display:
            normalized[f"{day.day_name}_start"] = start_display
        if end_display:
            normalized[f"{day.day_name}_end"] = end_display

        if start_error:
            errors.append(f"{day.day_name}: invalid start time")
            field_errors[f"{day.day_name}_start"] = "Invalid start time"
        if end_error:
            errors.append(f"{day.day_name}: invalid end time")
            field_errors[f"{day.day_name}_end"] = "Invalid end time"
        
        if start_error or end_error:
            return None, errors, warnings, normalized, field_errors

        if end_minutes <= start_minutes:
            errors.append(f"{day.day_name}: end time is before start time")
            field_errors[f"{day.day_name}_end"] = "End time before start time"
            return None, errors, warnings, normalized, field_errors


        duration_minutes = end_minutes - start_minutes

        # Lunch handling
        if not lunch_raw:
            lunch_minutes = 60
            warnings.append(f"{day.day_name}: lunch assumed to be 60 minutes")
        else:
            try:
                lunch_minutes = int(lunch_raw)
                if lunch_minutes < 0:
                    raise ValueError
            except ValueError:
                errors.append(f"{day.day_name}: invalid lunch duration")
                field_errors[f"{day.day_name}_lunch"] = "Invalid lunch duration"
                return None, errors, warnings, normalized, field_errors


        if lunch_minutes > duration_minutes:
            errors.append(f"{day.day_name}: lunch exceeds shift length")
            field_errors[f"{day.day_name}_lunch"] = "Lunch exceeds shift length"
            return None, errors, warnings, normalized, field_errors


        worked_minutes = duration_minutes - lunch_minutes
        return worked_minutes, errors, warnings, normalized, field_errors

    # ------------------------------------------------------------------
    # Friday Logic
    # ------------------------------------------------------------------

    def _calculate_friday_clock_out(
        self,
        days: List[DayInput],
        pre_friday_minutes: int,
        friday_minutes: Optional[int],
        warnings: List[str],
        successes: List[str],
        normalized: Dict[str, str],
    ) -> Optional[str]:
        """
        Calculates Friday clock out time needed to reach 40 hours.

        Args:
            days: List of DayInput.
            pre_friday_minutes: Minutes worked before Friday.
            friday_minutes: Minutes worked on Friday (if completed).
            warnings: Warning message accumulator.
            successes: Success message accumulator.
            normalized: Normalized value accumulator.

        Returns:
            Clock out time string or None.

        Raises:
            None.
        """
        friday = next(d for d in days if d.day_name.lower() == "friday")

        if pre_friday_minutes >= 40 * 60:
            successes.append("40 hours reached before Friday this week")
            return normalized.get("Friday_start", "8:00 AM")

        start_raw = friday.start_time.strip()
        lunch_raw = friday.lunch_minutes.strip()

        if not start_raw:
            start_minutes = 8 * 60
            normalized["Friday_start"] = "8:00 AM"
            warnings.append("Friday start time assumed to be 8:00 AM")
        else:
            start_minutes, display, error = self._parse_time(start_raw, assume_am=True)
            if error:
                return None
            normalized["Friday_start"] = display

        if not lunch_raw:
            lunch_minutes = 60
            warning_text = "Friday: lunch assumed to be 60 minutes"
            if warning_text not in warnings:
                warnings.append(warning_text)
        else:
            try:
                lunch_minutes = int(lunch_raw)
                if lunch_minutes < 0:
                    raise ValueError
            except ValueError:
                return None

        # If Friday already has an end time, return it
        if friday.end_time.strip():
            _, end_display, end_error = self._parse_time(
                friday.end_time.strip(), assume_am=False
            )
            if not end_error and end_display:
                normalized["Friday_end"] = end_display
                return end_display

        remaining_minutes = (40 * 60) - pre_friday_minutes + lunch_minutes
        clock_out_minutes = start_minutes + remaining_minutes

        return self._minutes_to_display(clock_out_minutes)

    # ------------------------------------------------------------------
    # Time Utilities
    # ------------------------------------------------------------------

    def _parse_time(
        self, raw: str, assume_am: bool
    ) -> Tuple[Optional[int], Optional[str], bool]:
        """
        Parses a time string into minutes since midnight.

        Args:
            raw: Raw time input string.
            assume_am: Whether to assume AM if no period is provided.

        Returns:
            Tuple of:
                - minutes since midnight.
                - normalized display string.
                - error flag.

        Raises:
            None.
        """
        if not raw:
            return None, None, True

        raw = raw.lower().strip()

        match = re.match(
            r"^(\d{1,2})(?::?(\d{0,2}))?\s*(a|p|am|pm)?$", raw
        )


        if not match:
            return None, None, True

        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        period = match.group(3)

        if period == "a":
            period = "am"
        elif period == "p":
            period = "pm"

        if hour > 23 or minute > 59:
            return None, None, True

        if period:
            if hour == 12:
                hour = 0
            if period == "pm":
                hour += 12
        else:
            # No AM/PM provided, apply default assumption
            # Treat 13-23 as 24-hour input to avoid adding 12 again.
            if hour <= 12:
                if assume_am:
                    if hour == 12:
                        hour = 0
                else:
                    if hour != 12:
                        hour += 12


        minutes = hour * 60 + minute
        return minutes, self._minutes_to_display(minutes), False

    def _minutes_to_display(self, minutes: int) -> str:
        """
        Converts minutes since midnight to hh:mm AM/PM format.

        Args:
            minutes: Minutes since midnight.

        Returns:
            Formatted time string.

        Raises:
            None.
        """
        hour = (minutes // 60) % 24
        minute = minutes % 60
        period = "AM" if hour < 12 else "PM"
        display_hour = hour % 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour}:{minute:02d} {period}"

    def _round_to_quarter(self, value: float) -> float:
        """
        Rounds a float to the nearest quarter hour.

        Args:
            value: Hour value.

        Returns:
            Rounded hour value.

        Raises:
            None.
        """
        rounded = round(value * 4) / 4
        return round(rounded, 2)
