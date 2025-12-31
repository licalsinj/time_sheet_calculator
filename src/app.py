"""
app.py

CustomTkinter user interface for the time sheet calculator.
"""

import os
import tkinter as tk
from tkinter import font as tkfont
import customtkinter as ctk
from timesheet_service import TimeSheetService, DayInput
from typing import Optional

# CONSTANTS
DEFAULT_BORDER_COLOR = "#444444"

class TimeSheetApp(ctk.CTkFrame):
    """
    Main application frame containing all UI elements.
    """

    def __init__(self, master: ctk.CTk) -> None:
        """
        Sets up the frame, service, and UI layout.

        Args:
            master: Root CustomTkinter application window.

        Returns:
            None.

        Raises:
            None.
        """
        super().__init__(master)
        self.service = TimeSheetService()
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.entries: dict[str, dict[str, object]] = {}
        self._about_tooltip: Optional[ctk.CTkToplevel] = None
        self._about_path: Optional[str] = None
        self._build_ui()
    # ----------------
    # Helper Methods
    # -----------------
    
    def _auto_insert_colon(self, event: object, entry: ctk.CTkEntry) -> None:
        """
        Automatically inserts a colon after the hour portion of a time
        while the user is typing.

        Args:
            event: Tkinter key event.
            entry: The CTkEntry widget being typed into.

        Returns:
            None.

        Raises:
            None.
        """
        # Ignore backspace, delete, and navigation keys
        if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Home", "End"):
            return

        value = entry.get()

        # Ignore empty input or values that already contain a colon
        if not value or ":" in value:
            return

        # Only auto-insert when the value is purely digits (1 or 2 chars)
        if value.isdigit() and len(value) in (1, 2):
            entry.insert("end", ":")

    def _clear_validation_styles(self) -> None:
        """
        Resets all entry widgets to default border.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        for day_fields in self.entries.values():
            for key in ("start", "end", "lunch"):
                entry = day_fields[key]
                entry.configure(border_color=DEFAULT_BORDER_COLOR)

    def _clear_hours_labels(self) -> None:
        """
        Clears the per-day hours labels.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        for day_fields in self.entries.values():
            day_fields["hours"].configure(text="")

    def _clear_kpis(self) -> None:
        """
        Clears the KPI displays at the top of the UI.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        self.total_hours_value.configure(text="")
        self.hours_to_40_value.configure(text="")
        self.friday_value.configure(text="")
        self.hours_to_40_value.configure(text_color=self._hours_to_40_default_color)

    def _format_hours_display(self, value: float) -> str:
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

    def _resolve_about_path(self) -> Optional[str]:
        """
        Finds the ABOUT.md file relative to the application source directory.

        Args:
            None.

        Returns:
            Absolute path to the ABOUT file if present, otherwise None.

        Raises:
            None.
        """
        base_dir = os.path.abspath(os.path.dirname(__file__))
        for filename in ("ABOUT.md", "about.md"):
            candidate = os.path.join(base_dir, filename)
            if os.path.exists(candidate):
                return candidate
        return None

    def _refresh_about_button_state(self) -> None:
        """
        Enables or disables the About button based on ABOUT file availability.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        self._about_path = self._resolve_about_path()
        if self._about_path:
            self.about_button.configure(
                state="normal",
                hover=True,
                fg_color="white",
                text_color="black",
                text_color_disabled="black",
                border_width=0,
                hover_color="#e6e6e6",
            )
            self.about_button.unbind("<Enter>")
            self.about_button.unbind("<Leave>")
            self._hide_disabled_about_tooltip(None)
        else:
            self.about_button.configure(
                state="disabled",
                hover=False,
                fg_color="#3a3a3a",
                text_color="black",
                text_color_disabled="black",
                border_color="white",
                border_width=1,
            )
            self.about_button.bind("<Enter>", self._show_disabled_about_tooltip)
            self.about_button.bind("<Leave>", self._hide_disabled_about_tooltip)

    def _get_textbox_base_font(self, textbox: ctk.CTkTextbox) -> tkfont.Font:
        """
        Reads the current textbox font and returns a usable font object.

        Args:
            textbox: The textbox that will receive formatted text.

        Returns:
            A tkfont.Font instance for base text.

        Raises:
            None.
        """
        font_setting = textbox.cget("font")
        if isinstance(font_setting, tkfont.Font):
            return font_setting
        if hasattr(font_setting, "cget"):
            try:
                return tkfont.Font(
                    family=font_setting.cget("family"),
                    size=font_setting.cget("size"),
                    weight=font_setting.cget("weight"),
                    slant=font_setting.cget("slant"),
                )
            except (tk.TclError, TypeError, ValueError):
                pass
        try:
            return tkfont.Font(font=font_setting)
        except (tk.TclError, TypeError):
            return tkfont.Font(family="Arial", size=14)

    def _build_markdown_fonts(self, base_font: tkfont.Font) -> dict[str, tkfont.Font]:
        """
        Creates font variants for markdown rendering.

        Args:
            base_font: The base font used by the textbox.

        Returns:
            Dictionary of font variants keyed by style name.

        Raises:
            None.
        """
        base_family = base_font.cget("family")
        try:
            base_size = abs(int(base_font.cget("size")))
        except (TypeError, ValueError):
            base_size = 14

        base_weight = base_font.cget("weight") if hasattr(base_font, "cget") else "normal"
        base_slant = base_font.cget("slant") if hasattr(base_font, "cget") else "roman"

        base_font = tkfont.Font(
            family=base_family,
            size=base_size,
            weight=base_weight,
            slant=base_slant,
        )
        bold_font = tkfont.Font(
            family=base_family,
            size=base_size,
            weight="bold",
            slant=base_slant,
        )
        italic_font = tkfont.Font(
            family=base_family,
            size=base_size,
            weight=base_weight,
            slant="italic",
        )
        h1_font = tkfont.Font(
            family=base_family,
            size=base_size + 8,
            weight="bold",
        )
        h2_font = tkfont.Font(
            family=base_family,
            size=base_size + 4,
            weight="bold",
        )

        return {
            "base": base_font,
            "bold": bold_font,
            "italic": italic_font,
            "h1": h1_font,
            "h2": h2_font,
        }

    def _insert_markdown_text(
        self, textbox: tk.Text, text: str, base_tags: tuple[str, ...]
    ) -> None:
        """
        Inserts a line of text with basic bold and italic styling.

        Args:
            textbox: The text widget that will receive formatted text.
            text: The raw line content to insert.
            base_tags: Tag tuple to apply to all inserted segments.

        Returns:
            None.

        Raises:
            None.
        """
        index = 0
        while index < len(text):
            if text.startswith("**", index):
                end = text.find("**", index + 2)
                if end != -1:
                    segment = text[index + 2:end]
                    textbox.insert("end", segment, base_tags + ("bold",))
                    index = end + 2
                    continue
            if text.startswith("*", index):
                end = text.find("*", index + 1)
                if end != -1:
                    segment = text[index + 1:end]
                    textbox.insert("end", segment, base_tags + ("italic",))
                    index = end + 1
                    continue
            textbox.insert("end", text[index], base_tags)
            index += 1

    def _render_markdown_to_textbox(
        self, textbox: ctk.CTkTextbox, content: str
    ) -> None:
        """
        Renders a small subset of markdown into the textbox.

        Args:
            textbox: The textbox that will receive formatted text.
            content: Raw markdown content to render.

        Returns:
            None.

        Raises:
            None.
        """
        text_widget = textbox._textbox
        text_widget.configure(state="normal")
        text_widget.delete("1.0", "end")

        base_font = self._get_textbox_base_font(textbox)
        fonts = self._build_markdown_fonts(base_font)

        text_widget.tag_config("base", font=fonts["base"])
        text_widget.tag_config("bold", font=fonts["bold"])
        text_widget.tag_config("italic", font=fonts["italic"])
        text_widget.tag_config("h1", font=fonts["h1"])
        text_widget.tag_config("h2", font=fonts["h2"])
        text_widget.tag_config("bullet", lmargin1=20, lmargin2=20)

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped:
                text_widget.insert("end", "\n", ("base",))
                continue
            if stripped.startswith("# "):
                self._insert_markdown_text(text_widget, stripped[2:].strip(), ("h1",))
                text_widget.insert("end", "\n\n", ("base",))
                continue
            if stripped.startswith("## "):
                self._insert_markdown_text(text_widget, stripped[3:].strip(), ("h2",))
                text_widget.insert("end", "\n\n", ("base",))
                continue
            if stripped.startswith("- "):
                text_widget.insert("end", "- ", ("bullet", "base"))
                self._insert_markdown_text(text_widget, stripped[2:].strip(), ("bullet", "base"))
                text_widget.insert("end", "\n", ("base",))
                continue
            self._insert_markdown_text(text_widget, line, ("base",))
            text_widget.insert("end", "\n", ("base",))

        text_widget.configure(state="disabled")

    def _update_day_hours(self, day_name: str) -> None:
        """
        Attempts to compute and display hours for a single day based on current row inputs.
        Silent failure: clears the hours label when inputs are invalid or incomplete.

        Args:
            day_name: Name of the weekday whose row should be recalculated.

        Returns:
            None.

        Raises:
            None.
        """
        fields = self.entries[day_name]
        start_raw = fields["start"].get().strip()
        end_raw = fields["end"].get().strip()
        lunch_raw = fields["lunch"].get().strip()

        # Incomplete rows clear the hours display
        if not start_raw or not end_raw:
            fields["hours"].configure(text="")
            # Clear warning highlight if lunch gets filled later
            fields["lunch"].configure(border_color=DEFAULT_BORDER_COLOR)
            return

        start_minutes, _, start_error = self.service._parse_time(
            start_raw, assume_am=True
        )
        end_minutes, _, end_error = self.service._parse_time(
            end_raw, assume_am=False
        )

        if start_error or end_error or start_minutes is None or end_minutes is None:
            fields["hours"].configure(text="")
            return

        if end_minutes <= start_minutes:
            fields["hours"].configure(text="")
            return

        duration = end_minutes - start_minutes

        # Lunch handling with silent failure on bad input
        if not lunch_raw:
            lunch_minutes = 60
            fields["lunch"].configure(border_color="yellow")
        else:
            try:
                lunch_minutes = int(lunch_raw)
                if lunch_minutes < 0:
                    raise ValueError
            except ValueError:
                fields["lunch"].configure(border_color="red")
                fields["hours"].configure(text="")
                return
            fields["lunch"].configure(border_color=DEFAULT_BORDER_COLOR)

        if lunch_minutes > duration:
            fields["hours"].configure(text="")
            return

        worked_minutes = duration - lunch_minutes
        worked_hours = self.service._round_to_quarter(worked_minutes / 60)
        fields["hours"].configure(text=self._format_hours_display(worked_hours))

    def _normalize_time_entry(self, entry: ctk.CTkEntry, assume_am: bool) -> None:
        """
        Normalizes a time entry field when focus is lost.

        Args:
            entry: The CTkEntry widget to normalize.
            assume_am: Whether to assume AM if no period is provided.

        Returns:
            None.

        Raises:
            None.
        """
        raw_value = entry.get().strip()

        # Do nothing if the field is empty
        if not raw_value:
            return

        minutes, display, error = self.service._parse_time(
            raw_value, assume_am=assume_am
        )

        # If parsing fails, leave the value untouched
        if error or display is None:
            return

        # Replace user input with normalized display value
        entry.delete(0, "end")
        entry.insert(0, display)


    def _build_ui(self) -> None:
        """
        Constructs the UI layout and binds all interactions.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        # Establish padding to keep the layout readable
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # Ensure columns stretch evenly to center content
        for col in range(5):
            self.grid_columnconfigure(col, weight=1)

        # KPI Section inside its own frame to center across the full width
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.grid(row=0, column=0, columnspan=5, sticky="nsew", pady=(0, 10))
        for col in range(3):
            kpi_frame.grid_columnconfigure(col, weight=1)

        self.total_hours_label = ctk.CTkLabel(kpi_frame, text="Total Hours Worked", anchor="center")
        self.total_hours_value = ctk.CTkLabel(kpi_frame, text="", font=("Arial", 28))

        self.hours_to_40_label = ctk.CTkLabel(kpi_frame, text="Hours to 40", anchor="center")
        self.hours_to_40_value = ctk.CTkLabel(kpi_frame, text="", font=("Arial", 28))

        self.friday_label = ctk.CTkLabel(kpi_frame, text="Friday Clock Out", anchor="center")
        self.friday_value = ctk.CTkLabel(kpi_frame, text="", font=("Arial", 28))

        # Preserve default colors for later resets
        self._hours_to_40_default_color = self.hours_to_40_value.cget("text_color")

        self.total_hours_label.grid(row=0, column=0, sticky="nsew")
        self.hours_to_40_label.grid(row=0, column=1, sticky="nsew")
        self.friday_label.grid(row=0, column=2, sticky="nsew")

        self.total_hours_value.grid(row=1, column=0, sticky="nsew")
        self.hours_to_40_value.grid(row=1, column=1, sticky="nsew")
        self.friday_value.grid(row=1, column=2, sticky="nsew")

        # Table Headers
        headers = ["Day", "Start", "End", "Lunch (min)", "Hours"]
        for col, header in enumerate(headers):
            ctk.CTkLabel(self, text=header, anchor="center").grid(row=2, column=col, sticky="nsew", padx=4, pady=6)

        # Day Rows
        for i, day in enumerate(self.days):
            row = i + 3
            ctk.CTkLabel(self, text=day, anchor="center").grid(row=row, column=0, sticky="nsew", padx=4, pady=6)

            start = ctk.CTkEntry(self)
            end = ctk.CTkEntry(self)
            lunch = ctk.CTkEntry(self)
            hours = ctk.CTkLabel(self, text="")

            # Normalize times when the user tabs or clicks away
            def on_start_focus_out(event: object, entry=start, day=day) -> None:
                """
                Normalizes start time and refreshes row hours when start loses focus.

                Args:
                    event: Tkinter focus event.
                    entry: Start entry widget for the day.
                    day: Name of the weekday being updated.

                Returns:
                    None.

                Raises:
                    None.
                """
                self._normalize_time_entry(entry, assume_am=True)
                self._update_day_hours(day)

            def on_end_focus_out(event: object, entry=end, day=day) -> None:
                """
                Normalizes end time and refreshes row hours when end loses focus.

                Args:
                    event: Tkinter focus event.
                    entry: End entry widget for the day.
                    day: Name of the weekday being updated.

                Returns:
                    None.

                Raises:
                    None.
                """
                self._normalize_time_entry(entry, assume_am=False)
                self._update_day_hours(day)

            def on_lunch_focus_out(event: object, day=day) -> None:
                """
                Refreshes row hours when lunch loses focus.

                Args:
                    event: Tkinter focus event.
                    day: Name of the weekday being updated.

                Returns:
                    None.

                Raises:
                    None.
                """
                self._update_day_hours(day)

            start.bind("<FocusOut>", on_start_focus_out)
            end.bind("<FocusOut>", on_end_focus_out)
            lunch.bind("<FocusOut>", on_lunch_focus_out)

            # Auto-insert colon while typing
            start.bind(
                "<KeyRelease>",
                lambda e, entry=start: self._auto_insert_colon(e, entry),
            )

            end.bind(
                "<KeyRelease>",
                lambda e, entry=end: self._auto_insert_colon(e, entry),
            )


            start.grid(row=row, column=1, padx=4, pady=6, sticky="nsew")
            end.grid(row=row, column=2, padx=4, pady=6, sticky="nsew")
            lunch.grid(row=row, column=3, padx=4, pady=6, sticky="nsew")
            hours.grid(row=row, column=4, padx=4, pady=6, sticky="nsew")

            self.entries[day] = {
                "start": start,
                "end": end,
                "lunch": lunch,
                "hours": hours
            }

        # Messages
        self.message_label = ctk.CTkLabel(self, text="", text_color="red")
        self.message_label.grid(row=9, column=0, columnspan=5)

        # Button container (centers buttons horizontally)
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=10, column=0, columnspan=5, pady=10)

        self.calculate_button = ctk.CTkButton(
            button_frame,
            text="Calculate",
            fg_color="green",
            command=self._calculate,
            width=140,
        )

        self.about_button = ctk.CTkButton(
            button_frame,
            text="About",
            fg_color="lightgray",
            command=self._show_about,
            width=100,
        )

        self.calculate_button.pack(side="left", padx=10)
        self.about_button.pack(side="left", padx=10)

        self._refresh_about_button_state()

        self.master.bind("<Return>", lambda _: self._calculate())
        
    def _calculate(self) -> None:
        """
        Collects input, runs calculation, applies validation highlighting, and updates UI.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        self._clear_validation_styles()
        self.message_label.configure(text="")
        self._clear_hours_labels()
        self._clear_kpis()

        # Collect all five days of input into service-friendly objects
        day_inputs = []
        for day in self.days:
            start = self.entries[day]["start"]
            end = self.entries[day]["end"]
            lunch = self.entries[day]["lunch"]
            day_inputs.append(
                DayInput(
                    day_name=day,
                    start_time=start.get(),
                    end_time=end.get(),
                    lunch_minutes=lunch.get(),
                )
            )

        result = self.service.calculate_week(day_inputs)

        # Highlight lunch warnings (blank lunch assumed)
        for day in self.days:
            lunch_value = self.entries[day]["lunch"].get().strip()
            if not lunch_value:
                self.entries[day]["lunch"].configure(border_color="yellow")

        # Apply red borders to invalid fields (always, even if errors exist)
        for field_key in getattr(result, "field_errors", {}):
            day, field = field_key.split("_")
            entry = self.entries[day][field]
            entry.configure(border_color="red")

            # Optional: clear red border when user types
            entry.bind("<KeyRelease>", lambda e, entry=entry: entry.configure(border_color=DEFAULT_BORDER_COLOR))

        # Display errors and exit early if any
        if result.errors:
            self.message_label.configure(
                text="\n".join(result.errors),
                text_color="red"
            )
            self._clear_kpis()
            return

        # Display warnings (yellow)
        if result.warnings:
            self.message_label.configure(
                text="\n".join(result.warnings),
                text_color="yellow"
            )
        else:
            self.message_label.configure(text="")

        # Update KPIs
        self.total_hours_value.configure(text=str(result.total_hours))
        # Hours to 40 color coding: green when over 40, neutral otherwise
        hours_to_40_text = str(result.hours_to_40)
        self.hours_to_40_value.configure(text=hours_to_40_text)
        if result.hours_to_40 is not None and result.hours_to_40 < 0:
            self.hours_to_40_value.configure(text_color="green")
        else:
            self.hours_to_40_value.configure(text_color=self._hours_to_40_default_color)

        if result.friday_clock_out:
            self.friday_value.configure(text=result.friday_clock_out)

        # Per-day hours column
        for day in self.days:
            hours_value = result.daily_hours.get(day)
            if hours_value is not None:
                display = self._format_hours_display(hours_value)
                self.entries[day]["hours"].configure(text=display)

        # Success messages (green)
        if getattr(result, "successes", []):
            self.message_label.configure(
                text="\n".join(result.successes),
                text_color="green"
            )


    def _show_about(self) -> None:
        """
        Displays the About popup with ABOUT.md contents.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        self._refresh_about_button_state()
        if not self._about_path:
            return
        popup = ctk.CTkToplevel(self)
        popup.title("About")

        textbox = ctk.CTkTextbox(popup, wrap="word", width=600, height=400)
        textbox.pack(padx=20, pady=20)

        with open(self._about_path, "r", encoding="utf-8") as file:
            content = file.read()

        self._render_markdown_to_textbox(textbox, content)

    def _show_disabled_about_tooltip(self, event: Optional[object]) -> None:
        """
        Shows a small tooltip explaining why About is disabled.

        Args:
            event: Tkinter enter event.

        Returns:
            None.

        Raises:
            None.
        """
        self._refresh_about_button_state()
        if self._about_path:
            return
        if hasattr(self, "_about_tooltip") and self._about_tooltip is not None:
            return
        tooltip = ctk.CTkToplevel(self)
        tooltip.overrideredirect(True)
        tooltip.attributes("-topmost", True)
        label = ctk.CTkLabel(tooltip, text="About disabled: src/ABOUT.md not found", fg_color="#333333", text_color="white", corner_radius=4, padx=6, pady=4)
        label.pack()
        x = self.about_button.winfo_rootx()
        y = self.about_button.winfo_rooty() - 30
        tooltip.geometry(f"+{x}+{y}")
        self._about_tooltip = tooltip

    def _hide_disabled_about_tooltip(self, event: Optional[object]) -> None:
        """
        Hides the About disabled tooltip.

        Args:
            event: Tkinter leave event.

        Returns:
            None.

        Raises:
            None.
        """
        if hasattr(self, "_about_tooltip") and self._about_tooltip is not None:
            self._about_tooltip.destroy()
            self._about_tooltip = None


def main() -> None:
    """
    Application entry point that creates the root window and starts the event loop.

    Args:
        None.

    Returns:
        None.

    Raises:
        None.
    """
    app = ctk.CTk()
    app.title("Time Sheet Calculator")
    TimeSheetApp(app)
    app.mainloop()


if __name__ == "__main__":
    main()
