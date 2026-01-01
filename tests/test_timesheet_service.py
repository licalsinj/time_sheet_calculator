"""
Tests for TimeSheetService behavior based on the spec and discussed rules.
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


@pytest.fixture()
def service() -> TimeSheetService:
    """
    Provides a fresh TimeSheetService instance.

    Args:
        None.

    Returns:
        TimeSheetService instance.

    Raises:
        None.
    """
    return TimeSheetService()


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


def test_parse_time_basic_formats(service: TimeSheetService) -> None:
    """
    Validates basic time parsing without an explicit period.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    minutes, display, error = service._parse_time("8", assume_am=True)
    assert minutes == 8 * 60
    assert display == "8:00 AM"
    assert error is False

    minutes, display, error = service._parse_time("8", assume_am=False)
    assert minutes == 20 * 60
    assert display == "8:00 PM"
    assert error is False


def test_parse_time_period_variants(service: TimeSheetService) -> None:
    """
    Validates parsing with AM/PM suffixes and 24-hour inputs.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    minutes, display, error = service._parse_time("8a", assume_am=True)
    assert minutes == 8 * 60
    assert display == "8:00 AM"
    assert error is False

    minutes, display, error = service._parse_time("8p", assume_am=True)
    assert minutes == 20 * 60
    assert display == "8:00 PM"
    assert error is False

    minutes, display, error = service._parse_time("16:35", assume_am=True)
    assert minutes == 16 * 60 + 35
    assert display == "4:35 PM"
    assert error is False


def test_parse_time_invalid_inputs(service: TimeSheetService) -> None:
    """
    Ensures invalid times are rejected.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    _, _, error = service._parse_time("25:00", assume_am=True)
    assert error is True

    _, _, error = service._parse_time("9:99", assume_am=True)
    assert error is True

    _, _, error = service._parse_time("", assume_am=True)
    assert error is True


def test_parse_time_no_period_handles_twelve(service: TimeSheetService) -> None:
    """
    Confirms 12 without a period respects the AM/PM assumption.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    minutes, display, error = service._parse_time("12", assume_am=True)
    assert minutes == 0
    assert display == "12:00 AM"
    assert error is False

    minutes, display, error = service._parse_time("12", assume_am=False)
    assert minutes == 12 * 60
    assert display == "12:00 PM"
    assert error is False


def test_minutes_to_display_boundaries(service: TimeSheetService) -> None:
    """
    Checks AM/PM conversion at day boundaries.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    assert service._minutes_to_display(0) == "12:00 AM"
    assert service._minutes_to_display(12 * 60) == "12:00 PM"
    assert service._minutes_to_display(23 * 60 + 59) == "11:59 PM"


def test_round_to_quarter_hours(service: TimeSheetService) -> None:
    """
    Verifies rounding to the nearest quarter hour.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    assert service._round_to_quarter(8.0) == 8.0
    assert service._round_to_quarter(8.1667) == 8.25
    assert service._round_to_quarter(8.375) == 8.5


def test_incomplete_day_assumes_eight_hours(service: TimeSheetService) -> None:
    """
    Confirms blank start/end days assume an 8-hour shift.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({})
    result = service.calculate_week(week)
    assert result.total_hours == 40.0
    assert result.errors == []


def test_partial_day_start_only_non_friday_validates_start(service: TimeSheetService) -> None:
    """
    Validates start-only entries and assumes 8 hours for non-Friday days.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8:00 AM", "", ""),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert result.errors == []
    assert result.total_hours == 32.0


def test_partial_day_start_only_invalid_start_errors(service: TimeSheetService) -> None:
    """
    Confirms invalid start times are reported even if end is blank.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("25:00", "", ""),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid start time" in result.errors
    assert result.field_errors.get("Monday_start") == "Invalid start time"


def test_incomplete_day_with_invalid_lunch_errors(service: TimeSheetService) -> None:
    """
    Rejects lunch input when both start and end are blank.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("", "", "abc"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid lunch duration" in result.errors
    assert result.field_errors.get("Monday_lunch") == "Invalid lunch duration"


def test_incomplete_day_with_negative_lunch_errors(service: TimeSheetService) -> None:
    """
    Rejects negative lunch values when both start and end are blank.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("", "", "-5"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid lunch duration" in result.errors
    assert result.field_errors.get("Monday_lunch") == "Invalid lunch duration"


def test_partial_day_start_only_invalid_lunch_errors(service: TimeSheetService) -> None:
    """
    Rejects invalid lunch when only start is provided for a non-Friday day.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8:00 AM", "", "abc"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid lunch duration" in result.errors
    assert result.field_errors.get("Monday_lunch") == "Invalid lunch duration"


def test_partial_day_start_only_negative_lunch_errors(service: TimeSheetService) -> None:
    """
    Rejects negative lunch when only start is provided for a non-Friday day.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8:00 AM", "", "-1"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid lunch duration" in result.errors
    assert result.field_errors.get("Monday_lunch") == "Invalid lunch duration"


def test_partial_day_start_only_friday_invalid_start_errors(service: TimeSheetService) -> None:
    """
    Reports invalid Friday start when end is blank.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Friday": ("25:00", "", ""),
    })
    result = service.calculate_week(week)
    assert "Friday: invalid start time" in result.errors
    assert result.field_errors.get("Friday_start") == "Invalid start time"


def test_partial_day_start_only_friday_invalid_lunch_errors(service: TimeSheetService) -> None:
    """
    Reports invalid Friday lunch when end is blank.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Friday": ("8:00 AM", "", "abc"),
    })
    result = service.calculate_week(week)
    assert "Friday: invalid lunch duration" in result.errors
    assert result.field_errors.get("Friday_lunch") == "Invalid lunch duration"


