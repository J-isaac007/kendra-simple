"""
app.py — The main window and navigation for Kendra.

This file:
  1. Creates the main window
  2. Builds the sidebar navigation buttons
  3. Switches between pages when a button is clicked
"""
import tkinter as tk
from database import setup_database
from pages.dashboard import DashboardPage
from pages.pets import PetsPage
from pages.feeding import FeedingPage
from pages.medications import MedicationsPage
from pages.health import HealthPage

# ── Colors ────────────────────────────────────────────────────────────────────
BG       = "#1e1e2e"   # dark background
SIDEBAR  = "#181825"   # slightly darker sidebar
ACCENT   = "#89b4fa"   # blue accent
TEXT     = "#cdd6f4"   # light text
MUTED    = "#6c7086"   # dimmed text
SELECTED = "#313244"   # selected sidebar item


class KendraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kendra – Pet Care Manager")
        self.root.geometry("1000x650")
        self.root.configure(bg=BG)
        self.root.minsize(800, 500)

        # Set up the database before building the UI
        setup_database()

        # Build the layout
        self._build_layout()
        self._build_sidebar()
        self._build_pages()

        # Start on the dashboard
        self.show_page("dashboard")

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        """Split the window into a sidebar (left) and main area (right)."""
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg=SIDEBAR, width=180)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)  # keep fixed width

        # Main content area
        self.content = tk.Frame(self.root, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

    def _build_sidebar(self):
        """Add the app title and navigation buttons to the sidebar."""
        # App title
        tk.Label(
            self.sidebar, text="🐾 Kendra",
            bg=SIDEBAR, fg=ACCENT,
            font=("Arial", 16, "bold"),
            pady=20
        ).pack(fill="x")

        # Divider line
        tk.Frame(self.sidebar, bg=MUTED, height=1).pack(fill="x", padx=12)

        # Navigation buttons — (label, page_key)
        nav_items = [
            ("🏠  Dashboard",   "dashboard"),
            ("🐶  My Pets",     "pets"),
            ("🍽  Feeding",     "feeding"),
            ("💊  Medications", "medications"),
            ("⚖  Health",      "health"),
            ("✂  Grooming",    "grooming"),
            ("📅  Calendar",   "calendar"),
        ]

        self.nav_buttons = {}
        for label, key in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=label,
                bg=SIDEBAR, fg=TEXT,
                font=("Arial", 11),
                anchor="w",
                padx=16, pady=10,
                relief="flat",
                cursor="hand2",
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x")
            self.nav_buttons[key] = btn

    def _build_pages(self):
        """Create all pages and stack them in the content area."""
        # Each page gets the same parent frame and a reference to this app
        self.pages = {
            "dashboard":   DashboardPage(self.content, self),
            "pets":        PetsPage(self.content, self),
            "feeding":     FeedingPage(self.content, self),
            "medications": MedicationsPage(self.content, self),
            "health":      HealthPage(self.content, self),
        }
        # Place all pages in the same spot — we'll raise one on top when needed
        for page in self.pages.values():
            page.place(x=0, y=0, relwidth=1, relheight=1)

    # ── Navigation ────────────────────────────────────────────────────────────

    def show_page(self, key):
        """Switch to a page and highlight its sidebar button."""
        # Reset all buttons to normal style
        for k, btn in self.nav_buttons.items():
            btn.config(bg=SIDEBAR, fg=TEXT)

        # Highlight the active button
        if key in self.nav_buttons:
            self.nav_buttons[key].config(bg=SELECTED, fg=ACCENT)

        # Bring the selected page to the front
        page = self.pages[key]
        page.reload()   # refresh data each time we visit
        page.tkraise()

    # ── Shared helpers ────────────────────────────────────────────────────────

    def get_active_pet(self):
        """Return the currently selected pet (stored in PetsPage)."""
        return self.pages["pets"].active_pet

    def show_message(self, title, message):
        """Show a simple popup message."""
        from tkinter import messagebox
        messagebox.showinfo(title, message)

    def ask_yes_no(self, title, message):
        """Ask a yes/no question and return True or False."""
        from tkinter import messagebox
        return messagebox.askyesno(title, message)