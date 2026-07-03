"""
Minimal SQLite persistence so completed runs survive a server restart and
can be listed in the UI's history/report view.
"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager

import os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs.db")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                user_story TEXT,
                language TEXT,
                status TEXT,
                started_at TEXT,
                finished_at TEXT,
                result_json TEXT
            )
            """
        )
        conn.commit()


def create_run(user_story: str, language: str) -> str:
    run_id = str(uuid.uuid4())
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO runs (id, user_story, language, status, started_at) VALUES (?, ?, ?, ?, ?)",
            (run_id, user_story, language, "running", datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    return run_id


def complete_run(run_id: str, status: str, result: dict):
    with get_conn() as conn:
        conn.execute(
            "UPDATE runs SET status = ?, finished_at = ?, result_json = ? WHERE id = ?",
            (status, datetime.now(timezone.utc).isoformat(), json.dumps(result, default=str), run_id),
        )
        conn.commit()


def get_run(run_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        return dict(row) if row else None


def list_runs(limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, user_story, language, status, started_at, finished_at FROM runs "
            "ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
