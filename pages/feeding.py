"""
pages/feeding.py — Track feeding schedules and log meals.

Lets you:
  - View all meal schedules for the active pet
  - Add a new meal schedule (name, time, food type, portion)
  - Mark a meal as done today
  - Delete a schedule
"""
import tkinter as tk
from datetime import datetime
from pages.base import BasePage, BG, SURFACE, ACCENT, GREEN, RED, TEXT, MUTED, BORDER
from database import get_connection


class FeedingPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app, title="🍽  Feeding",
                         subtitle="Manage meal schedules and log when your pet has been fed.")

        # ── Top bar ───────────────────────────────────────────────
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=30, pady=(16, 0))
        self.make_button(top, "＋ Add Meal", self._open_add_dialog).pack(side="left")

        # ── Content ───────────────────────────────────────────────
        self.list_frame = tk.Frame(self, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=30, pady=16)

    def reload(self):
        """Reload schedules for the current active pet."""
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        pet = self.app.get_active_pet()
        if not pet:
            self.show_empty(self.list_frame,
                            "Select a pet first to view feeding schedules.")
            return

        schedules = self._load_schedules(pet["id"])
        if not schedules:
            self.show_empty(self.list_frame,
                            "No meal schedules yet. Click '＋ Add Meal' to create one.")
            return

        # Show how many meals are done today
        today = datetime.now().strftime("%Y-%m-%d")
        done_ids = self._get_done_ids(pet["id"], today)

        tk.Label(
            self.list_frame,
            text=f"{len(done_ids)} of {len(schedules)} meals done today",
            bg=BG, fg=MUTED, font=("Arial", 10)
        ).pack(anchor="w", pady=(0, 10))

        for s in schedules:
            self._make_schedule_row(s, pet["id"], s["id"] in done_ids)

    # ── Database calls ────────────────────────────────────────────

    def _load_schedules(self, pet_id):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM feeding_schedules WHERE pet_id=? ORDER BY time",
            (pet_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _get_done_ids(self, pet_id, date_str):
        """Return a set of schedule IDs that have been logged as done today."""
        conn = get_connection()
        rows = conn.execute(
            """SELECT DISTINCT schedule_id FROM feeding_logs
               WHERE pet_id=? AND date(logged_at)=? AND schedule_id IS NOT NULL""",
            (pet_id, date_str)
        ).fetchall()
        conn.close()
        return {r["schedule_id"] for r in rows}

    def _add_schedule(self, pet_id, meal_name, time, food_type, portion):
        conn = get_connection()
        conn.execute(
            "INSERT INTO feeding_schedules (pet_id, meal_name, time, food_type, portion) VALUES (?,?,?,?,?)",
            (pet_id, meal_name, time, food_type or None, portion or None)
        )
        conn.commit()
        conn.close()

    def _log_feeding(self, pet_id, schedule_id):
        conn = get_connection()
        conn.execute(
            "INSERT INTO feeding_logs (pet_id, schedule_id) VALUES (?,?)",
            (pet_id, schedule_id)
        )
        conn.commit()
        conn.close()

    def _delete_schedule(self, schedule_id):
        conn = get_connection()
        conn.execute("DELETE FROM feeding_schedules WHERE id=?", (schedule_id,))
        conn.commit()
        conn.close()

    # ── UI builders ───────────────────────────────────────────────

    def _make_schedule_row(self, schedule, pet_id, done_today):
        """Build one row for a meal schedule."""
        outer = tk.Frame(self.list_frame, bg=BORDER)
        outer.pack(fill="x", pady=(0, 6))
        inner = tk.Frame(outer, bg=SURFACE, padx=14, pady=10)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Left accent bar (green = done, yellow = pending)
        bar_color = GREEN if done_today else ACCENT
        tk.Frame(inner, bg=bar_color, width=4).pack(side="left", fill="y", padx=(0, 12))

        # Meal info
        info = tk.Frame(inner, bg=SURFACE)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(info, text=schedule["meal_name"], bg=SURFACE, fg=TEXT,
                 font=("Arial", 12, "bold"), anchor="w").pack(fill="x")

        details = schedule["time"]
        if schedule["food_type"]:
            details += f"  ·  {schedule['food_type']}"
        if schedule["portion"]:
            details += f"  ·  {schedule['portion']}"
        tk.Label(info, text=details, bg=SURFACE, fg=MUTED,
                 font=("Arial", 10), anchor="w").pack(fill="x")

        # Buttons on the right
        btn_frame = tk.Frame(inner, bg=SURFACE)
        btn_frame.pack(side="right")

        if done_today:
            tk.Label(btn_frame, text="✓ Done", bg=SURFACE, fg=GREEN,
                     font=("Arial", 10, "bold")).pack(side="left", padx=(0, 8))
        else:
            self.make_button(
                btn_frame, "Mark Done",
                lambda s=schedule: self._mark_done(s, pet_id),
                color=GREEN
            ).pack(side="left", padx=(0, 6))

        self.make_danger_button(
            btn_frame, "Delete",
            lambda s=schedule: self._confirm_delete(s)
        ).pack(side="left")

    def _mark_done(self, schedule, pet_id):
        """Log that this meal was given today."""
        self._log_feeding(pet_id, schedule["id"])
        self.reload()

    def _confirm_delete(self, schedule):
        confirmed = self.app.ask_yes_no("Delete Meal",
                                         f"Delete '{schedule['meal_name']}'?")
        if confirmed:
            self._delete_schedule(schedule["id"])
            self.reload()

    # ── Add Schedule Dialog ───────────────────────────────────────

    def _open_add_dialog(self):
        pet = self.app.get_active_pet()
        if not pet:
            self.app.show_message("No Pet", "Please select a pet first.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Meal Schedule")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.grab_set()

        tk.Label(dialog, text="Add Meal Schedule", bg=BG, fg=TEXT,
                 font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2,
                                                   padx=24, pady=(20, 12), sticky="w")

        # Form fields
        form_rows = [
            ("Meal Name *", "meal_name", "e.g. Breakfast"),
            ("Time *",      "time",      "e.g. 08:00"),
            ("Food Type",   "food_type", "e.g. Dry kibble"),
            ("Portion",     "portion",   "e.g. 1 cup"),
        ]

        fields = {}
        for i, (label, key, placeholder) in enumerate(form_rows, start=1):
            tk.Label(dialog, text=label, bg=BG, fg=MUTED,
                     font=("Arial", 10)).grid(row=i, column=0, padx=(24, 8),
                                               pady=4, sticky="w")
            entry = self.make_entry(dialog, width=25)
            entry.insert(0, placeholder)
            entry.config(fg=MUTED)

            def on_focus(e, ent=entry, ph=placeholder):
                if ent.get() == ph:
                    ent.delete(0, "end")
                    ent.config(fg=TEXT)

            entry.bind("<FocusIn>", on_focus)
            entry.grid(row=i, column=1, padx=(0, 24), pady=4)
            fields[key] = (entry, placeholder)

        error_lbl = tk.Label(dialog, text="", bg=BG, fg=RED, font=("Arial", 10))
        error_lbl.grid(row=len(form_rows) + 1, column=0, columnspan=2, padx=24)

        def get_val(key):
            entry, placeholder = fields[key]
            val = entry.get().strip()
            return "" if val == placeholder else val

        def submit():
            meal_name = get_val("meal_name")
            time      = get_val("time")
            if not meal_name:
                error_lbl.config(text="Meal name is required.")
                return
            if not time:
                error_lbl.config(text="Time is required.")
                return
            self._add_schedule(pet["id"], meal_name, time,
                               get_val("food_type"), get_val("portion"))
            dialog.destroy()
            self.reload()

        btn_row = tk.Frame(dialog, bg=BG)
        btn_row.grid(row=len(form_rows) + 2, column=0, columnspan=2,
                     padx=24, pady=(8, 20), sticky="e")
        tk.Button(btn_row, text="Cancel", command=dialog.destroy,
                  bg=SURFACE, fg=MUTED, relief="flat", padx=10, pady=6,
                  cursor="hand2").pack(side="left", padx=(0, 8))
        self.make_button(btn_row, "Add Meal", submit).pack(side="left")