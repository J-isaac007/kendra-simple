"""
pages/health.py — Track weight history for the active pet.

Lets you:
  - View a log of past weight entries
  - Add a new weight entry (weight, unit, date, notes)
  - Delete an entry
  - See basic stats (current, min, max weight)
"""
import tkinter as tk
from datetime import date
from pages.base import BasePage, BG, SURFACE, ACCENT, GREEN, RED, TEXT, MUTED, BORDER
from database import get_connection


class HealthPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app, title="⚖  Health & Weight",
                         subtitle="Log your pet's weight over time to track their health.")

        # ── Top bar ───────────────────────────────────────────────
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=30, pady=(16, 0))
        self.make_button(top, "＋ Log Weight", self._open_add_dialog).pack(side="left")

        # ── Stats row ─────────────────────────────────────────────
        self.stats_frame = tk.Frame(self, bg=BG)
        self.stats_frame.pack(fill="x", padx=30, pady=(16, 0))

        # ── List area ─────────────────────────────────────────────
        self.list_frame = tk.Frame(self, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=30, pady=12)

    def reload(self):
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        pet = self.app.get_active_pet()
        if not pet:
            self.show_empty(self.list_frame, "Select a pet first.")
            return

        logs = self._load_logs(pet["id"])

        if not logs:
            self.show_empty(self.list_frame,
                            "No weight entries yet. Click '＋ Log Weight' to start.")
            return

        # Show stats
        self._build_stats(logs)

        # Show log entries
        tk.Label(self.list_frame, text="Weight History",
                 bg=BG, fg=MUTED, font=("Arial", 10)).pack(anchor="w", pady=(0, 8))

        for entry in logs:
            self._make_log_row(entry)

    # ── Database calls ────────────────────────────────────────────

    def _load_logs(self, pet_id):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM weight_logs WHERE pet_id=? ORDER BY date DESC",
            (pet_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _add_log(self, pet_id, weight, unit, log_date, notes):
        conn = get_connection()
        conn.execute(
            "INSERT INTO weight_logs (pet_id, weight, unit, date, notes) VALUES (?,?,?,?,?)",
            (pet_id, weight, unit, log_date, notes or None)
        )
        conn.commit()
        conn.close()

    def _delete_log(self, log_id):
        conn = get_connection()
        conn.execute("DELETE FROM weight_logs WHERE id=?", (log_id,))
        conn.commit()
        conn.close()

    # ── UI builders ───────────────────────────────────────────────

    def _build_stats(self, logs):
        """Show current, min, and max weight at the top."""
        weights = [e["weight"] for e in logs]
        unit    = logs[0]["unit"]

        stats = [
            ("Current",  f"{logs[0]['weight']} {unit}"),
            ("Lowest",   f"{min(weights)} {unit}"),
            ("Highest",  f"{max(weights)} {unit}"),
            ("Entries",  str(len(logs))),
        ]

        for label, value in stats:
            outer = tk.Frame(self.stats_frame, bg=BORDER)
            outer.pack(side="left", fill="x", expand=True, padx=(0, 8))
            inner = tk.Frame(outer, bg=SURFACE, padx=14, pady=10)
            inner.pack(fill="both", expand=True, padx=1, pady=1)
            tk.Label(inner, text=value, bg=SURFACE, fg=ACCENT,
                     font=("Arial", 16, "bold")).pack(anchor="w")
            tk.Label(inner, text=label, bg=SURFACE, fg=MUTED,
                     font=("Arial", 10)).pack(anchor="w")

    def _make_log_row(self, entry):
        """Build one row for a weight log entry."""
        outer = tk.Frame(self.list_frame, bg=BORDER)
        outer.pack(fill="x", pady=(0, 5))
        inner = tk.Frame(outer, bg=SURFACE, padx=14, pady=10)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        tk.Frame(inner, bg=ACCENT, width=4).pack(side="left", fill="y", padx=(0, 12))

        # Weight value (big)
        tk.Label(inner, text=f"{entry['weight']} {entry['unit']}",
                 bg=SURFACE, fg=ACCENT,
                 font=("Arial", 16, "bold")).pack(side="left", padx=(0, 16))

        # Date and notes
        info = tk.Frame(inner, bg=SURFACE)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=entry["date"], bg=SURFACE, fg=TEXT,
                 font=("Arial", 11, "bold"), anchor="w").pack(fill="x")
        if entry["notes"]:
            tk.Label(info, text=entry["notes"], bg=SURFACE, fg=MUTED,
                     font=("Arial", 10), anchor="w").pack(fill="x")

        # Delete button
        self.make_danger_button(
            inner, "Delete",
            lambda e=entry: self._confirm_delete(e)
        ).pack(side="right")

    def _confirm_delete(self, entry):
        confirmed = self.app.ask_yes_no("Delete Entry",
                                         f"Delete weight entry from {entry['date']}?")
        if confirmed:
            self._delete_log(entry["id"])
            self.reload()

    # ── Add Weight Dialog ─────────────────────────────────────────

    def _open_add_dialog(self):
        pet = self.app.get_active_pet()
        if not pet:
            self.app.show_message("No Pet", "Please select a pet first.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Log Weight")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.grab_set()

        tk.Label(dialog, text="Log Weight", bg=BG, fg=TEXT,
                 font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2,
                                                   padx=24, pady=(20, 12), sticky="w")

        unit_var = tk.StringVar(value="kg")

        form_rows = [
            ("Weight *", "weight", "e.g. 5.2"),
            ("Date",     "date",   str(date.today())),
            ("Notes",    "notes",  "e.g. Vet visit"),
        ]

        fields = {}
        for i, (label, key, placeholder) in enumerate(form_rows, start=1):
            tk.Label(dialog, text=label, bg=BG, fg=MUTED,
                     font=("Arial", 10)).grid(row=i, column=0, padx=(24, 8),
                                               pady=4, sticky="w")
            entry = self.make_entry(dialog, width=20)
            entry.insert(0, placeholder)
            entry.config(fg=TEXT if key == "date" else MUTED)

            def on_focus(e, ent=entry, ph=placeholder):
                if ent.get() == ph and ph != str(date.today()):
                    ent.delete(0, "end")
                    ent.config(fg=TEXT)

            entry.bind("<FocusIn>", on_focus)
            entry.grid(row=i, column=1, padx=(0, 24), pady=4)
            fields[key] = (entry, placeholder)

        # Unit dropdown
        row_num = len(form_rows) + 1
        tk.Label(dialog, text="Unit", bg=BG, fg=MUTED,
                 font=("Arial", 10)).grid(row=row_num, column=0, padx=(24, 8),
                                          pady=4, sticky="w")
        unit_menu = tk.OptionMenu(dialog, unit_var, "kg", "lbs")
        unit_menu.config(bg=SURFACE, fg=TEXT, relief="flat",
                         font=("Arial", 10), activebackground=ACCENT)
        unit_menu.grid(row=row_num, column=1, padx=(0, 24), pady=4, sticky="w")

        error_lbl = tk.Label(dialog, text="", bg=BG, fg=RED, font=("Arial", 10))
        error_lbl.grid(row=row_num + 1, column=0, columnspan=2, padx=24)

        def get_val(key):
            entry, placeholder = fields[key]
            val = entry.get().strip()
            return "" if val == placeholder else val

        def submit():
            weight_str = get_val("weight")
            if not weight_str:
                error_lbl.config(text="Weight is required.")
                return
            try:
                weight = float(weight_str)
            except ValueError:
                error_lbl.config(text="Weight must be a number.")
                return
            log_date = get_val("date") or str(date.today())
            self._add_log(pet["id"], weight, unit_var.get(), log_date, get_val("notes"))
            dialog.destroy()
            self.reload()

        btn_row = tk.Frame(dialog, bg=BG)
        btn_row.grid(row=row_num + 2, column=0, columnspan=2,
                     padx=24, pady=(8, 20), sticky="e")
        tk.Button(btn_row, text="Cancel", command=dialog.destroy,
                  bg=SURFACE, fg=MUTED, relief="flat", padx=10, pady=6,
                  cursor="hand2").pack(side="left", padx=(0, 8))
        self.make_button(btn_row, "Log Weight", submit).pack(side="left")