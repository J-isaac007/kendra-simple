"""
main.py - Kendra Pet Care Manager
Run with: python main.py

A simple tkinter app to help pet owners track their pets'
feeding schedules, medications, and weight history.
"""
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import date, timedelta
import calendar as cal_module
import csv
from database import setup_database, get_connection

# ── Colors ────────────────────────────────────────────────────
BG      = "#1e1e2e"
SURFACE = "#313244"
ACCENT  = "#89b4fa"
GREEN   = "#a6e3a1"
RED     = "#f38ba8"
TEXT    = "#cdd6f4"
MUTED   = "#6c7086"
BORDER  = "#45475a"


# ─────────────────────────────────────────────────────────────
#  MAIN APP WINDOW
# ─────────────────────────────────────────────────────────────

class KendraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kendra – Pet Care Manager")
        self.root.geometry("900x600")
        self.root.configure(bg=BG)
        self.root.minsize(750, 480)

        self.active_pet = None  # currently selected pet dict

        setup_database()
        self._build_ui()
        self._show_page("dashboard")

    def _build_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg="#181825", width=160)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="🐾 Kendra", bg="#181825", fg=ACCENT,
                 font=("Arial", 15, "bold"), pady=18).pack(fill="x")
        tk.Frame(self.sidebar, bg=MUTED, height=1).pack(fill="x", padx=12)

        self.nav_btns = {}
        nav = [
            ("🏠  Dashboard",   "dashboard"),
            ("🐶  My Pets",     "pets"),
            ("🍽  Feeding",     "feeding"),
            ("💊  Medications", "medications"),
            ("⚖  Health",      "health"),
            ("✂  Grooming",    "grooming"),
            ("📅  Calendar",   "calendar"),
        ]
        for label, key in nav:
            btn = tk.Button(
                self.sidebar, text=label, bg="#181825", fg=TEXT,
                font=("Arial", 11), anchor="w", padx=14, pady=9,
                relief="flat", cursor="hand2",
                command=lambda k=key: self._show_page(k)
            )
            btn.pack(fill="x")
            self.nav_btns[key] = btn

        # Content area
        self.content = tk.Frame(self.root, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        # Build all pages (stacked)
        self.pages = {
            "dashboard":   DashboardPage(self.content, self),
            "pets":        PetsPage(self.content, self),
            "feeding":     FeedingPage(self.content, self),
            "medications": MedicationsPage(self.content, self),
            "health":      HealthPage(self.content, self),
            "grooming":    GroomingPage(self.content, self),
            "calendar":    CalendarPage(self.content, self),
        }
        for page in self.pages.values():
            page.place(x=0, y=0, relwidth=1, relheight=1)

    def _show_page(self, key):
        for k, btn in self.nav_btns.items():
            btn.config(bg="#181825", fg=TEXT)
        self.nav_btns[key].config(bg="#313244", fg=ACCENT)
        self.pages[key].reload()
        self.pages[key].tkraise()

    # Shared helpers
    def ask(self, title, msg):
        return messagebox.askyesno(title, msg)

    def info(self, title, msg):
        messagebox.showinfo(title, msg)


# ─────────────────────────────────────────────────────────────
#  BASE PAGE
# ─────────────────────────────────────────────────────────────

class BasePage(tk.Frame):
    def __init__(self, parent, app, title, subtitle=""):
        super().__init__(parent, bg=BG)
        self.app = app
        self._header(title, subtitle)

    def _header(self, title, subtitle):
        tk.Label(self, text=title, bg=BG, fg=TEXT,
                 font=("Arial", 20, "bold"), anchor="w"
                 ).pack(fill="x", padx=28, pady=(22, 0))
        if subtitle:
            tk.Label(self, text=subtitle, bg=BG, fg=MUTED,
                     font=("Arial", 10), anchor="w"
                     ).pack(fill="x", padx=28)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(10, 0))

    def reload(self):
        pass

    # Widget helpers
    def btn(self, parent, text, cmd, color=None):
        return tk.Button(parent, text=text, command=cmd,
                         bg=color or ACCENT, fg=BG,
                         font=("Arial", 10, "bold"),
                         relief="flat", padx=10, pady=5, cursor="hand2")

    def danger_btn(self, parent, text, cmd):
        return self.btn(parent, text, cmd, color=RED)

    def entry(self, parent, width=22):
        return tk.Entry(parent, bg=SURFACE, fg=TEXT,
                        insertbackground=ACCENT,
                        font=("Arial", 11), relief="flat", bd=6, width=width)

    def empty(self, parent, msg):
        tk.Label(parent, text=msg, bg=BG, fg=MUTED,
                 font=("Arial", 12)).pack(expand=True)

    def row_card(self, parent):
        """Returns (outer_frame, inner_frame) for a bordered card row."""
        outer = tk.Frame(parent, bg=BORDER)
        outer.pack(fill="x", pady=(0, 5))
        inner = tk.Frame(outer, bg=SURFACE, padx=12, pady=9)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        return outer, inner

    def dialog(self, title):
        """Open a basic modal dialog window."""
        d = tk.Toplevel(self)
        d.title(title)
        d.configure(bg=BG)
        d.resizable(False, False)
        d.grab_set()
        return d

    def form_row(self, parent, row, label, placeholder, width=22):
        """Add a label + entry row to a grid dialog. Returns the Entry."""
        tk.Label(parent, text=label, bg=BG, fg=MUTED,
                 font=("Arial", 10)).grid(row=row, column=0,
                                          padx=(22, 8), pady=4, sticky="w")
        e = self.entry(parent, width=width)
        e.insert(0, placeholder)
        e.config(fg=MUTED)
        e.bind("<FocusIn>", lambda ev, ent=e, ph=placeholder: (
            ent.delete(0, "end") or ent.config(fg=TEXT)
        ) if ent.get() == ph else None)
        e.grid(row=row, column=1, padx=(0, 22), pady=4)
        return e

    def get_val(self, entry_widget, placeholder):
        v = entry_widget.get().strip()
        return "" if v == placeholder else v


