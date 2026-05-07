"""
database.py - Sets up and connects to the SQLite database.
All pet data is stored in kendra.db in the same folder.
"""
import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kendra.db")


def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def setup_database():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL,
            species  TEXT NOT NULL,
            breed    TEXT,
            birthday TEXT,
            notes    TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS feeding_schedules (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id    INTEGER NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
            meal_name TEXT NOT NULL,
            time      TEXT NOT NULL,
            food_type TEXT,
            portion   TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id    INTEGER NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
            name      TEXT NOT NULL,
            dosage    TEXT,
            frequency TEXT NOT NULL,
            notes     TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS weight_logs (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
            weight REAL NOT NULL,
            unit   TEXT NOT NULL DEFAULT 'kg',
            date   TEXT NOT NULL DEFAULT (date('now')),
            notes  TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS feeding_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id      INTEGER NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
            schedule_id INTEGER REFERENCES feeding_schedules(id) ON DELETE SET NULL,
            logged_at   TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS grooming_tasks (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id        INTEGER NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
            task_name     TEXT NOT NULL,
            interval_days INTEGER NOT NULL DEFAULT 7,
            last_done     TEXT,
            next_due      TEXT,
            notes         TEXT
        )
    """)

    conn.commit()
    conn.close()