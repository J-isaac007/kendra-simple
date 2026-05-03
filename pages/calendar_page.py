"""
pages/calendar_page.py — A simple monthly calendar view.

Shows the current month as a grid. Days are highlighted if:
  - There are any events on that day (grooming due, feeding, medications)
  - Today's date (blue accent)

Clicking a day shows a summary of what's happening that day.
"""
import tkinter as tk
from datetime import date
import calendar
from pages.base import BasePage, BG, SURFACE, ACCENT, GREEN, RED, TEXT, MUTED, BORDER
from database import get_connection


DAYS_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class CalendarPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(
            parent, app,
            title="📅  Calendar",
            subtitle="See all your pet's events — grooming, feeding, and medications."
        )

        # Track which month/year is displayed
        self.viewed_year  = date.today().year
        self.viewed_month = date.today().month

        # Navigation bar: [◀ Prev]  "May 2025"  [Next ▶]
        nav = tk.Frame(self, bg=BG)
        nav.pack(fill="x", padx=30, pady=(16, 0))
        self.make_button(nav, "◀ Prev", self._go_prev_month).pack(side="left")
        self.month_label = tk.Label(nav, text="", bg=BG, fg=TEXT,
                                     font=("Arial", 14, "bold"))
        self.month_label.pack(side="left", padx=16)
        self.make_button(nav, "Next ▶", self._go_next_month).pack(side="left")

        # Legend
        legend = tk.Frame(self, bg=BG)
        legend.pack(fill="x", padx=30, pady=(10, 0))
        for color, label in [(ACCENT, "Today"), (GREEN, "Events"), (RED, "Overdue grooming")]:
            tk.Frame(legend, bg=color, width=12, height=12).pack(side="left", padx=(0, 4))
            tk.Label(legend, text=label, bg=BG, fg=MUTED,
                     font=("Arial", 9)).pack(side="left", padx=(0, 16))

        # The calendar grid
        self.grid_frame = tk.Frame(self, bg=BG)
        self.grid_frame.pack(fill="both", expand=True, padx=30, pady=12)

        # Clicked day details shown here
        self.detail_label = tk.Label(
            self, text="Click a highlighted day to see details.",
            bg=BG, fg=MUTED, font=("Arial", 10), wraplength=700, anchor="w"
        )
        self.detail_label.pack(padx=30, pady=(0, 16), fill="x")

    def reload(self):
        self._draw_calendar()

    def _go_prev_month(self):
        if self.viewed_month == 1:
            self.viewed_month = 12
            self.viewed_year -= 1
        else:
            self.viewed_month -= 1
        self._draw_calendar()

    def _go_next_month(self):
        if self.viewed_month == 12:
            self.viewed_month = 1
            self.viewed_year += 1
        else:
            self.viewed_month += 1
        self._draw_calendar()

    def _draw_calendar(self):
        """Rebuild the calendar grid for the current viewed month."""
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.detail_label.config(text="Click a highlighted day to see details.")

        month_name = date(self.viewed_year, self.viewed_month, 1).strftime("%B %Y")
        self.month_label.config(text=month_name)

        # Get all events: { "2025-05-10": ["Bath", "Morning feed", ...] }
        events, overdue_dates = self._get_all_events()

        # Day-of-week header row
        for col, day_name in enumerate(DAYS_OF_WEEK):
            tk.Label(
                self.grid_frame, text=day_name,
                bg=BG, fg=MUTED, font=("Arial", 10, "bold"),
                width=6, anchor="center"
            ).grid(row=0, column=col, padx=2, pady=(0, 4))

        today = date.today()
        # calendar.monthcalendar() gives us a list of weeks,
        # each week is 7 day numbers (0 = day outside this month)
        weeks = calendar.monthcalendar(self.viewed_year, self.viewed_month)

        for row_idx, week in enumerate(weeks, start=1):
            for col_idx, day_num in enumerate(week):
                if day_num == 0:
                    # Blank cell for days outside this month
                    tk.Label(self.grid_frame, text="", bg=BG, width=6
                             ).grid(row=row_idx, column=col_idx, padx=2, pady=2)
                    continue

                this_date = date(self.viewed_year, self.viewed_month, day_num)
                date_str  = str(this_date)

                # Choose cell color based on what's happening that day
                if this_date == today:
                    cell_bg, cell_fg = ACCENT, "#1e1e2e"
                elif date_str in overdue_dates:
                    cell_bg, cell_fg = RED, "#1e1e2e"
                elif date_str in events:
                    cell_bg, cell_fg = GREEN, "#1e1e2e"
                else:
                    cell_bg, cell_fg = SURFACE, TEXT

                has_events = date_str in events
                cell = tk.Label(
                    self.grid_frame,
                    text=str(day_num),
                    bg=cell_bg, fg=cell_fg,
                    font=("Arial", 11),
                    width=6, pady=6,
                    cursor="hand2" if has_events else "arrow"
                )
                cell.grid(row=row_idx, column=col_idx, padx=2, pady=2)

                # Bind a click only for days that have events
                if has_events:
                    day_events = events[date_str]
                    cell.bind("<Button-1>",
                              lambda e, d=this_date, ev=day_events: self._show_detail(d, ev))

    def _get_all_events(self):
        """
        Returns two things:
          events        — dict { date_str: [list of event strings] }
          overdue_dates — set of date strings where grooming is overdue

        Sources:
          - Grooming tasks  → shown on their next_due date
          - Feeding schedules → shown on every day (they repeat daily)
          - Medications       → shown on every day (they are ongoing)
        """
        pet = self.app.get_active_pet()
        if not pet:
            return {}, set()

        conn = get_connection()
        events = {}
        overdue_dates = set()
        today = str(date.today())

        # ── Grooming: show on the specific due date ───────────────
        grooming_rows = conn.execute(
            "SELECT task_name, next_due FROM grooming_tasks WHERE pet_id=? AND next_due IS NOT NULL",
            (pet["id"],)
        ).fetchall()

        for row in grooming_rows:
            d = row["next_due"]
            events.setdefault(d, []).append(f"✂ {row['task_name']}")
            if d <= today:
                overdue_dates.add(d)

        # ── Feeding & Medications: show on every day this month ───
        feeding_rows = conn.execute(
            "SELECT meal_name, time FROM feeding_schedules WHERE pet_id=?",
            (pet["id"],)
        ).fetchall()

        med_rows = conn.execute(
            "SELECT name, frequency FROM medications WHERE pet_id=?",
            (pet["id"],)
        ).fetchall()

        # Only loop through days if there's something to show
        if feeding_rows or med_rows:
            _, days_in_month = calendar.monthrange(self.viewed_year, self.viewed_month)
            for day in range(1, days_in_month + 1):
                d = str(date(self.viewed_year, self.viewed_month, day))
                for row in feeding_rows:
                    events.setdefault(d, []).append(f"🍽 {row['meal_name']} ({row['time']})")
                for row in med_rows:
                    events.setdefault(d, []).append(f"💊 {row['name']} ({row['frequency']})")

        conn.close()
        return events, overdue_dates

    def _show_detail(self, clicked_date, events):
        """Show a list of events at the bottom when a day is clicked."""
        date_str   = clicked_date.strftime("%A, %B %d")
        event_list = "   •   ".join(events)
        self.detail_label.config(text=f"📅 {date_str}:   {event_list}", fg=TEXT)