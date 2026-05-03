"""
pages/grooming.py — Track grooming tasks for the active pet.

Lets you:
  - View all grooming tasks (e.g. bath, nail trim)
  - Add a new task with how often it should be done
  - Mark a task as done today (updates the next due date)
  - Delete a task
"""
import tkinter as tk
from datetime import date, timedelta
from pages.base import BasePage, BG, SURFACE, ACCENT, GREEN, RED, TEXT, MUTED, BORDER
from database import get_connection


class GroomingPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(
            parent, app,
            title="✂  Grooming",
            subtitle="Track grooming tasks and when they are next due."
        )

        # Button to open the "add task" dialog
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=30, pady=(16, 0))
        self.make_button(top, "＋ Add Task", self._open_add_dialog).pack(side="left")

        # This frame holds the list of grooming task cards
        self.list_frame = tk.Frame(self, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=30, pady=16)

    # ── Called every time you navigate to this page ───────────────

    def reload(self):
        # Clear old cards
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        pet = self.app.get_active_pet()
        if not pet:
            self.show_empty(self.list_frame, "Select a pet first.")
            return

        tasks = self._load_tasks(pet["id"])
        if not tasks:
            self.show_empty(self.list_frame,
                            "No grooming tasks yet. Click '＋ Add Task' to create one.")
            return

        for task in tasks:
            self._make_task_row(task, pet["id"])

    # ── Database helpers ──────────────────────────────────────────

    def _load_tasks(self, pet_id):
        """Get all grooming tasks for this pet, ordered by due date."""
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM grooming_tasks WHERE pet_id=? ORDER BY next_due",
            (pet_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _add_task(self, pet_id, task_name, interval_days, notes):
        """
        Insert a new grooming task.
        next_due is set to TODAY so the task shows up as due immediately,
        prompting the user to mark it done and establish the first cycle.
        """
        today = str(date.today())
        conn = get_connection()
        conn.execute(
            """INSERT INTO grooming_tasks
               (pet_id, task_name, interval_days, last_done, next_due, notes)
               VALUES (?, ?, ?, NULL, ?, ?)""",
            (pet_id, task_name, interval_days, today, notes or None)
        )
        conn.commit()
        conn.close()

    def _mark_done(self, task_id, interval_days):
        """Record today as last_done and set next_due = today + interval."""
        today    = str(date.today())
        next_due = str(date.today() + timedelta(days=interval_days))
        conn = get_connection()
        conn.execute(
            "UPDATE grooming_tasks SET last_done=?, next_due=? WHERE id=?",
            (today, next_due, task_id)
        )
        conn.commit()
        conn.close()

    def _delete_task(self, task_id):
        conn = get_connection()
        conn.execute("DELETE FROM grooming_tasks WHERE id=?", (task_id,))
        conn.commit()
        conn.close()

    # ── UI builders ───────────────────────────────────────────────

    def _make_task_row(self, task, pet_id):
        """Build one card for a grooming task."""
        today     = str(date.today())
        is_overdue = task["next_due"] and task["next_due"] <= today

        # Red left bar if overdue, green if fine
        bar_color = RED if is_overdue else GREEN

        outer = tk.Frame(self.list_frame, bg=BORDER)
        outer.pack(fill="x", pady=(0, 6))
        inner = tk.Frame(outer, bg=SURFACE, padx=14, pady=10)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        tk.Frame(inner, bg=bar_color, width=4).pack(side="left", fill="y", padx=(0, 12))

        # Task name and details
        info = tk.Frame(inner, bg=SURFACE)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(info, text=task["task_name"], bg=SURFACE, fg=TEXT,
                 font=("Arial", 12, "bold"), anchor="w").pack(fill="x")

        # Detail line: "Every 7 days  ·  ⚠ Overdue" or "Next due: 2025-05-15"
        detail = f"Every {task['interval_days']} days"
        if task["next_due"]:
            status = "⚠ Overdue" if is_overdue else f"Next due: {task['next_due']}"
            detail += f"  ·  {status}"
        if task["notes"]:
            detail += f"  ·  {task['notes']}"

        tk.Label(info, text=detail, bg=SURFACE,
                 fg=RED if is_overdue else MUTED,
                 font=("Arial", 10), anchor="w").pack(fill="x")

        # Buttons on the right
        btn_frame = tk.Frame(inner, bg=SURFACE)
        btn_frame.pack(side="right")

        self.make_button(
            btn_frame, "Mark Done",
            lambda t=task: self._on_mark_done(t),
            color=GREEN
        ).pack(side="left", padx=(0, 6))

        self.make_danger_button(
            btn_frame, "Delete",
            lambda t=task: self._on_delete(t)
        ).pack(side="left")

    def _on_mark_done(self, task):
        self._mark_done(task["id"], task["interval_days"])
        self.reload()

    def _on_delete(self, task):
        confirmed = self.app.ask_yes_no("Delete Task",
                                         f"Delete '{task['task_name']}'?")
        if confirmed:
            self._delete_task(task["id"])
            self.reload()

    # ── Add Task Dialog ───────────────────────────────────────────

    def _open_add_dialog(self):
        pet = self.app.get_active_pet()
        if not pet:
            self.app.show_message("No Pet", "Please select a pet first.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Grooming Task")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.grab_set()

        tk.Label(dialog, text="Add Grooming Task", bg=BG, fg=TEXT,
                 font=("Arial", 14, "bold")).grid(
            row=0, column=0, columnspan=2, padx=24, pady=(20, 12), sticky="w"
        )

        form_rows = [
            ("Task Name *",    "task_name",    "e.g. Bath"),
            ("Every (days) *", "interval_days","e.g. 7"),
            ("Notes",          "notes",        "e.g. Use gentle shampoo"),
        ]

        fields = {}
        for i, (label, key, placeholder) in enumerate(form_rows, start=1):
            tk.Label(dialog, text=label, bg=BG, fg=MUTED,
                     font=("Arial", 10)).grid(row=i, column=0,
                                               padx=(24, 8), pady=4, sticky="w")
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
            task_name = get_val("task_name")
            interval  = get_val("interval_days")

            if not task_name:
                error_lbl.config(text="Task name is required.")
                return
            if not interval:
                error_lbl.config(text="Interval (days) is required.")
                return
            try:
                interval_days = int(interval)
                if interval_days < 1:
                    raise ValueError
            except ValueError:
                error_lbl.config(text="Interval must be a whole number (e.g. 7).")
                return

            self._add_task(pet["id"], task_name, interval_days, get_val("notes"))
            dialog.destroy()
            self.reload()

        btn_row = tk.Frame(dialog, bg=BG)
        btn_row.grid(row=len(form_rows) + 2, column=0, columnspan=2,
                     padx=24, pady=(8, 20), sticky="e")

        tk.Button(btn_row, text="Cancel", command=dialog.destroy,
                  bg=SURFACE, fg=MUTED, relief="flat", padx=10, pady=6,
                  cursor="hand2").pack(side="left", padx=(0, 8))

        self.make_button(btn_row, "Add Task", submit).pack(side="left")