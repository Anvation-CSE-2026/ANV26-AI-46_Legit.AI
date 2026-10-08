"""Postgres store. One row per analysed case."""
import json
import os
from typing import Dict, List, Optional

import psycopg
from psycopg.rows import dict_row


def _conn() -> psycopg.Connection:
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def init_db() -> None:
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY, mode TEXT, input_type TEXT,
            decision TEXT, created_at TEXT, payload TEXT NOT NULL)""")


def save_case(case: Dict) -> None:
    with _conn() as c:
        c.execute(
            """INSERT INTO cases (case_id, mode, input_type, decision, created_at, payload)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (case_id) DO UPDATE SET
                 mode = EXCLUDED.mode,
                 input_type = EXCLUDED.input_type,
                 decision = EXCLUDED.decision,
                 created_at = EXCLUDED.created_at,
                 payload = EXCLUDED.payload""",
            (case["case_id"], case["mode"], case["input"]["type"],
             case["overall"]["decision"], case["created_at"], json.dumps(case)),
        )


def get_case(case_id: str) -> Optional[Dict]:
    with _conn() as c:
        row = c.execute("SELECT payload FROM cases WHERE case_id = %s", (case_id,)).fetchone()
    return json.loads(row["payload"]) if row else None


def list_cases(limit: int = 20) -> List[Dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT case_id, mode, input_type, decision, created_at FROM cases "
            "ORDER BY created_at DESC LIMIT %s", (limit,)
        ).fetchall()
    return list(rows)