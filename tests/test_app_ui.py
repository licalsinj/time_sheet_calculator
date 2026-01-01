"""
Tests for app UI helpers and view wiring.
"""

from __future__ import annotations

from pathlib import Path
import sys
import types
from typing import Generator, Optional

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
sys.path.append(str(SRC_PATH))

import tkinter as tk
from tkinter import font as tkfont
import customtkinter as ctk

from app import TimeSheetApp, DEFAULT_BORDER_COLOR


def test_main_entrypoint_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Exercises the module entry point without blocking.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        None.

    Raises:
        None.
    """
    import runpy
    import customtkinter as ctk_module

    created: list[ctk_module.CTk] = []

    original_ctk = ctk_module.CTk

    class DummyCTk(original_ctk):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            created.append(self)

    monkeypatch.setattr(ctk_module, "CTk", DummyCTk)
    monkeypatch.setattr(ctk_module.CTk, "mainloop", lambda self: None)

    runpy.run_module("app", run_name="__main__")

    for instance in created:
        instance.destroy()


@pytest.fixture()
def app_instance() -> Generator[TimeSheetApp, None, None]:
    """
    Creates and destroys a TimeSheetApp instance.

    Args:
        None.

    Returns:
        TimeSheetApp instance.

    Raises:
        None.
    """
    root: Optional[ctk.CTk] = None
    try:
        root = ctk.CTk()
        root.withdraw()
        app = TimeSheetApp(root)
        yield app
    except tk.TclError:
        pytest.skip("Tkinter display not available for UI tests.")
    finally:
        if root is not None:
            root.destroy()


def test_auto_insert_colon_inserts_once(app_instance: TimeSheetApp) -> None:
    """
    Inserts a colon for numeric hour input.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    entry = app_instance.entries["Monday"]["start"]
    entry.delete(0, "end")
    entry.insert(0, "8")
    event = types.SimpleNamespace(keysym="8")
    app_instance._auto_insert_colon(event, entry)
    assert entry.get() == "8:"


def test_auto_insert_colon_ignores_navigation(app_instance: TimeSheetApp) -> None:
    """
    Skips colon insertion for navigation keys.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    entry = app_instance.entries["Monday"]["start"]
    entry.delete(0, "end")
    entry.insert(0, "8")
    event = types.SimpleNamespace(keysym="BackSpace")
    app_instance._auto_insert_colon(event, entry)
    assert entry.get() == "8"


def test_auto_insert_colon_skips_existing_colon(app_instance: TimeSheetApp) -> None:
    """
    Leaves input unchanged when a colon is already present.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    entry = app_instance.entries["Monday"]["start"]
    entry.delete(0, "end")
    entry.insert(0, "8:")
    event = types.SimpleNamespace(keysym="8")
    app_instance._auto_insert_colon(event, entry)
    assert entry.get() == "8:"


def test_normalize_time_entry_valid(app_instance: TimeSheetApp) -> None:
    """
    Normalizes a valid time input on focus loss.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    entry = app_instance.entries["Monday"]["start"]
    entry.delete(0, "end")
    entry.insert(0, "8")
    app_instance._normalize_time_entry(entry, assume_am=True)
    assert entry.get() == "8:00 AM"


def test_normalize_time_entry_invalid_sets_border(app_instance: TimeSheetApp) -> None:
    """
    Flags invalid time input with a red border.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    entry = app_instance.entries["Monday"]["start"]
    entry.delete(0, "end")
    entry.insert(0, "25:00")
    app_instance._normalize_time_entry(entry, assume_am=True)
    assert entry.cget("border_color") == "red"


