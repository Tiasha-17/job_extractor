"""
A tiny SQLite database (one file, postings.db) that remembers every
posting you've ever extracted, so you build up real usage data over
your job search instead of starting fresh each time.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().with_name("postings.db"))


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS postings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            saved_at TEXT NOT NULL,
            source_note TEXT,
            raw_text TEXT NOT NULL,
            extracted_json TEXT NOT NULL,
            company TEXT,
            job_title TEXT,
            seniority_level TEXT,
            sponsorship_signal TEXT
        )
        """
    )
    conn.commit()
    return conn


def save_posting(conn: sqlite3.Connection, raw_text: str, extracted: dict, source_note: str = "") -> int:
    # Serialize check + insert across connections, preserving all legacy rows.
    raw_text = raw_text.strip()
    if not raw_text:
        raise ValueError("Cannot save an empty posting")
    try:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute("SELECT id, raw_text FROM postings ORDER BY id").fetchall()
        for row_id, saved_text in existing:
            if saved_text.strip() == raw_text:
                conn.commit()
                return row_id
        row_id = _insert_posting(conn, raw_text, extracted, source_note)
        conn.commit()
        return row_id
    except Exception:
        conn.rollback()
        raise


def _insert_posting(conn, raw_text, extracted, source_note):
    cur = conn.execute(
        """
        INSERT INTO postings
            (saved_at, source_note, raw_text, extracted_json,
             company, job_title, seniority_level, sponsorship_signal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            source_note,
            raw_text,
            json.dumps(extracted),
            extracted.get("company", ""),
            extracted.get("job_title", ""),
            extracted.get("seniority_level", ""),
            extracted.get("sponsorship_signal", ""),
        ),
    )
    return cur.lastrowid


def all_postings(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.execute(
        "SELECT id, saved_at, source_note, extracted_json FROM postings ORDER BY id DESC"
    )
    rows = []
    for row_id, saved_at, source_note, extracted_json in cur.fetchall():
        record = json.loads(extracted_json)
        record["id"] = row_id
        record["saved_at"] = saved_at
        record["source_note"] = source_note
        rows.append(record)
    return rows
