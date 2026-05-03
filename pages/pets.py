"""
pages/pets.py — Manage your pets.

Lets you:
  - View all pets in a list
  - Select which pet is "active" (used by other pages)
  - Add a new pet
  - Delete a pet
"""
import tkinter as tk
from pages.base import BasePage, BG, SURFACE, ACCENT, GREEN, RED, TEXT, MUTED, BORDER
from database import get_connection


class PetsPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app, title="🐶  My Pets",
                         subtitle="Select a pet to view their care data on other pages.")
        self.active_pet = None  # the currently selected pet (a dict)

        # ── Top bar: Add Pet button ───────────────────────────────
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=30, pady=(16, 0))
        self.make_button(top, "＋ Add Pet", self._open_add_dialog).pack(side="left")

        # ── List area ─────────────────────────────────────────────
        self.list_frame = tk.Frame(self, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=30, pady=16)

    def reload(self):
        """Refresh the pet list from the database."""
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        pets = self._load_pets()

        if not pets:
            self.show_empty(self.list_frame,
                            "No pets yet. Click '＋ Add Pet' to get started!")
            return

        for pet in pets:
            self._make_pet_row(pet)

    # ── Database calls ────────────────────────────────────────────

    def _load_pets(self):
        conn = get_connection()
        rows = conn.execute("SELECT * FROM pets ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _add_pet(self, name, species, breed, birthday, notes):
        conn = get_connection()
        conn.execute(
            "INSERT INTO pets (name, species, breed, birthday, notes) VALUES (?,?,?,?,?)",
            (name, species, breed or None, birthday or None, notes or None)
        )
        conn.commit()
        conn.close()

    def _delete_pet(self, pet_id):
        conn = get_connection()
        conn.execute("DELETE FROM pets WHERE id=?", (pet_id,))
        conn.commit()
        conn.close()

    # ── UI builders ───────────────────────────────────────────────

    def _make_pet_row(self, pet):
        """Build one row in the pet list for a single pet."""
        is_active = self.active_pet and self.active_pet["id"] == pet["id"]

        outer = tk.Frame(self.list_frame, bg=ACCENT if is_active else BORDER)
        outer.pack(fill="x", pady=(0, 6))
        inner = tk.Frame(outer, bg=SURFACE, padx=14, pady=10)
        inner.pack(fill="both", expand=True, padx=1 if is_active else 1, pady=1)

        # Pet name and details
        species_emoji = {
            "dog": "🐶", "cat": "🐱", "bird": "🦜", "rabbit": "🐰",
            "fish": "🐠", "hamster": "🐹", "other": "🐾",
        }.get(pet["species"].lower(), "🐾")

        name_text = f"{species_emoji}  {pet['name']}"
        if is_active:
            name_text += "  ✓ Active"

        tk.Label(
            inner, text=name_text,
            bg=SURFACE, fg=ACCENT if is_active else TEXT,
            font=("Arial", 12, "bold"),
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

        details = pet["species"].capitalize()
        if pet["breed"]:
            details += f" · {pet['breed']}"

        tk.Label(
            inner, text=details,
            bg=SURFACE, fg=MUTED,
            font=("Arial", 10),
            anchor="w"
        ).pack(side="left", padx=(0, 20))

        # Buttons
        if not is_active:
            self.make_button(inner, "Select", lambda p=pet: self._select_pet(p)
                             ).pack(side="left", padx=(0, 6))

        self.make_danger_button(inner, "Delete",
                                lambda p=pet: self._confirm_delete(p)
                                ).pack(side="left")

    def _select_pet(self, pet):
        """Set this pet as the active pet."""
        self.active_pet = pet
        self.reload()

    def _confirm_delete(self, pet):
        """Ask before deleting a pet."""
        confirmed = self.app.ask_yes_no(
            "Delete Pet",
            f"Delete {pet['name']}? All their data will be removed."
        )
        if confirmed:
            if self.active_pet and self.active_pet["id"] == pet["id"]:
                self.active_pet = None
            self._delete_pet(pet["id"])
            self.reload()

    # ── Add Pet Dialog ────────────────────────────────────────────

    def _open_add_dialog(self):
        """Open a popup window to add a new pet."""
        dialog = tk.Toplevel(self)
        dialog.title("Add a Pet")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.grab_set()  # make dialog modal

        tk.Label(dialog, text="Add a New Pet", bg=BG, fg=TEXT,
                 font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2,
                                                   padx=24, pady=(20, 12), sticky="w")

        # Form fields
        fields = {}
        form_rows = [
            ("Name *",    "name",     "e.g. Buddy"),
            ("Species *", "species",  "dog, cat, bird…"),
            ("Breed",     "breed",    "e.g. Labrador"),
            ("Birthday",  "birthday", "YYYY-MM-DD"),
            ("Notes",     "notes",    "Allergies, diet, etc."),
        ]

        for i, (label, key, placeholder) in enumerate(form_rows, start=1):
            tk.Label(dialog, text=label, bg=BG, fg=MUTED,
                     font=("Arial", 10)).grid(row=i, column=0, padx=(24, 8),
                                               pady=4, sticky="w")
            entry = self.make_entry(dialog, width=28)
            entry.insert(0, placeholder)
            entry.config(fg=MUTED)

            # Clear placeholder on focus
            def on_focus(e, ent=entry, ph=placeholder):
                if ent.get() == ph:
                    ent.delete(0, "end")
                    ent.config(fg=TEXT)

            entry.bind("<FocusIn>", on_focus)
            entry.grid(row=i, column=1, padx=(0, 24), pady=4)
            fields[key] = (entry, placeholder)

        # Error label
        error_lbl = tk.Label(dialog, text="", bg=BG, fg=RED, font=("Arial", 10))
        error_lbl.grid(row=len(form_rows) + 1, column=0, columnspan=2, padx=24)

        def submit():
            # Get values, treating placeholder text as empty
            def get_val(key):
                entry, placeholder = fields[key]
                val = entry.get().strip()
                return "" if val == placeholder else val

            name    = get_val("name")
            species = get_val("species")

            if not name:
                error_lbl.config(text="Name is required.")
                return
            if not species:
                error_lbl.config(text="Species is required.")
                return

            self._add_pet(name, species, get_val("breed"),
                          get_val("birthday"), get_val("notes"))
            dialog.destroy()
            self.reload()

        # Buttons
        btn_row = tk.Frame(dialog, bg=BG)
        btn_row.grid(row=len(form_rows) + 2, column=0, columnspan=2,
                     padx=24, pady=(8, 20), sticky="e")

        tk.Button(btn_row, text="Cancel", command=dialog.destroy,
                  bg=SURFACE, fg=MUTED, relief="flat", padx=10, pady=6,
                  cursor="hand2").pack(side="left", padx=(0, 8))
        self.make_button(btn_row, "Add Pet", submit).pack(side="left")