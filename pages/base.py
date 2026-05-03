"""
pages/base.py — Shared base class for all pages.

Every page inherits from BasePage, which gives it:
  - A consistent background color
  - A page title and subtitle at the top
  - A reload() method to refresh data
  - Helper functions for common widgets (buttons, labels, etc.)
"""
import tkinter as tk

# Shared colors (same as app.py)
BG      = "#1e1e2e"
SURFACE = "#313244"
ACCENT  = "#89b4fa"
GREEN   = "#a6e3a1"
RED     = "#f38ba8"
TEXT    = "#cdd6f4"
MUTED   = "#6c7086"
BORDER  = "#45475a"


class BasePage(tk.Frame):
    """All pages inherit from this. Provides a consistent header and helpers."""

    def __init__(self, parent, app, title, subtitle=""):
        super().__init__(parent, bg=BG)
        self.app = app
        self._build_header(title, subtitle)

    def _build_header(self, title, subtitle):
        """Add a title and optional subtitle at the top of the page."""
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=30, pady=(24, 0))

        tk.Label(
            header, text=title,
            bg=BG, fg=TEXT,
            font=("Arial", 22, "bold"),
            anchor="w"
        ).pack(side="left")

        if subtitle:
            tk.Label(
                self, text=subtitle,
                bg=BG, fg=MUTED,
                font=("Arial", 11),
                anchor="w"
            ).pack(fill="x", padx=30, pady=(2, 0))

        # Horizontal divider
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=30, pady=(12, 0))

    def reload(self):
        """Called every time this page is navigated to. Override in subclass."""
        pass

    # ── Widget helpers ────────────────────────────────────────────────────────

    def make_button(self, parent, text, command, color=None, fg=None):
        """Create a styled button."""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color or ACCENT,
            fg=fg or "#1e1e2e",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=12, pady=6,
            cursor="hand2",
        )
        return btn

    def make_danger_button(self, parent, text, command):
        """A red button for destructive actions like Delete."""
        return self.make_button(parent, text, command, color=RED, fg="#1e1e2e")

    def make_label(self, parent, text, size=11, bold=False, color=None):
        """Create a simple text label."""
        weight = "bold" if bold else "normal"
        return tk.Label(
            parent,
            text=text,
            bg=BG,
            fg=color or TEXT,
            font=("Arial", size, weight),
        )

    def make_entry(self, parent, width=25):
        """Create a styled text input field."""
        entry = tk.Entry(
            parent,
            bg=SURFACE,
            fg=TEXT,
            insertbackground=ACCENT,
            font=("Arial", 11),
            relief="flat",
            bd=6,
            width=width,
        )
        return entry

    def make_card(self, parent):
        """Create a card-like container with a border."""
        outer = tk.Frame(parent, bg=BORDER)
        inner = tk.Frame(outer, bg=SURFACE, padx=14, pady=10)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        return outer, inner

    def show_empty(self, parent, message):
        """Show a centered message when there's no data to display."""
        tk.Label(
            parent,
            text=message,
            bg=BG, fg=MUTED,
            font=("Arial", 12),
        ).pack(expand=True)