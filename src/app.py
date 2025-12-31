"""
app.py

CustomTkinter user interface for the time sheet calculator.
"""

import os
import customtkinter as ctk
from timesheet_service import TimeSheetService, DayInput

# CONSTANTS
DEFAULT_BORDER_COLOR = "#444444"

class TimeSheetApp(ctk.CTkFrame):
    """
    Main application frame containing all UI elements.
    """

    def __init__(self, master):
        super().__init__(master)
        self.service = TimeSheetService()
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.entries = {}
        self._build_ui()
    # ----------------
    # Helper Methods
    # -----------------
    
    def _auto_insert_colon(self, event, entry: ctk.CTkEntry):
        """
        Automatically inserts a colon after the hour portion of a time
        while the user is typing.

        Args:
            event: Tkinter key event
            entry: The CTkEntry widget being typed into
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

    def _clear_validation_styles(self):
        """
        Resets all entry widgets to default border.
        """
        for day_fields in self.entries.values():
            for key in ("start", "end", "lunch"):
                entry = day_fields[key]
                entry.configure(border_color=DEFAULT_BORDER_COLOR)

    def _normalize_time_entry(self, entry: ctk.CTkEntry, assume_am: bool):
        """
        Normalizes a time entry field when focus is lost.

        Args:
            entry: The CTkEntry widget to normalize
            assume_am: Whether to assume AM if no period is provided
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


    def _build_ui(self):
        """Constructs the UI layout."""
        self.pack(fill="both", expand=True, padx=20, pady=20)

        # KPI Section
        self.total_hours_label = ctk.CTkLabel(self, text="Total Hours Worked")
        self.total_hours_value = ctk.CTkLabel(self, text="", font=("Arial", 28))

        self.hours_to_40_label = ctk.CTkLabel(self, text="Hours to 40")
        self.hours_to_40_value = ctk.CTkLabel(self, text="", font=("Arial", 28))

        self.friday_label = ctk.CTkLabel(self, text="Friday Clock Out")
        self.friday_value = ctk.CTkLabel(self, text="", font=("Arial", 28))

        self.total_hours_label.grid(row=0, column=0)
        self.hours_to_40_label.grid(row=0, column=1)
        self.friday_label.grid(row=0, column=2)

        self.total_hours_value.grid(row=1, column=0)
        self.hours_to_40_value.grid(row=1, column=1)
        self.friday_value.grid(row=1, column=2)

        # Table Headers
        headers = ["Day", "Start", "End", "Lunch (min)", "Hours"]
        for col, header in enumerate(headers):
            ctk.CTkLabel(self, text=header).grid(row=2, column=col)

        # Day Rows
        for i, day in enumerate(self.days):
            row = i + 3
            ctk.CTkLabel(self, text=day).grid(row=row, column=0)

            start = ctk.CTkEntry(self)
            end = ctk.CTkEntry(self)
            lunch = ctk.CTkEntry(self)
            hours = ctk.CTkLabel(self, text="")

            # Normalize times when the user tabs or clicks away
            start.bind(
                "<FocusOut>",
                lambda e, entry=start: self._normalize_time_entry(entry, assume_am=True),
            )

            end.bind(
                "<FocusOut>",
                lambda e, entry=end: self._normalize_time_entry(entry, assume_am=False),
            )

            # Auto-insert colon while typing
            start.bind(
                "<KeyRelease>",
                lambda e, entry=start: self._auto_insert_colon(e, entry),
            )

            end.bind(
                "<KeyRelease>",
                lambda e, entry=end: self._auto_insert_colon(e, entry),
            )


            start.grid(row=row, column=1)
            end.grid(row=row, column=2)
            lunch.grid(row=row, column=3)
            hours.grid(row=row, column=4)

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

        if not os.path.exists("readme.md"):
            self.about_button.configure(state="disabled")

        self.master.bind("<Return>", lambda _: self._calculate())
        
    def _calculate(self):
        """Collects input, runs calculation, applies validation highlighting, and updates UI."""
        self._clear_validation_styles()
        self.message_label.configure(text="")

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
        self.hours_to_40_value.configure(text=str(result.hours_to_40))

        if result.friday_clock_out:
            self.friday_value.configure(text=result.friday_clock_out)

        # Success messages (green)
        if getattr(result, "successes", []):
            self.message_label.configure(
                text="\n".join(result.successes),
                text_color="green"
            )


    def _show_about(self):
        """Displays the About popup with readme.md contents."""
        popup = ctk.CTkToplevel(self)
        popup.title("About")

        textbox = ctk.CTkTextbox(popup, wrap="word", width=600, height=400)
        textbox.pack(padx=20, pady=20)

        with open("readme.md", "r", encoding="utf-8") as file:
            textbox.insert("1.0", file.read())

        textbox.configure(state="disabled")


def main():
    """Application entry point."""
    app = ctk.CTk()
    app.title("Time Sheet Calculator")
    TimeSheetApp(app)
    app.mainloop()


if __name__ == "__main__":
    main()