def test_normalize_time_entry_empty_no_change(app_instance: TimeSheetApp) -> None:
    """
    Leaves empty entries untouched on normalization.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    entry = app_instance.entries["Monday"]["start"]
    entry.delete(0, "end")
    app_instance._normalize_time_entry(entry, assume_am=True)
    assert entry.get() == ""


def test_validate_time_entry_sets_border(app_instance: TimeSheetApp) -> None:
    """
    Applies validation coloring based on time validity.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    entry = app_instance.entries["Monday"]["start"]
    entry.delete(0, "end")
    entry.insert(0, "25:00")
    app_instance._validate_time_entry(entry, assume_am=True)
    assert entry.cget("border_color") == "red"

    entry.delete(0, "end")
    entry.insert(0, "8:00 AM")
    app_instance._validate_time_entry(entry, assume_am=True)
    assert entry.cget("border_color") != "red"

    entry.delete(0, "end")
    app_instance._validate_time_entry(entry, assume_am=True)
    assert entry.cget("border_color") == DEFAULT_BORDER_COLOR


def test_validate_lunch_entry(app_instance: TimeSheetApp) -> None:
    """
    Marks invalid lunch values in red and clears for valid input.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    entry = app_instance.entries["Monday"]["lunch"]
    entry.delete(0, "end")
    entry.insert(0, "abc")
    app_instance._validate_lunch_entry(entry)
    assert entry.cget("border_color") == "red"

    entry.delete(0, "end")
    entry.insert(0, "-1")
    app_instance._validate_lunch_entry(entry)
    assert entry.cget("border_color") == "red"

    entry.delete(0, "end")
    entry.insert(0, "30")
    app_instance._validate_lunch_entry(entry)
    assert entry.cget("border_color") != "red"

    entry.delete(0, "end")
    app_instance._validate_lunch_entry(entry)
    assert entry.cget("border_color") == DEFAULT_BORDER_COLOR


def test_validate_time_range_sets_end_red(app_instance: TimeSheetApp) -> None:
    """
    Flags end time when it is before the start time.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    start_entry = app_instance.entries["Monday"]["start"]
    end_entry = app_instance.entries["Monday"]["end"]
    start_entry.delete(0, "end")
    end_entry.delete(0, "end")
    start_entry.insert(0, "5:00 PM")
    end_entry.insert(0, "8:00 AM")
    app_instance._validate_time_range("Monday")
    assert end_entry.cget("border_color") == "red"


def test_validate_time_range_early_returns(app_instance: TimeSheetApp) -> None:
    """
    Returns early when a start or end value is missing.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    start_entry = app_instance.entries["Monday"]["start"]
    end_entry = app_instance.entries["Monday"]["end"]
    start_entry.delete(0, "end")
    end_entry.delete(0, "end")
    start_entry.insert(0, "8:00 AM")
    app_instance._validate_time_range("Monday")
    assert end_entry.cget("border_color") != "red"

    start_entry.delete(0, "end")
    end_entry.delete(0, "end")
    start_entry.insert(0, "asdf")
    end_entry.insert(0, "5:00 PM")
    app_instance._validate_time_range("Monday")
    assert end_entry.cget("border_color") != "red"


def test_update_day_hours_with_blank_lunch(app_instance: TimeSheetApp) -> None:
    """
    Calculates hours with assumed lunch and highlights lunch warning.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    fields = app_instance.entries["Monday"]
    fields["start"].delete(0, "end")
    fields["end"].delete(0, "end")
    fields["lunch"].delete(0, "end")
    fields["start"].insert(0, "8:00 AM")
    fields["end"].insert(0, "5:00 PM")
    app_instance._update_day_hours("Monday")
    assert fields["hours"].cget("text") == "8"
    assert fields["lunch"].cget("border_color") == "yellow"


def test_update_day_hours_incomplete_clears(app_instance: TimeSheetApp) -> None:
    """
    Clears hours and lunch highlight when a row is incomplete.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    fields = app_instance.entries["Monday"]
    fields["start"].delete(0, "end")
    fields["end"].delete(0, "end")
    fields["lunch"].configure(border_color="red")
    app_instance._update_day_hours("Monday")
    assert fields["hours"].cget("text") == ""
    assert fields["lunch"].cget("border_color") == DEFAULT_BORDER_COLOR


def test_update_day_hours_invalid_lunch_clears(app_instance: TimeSheetApp) -> None:
    """
    Clears hours and marks lunch red for invalid lunch input.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    fields = app_instance.entries["Monday"]
    fields["start"].delete(0, "end")
    fields["end"].delete(0, "end")
    fields["lunch"].delete(0, "end")
    fields["start"].insert(0, "8:00 AM")
    fields["end"].insert(0, "5:00 PM")
    fields["lunch"].insert(0, "abc")
    app_instance._update_day_hours("Monday")
    assert fields["hours"].cget("text") == ""
    assert fields["lunch"].cget("border_color") == "red"


