"""
pages/dashboard.py — The home/overview page.

Shows a greeting, the active pet, quick stats for today,
and a button to export all pet data to a CSV file.
"""
import tkinter as tk
import csv
import os
from datetime import datetime
from tkinter import filedialog
from pages.base import BasePage, BG, SURFACE, ACCENT, GREEN, RED, TEXT, MUTED, BORDER
from database import get_connection


class DashboardPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app, title="Dashboard")
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill="both", expand=True, padx=30, pady=20)

    def reload(self):
        """Refresh everything shown on the dashboard."""
        for widget in self.content.winfo_children():
            widget.destroy()

        pet = self.app.get_active_pet()

        # ── Greeting ──────────────────────────────────────────────
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning! ☀️"
        elif hour < 18:
            greeting = "Good afternoon! 🌤"
        else:
            greeting = "Good evening! 🌙"

        tk.Label(
            self.content, text=greeting,
            bg=BG, fg=TEXT, font=("Arial", 18, "bold"), anchor="w"
        ).pack(fill="x", pady=(0, 4))

        tk.Label(
            self.content, text=datetime.now().strftime("%A, %B %d"),
            bg=BG, fg=MUTED, font=("Arial", 11), anchor="w"
        ).pack(fill="x", pady=(0, 20))

        # ── No pet selected ───────────────────────────────────────
        if not pet:
            tk.Label(
                self.content,
                text="🐾  No pet selected.\nGo to 'My Pets' to add or select one.",
                bg=BG, fg=MUTED, font=("Arial", 13), justify="center"
            ).pack(expand=True)
            return

        # ── Active pet card ───────────────────────────────────────
        outer, card = self.make_card(self.content)
        outer.pack(fill="x", pady=(0, 20))

        tk.Label(
            card, text=f"Active Pet: {pet['name']}",
            bg=SURFACE, fg=ACCENT, font=("Arial", 13, "bold"), anchor="w"
        ).pack(fill="x")

        details = pet["species"].capitalize()
        if pet["breed"]:
            details += f" · {pet['breed']}"
        if pet["birthday"]:
            details += f" · Born {pet['birthday']}"
        tk.Label(card, text=details, bg=SURFACE, fg=MUTED,
                 font=("Arial", 10), anchor="w").pack(fill="x")

        # ── Today's summary ───────────────────────────────────────
        tk.Label(
            self.content, text="Today's Summary",
            bg=BG, fg=TEXT, font=("Arial", 14, "bold"), anchor="w"
        ).pack(fill="x", pady=(0, 4))

        tk.Label(
            self.content, text="Click a card to go to that page.",
            bg=BG, fg=MUTED, font=("Arial", 9), anchor="w"
        ).pack(fill="x", pady=(0, 10))

        stats = self._get_today_stats(pet["id"])

        stats_row = tk.Frame(self.content, bg=BG)
        stats_row.pack(fill="x")

        cards = [
            (
                f"{stats['meals_done']} / {stats['meals_total']}",
                "🍽  Meals Fed Today",
                GREEN if stats["meals_done"] >= stats["meals_total"] > 0 else ACCENT,
                "feeding"
            ),
            (
                str(stats["meds_total"]),
                "💊  Medications",
                ACCENT,
                "medications"
            ),
            (
                f"{stats['grooming_overdue']} overdue" if stats["grooming_overdue"] else "All OK",
                "✂  Grooming",
                RED if stats["grooming_overdue"] else GREEN,
                "grooming"
            ),
            (
                str(stats["weight_entries"]),
                "⚖  Weight Entries",
                ACCENT,
                "health"
            ),
        ]

        for value, label, color, page_key in cards:
            self._make_stat_card(stats_row, label, value, color, page_key)

        # ── Divider ───────────────────────────────────────────────
        tk.Frame(self.content, bg=BORDER, height=1).pack(fill="x", pady=(24, 16))

        # ── Export section ────────────────────────────────────────
        export_row = tk.Frame(self.content, bg=BG)
        export_row.pack(fill="x")

        tk.Label(
            export_row,
            text="📄  Export Pet Data",
            bg=BG, fg=TEXT, font=("Arial", 12, "bold")
        ).pack(side="left")

        tk.Label(
            export_row,
            text="  —  Save all records for this pet as a CSV file.",
            bg=BG, fg=MUTED, font=("Arial", 10)
        ).pack(side="left")

        self.make_button(
            export_row, "⬇ Download CSV",
            lambda: self._export_csv(pet),
        ).pack(side="right")

    # ── Stat cards ────────────────────────────────────────────────

    def _make_stat_card(self, parent, label, value, color, page_key):
        """A clickable stat card that navigates to page_key when clicked."""
        outer = tk.Frame(parent, bg=BORDER, cursor="hand2")
        outer.pack(side="left", fill="x", expand=True, padx=(0, 10))
        inner = tk.Frame(outer, bg=SURFACE, padx=16, pady=14, cursor="hand2")
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        val_lbl  = tk.Label(inner, text=value,  bg=SURFACE, fg=color,
                            font=("Arial", 18, "bold"))
        val_lbl.pack(anchor="w")

        name_lbl = tk.Label(inner, text=label,  bg=SURFACE, fg=MUTED,
                            font=("Arial", 10))
        name_lbl.pack(anchor="w")

        hint_lbl = tk.Label(inner, text="→ click to view", bg=SURFACE, fg=BORDER,
                            font=("Arial", 8))
        hint_lbl.pack(anchor="w")

        HOVER_BG = "#3d3f54"

        def on_enter(e):
            inner.config(bg=HOVER_BG)
            for w in (val_lbl, name_lbl, hint_lbl):
                w.config(bg=HOVER_BG)
            hint_lbl.config(fg=MUTED)

        def on_leave(e):
            inner.config(bg=SURFACE)
            for w in (val_lbl, name_lbl, hint_lbl):
                w.config(bg=SURFACE)
            hint_lbl.config(fg=BORDER)

        def on_click(e):
            self.app.show_page(page_key)

        for widget in (outer, inner, val_lbl, name_lbl, hint_lbl):
            widget.bind("<Enter>",    on_enter)
            widget.bind("<Leave>",    on_leave)
            widget.bind("<Button-1>", on_click)

    # ── CSV export ────────────────────────────────────────────────

    def _export_csv(self, pet):
        """
        Ask the user where to save the file, then write all of the
        pet's data (feeding, medications, weight, grooming) into one CSV.

        Each section has its own header row so the file is easy to read.
        """
        # Open a "Save As" dialog so the user picks the location
        default_name = f"{pet['name'].lower().replace(' ', '_')}_data.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_name,
            title="Save Pet Data As"
        )

        # User cancelled the dialog
        if not filepath:
            return

        conn = get_connection()

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # ── Pet info ──────────────────────────────────────────
            writer.writerow(["PET INFO"])
            writer.writerow(["Name", "Species", "Breed", "Birthday", "Notes"])
            writer.writerow([
                pet["name"], pet["species"],
                pet["breed"] or "", pet["birthday"] or "", pet["notes"] or ""
            ])

            writer.writerow([])  # blank line between sections

            # ── Feeding schedules ─────────────────────────────────
            writer.writerow(["FEEDING SCHEDULES"])
            writer.writerow(["Meal Name", "Time", "Food Type", "Portion"])
            rows = conn.execute(
                "SELECT meal_name, time, food_type, portion FROM feeding_schedules WHERE pet_id=?",
                (pet["id"],)
            ).fetchall()
            for r in rows:
                writer.writerow([r["meal_name"], r["time"],
                                  r["food_type"] or "", r["portion"] or ""])

            writer.writerow([])

            # ── Medications ───────────────────────────────────────
            writer.writerow(["MEDICATIONS"])
            writer.writerow(["Name", "Dosage", "Frequency", "Notes"])
            rows = conn.execute(
                "SELECT name, dosage, frequency, notes FROM medications WHERE pet_id=?",
                (pet["id"],)
            ).fetchall()
            for r in rows:
                writer.writerow([r["name"], r["dosage"] or "",
                                  r["frequency"], r["notes"] or ""])

            writer.writerow([])

            # ── Weight logs ───────────────────────────────────────
            writer.writerow(["WEIGHT HISTORY"])
            writer.writerow(["Date", "Weight", "Unit", "Notes"])
            rows = conn.execute(
                "SELECT date, weight, unit, notes FROM weight_logs WHERE pet_id=? ORDER BY date",
                (pet["id"],)
            ).fetchall()
            for r in rows:
                writer.writerow([r["date"], r["weight"],
                                  r["unit"], r["notes"] or ""])

            writer.writerow([])

            # ── Grooming tasks ────────────────────────────────────
            writer.writerow(["GROOMING TASKS"])
            writer.writerow(["Task", "Every (days)", "Last Done", "Next Due", "Notes"])
            rows = conn.execute(
                "SELECT task_name, interval_days, last_done, next_due, notes FROM grooming_tasks WHERE pet_id=?",
                (pet["id"],)
            ).fetchall()
            for r in rows:
                writer.writerow([r["task_name"], r["interval_days"],
                                  r["last_done"] or "", r["next_due"] or "",
                                  r["notes"] or ""])

        conn.close()

        # Let the user know it worked and where the file is
        self.app.show_message(
            "Export Successful",
            f"Data for {pet['name']} saved to:\n{filepath}"
        )

    # ── Stats query ───────────────────────────────────────────────

    def _get_today_stats(self, pet_id):
        """Query the database for all summary counts used by the stat cards."""
        conn = get_connection()
        today = datetime.now().strftime("%Y-%m-%d")

        meals_total = conn.execute(
            "SELECT COUNT(*) FROM feeding_schedules WHERE pet_id=?", (pet_id,)
        ).fetchone()[0]

        meals_done = conn.execute(
            "SELECT COUNT(*) FROM feeding_logs WHERE pet_id=? AND date(logged_at)=?",
            (pet_id, today)
        ).fetchone()[0]

        meds_total = conn.execute(
            "SELECT COUNT(*) FROM medications WHERE pet_id=?", (pet_id,)
        ).fetchone()[0]

        # Overdue = next_due is today or earlier
        grooming_overdue = conn.execute(
            "SELECT COUNT(*) FROM grooming_tasks WHERE pet_id=? AND next_due<=?",
            (pet_id, today)
        ).fetchone()[0]

        weight_entries = conn.execute(
            "SELECT COUNT(*) FROM weight_logs WHERE pet_id=?", (pet_id,)
        ).fetchone()[0]

        conn.close()
        return {
            "meals_total":      meals_total,
            "meals_done":       meals_done,
            "meds_total":       meds_total,
            "grooming_overdue": grooming_overdue,
            "weight_entries":   weight_entries,
        }