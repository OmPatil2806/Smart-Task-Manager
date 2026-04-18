"""
Database initialization and helper utilities.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            title       TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            category    TEXT    DEFAULT 'other',
            due_date    TEXT,
            status      TEXT    DEFAULT 'pending'  CHECK(status IN ('pending','completed')),
            priority    TEXT    DEFAULT 'MEDIUM'   CHECK(priority IN ('HIGH','MEDIUM','LOW')),
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TRIGGER IF NOT EXISTS update_task_timestamp
        AFTER UPDATE ON tasks
        BEGIN
            UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    """)
    conn.commit()
    conn.close()
    print(" Database initialized.")