def test_update_day_hours_invalid_time_clears(app_instance: TimeSheetApp) -> None:
    """
    Clears hours when time parsing fails.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    fields = app_instance.entries["Monday"]
    fields["start"].delete(0, "end")
    fields["end"].delete(0, "end")
    fields["start"].insert(0, "asdf")
    fields["end"].insert(0, "5:00 PM")
    app_instance._update_day_hours("Monday")
    assert fields["hours"].cget("text") == ""


def test_update_day_hours_end_before_start_clears(app_instance: TimeSheetApp) -> None:
    """
    Clears hours when end time is before start time.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    fields = app_instance.entries["Monday"]
    fields["start"].delete(0, "end")
    fields["end"].delete(0, "end")
    fields["start"].insert(0, "5:00 PM")
    fields["end"].insert(0, "8:00 AM")
    app_instance._update_day_hours("Monday")
    assert fields["hours"].cget("text") == ""


def test_update_day_hours_negative_lunch_clears(app_instance: TimeSheetApp) -> None:
    """
    Clears hours and marks lunch red for negative lunch input.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    fields = app_instance.entries["Monday"]
    fields["start"].delete(0, "end")
    fields["end"].delete(0, "end")
    fields["lunch"].delete(0, "end")
    fields["start"].insert(0, "8:00 AM")
    fields["end"].insert(0, "5:00 PM")
    fields["lunch"].insert(0, "-1")
    app_instance._update_day_hours("Monday")
    assert fields["hours"].cget("text") == ""
    assert fields["lunch"].cget("border_color") == "red"


def test_update_day_hours_lunch_exceeds_shift(app_instance: TimeSheetApp) -> None:
    """
    Clears hours when lunch exceeds the shift length.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    fields = app_instance.entries["Monday"]
    fields["start"].delete(0, "end")
    fields["end"].delete(0, "end")
    fields["lunch"].delete(0, "end")
    fields["start"].insert(0, "8:00 AM")
    fields["end"].insert(0, "9:00 AM")
    fields["lunch"].insert(0, "120")
    app_instance._update_day_hours("Monday")
    assert fields["hours"].cget("text") == ""

def test_clear_validation_styles_resets_borders(app_instance: TimeSheetApp) -> None:
    """
    Restores default borders for all inputs.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    entry = app_instance.entries["Monday"]["start"]
    entry.configure(border_color="red")
    app_instance._clear_validation_styles()
    assert entry.cget("border_color") == DEFAULT_BORDER_COLOR


def test_resolve_about_path_none(app_instance: TimeSheetApp, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Returns None when ABOUT.md is not found.

    Args:
        app_instance: TimeSheetApp instance.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        None.

    Raises:
        None.
    """
    def fake_exists(_: str) -> bool:
        return False

    monkeypatch.setattr("os.path.exists", fake_exists)
    assert app_instance._resolve_about_path() is None


def test_refresh_about_button_state_enabled(app_instance: TimeSheetApp) -> None:
    """
    Enables About when ABOUT.md exists.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    app_instance._refresh_about_button_state()
    assert app_instance.about_button.cget("state") == "normal"


def test_refresh_about_button_state_disabled(app_instance: TimeSheetApp) -> None:
    """
    Disables About when ABOUT.md is missing.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    app_instance._get_about_content = types.MethodType(lambda self: None, app_instance)
    app_instance._refresh_about_button_state()
    assert app_instance.about_button.cget("state") == "disabled"


