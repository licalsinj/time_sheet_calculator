"""
ui_view_model.py

Pure helpers for mapping service results into UI-friendly state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set

from timesheet_service import DayInput, TimeSheetService


@dataclass
class UIState:
    """
    UI-facing state derived from the service calculation.

    Attributes:
        errors: List of blocking error messages.
        warnings: List of non-blocking warning messages.
        successes: List of informational success messages.
        total_hours_text: Display text for total hours.
        hours_to_40_text: Display text for hours to 40.
        hours_to_40_is_overtime: Whether the value indicates overtime.
        friday_clock_out_text: Display text for Friday clock-out time.
        daily_hours_text: Mapping of day name to display hours.
        field_errors: Mapping of field identifiers to error messages.
        lunch_warning_days: Set of day names with blank lunch entries.
    """
    errors: List[str]
    warnings: List[str]
    successes: List[str]
    total_hours_text: str
    hours_to_40_text: str
    hours_to_40_is_overtime: bool
    friday_clock_out_text: str
    daily_hours_text: Dict[str, str]
    field_errors: Dict[str, str]
    lunch_warning_days: Set[str]


def format_hours_display(value: float) -> str:
    """
    Formats hour values by trimming unnecessary trailing zeros.

    Args:
        value: Hour value to display.

    Returns:
        Human-friendly string (e.g., 8 -> "8", 7.5 -> "7.5").

    Raises:
        None.
    """
    return f"{value:.2f}".rstrip("0").rstrip(".")


def compute_ui_state(
    service: TimeSheetService, day_inputs: List[DayInput]
) -> UIState:
    """
    Computes UI display state from inputs using the service.

    Args:
        service: TimeSheetService instance.
        day_inputs: List of DayInput objects for the week.

    Returns:
        UIState containing display-ready values.

    Raises:
        None.
    """
    result = service.calculate_week(day_inputs)

    daily_hours_text = {
        day: format_hours_display(hours)
        for day, hours in result.daily_hours.items()
    }

    total_hours_text = "" if result.total_hours is None else str(result.total_hours)
    hours_to_40_text = "" if result.hours_to_40 is None else str(result.hours_to_40)
    friday_clock_out_text = (
        "" if result.friday_clock_out is None else str(result.friday_clock_out)
    )

    hours_to_40_is_overtime = (
        result.hours_to_40 is not None and result.hours_to_40 < 0
    )

    lunch_warning_days = {
        day.day_name for day in day_inputs if not day.lunch_minutes.strip()
    }

    return UIState(
        errors=result.errors,
        warnings=result.warnings,
        successes=result.successes,
        total_hours_text=total_hours_text,
        hours_to_40_text=hours_to_40_text,
        hours_to_40_is_overtime=hours_to_40_is_overtime,
        friday_clock_out_text=friday_clock_out_text,
        daily_hours_text=daily_hours_text,
        field_errors=result.field_errors,
        lunch_warning_days=lunch_warning_days,
    )