def test_partial_day_start_only_friday_negative_lunch_errors(service: TimeSheetService) -> None:
    """
    Rejects negative Friday lunch when end is blank.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Friday": ("8:00 AM", "", "-1"),
    })
    result = service.calculate_week(week)
    assert "Friday: invalid lunch duration" in result.errors
    assert result.field_errors.get("Friday_lunch") == "Invalid lunch duration"


def test_partial_day_end_only_validates_end(service: TimeSheetService) -> None:
    """
    Validates end-only entries and assumes 8 hours for non-Friday days.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("", "5:00 PM", ""),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert result.errors == []
    assert result.total_hours == 32.0


def test_partial_day_end_only_invalid_end_errors(service: TimeSheetService) -> None:
    """
    Confirms invalid end times are reported even if start is blank.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("", "25:00", ""),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid end time" in result.errors
    assert result.field_errors.get("Monday_end") == "Invalid end time"


def test_partial_day_end_only_invalid_lunch_errors(service: TimeSheetService) -> None:
    """
    Rejects invalid lunch when only end is provided.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("", "5:00 PM", "abc"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid lunch duration" in result.errors
    assert result.field_errors.get("Monday_lunch") == "Invalid lunch duration"


def test_partial_day_end_only_negative_lunch_errors(service: TimeSheetService) -> None:
    """
    Rejects negative lunch when only end is provided.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("", "5:00 PM", "-1"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid lunch duration" in result.errors
    assert result.field_errors.get("Monday_lunch") == "Invalid lunch duration"


def test_blank_lunch_produces_warning(service: TimeSheetService) -> None:
    """
    Ensures blank lunch generates a warning but no error.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8:00 AM", "5:00 PM", ""),
        "Tuesday": ("8:00 AM", "5:00 PM", ""),
        "Wednesday": ("8:00 AM", "5:00 PM", ""),
        "Thursday": ("8:00 AM", "5:00 PM", ""),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert result.errors == []
    assert "Monday: lunch assumed to be 60 minutes" in result.warnings


def test_negative_lunch_is_error(service: TimeSheetService) -> None:
    """
    Confirms negative lunch values are rejected.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8:00 AM", "5:00 PM", "-1"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid lunch duration" in result.errors
    assert result.field_errors.get("Monday_lunch") == "Invalid lunch duration"


def test_non_numeric_lunch_is_error(service: TimeSheetService) -> None:
    """
    Confirms non-numeric lunch values are rejected.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8:00 AM", "5:00 PM", "abc"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid lunch duration" in result.errors


def test_lunch_exceeds_shift_is_error(service: TimeSheetService) -> None:
    """
    Rejects lunch durations longer than the shift.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8:00 AM", "9:00 AM", "120"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: lunch exceeds shift length" in result.errors


def test_end_before_start_is_error(service: TimeSheetService) -> None:
    """
    Rejects negative time ranges.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("5:00 PM", "8:00 AM", "0"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: end time is before start time" in result.errors


def test_invalid_end_with_valid_start_is_error(service: TimeSheetService) -> None:
    """
    Reports invalid end when both start and end are provided.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8:00 AM", "25:00", "0"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid end time" in result.errors
    assert result.field_errors.get("Monday_end") == "Invalid end time"


def test_errors_propagate_for_multiple_days(service: TimeSheetService) -> None:
    """
    Confirms errors are reported for every invalid field in the week.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("asdf", "", ""),
        "Tuesday": ("25:00", "", ""),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid start time" in result.errors
    assert "Tuesday: invalid start time" in result.errors
    assert result.field_errors.get("Monday_start") == "Invalid start time"
    assert result.field_errors.get("Tuesday_start") == "Invalid start time"


def test_errors_do_not_drop_warnings(service: TimeSheetService) -> None:
    """
    Ensures warnings are still returned when errors exist.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("asdf", "", ""),
        "Tuesday": ("8:00 AM", "5:00 PM", ""),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Monday: invalid start time" in result.errors
    assert "Tuesday: lunch assumed to be 60 minutes" in result.warnings


def test_friday_clock_out_for_partial_friday(service: TimeSheetService) -> None:
    """
    Calculates Friday clock-out based on pre-Friday totals.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8:00 AM", "5:00 PM", ""),
        "Tuesday": ("8:00 AM", "5:00 PM", ""),
        "Wednesday": ("8:00 AM", "5:00 PM", ""),
        "Thursday": ("8:00 AM", "5:00 PM", ""),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert result.friday_clock_out == "5:00 PM"


def test_friday_clock_out_when_40_reached_before_friday(service: TimeSheetService) -> None:
    """
    Uses the start time as the clock-out when 40 hours are already reached.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8:00 AM", "7:00 PM", "60"),
        "Tuesday": ("8:00 AM", "7:00 PM", "60"),
        "Wednesday": ("8:00 AM", "7:00 PM", "60"),
        "Thursday": ("8:00 AM", "7:00 PM", "60"),
        "Friday": ("9:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert result.friday_clock_out == "9:00 AM"
    assert "40 hours reached before Friday this week" in result.successes


def test_friday_end_time_is_used_when_present(service: TimeSheetService) -> None:
    """
    Uses Friday end time for clock-out when provided.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8:00 AM", "5:00 PM", "60"),
        "Tuesday": ("8:00 AM", "5:00 PM", "60"),
        "Wednesday": ("8:00 AM", "5:00 PM", "60"),
        "Thursday": ("8:00 AM", "5:00 PM", "60"),
        "Friday": ("8:00 AM", "12:00 PM", "0"),
    })
    result = service.calculate_week(week)
    assert result.friday_clock_out == "12:00 PM"