def test_show_about_returns_when_missing(app_instance: TimeSheetApp) -> None:
    """
    Returns early when ABOUT.md is missing.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    app_instance._about_content = None
    app_instance._get_about_content = types.MethodType(lambda self: None, app_instance)
    app_instance._show_about()
    toplevels = [w for w in app_instance.master.winfo_children() if isinstance(w, ctk.CTkToplevel)]
    assert len(toplevels) == 0


def test_show_and_hide_tooltip(app_instance: TimeSheetApp) -> None:
    """
    Creates and removes the About tooltip when disabled.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    app_instance._get_about_content = types.MethodType(lambda self: None, app_instance)
    app_instance._refresh_about_button_state()
    app_instance._show_disabled_about_tooltip(None)
    assert app_instance._about_tooltip is not None
    app_instance._hide_disabled_about_tooltip(None)
    assert app_instance._about_tooltip is None


def test_show_disabled_tooltip_returns_when_about_exists(app_instance: TimeSheetApp) -> None:
    """
    Does not create a tooltip when About is enabled.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    app_instance._get_about_content = types.MethodType(lambda self: "## About", app_instance)
    app_instance._show_disabled_about_tooltip(None)
    assert app_instance._about_tooltip is None


def test_show_disabled_tooltip_returns_when_tooltip_exists(app_instance: TimeSheetApp) -> None:
    """
    Avoids creating a duplicate tooltip.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    app_instance._get_about_content = types.MethodType(lambda self: None, app_instance)
    app_instance._refresh_about_button_state = types.MethodType(lambda self: None, app_instance)
    app_instance._about_tooltip = ctk.CTkToplevel(app_instance)
    app_instance._show_disabled_about_tooltip(None)
    assert app_instance._about_tooltip is not None
    app_instance._about_tooltip.destroy()
    app_instance._about_tooltip = None


def test_show_about_renders_markdown(app_instance: TimeSheetApp) -> None:
    """
    Opens About dialog and renders markdown content.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    app_instance._get_about_content = types.MethodType(lambda self: "## About", app_instance)
    rendered: dict[str, bool] = {"called": False}

    def fake_render(textbox: ctk.CTkTextbox, content: str) -> None:
        rendered["called"] = True

    app_instance._render_markdown_to_textbox = types.MethodType(
        lambda self, textbox, content: fake_render(textbox, content), app_instance
    )
    app_instance._show_about()
    assert rendered["called"] is True


def test_render_markdown_handles_styles(app_instance: TimeSheetApp) -> None:
    """
    Renders headings, bullets, bold, and italic text.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    textbox = ctk.CTkTextbox(app_instance.master, wrap="word", width=200, height=100)
    content = "# Title\n\n## Subtitle\n- **Bold** item\n- *Italic* item\nPlain"
    app_instance._render_markdown_to_textbox(textbox, content)
    raw_text = textbox._textbox.get("1.0", "end").strip()
    assert "Title" in raw_text
    assert "Subtitle" in raw_text
    assert "Bold" in raw_text
    assert "Italic" in raw_text
    textbox.destroy()


def test_get_textbox_base_font_handles_variants(app_instance: TimeSheetApp) -> None:
    """
    Handles font objects and fallback font settings.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    textbox = ctk.CTkTextbox(app_instance.master, wrap="word", width=100, height=60)
    font_obj = app_instance._get_textbox_base_font(textbox)
    assert font_obj is not None
    textbox.destroy()

    class DummyFont:
        def cget(self, key: str) -> str:
            return {"family": "Arial", "size": "14", "weight": "normal", "slant": "roman"}[key]

    class DummyText:
        def cget(self, key: str) -> object:
            return DummyFont()

    dummy_text = DummyText()
    assert app_instance._get_textbox_base_font(dummy_text) is not None

    class BadFont:
        def cget(self, key: str) -> str:
            raise tk.TclError("bad font")

    class BadText:
        def cget(self, key: str) -> object:
            return BadFont()

    bad_text = BadText()
    assert app_instance._get_textbox_base_font(bad_text) is not None

    base_font = tkfont.Font(family="Arial", size=12)

    class FontText:
        def cget(self, key: str) -> object:
            return base_font

    font_text = FontText()
    assert app_instance._get_textbox_base_font(font_text) is base_font


def test_build_markdown_fonts_handles_bad_size(app_instance: TimeSheetApp) -> None:
    """
    Builds fonts when base size cannot be coerced to an integer.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    class DummyFont:
        def cget(self, key: str) -> str:
            if key == "size":
                return "bad"
            if key == "family":
                return "Arial"
            if key == "weight":
                return "normal"
            if key == "slant":
                return "roman"
            return ""

    fonts = app_instance._build_markdown_fonts(DummyFont())
    assert "h1" in fonts

