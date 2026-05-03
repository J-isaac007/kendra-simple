"""
pages/medications.py — Track medications for the active pet.

Lets you:
  - View all medications
  - Add a new medication (name, dosage, frequency, notes)
  - Delete a medication
"""
import tkinter as tk
from pages.base import BasePage, BG, SURFACE, ACCENT, GREEN, RED, TEXT, MUTED, BORDER
from database import get_connection


FREQUENCY_OPTIONS = ["Daily", "Twice daily", "Weekly", "Monthly", "As needed"]


class MedicationsPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app, title="💊  Medications",
                         subtitle="Keep track of your pet's medications and dosage schedules.")

        # ── Top bar ───────────────────────────────────────────────
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=30, pady=(16, 0))
        self.make_button(top, "＋ Add Medication", self._open_add_dialog).pack(side="left")

        # ── List area ─────────────────────────────────────────────
        self.list_frame = tk.Frame(self, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=30, pady=16)

    def reload(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        pet = self.app.get_active_pet()
        if not pet:
            self.show_empty(self.list_frame, "Select a pet first.")
            return

        meds = self._load_meds(pet["id"])
        if not meds:
            self.show_empty(self.list_frame,
                            "No medications added yet. Click '＋ Add Medication'.")
            return

        for med in meds:
            self._make_med_row(med)

    # ── Database calls ────────────────────────────────────────────

    def _load_meds(self, pet_id):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM medications WHERE pet_id=? ORDER BY name",
            (pet_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _add_med(self, pet_id, name, dosage, frequency, notes):
        conn = get_connection()
        conn.execute(
            "INSERT INTO medications (pet_id, name, dosage, frequency, notes) VALUES (?,?,?,?,?)",
            (pet_id, name, dosage or None, frequency, notes or None)
        )
        conn.commit()
        conn.close()

    def _delete_med(self, med_id):
        conn = get_connection()
        conn.execute("DELETE FROM medications WHERE id=?", (med_id,))
        conn.commit()
        conn.close()

    # ── UI builders ───────────────────────────────────────────────

    def _make_med_row(self, med):
        """Build one row for a medication."""
        outer = tk.Frame(self.list_frame, bg=BORDER)
        outer.pack(fill="x", pady=(0, 6))
        inner = tk.Frame(outer, bg=SURFACE, padx=14, pady=10)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Purple accent bar for medications
        tk.Frame(inner, bg="#cba6f7", width=4).pack(side="left", fill="y", padx=(0, 12))

        # Med info
        info = tk.Frame(inner, bg=SURFACE)
        info.pack(side="left", fill="x", expand=True)

        tk.Label(info, text=med["name"], bg=SURFACE, fg=TEXT,
                 font=("Arial", 12, "bold"), anchor="w").pack(fill="x")

        details = med["frequency"]
        if med["dosage"]:
            details = f"{med['dosage']}  ·  " + details
        if med["notes"]:
            details += f"  ·  {med['notes']}"
        tk.Label(info, text=details, bg=SURFACE, fg=MUTED,
                 font=("Arial", 10), anchor="w").pack(fill="x")

        # Delete button
        self.make_danger_button(
            inner, "Delete",
            lambda m=med: self._confirm_delete(m)
        ).pack(side="right")

    def _confirm_delete(self, med):
        confirmed = self.app.ask_yes_no("Delete Medication",
                                         f"Delete '{med['name']}'?")
        if confirmed:
            self._delete_med(med["id"])
            self.reload()

    # ── Add Medication Dialog ─────────────────────────────────────

    def _open_add_dialog(self):
        pet = self.app.get_active_pet()
        if not pet:
            self.app.show_message("No Pet", "Please select a pet first.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Medication")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.grab_set()

        tk.Label(dialog, text="Add Medication", bg=BG, fg=TEXT,
                 font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2,
                                                   padx=24, pady=(20, 12), sticky="w")

        # Frequency dropdown variable
        freq_var = tk.StringVar(value="Daily")

        # Text fields
        text_fields = [
            ("Name *",    "name",   "e.g. Flea treatment"),
            ("Dosage",    "dosage", "e.g. 1 tablet"),
            ("Notes",     "notes",  "e.g. Give with food"),
        ]

        fields = {}
        for i, (label, key, placeholder) in enumerate(text_fields, start=1):
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

        # Frequency dropdown
        row_num = len(text_fields) + 1
        tk.Label(dialog, text="Frequency *", bg=BG, fg=MUTED,
                 font=("Arial", 10)).grid(row=row_num, column=0, padx=(24, 8),
                                          pady=4, sticky="w")
        freq_menu = tk.OptionMenu(dialog, freq_var, *FREQUENCY_OPTIONS)
        freq_menu.config(bg=SURFACE, fg=TEXT, relief="flat",
                         font=("Arial", 10), activebackground=ACCENT)
        freq_menu.grid(row=row_num, column=1, padx=(0, 24), pady=4, sticky="w")

        error_lbl = tk.Label(dialog, text="", bg=BG, fg=RED, font=("Arial", 10))
        error_lbl.grid(row=row_num + 1, column=0, columnspan=2, padx=24)

        def get_val(key):
            entry, placeholder = fields[key]
            val = entry.get().strip()
            return "" if val == placeholder else val

        def submit():
            name = get_val("name")
            if not name:
                error_lbl.config(text="Name is required.")
                return
            self._add_med(pet["id"], name, get_val("dosage"),
                          freq_var.get(), get_val("notes"))
            dialog.destroy()
            self.reload()

        btn_row = tk.Frame(dialog, bg=BG)
        btn_row.grid(row=row_num + 2, column=0, columnspan=2,
                     padx=24, pady=(8, 20), sticky="e")
        tk.Button(btn_row, text="Cancel", command=dialog.destroy,
                  bg=SURFACE, fg=MUTED, relief="flat", padx=10, pady=6,
                  cursor="hand2").pack(side="left", padx=(0, 8))
        self.make_button(btn_row, "Add Medication", submit).pack(side="left")