# ─────────────────────────────────────────────────────────────
#  PETS PAGE
# ─────────────────────────────────────────────────────────────

class PetsPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app, "🐶  My Pets",
                         "Add pets and select which one is active.")
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=28, pady=(14, 0))
        self.btn(top, "＋ Add Pet", self._add_dialog).pack(side="left")

        self.list_frame = tk.Frame(self, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=28, pady=14)

    def reload(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        pets = self._load()
        if not pets:
            self.empty(self.list_frame, "No pets yet. Click '＋ Add Pet' to start!")
            return
        for p in pets:
            self._row(p)

    def _load(self):
        conn = get_connection()
        rows = conn.execute("SELECT * FROM pets ORDER BY name").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _row(self, pet):
        is_active = self.app.active_pet and self.app.active_pet["id"] == pet["id"]
        _, inner = self.row_card(self.list_frame)

        emoji = {"dog":"🐶","cat":"🐱","bird":"🦜","rabbit":"🐰",
                 "fish":"🐠","hamster":"🐹"}.get(pet["species"].lower(), "🐾")
        name = f"{emoji}  {pet['name']}"
        if is_active:
            name += "  ✓ Active"

        tk.Label(inner, text=name, bg=SURFACE,
                 fg=ACCENT if is_active else TEXT,
                 font=("Arial", 12, "bold"), anchor="w"
                 ).pack(side="left", fill="x", expand=True)

        detail = pet["species"].capitalize()
        if pet["breed"]:
            detail += f" · {pet['breed']}"
        tk.Label(inner, text=detail, bg=SURFACE, fg=MUTED,
                 font=("Arial", 10), anchor="w").pack(side="left", padx=(0, 16))

        if not is_active:
            self.btn(inner, "Select", lambda p=pet: self._select(p)
                     ).pack(side="left", padx=(0, 6))
        self.danger_btn(inner, "Delete", lambda p=pet: self._delete(p)).pack(side="left")

    def _select(self, pet):
        self.app.active_pet = pet
        self.reload()

    def _delete(self, pet):
        if self.app.ask("Delete Pet", f"Delete {pet['name']}? All data will be removed."):
            if self.app.active_pet and self.app.active_pet["id"] == pet["id"]:
                self.app.active_pet = None
            conn = get_connection()
            conn.execute("DELETE FROM pets WHERE id=?", (pet["id"],))
            conn.commit()
            conn.close()
            self.reload()

    def _add_dialog(self):
        d = self.dialog("Add a Pet")

        tk.Label(d, text="Add a New Pet", bg=BG, fg=TEXT,
                 font=("Arial", 13, "bold")).grid(
            row=0, column=0, columnspan=2, padx=22, pady=(18, 10), sticky="w")

        ph = ["e.g. Buddy", "dog, cat, bird…", "e.g. Labrador", "YYYY-MM-DD"]
        labels = ["Name *", "Species *", "Breed", "Birthday"]
        entries = [self.form_row(d, i+1, labels[i], ph[i]) for i in range(4)]
        err = tk.Label(d, text="", bg=BG, fg=RED, font=("Arial", 10))
        err.grid(row=5, column=0, columnspan=2)

        def submit():
            name    = self.get_val(entries[0], ph[0])
            species = self.get_val(entries[1], ph[1])
            if not name:
                err.config(text="Name is required."); return
            if not species:
                err.config(text="Species is required."); return
            conn = get_connection()
            conn.execute(
                "INSERT INTO pets (name, species, breed, birthday) VALUES (?,?,?,?)",
                (name, species,
                 self.get_val(entries[2], ph[2]) or None,
                 self.get_val(entries[3], ph[3]) or None)
            )
            conn.commit(); conn.close()
            d.destroy(); self.reload()

        brow = tk.Frame(d, bg=BG)
        brow.grid(row=6, column=0, columnspan=2, padx=22, pady=(6, 18), sticky="e")
        tk.Button(brow, text="Cancel", command=d.destroy,
                  bg=SURFACE, fg=MUTED, relief="flat", padx=10, pady=5,
                  cursor="hand2").pack(side="left", padx=(0, 8))
        self.btn(brow, "Add Pet", submit).pack(side="left")


# ─────────────────────────────────────────────────────────────
#  FEEDING PAGE
# ─────────────────────────────────────────────────────────────

class FeedingPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app, "🍽  Feeding",
                         "Manage meal schedules for your pet.")
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=28, pady=(14, 0))
        self.btn(top, "＋ Add Meal", self._add_dialog).pack(side="left")
        self.list_frame = tk.Frame(self, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=28, pady=14)

    def reload(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        pet = self.app.active_pet
        if not pet:
            self.empty(self.list_frame, "Select a pet first."); return
        rows = self._load(pet["id"])
        if not rows:
            self.empty(self.list_frame, "No meal schedules yet. Click '＋ Add Meal'."); return
        for r in rows:
            self._row(r)

    def _load(self, pet_id):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM feeding_schedules WHERE pet_id=? ORDER BY time",
            (pet_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _row(self, s):
        _, inner = self.row_card(self.list_frame)
        tk.Frame(inner, bg=ACCENT, width=4).pack(side="left", fill="y", padx=(0, 10))

        info = tk.Frame(inner, bg=SURFACE)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=s["meal_name"], bg=SURFACE, fg=TEXT,
                 font=("Arial", 12, "bold"), anchor="w").pack(fill="x")
        detail = s["time"]
        if s["food_type"]:
            detail += f"  ·  {s['food_type']}"
        if s["portion"]:
            detail += f"  ·  {s['portion']}"
        tk.Label(info, text=detail, bg=SURFACE, fg=MUTED,
                 font=("Arial", 10), anchor="w").pack(fill="x")

        self.danger_btn(inner, "Delete", lambda sid=s["id"]: self._delete(sid)
                        ).pack(side="right")

    def _delete(self, sid):
        if self.app.ask("Delete Meal", "Delete this meal schedule?"):
            conn = get_connection()
            conn.execute("DELETE FROM feeding_schedules WHERE id=?", (sid,))
            conn.commit(); conn.close()
            self.reload()

    def _add_dialog(self):
        pet = self.app.active_pet
        if not pet:
            self.app.info("No Pet", "Select a pet first."); return
        d = self.dialog("Add Meal")
        tk.Label(d, text="Add Meal Schedule", bg=BG, fg=TEXT,
                 font=("Arial", 13, "bold")).grid(
            row=0, column=0, columnspan=2, padx=22, pady=(18, 10), sticky="w")

        ph = ["e.g. Breakfast", "e.g. 08:00", "e.g. Dry kibble", "e.g. 1 cup"]
        labels = ["Meal Name *", "Time *", "Food Type", "Portion"]
        entries = [self.form_row(d, i+1, labels[i], ph[i]) for i in range(4)]
        err = tk.Label(d, text="", bg=BG, fg=RED, font=("Arial", 10))
        err.grid(row=5, column=0, columnspan=2)

        def submit():
            name = self.get_val(entries[0], ph[0])
            time = self.get_val(entries[1], ph[1])
            if not name: err.config(text="Meal name is required."); return
            if not time: err.config(text="Time is required."); return
            conn = get_connection()
            conn.execute(
                "INSERT INTO feeding_schedules (pet_id, meal_name, time, food_type, portion) VALUES (?,?,?,?,?)",
                (pet["id"], name, time,
                 self.get_val(entries[2], ph[2]) or None,
                 self.get_val(entries[3], ph[3]) or None)
            )
            conn.commit(); conn.close()
            d.destroy(); self.reload()

        brow = tk.Frame(d, bg=BG)
        brow.grid(row=6, column=0, columnspan=2, padx=22, pady=(6, 18), sticky="e")
        tk.Button(brow, text="Cancel", command=d.destroy,
                  bg=SURFACE, fg=MUTED, relief="flat", padx=10, pady=5,
                  cursor="hand2").pack(side="left", padx=(0, 8))
        self.btn(brow, "Add Meal", submit).pack(side="left")


# ─────────────────────────────────────────────────────────────
#  MEDICATIONS PAGE
# ─────────────────────────────────────────────────────────────

FREQ_OPTIONS = ["Daily", "Twice daily", "Weekly", "Monthly", "As needed"]

class MedicationsPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app, "💊  Medications",
                         "Track your pet's medications and dosages.")
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=28, pady=(14, 0))
        self.btn(top, "＋ Add Medication", self._add_dialog).pack(side="left")
        self.list_frame = tk.Frame(self, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=28, pady=14)

    def reload(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        pet = self.app.active_pet
        if not pet:
            self.empty(self.list_frame, "Select a pet first."); return
        rows = self._load(pet["id"])
        if not rows:
            self.empty(self.list_frame, "No medications yet. Click '＋ Add Medication'."); return
        for r in rows:
            self._row(r)

    def _load(self, pet_id):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM medications WHERE pet_id=? ORDER BY name",
            (pet_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _row(self, med):
        _, inner = self.row_card(self.list_frame)
        tk.Frame(inner, bg="#cba6f7", width=4).pack(side="left", fill="y", padx=(0, 10))

        info = tk.Frame(inner, bg=SURFACE)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=med["name"], bg=SURFACE, fg=TEXT,
                 font=("Arial", 12, "bold"), anchor="w").pack(fill="x")
        detail = med["frequency"]
        if med["dosage"]:
            detail = med["dosage"] + "  ·  " + detail
        if med["notes"]:
            detail += f"  ·  {med['notes']}"
        tk.Label(info, text=detail, bg=SURFACE, fg=MUTED,
                 font=("Arial", 10), anchor="w").pack(fill="x")

        self.danger_btn(inner, "Delete", lambda mid=med["id"]: self._delete(mid)
                        ).pack(side="right")

    def _delete(self, mid):
        if self.app.ask("Delete Medication", "Delete this medication?"):
            conn = get_connection()
            conn.execute("DELETE FROM medications WHERE id=?", (mid,))
            conn.commit(); conn.close()
            self.reload()

    def _add_dialog(self):
        pet = self.app.active_pet
        if not pet:
            self.app.info("No Pet", "Select a pet first."); return
        d = self.dialog("Add Medication")
        tk.Label(d, text="Add Medication", bg=BG, fg=TEXT,
                 font=("Arial", 13, "bold")).grid(
            row=0, column=0, columnspan=2, padx=22, pady=(18, 10), sticky="w")

        ph = ["e.g. Flea treatment", "e.g. 1 tablet", "e.g. Give with food"]
        labels = ["Name *", "Dosage", "Notes"]
        entries = [self.form_row(d, i+1, labels[i], ph[i]) for i in range(3)]

        freq_var = tk.StringVar(value="Daily")
        tk.Label(d, text="Frequency *", bg=BG, fg=MUTED, font=("Arial", 10)
                 ).grid(row=4, column=0, padx=(22, 8), pady=4, sticky="w")
        tk.OptionMenu(d, freq_var, *FREQ_OPTIONS).grid(row=4, column=1, sticky="w",
                                                        padx=(0, 22), pady=4)

        err = tk.Label(d, text="", bg=BG, fg=RED, font=("Arial", 10))
        err.grid(row=5, column=0, columnspan=2)

        def submit():
            name = self.get_val(entries[0], ph[0])
            if not name: err.config(text="Name is required."); return
            conn = get_connection()
            conn.execute(
                "INSERT INTO medications (pet_id, name, dosage, frequency, notes) VALUES (?,?,?,?,?)",
                (pet["id"], name,
                 self.get_val(entries[1], ph[1]) or None,
                 freq_var.get(),
                 self.get_val(entries[2], ph[2]) or None)
            )
            conn.commit(); conn.close()
            d.destroy(); self.reload()

        brow = tk.Frame(d, bg=BG)
        brow.grid(row=6, column=0, columnspan=2, padx=22, pady=(6, 18), sticky="e")
        tk.Button(brow, text="Cancel", command=d.destroy,
                  bg=SURFACE, fg=MUTED, relief="flat", padx=10, pady=5,
                  cursor="hand2").pack(side="left", padx=(0, 8))
        self.btn(brow, "Add Medication", submit).pack(side="left")


# ─────────────────────────────────────────────────────────────
#  HEALTH / WEIGHT PAGE
# ─────────────────────────────────────────────────────────────

class HealthPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app, "⚖  Health & Weight",
                         "Log your pet's weight over time.")
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=28, pady=(14, 0))
        self.btn(top, "＋ Log Weight", self._add_dialog).pack(side="left")
        self.stats_frame = tk.Frame(self, bg=BG)
        self.stats_frame.pack(fill="x", padx=28, pady=(14, 0))
        self.list_frame = tk.Frame(self, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=28, pady=10)

    def reload(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()
        for w in self.list_frame.winfo_children():
            w.destroy()
        pet = self.app.active_pet
        if not pet:
            self.empty(self.list_frame, "Select a pet first."); return
        logs = self._load(pet["id"])
        if not logs:
            self.empty(self.list_frame, "No weight entries yet. Click '＋ Log Weight'."); return
        self._stats(logs)
        tk.Label(self.list_frame, text="Weight History", bg=BG, fg=MUTED,
                 font=("Arial", 10)).pack(anchor="w", pady=(0, 6))
        for e in logs:
            self._row(e)

    def _load(self, pet_id):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM weight_logs WHERE pet_id=? ORDER BY date DESC",
            (pet_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _stats(self, logs):
        weights = [e["weight"] for e in logs]
        unit = logs[0]["unit"]
        for label, val in [("Current", f"{logs[0]['weight']} {unit}"),
                            ("Lowest",  f"{min(weights)} {unit}"),
                            ("Highest", f"{max(weights)} {unit}"),
                            ("Entries", str(len(logs)))]:
            outer = tk.Frame(self.stats_frame, bg=BORDER)
            outer.pack(side="left", fill="x", expand=True, padx=(0, 8))
            inner = tk.Frame(outer, bg=SURFACE, padx=12, pady=8)
            inner.pack(fill="both", expand=True, padx=1, pady=1)
            tk.Label(inner, text=val, bg=SURFACE, fg=ACCENT,
                     font=("Arial", 15, "bold")).pack(anchor="w")
            tk.Label(inner, text=label, bg=SURFACE, fg=MUTED,
                     font=("Arial", 9)).pack(anchor="w")

    def _row(self, entry):
        _, inner = self.row_card(self.list_frame)
        tk.Frame(inner, bg=ACCENT, width=4).pack(side="left", fill="y", padx=(0, 10))
        tk.Label(inner, text=f"{entry['weight']} {entry['unit']}",
                 bg=SURFACE, fg=ACCENT, font=("Arial", 15, "bold")
                 ).pack(side="left", padx=(0, 14))

        info = tk.Frame(inner, bg=SURFACE)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=entry["date"], bg=SURFACE, fg=TEXT,
                 font=("Arial", 11, "bold"), anchor="w").pack(fill="x")
        if entry["notes"]:
            tk.Label(info, text=entry["notes"], bg=SURFACE, fg=MUTED,
                     font=("Arial", 10), anchor="w").pack(fill="x")

        self.danger_btn(inner, "Delete", lambda eid=entry["id"]: self._delete(eid)
                        ).pack(side="right")

    def _delete(self, eid):
        if self.app.ask("Delete Entry", "Delete this weight entry?"):
            conn = get_connection()
            conn.execute("DELETE FROM weight_logs WHERE id=?", (eid,))
            conn.commit(); conn.close()
            self.reload()

    def _add_dialog(self):
        pet = self.app.active_pet
        if not pet:
            self.app.info("No Pet", "Select a pet first."); return
        d = self.dialog("Log Weight")
        tk.Label(d, text="Log Weight", bg=BG, fg=TEXT,
                 font=("Arial", 13, "bold")).grid(
            row=0, column=0, columnspan=2, padx=22, pady=(18, 10), sticky="w")

        ph = ["e.g. 5.2", str(date.today()), "e.g. Vet visit"]
        labels = ["Weight *", "Date", "Notes"]
        entries = [self.form_row(d, i+1, labels[i], ph[i]) for i in range(3)]

        unit_var = tk.StringVar(value="kg")
        tk.Label(d, text="Unit", bg=BG, fg=MUTED, font=("Arial", 10)
                 ).grid(row=4, column=0, padx=(22, 8), pady=4, sticky="w")
        tk.OptionMenu(d, unit_var, "kg", "lbs").grid(row=4, column=1, sticky="w",
                                                      padx=(0, 22), pady=4)

        err = tk.Label(d, text="", bg=BG, fg=RED, font=("Arial", 10))
        err.grid(row=5, column=0, columnspan=2)

        def submit():
            w_str = self.get_val(entries[0], ph[0])
            if not w_str: err.config(text="Weight is required."); return
            try:
                weight = float(w_str)
            except ValueError:
                err.config(text="Weight must be a number."); return
            log_date = self.get_val(entries[1], ph[1]) or str(date.today())
            conn = get_connection()
            conn.execute(
                "INSERT INTO weight_logs (pet_id, weight, unit, date, notes) VALUES (?,?,?,?,?)",
                (pet["id"], weight, unit_var.get(), log_date,
                 self.get_val(entries[2], ph[2]) or None)
            )
            conn.commit(); conn.close()
            d.destroy(); self.reload()

        brow = tk.Frame(d, bg=BG)
        brow.grid(row=6, column=0, columnspan=2, padx=22, pady=(6, 18), sticky="e")
        tk.Button(brow, text="Cancel", command=d.destroy,
                  bg=SURFACE, fg=MUTED, relief="flat", padx=10, pady=5,
                  cursor="hand2").pack(side="left", padx=(0, 8))
        self.btn(brow, "Log Weight", submit).pack(side="left")


# ─────────────────────────────────────────────────────────────
#  DASHBOARD PAGE
# ─────────────────────────────────────────────────────────────

class DashboardPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app, "🏠  Dashboard")
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(fill="both", expand=True, padx=28, pady=18)

    def reload(self):
        for w in self.content.winfo_children():
            w.destroy()

        hour = date.today().timetuple().tm_hour
        from datetime import datetime
        hour = datetime.now().hour
        greeting = "Good morning! ☀️" if hour < 12 else ("Good afternoon! 🌤" if hour < 18 else "Good evening! 🌙")
        tk.Label(self.content, text=greeting, bg=BG, fg=TEXT,
                 font=("Arial", 17, "bold"), anchor="w").pack(fill="x")
        tk.Label(self.content, text=date.today().strftime("%A, %B %d"),
                 bg=BG, fg=MUTED, font=("Arial", 11), anchor="w").pack(fill="x", pady=(0, 18))

        pet = self.app.active_pet
        if not pet:
            tk.Label(self.content, text="🐾  No pet selected.\nGo to 'My Pets' to add or select one.",
                     bg=BG, fg=MUTED, font=("Arial", 13), justify="center").pack(expand=True)
            return

        # Active pet card
        outer = tk.Frame(self.content, bg=BORDER)
        outer.pack(fill="x", pady=(0, 18))
        inner = tk.Frame(outer, bg=SURFACE, padx=14, pady=10)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(inner, text=f"Active Pet: {pet['name']}", bg=SURFACE, fg=ACCENT,
                 font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
        detail = pet["species"].capitalize()
        if pet["breed"]: detail += f" · {pet['breed']}"
        if pet["birthday"]: detail += f" · Born {pet['birthday']}"
        tk.Label(inner, text=detail, bg=SURFACE, fg=MUTED,
                 font=("Arial", 10), anchor="w").pack(fill="x")

        # Stats
        tk.Label(self.content, text="Today's Summary", bg=BG, fg=TEXT,
                 font=("Arial", 13, "bold"), anchor="w").pack(fill="x", pady=(0, 8))

        stats = self._stats(pet["id"])
        row = tk.Frame(self.content, bg=BG)
        row.pack(fill="x")

        cards = [
            (f"{stats['meals_done']} / {stats['meals_total']}", "🍽  Meals Today",
             GREEN if stats["meals_done"] >= stats["meals_total"] > 0 else ACCENT, "feeding"),
            (str(stats["meds_total"]), "💊  Medications", ACCENT, "medications"),
            (f"{stats['overdue']} overdue" if stats["overdue"] else "All OK",
             "✂  Grooming", RED if stats["overdue"] else GREEN, "grooming"),
            (str(stats["weight_entries"]), "⚖  Weight Entries", ACCENT, "health"),
        ]
        for value, label, color, page_key in cards:
            self._stat_card(row, value, label, color, page_key)

        # Divider
        tk.Frame(self.content, bg=BORDER, height=1).pack(fill="x", pady=(22, 14))

        # Export row
        export_row = tk.Frame(self.content, bg=BG)
        export_row.pack(fill="x")
        tk.Label(export_row, text="📄  Export Pet Data", bg=BG, fg=TEXT,
                 font=("Arial", 12, "bold")).pack(side="left")
        tk.Label(export_row, text="  —  Save all records as a CSV file.",
                 bg=BG, fg=MUTED, font=("Arial", 10)).pack(side="left")
        self.btn(export_row, "⬇ Download CSV", lambda: self._export_csv(pet)
                 ).pack(side="right")

    def _export_csv(self, pet):
        default_name = f"{pet['name'].lower().replace(' ', '_')}_data.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_name,
            title="Save Pet Data As"
        )
        if not filepath:
            return

        conn = get_connection()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Pet info
            writer.writerow(["PET INFO"])
            writer.writerow(["Name", "Species", "Breed", "Birthday", "Notes"])
            writer.writerow([pet["name"], pet["species"],
                             pet["breed"] or "", pet["birthday"] or "", pet["notes"] or ""])
            writer.writerow([])

            # Feeding schedules
            writer.writerow(["FEEDING SCHEDULES"])
            writer.writerow(["Meal Name", "Time", "Food Type", "Portion"])
            for r in conn.execute(
                    "SELECT meal_name, time, food_type, portion FROM feeding_schedules WHERE pet_id=?",
                    (pet["id"],)).fetchall():
                writer.writerow([r["meal_name"], r["time"], r["food_type"] or "", r["portion"] or ""])
            writer.writerow([])

            # Medications
            writer.writerow(["MEDICATIONS"])
            writer.writerow(["Name", "Dosage", "Frequency", "Notes"])
            for r in conn.execute(
                    "SELECT name, dosage, frequency, notes FROM medications WHERE pet_id=?",
                    (pet["id"],)).fetchall():
                writer.writerow([r["name"], r["dosage"] or "", r["frequency"], r["notes"] or ""])
            writer.writerow([])

            # Weight logs
            writer.writerow(["WEIGHT HISTORY"])
            writer.writerow(["Date", "Weight", "Unit", "Notes"])
            for r in conn.execute(
                    "SELECT date, weight, unit, notes FROM weight_logs WHERE pet_id=? ORDER BY date",
                    (pet["id"],)).fetchall():
                writer.writerow([r["date"], r["weight"], r["unit"], r["notes"] or ""])
            writer.writerow([])

            # Grooming tasks
            writer.writerow(["GROOMING TASKS"])
            writer.writerow(["Task", "Every (days)", "Last Done", "Next Due", "Notes"])
            for r in conn.execute(
                    "SELECT task_name, interval_days, last_done, next_due, notes FROM grooming_tasks WHERE pet_id=?",
                    (pet["id"],)).fetchall():
                writer.writerow([r["task_name"], r["interval_days"],
                                 r["last_done"] or "", r["next_due"] or "", r["notes"] or ""])

        conn.close()
        self.app.info("Export Successful", f"Data for {pet['name']} saved to:\n{filepath}")

    def _stat_card(self, parent, value, label, color, page_key):
        outer = tk.Frame(parent, bg=BORDER, cursor="hand2")
        outer.pack(side="left", fill="x", expand=True, padx=(0, 8))
        inner = tk.Frame(outer, bg=SURFACE, padx=14, pady=12, cursor="hand2")
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        vl = tk.Label(inner, text=value, bg=SURFACE, fg=color,
                      font=("Arial", 17, "bold"))
        vl.pack(anchor="w")
        nl = tk.Label(inner, text=label, bg=SURFACE, fg=MUTED, font=("Arial", 10))
        nl.pack(anchor="w")
        for w in (outer, inner, vl, nl):
            w.bind("<Button-1>", lambda e, k=page_key: self.app._show_page(k))

    def _stats(self, pet_id):
        conn = get_connection()
        today = str(date.today())
        meals_total = conn.execute(
            "SELECT COUNT(*) FROM feeding_schedules WHERE pet_id=?", (pet_id,)).fetchone()[0]
        meals_done = conn.execute(
            "SELECT COUNT(DISTINCT schedule_id) FROM feeding_logs WHERE pet_id=? AND date(logged_at)=?",
            (pet_id, today)).fetchone()[0]
        meds_total = conn.execute(
            "SELECT COUNT(*) FROM medications WHERE pet_id=?", (pet_id,)).fetchone()[0]
        overdue = conn.execute(
            "SELECT COUNT(*) FROM grooming_tasks WHERE pet_id=? AND next_due<=?",
            (pet_id, today)).fetchone()[0]
        weight_entries = conn.execute(
            "SELECT COUNT(*) FROM weight_logs WHERE pet_id=?", (pet_id,)).fetchone()[0]
        conn.close()
        return {"meals_total": meals_total, "meals_done": meals_done,
                "meds_total": meds_total, "overdue": overdue, "weight_entries": weight_entries}