def test_calculate_error_flow(app_instance: TimeSheetApp) -> None:
    """
    Populates invalid inputs and confirms error display flow.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    app_instance.entries["Monday"]["start"].insert(0, "asdf")
    app_instance.entries["Tuesday"]["start"].insert(0, "25:00")
    app_instance._calculate()
    assert "invalid start time" in app_instance.error_label.cget("text").lower()
    assert app_instance.total_hours_value.cget("text") == ""


def test_calculate_errors_and_warnings(app_instance: TimeSheetApp) -> None:
    """
    Shows warnings even when errors are present.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    app_instance.entries["Monday"]["start"].insert(0, "asdf")
    app_instance.entries["Tuesday"]["start"].insert(0, "8:00 AM")
    app_instance.entries["Tuesday"]["end"].insert(0, "5:00 PM")
    app_instance._calculate()
    assert "invalid start time" in app_instance.error_label.cget("text").lower()
    assert "lunch assumed" in app_instance.warning_label.cget("text").lower()


def test_calculate_overtime_flow(app_instance: TimeSheetApp) -> None:
    """
    Confirms overtime coloring and success message display.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday"]:
        app_instance.entries[day]["start"].delete(0, "end")
        app_instance.entries[day]["end"].delete(0, "end")
        app_instance.entries[day]["lunch"].delete(0, "end")
        app_instance.entries[day]["start"].insert(0, "7:00 AM")
        app_instance.entries[day]["end"].insert(0, "7:00 PM")
        app_instance.entries[day]["lunch"].insert(0, "60")
    app_instance.entries["Friday"]["start"].delete(0, "end")
    app_instance.entries["Friday"]["start"].insert(0, "8:00 AM")
    app_instance._calculate()
    assert app_instance.hours_to_40_value.cget("text_color") == "green"
    assert "40 hours reached" in app_instance.success_label.cget("text")


def test_calculate_warning_flow(app_instance: TimeSheetApp) -> None:
    """
    Confirms warning display for assumed lunch and Friday defaults.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday"]:
        app_instance.entries[day]["start"].delete(0, "end")
        app_instance.entries[day]["end"].delete(0, "end")
        app_instance.entries[day]["lunch"].delete(0, "end")
        app_instance.entries[day]["start"].insert(0, "8:00 AM")
        app_instance.entries[day]["end"].insert(0, "5:00 PM")
    app_instance.entries["Friday"]["start"].delete(0, "end")
    app_instance.entries["Friday"]["start"].insert(0, "8:00 AM")
    app_instance._calculate()
    assert "lunch assumed" in app_instance.warning_label.cget("text").lower()
    assert app_instance.friday_value.cget("text") != ""


def test_focus_out_bindings_update_hours(app_instance: TimeSheetApp) -> None:
    """
    Triggers focus-out bindings to exercise bound callbacks.

    Args:
        app_instance: TimeSheetApp instance.

    Returns:
        None.

    Raises:
        None.
    """
    start_entry = app_instance.entries["Monday"]["start"]
    end_entry = app_instance.entries["Monday"]["end"]
    lunch_entry = app_instance.entries["Monday"]["lunch"]
    start_entry.delete(0, "end")
    end_entry.delete(0, "end")
    lunch_entry.delete(0, "end")
    start_entry.insert(0, "8:00 AM")
    end_entry.insert(0, "5:00 PM")
    app_instance.master.deiconify()
    app_instance.master.update()
    start_entry.focus_force()
    app_instance.master.update()
    start_entry.event_generate("<FocusOut>", when="tail")
    end_entry.focus_force()
    app_instance.master.update()
    end_entry.event_generate("<FocusOut>", when="tail")
    lunch_entry.focus_force()
    app_instance.master.update()
    start_entry.focus_force()
    app_instance.master.update()
    assert app_instance.entries["Monday"]["hours"].cget("text") != ""
