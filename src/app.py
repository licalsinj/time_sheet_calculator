"""
app.py

CustomTkinter user interface for the time sheet calculator.
"""

import os
import customtkinter as ctk
from timesheet_service import TimeSheetService, DayInput


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

            start.grid(row=row, column=1)
            end.grid(row=row, column=2)
            lunch.grid(row=row, column=3)
            hours.grid(row=row, column=4)

            self.entries[day] = (start, end, lunch, hours)

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
        """Collects input, runs calculation, and updates UI."""
        day_inputs = []

        for day in self.days:
            start, end, lunch, _ = self.entries[day]
            day_inputs.append(
                DayInput(
                    day_name=day,
                    start_time=start.get(),
                    end_time=end.get(),
                    lunch_minutes=lunch.get(),
                )
            )

        result = self.service.calculate_week(day_inputs)

        self.message_label.configure(text="")

        if result.errors:
            self.message_label.configure(text="\n".join(result.errors), text_color="red")
            return

        messages = result.warnings + result.successes
        self.message_label.configure(text="\n".join(messages), text_color="yellow")

        self.total_hours_value.configure(text=str(result.total_hours))
        self.hours_to_40_value.configure(text=str(result.hours_to_40))

        if result.friday_clock_out:
            self.friday_value.configure(text=result.friday_clock_out)

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
