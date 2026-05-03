"""
main.py — Kendra Pet Care Manager
Run with: python main.py
"""
import tkinter as tk
from app import KendraApp

if __name__ == "__main__":
    root = tk.Tk()
    app = KendraApp(root)
    root.mainloop()