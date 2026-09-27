import sqlite3
from pathlib import Path
from typing import Optional


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATA_DIR / "workflowos.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp TEXT NOT NULL,

            application TEXT NOT NULL,

            event_type TEXT NOT NULL,

            window_title TEXT,

            metadata TEXT

        )
        """
    )

    connection.commit()

    connection.close()


# ============================================================
# INSERT EVENT
# ============================================================

def insert_event(
    timestamp: str,
    application: str,
    event_type: str,
    window_title: str,
    metadata: str
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO activity_events
        (
            timestamp,
            application,
            event_type,
            window_title,
            metadata
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            application,
            event_type,
            window_title,
            metadata
        )
    )

    connection.commit()

    event_id = cursor.lastrowid

    connection.close()

    return event_id


# ============================================================
# GET EVENTS
# ============================================================

def get_events(limit: int = 500):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            timestamp,
            application,
            event_type,
            window_title,
            metadata

        FROM activity_events

        ORDER BY id DESC

        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    connection.close()

    return [dict(row) for row in rows]


# ============================================================
# CLEAR EVENTS
# ============================================================

def clear_events():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM activity_events"
    )

    connection.commit()

    connection.close()