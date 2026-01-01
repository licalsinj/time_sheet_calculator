"""
Tests for UI view-model helpers.
"""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Dict, List, Tuple

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
sys.path.append(str(SRC_PATH))

from timesheet_service import DayInput, TimeSheetService
from ui_view_model import UIState, compute_ui_state, format_hours_display


def build_week(overrides: Dict[str, Tuple[str, str, str]]) -> List[DayInput]:
    """
    Builds a Monday–Friday list of DayInput objects with optional overrides.

    Args:
        overrides: Mapping of day name to (start, end, lunch) strings.

    Returns:
        List of DayInput objects in weekday order.

    Raises:
        None.
    """
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    inputs: List[DayInput] = []
    for day in days:
        start, end, lunch = overrides.get(day, ("", "", ""))
        inputs.append(DayInput(day_name=day, start_time=start, end_time=end, lunch_minutes=lunch))
    return inputs


def test_format_hours_display_trims() -> None:
    """
    Confirms trailing zeros are trimmed in hour display formatting.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """
    assert format_hours_display(8.0) == "8"
    assert format_hours_display(7.5) == "7.5"
    assert format_hours_display(7.25) == "7.25"
    assert format_hours_display(7.333) == "7.33"
    assert format_hours_display(0.0) == "0"


def test_compute_ui_state_error_clears_kpis() -> None:
    """
    Ensures error state clears KPI display fields.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """
    service = TimeSheetService()
    week = build_week({
        "Monday": ("asdf", "5:00 PM", "60"),
        "Friday": ("8:00 AM", "", ""),
    })
    state = compute_ui_state(service, week)
    assert state.errors
    assert state.total_hours_text == ""
    assert state.hours_to_40_text == ""
    assert state.friday_clock_out_text == ""
    assert state.daily_hours_text == {}


def test_compute_ui_state_overtime_flags() -> None:
    """
    Confirms overtime flag and KPI text for an over-40 week.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """
    service = TimeSheetService()
    week = build_week({
        "Monday": ("7:00 AM", "7:00 PM", "60"),
        "Tuesday": ("7:00 AM", "7:00 PM", "60"),
        "Wednesday": ("7:00 AM", "7:00 PM", "60"),
        "Thursday": ("7:00 AM", "7:00 PM", "60"),
        "Friday": ("8:00 AM", "", ""),
    })
    state = compute_ui_state(service, week)
    assert state.total_hours_text == "44.0"
    assert state.hours_to_40_text == "-4.0"
    assert state.hours_to_40_is_overtime is True
    assert state.friday_clock_out_text == "8:00 AM"
    assert state.daily_hours_text["Monday"] == "11"


def test_compute_ui_state_lunch_warning_days() -> None:
    """
    Tracks which days have blank lunch entries.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """
    service = TimeSheetService()
    week = build_week({
        "Monday": ("8:00 AM", "5:00 PM", ""),
        "Tuesday": ("8:00 AM", "5:00 PM", "30"),
        "Wednesday": ("8:00 AM", "5:00 PM", ""),
        "Thursday": ("8:00 AM", "5:00 PM", "45"),
        "Friday": ("8:00 AM", "", ""),
    })
    state = compute_ui_state(service, week)
    assert state.lunch_warning_days == {"Monday", "Wednesday", "Friday"}


def test_compute_ui_state_daily_hours_formatting() -> None:
    """
    Formats daily hours using trimmed trailing zeros.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """
    service = TimeSheetService()
    week = build_week({
        "Monday": ("8:00 AM", "5:00 PM", "30"),
        "Friday": ("8:00 AM", "", ""),
    })
    state = compute_ui_state(service, week)
    assert state.daily_hours_text["Monday"] == "8.5"


def test_compute_ui_state_field_errors() -> None:
    """
    Surfaces field-level errors from the service.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """
    service = TimeSheetService()
    week = build_week({
        "Monday": ("25:00", "", ""),
        "Friday": ("8:00 AM", "", ""),
    })
    state = compute_ui_state(service, week)
    assert state.field_errors.get("Monday_start") == "Invalid start time"


def test_compute_ui_state_empty_week_warnings() -> None:
    """
    Confirms Friday defaults contribute warnings for an empty week.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """
    service = TimeSheetService()
    week = build_week({})
    state = compute_ui_state(service, week)
    assert "Friday start time assumed to be 8:00 AM" in state.warnings
    assert "Friday: lunch assumed to be 60 minutes" in state.warnings