# ─────────────────────────────────────────────────────────────
#  GROOMING PAGE
# ─────────────────────────────────────────────────────────────

class GroomingPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app, "✂  Grooming",
                         "Track grooming tasks and when they are next due.")
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=28, pady=(14, 0))
        self.btn(top, "＋ Add Task", self._add_dialog).pack(side="left")
        self.list_frame = tk.Frame(self, bg=BG)
        self.list_frame.pack(fill="both", expand=True, padx=28, pady=14)

    def reload(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        pet = self.app.active_pet
        if not pet:
            self.empty(self.list_frame, "Select a pet first."); return
        tasks = self._load(pet["id"])
        if not tasks:
            self.empty(self.list_frame, "No grooming tasks yet. Click '＋ Add Task'."); return
        for t in tasks:
            self._row(t)

    def _load(self, pet_id):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM grooming_tasks WHERE pet_id=? ORDER BY next_due",
            (pet_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _row(self, task):
        today = str(date.today())
        overdue = task["next_due"] and task["next_due"] <= today
        bar = RED if overdue else GREEN

        _, inner = self.row_card(self.list_frame)
        tk.Frame(inner, bg=bar, width=4).pack(side="left", fill="y", padx=(0, 10))

        info = tk.Frame(inner, bg=SURFACE)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=task["task_name"], bg=SURFACE, fg=TEXT,
                 font=("Arial", 12, "bold"), anchor="w").pack(fill="x")
        detail = f"Every {task['interval_days']} days"
        if task["next_due"]:
            detail += f"  ·  {'⚠ Overdue' if overdue else 'Next due: ' + task['next_due']}"
        if task["notes"]:
            detail += f"  ·  {task['notes']}"
        tk.Label(info, text=detail, bg=SURFACE, fg=RED if overdue else MUTED,
                 font=("Arial", 10), anchor="w").pack(fill="x")

        btns = tk.Frame(inner, bg=SURFACE)
        btns.pack(side="right")
        self.btn(btns, "Mark Done", lambda t=task: self._mark_done(t), color=GREEN
                 ).pack(side="left", padx=(0, 6))
        self.danger_btn(btns, "Delete", lambda t=task: self._delete(t)).pack(side="left")

    def _mark_done(self, task):
        today = str(date.today())
        next_due = str(date.today() + timedelta(days=task["interval_days"]))
        conn = get_connection()
        conn.execute("UPDATE grooming_tasks SET last_done=?, next_due=? WHERE id=?",
                     (today, next_due, task["id"]))
        conn.commit(); conn.close()
        self.reload()

    def _delete(self, task):
        if self.app.ask("Delete Task", f"Delete '{task['task_name']}'?"):
            conn = get_connection()
            conn.execute("DELETE FROM grooming_tasks WHERE id=?", (task["id"],))
            conn.commit(); conn.close()
            self.reload()

    def _add_dialog(self):
        pet = self.app.active_pet
        if not pet:
            self.app.info("No Pet", "Select a pet first."); return
        d = self.dialog("Add Grooming Task")
        tk.Label(d, text="Add Grooming Task", bg=BG, fg=TEXT,
                 font=("Arial", 13, "bold")).grid(
            row=0, column=0, columnspan=2, padx=22, pady=(18, 10), sticky="w")

        ph = ["e.g. Bath", "e.g. 7", "e.g. Use gentle shampoo"]
        labels = ["Task Name *", "Every (days) *", "Notes"]
        entries = [self.form_row(d, i+1, labels[i], ph[i]) for i in range(3)]
        err = tk.Label(d, text="", bg=BG, fg=RED, font=("Arial", 10))
        err.grid(row=4, column=0, columnspan=2)

        def submit():
            name = self.get_val(entries[0], ph[0])
            interval = self.get_val(entries[1], ph[1])
            if not name: err.config(text="Task name is required."); return
            if not interval: err.config(text="Interval is required."); return
            try:
                days = int(interval)
                if days < 1: raise ValueError
            except ValueError:
                err.config(text="Interval must be a whole number."); return
            today = str(date.today())
            conn = get_connection()
            conn.execute(
                "INSERT INTO grooming_tasks (pet_id, task_name, interval_days, last_done, next_due, notes) VALUES (?,?,?,NULL,?,?)",
                (pet["id"], name, days, today, self.get_val(entries[2], ph[2]) or None))
            conn.commit(); conn.close()
            d.destroy(); self.reload()

        brow = tk.Frame(d, bg=BG)
        brow.grid(row=5, column=0, columnspan=2, padx=22, pady=(6, 18), sticky="e")
        tk.Button(brow, text="Cancel", command=d.destroy,
                  bg=SURFACE, fg=MUTED, relief="flat", padx=10, pady=5,
                  cursor="hand2").pack(side="left", padx=(0, 8))
        self.btn(brow, "Add Task", submit).pack(side="left")


# ─────────────────────────────────────────────────────────────
#  CALENDAR PAGE
# ─────────────────────────────────────────────────────────────

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

class CalendarPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app, "📅  Calendar",
                         "See grooming, feeding, and medication events by day.")
        self.viewed_year  = date.today().year
        self.viewed_month = date.today().month

        nav = tk.Frame(self, bg=BG)
        nav.pack(fill="x", padx=28, pady=(14, 0))
        self.btn(nav, "◀ Prev", self._prev).pack(side="left")
        self.month_lbl = tk.Label(nav, text="", bg=BG, fg=TEXT, font=("Arial", 13, "bold"))
        self.month_lbl.pack(side="left", padx=14)
        self.btn(nav, "Next ▶", self._next).pack(side="left")

        legend = tk.Frame(self, bg=BG)
        legend.pack(fill="x", padx=28, pady=(8, 0))
        for color, lbl in [(ACCENT, "Today"), (GREEN, "Events"), (RED, "Overdue")]:
            tk.Frame(legend, bg=color, width=12, height=12).pack(side="left", padx=(0, 4))
            tk.Label(legend, text=lbl, bg=BG, fg=MUTED, font=("Arial", 9)).pack(side="left", padx=(0, 14))

        self.grid_frame = tk.Frame(self, bg=BG)
        self.grid_frame.pack(fill="both", expand=True, padx=28, pady=10)
        self.detail_lbl = tk.Label(self, text="Click a highlighted day to see details.",
                                    bg=BG, fg=MUTED, font=("Arial", 10), wraplength=650, anchor="w")
        self.detail_lbl.pack(padx=28, pady=(0, 14), fill="x")

    def reload(self):
        self._draw()

    def _prev(self):
        if self.viewed_month == 1:
            self.viewed_month = 12; self.viewed_year -= 1
        else:
            self.viewed_month -= 1
        self._draw()

    def _next(self):
        if self.viewed_month == 12:
            self.viewed_month = 1; self.viewed_year += 1
        else:
            self.viewed_month += 1
        self._draw()

    def _draw(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.detail_lbl.config(text="Click a highlighted day to see details.")
        self.month_lbl.config(text=date(self.viewed_year, self.viewed_month, 1).strftime("%B %Y"))

        events, overdue_dates = self._get_events()
        today = date.today()

        for col, day_name in enumerate(DAYS):
            tk.Label(self.grid_frame, text=day_name, bg=BG, fg=MUTED,
                     font=("Arial", 10, "bold"), width=6, anchor="center"
                     ).grid(row=0, column=col, padx=2, pady=(0, 4))

        weeks = cal_module.monthcalendar(self.viewed_year, self.viewed_month)
        for r, week in enumerate(weeks, start=1):
            for c, day_num in enumerate(week):
                if day_num == 0:
                    tk.Label(self.grid_frame, text="", bg=BG, width=6).grid(row=r, column=c, padx=2, pady=2)
                    continue
                this_date = date(self.viewed_year, self.viewed_month, day_num)
                ds = str(this_date)
                if this_date == today:
                    cbg, cfg = ACCENT, BG
                elif ds in overdue_dates:
                    cbg, cfg = RED, BG
                elif ds in events:
                    cbg, cfg = GREEN, BG
                else:
                    cbg, cfg = SURFACE, TEXT

                cell = tk.Label(self.grid_frame, text=str(day_num),
                                bg=cbg, fg=cfg, font=("Arial", 11),
                                width=6, pady=6,
                                cursor="hand2" if ds in events else "arrow")
                cell.grid(row=r, column=c, padx=2, pady=2)
                if ds in events:
                    cell.bind("<Button-1>", lambda e, d=this_date, ev=events[ds]: self._detail(d, ev))

    def _get_events(self):
        pet = self.app.active_pet
        if not pet:
            return {}, set()
        conn = get_connection()
        events = {}
        overdue_dates = set()
        today = str(date.today())

        # Grooming — show on next_due date
        for row in conn.execute(
                "SELECT task_name, next_due FROM grooming_tasks WHERE pet_id=? AND next_due IS NOT NULL",
                (pet["id"],)).fetchall():
            d = row["next_due"]
            events.setdefault(d, []).append(f"✂ {row['task_name']}")
            if d <= today:
                overdue_dates.add(d)

        # Feeding + Medications — show every day of the month
        feeding = conn.execute(
            "SELECT meal_name, time FROM feeding_schedules WHERE pet_id=?", (pet["id"],)).fetchall()
        meds = conn.execute(
            "SELECT name, frequency FROM medications WHERE pet_id=?", (pet["id"],)).fetchall()

        if feeding or meds:
            _, days_in_month = cal_module.monthrange(self.viewed_year, self.viewed_month)
            for day in range(1, days_in_month + 1):
                ds = str(date(self.viewed_year, self.viewed_month, day))
                for r in feeding:
                    events.setdefault(ds, []).append(f"🍽 {r['meal_name']} ({r['time']})")
                for r in meds:
                    events.setdefault(ds, []).append(f"💊 {r['name']} ({r['frequency']})")

        conn.close()
        return events, overdue_dates

    def _detail(self, clicked_date, evs):
        self.detail_lbl.config(
            text=f"📅 {clicked_date.strftime('%A, %B %d')}:   {'   •   '.join(evs)}",
            fg=TEXT)


# ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    KendraApp(root)
    root.mainloop()