def test_daily_hours_excludes_partial_friday(service: TimeSheetService) -> None:
    """
    Ensures daily hours omit Friday when it has no end time.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8:00 AM", "5:00 PM", "60"),
        "Tuesday": ("8:00 AM", "5:00 PM", "60"),
        "Wednesday": ("8:00 AM", "5:00 PM", "60"),
        "Thursday": ("8:00 AM", "5:00 PM", "60"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert "Friday" not in result.daily_hours


def test_hours_to_40_signs(service: TimeSheetService) -> None:
    """
    Confirms Hours to 40 is positive when under and negative when over.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    under_week = build_week({
        "Monday": ("8:00 AM", "5:00 PM", "60"),
        "Tuesday": ("8:00 AM", "5:00 PM", "60"),
        "Wednesday": ("8:00 AM", "5:00 PM", "60"),
        "Thursday": ("8:00 AM", "5:00 PM", "60"),
        "Friday": ("8:00 AM", "", ""),
    })
    under_result = service.calculate_week(under_week)
    assert under_result.hours_to_40 == 8.0

    over_week = build_week({
        "Monday": ("7:00 AM", "7:00 PM", "60"),
        "Tuesday": ("7:00 AM", "7:00 PM", "60"),
        "Wednesday": ("7:00 AM", "7:00 PM", "60"),
        "Thursday": ("7:00 AM", "7:00 PM", "60"),
        "Friday": ("8:00 AM", "", ""),
    })
    over_result = service.calculate_week(over_week)
    assert over_result.hours_to_40 == -4.0


def test_normalized_times_mapping(service: TimeSheetService) -> None:
    """
    Confirms normalized time strings are returned for valid inputs.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("8", "5", "60"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert result.normalized_times.get("Monday_start") == "8:00 AM"
    assert result.normalized_times.get("Monday_end") == "5:00 PM"


def test_errors_block_kpi_values(service: TimeSheetService) -> None:
    """
    Ensures totals and Friday clock-out are cleared when errors exist.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    week = build_week({
        "Monday": ("asdf", "5:00 PM", "60"),
        "Friday": ("8:00 AM", "", ""),
    })
    result = service.calculate_week(week)
    assert result.total_hours is None
    assert result.hours_to_40 is None
    assert result.friday_clock_out is None


def test_friday_clock_out_invalid_start_returns_none(service: TimeSheetService) -> None:
    """
    Returns None when Friday start is invalid during clock-out calculation.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    days = build_week({
        "Friday": ("25:00", "", ""),
    })
    result = service._calculate_friday_clock_out(
        days=days,
        pre_friday_minutes=0,
        friday_minutes=None,
        warnings=[],
        successes=[],
        normalized={},
    )
    assert result is None


def test_friday_clock_out_invalid_lunch_returns_none(service: TimeSheetService) -> None:
    """
    Returns None when Friday lunch is invalid during clock-out calculation.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    days = build_week({
        "Friday": ("8:00 AM", "", "abc"),
    })
    result = service._calculate_friday_clock_out(
        days=days,
        pre_friday_minutes=0,
        friday_minutes=None,
        warnings=[],
        successes=[],
        normalized={},
    )
    assert result is None


def test_friday_clock_out_negative_lunch_returns_none(service: TimeSheetService) -> None:
    """
    Returns None when Friday lunch is negative during clock-out calculation.

    Args:
        service: TimeSheetService instance.

    Returns:
        None.

    Raises:
        None.
    """
    days = build_week({
        "Friday": ("8:00 AM", "", "-1"),
    })
    result = service._calculate_friday_clock_out(
        days=days,
        pre_friday_minutes=0,
        friday_minutes=None,
        warnings=[],
        successes=[],
        normalized={},
    )
    assert result is None
