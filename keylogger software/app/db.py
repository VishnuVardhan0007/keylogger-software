"""SQLite persistence for encrypted keystroke logs and crypto metadata."""

from __future__ import annotations

import datetime as dt
import os
import sqlite3
from dataclasses import dataclass
from typing import Iterable, Optional

from .constants import DEFAULT_KDF_ITERS
from .crypto import CryptoParams

META_ID = 1


def _connect(db_path: str) -> sqlite3.Connection:
    """Open a connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Create meta and logs tables if they do not exist."""
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            salt BLOB NOT NULL,
            kdf_iters INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            event_type TEXT NOT NULL,
            keysym TEXT NOT NULL,
            keycode INTEGER NOT NULL,
            ciphertext BLOB NOT NULL
        )
        """
    )
    conn.commit()


def get_or_create_crypto_params(db_path: str) -> CryptoParams:
    """Return existing crypto params for the DB, or create and store new ones."""
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("SELECT salt, kdf_iters FROM meta WHERE id = ?", (META_ID,))
        row = cur.fetchone()
        if row is not None:
            return CryptoParams(salt=row["salt"], kdf_iters=row["kdf_iters"])

        salt = os.urandom(16)
        kdf_iters = DEFAULT_KDF_ITERS
        now = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
        cur.execute(
            "INSERT INTO meta (id, salt, kdf_iters, created_at) VALUES (?, ?, ?, ?)",
            (META_ID, salt, kdf_iters, now),
        )
        conn.commit()
        return CryptoParams(salt=salt, kdf_iters=kdf_iters)
    finally:
        conn.close()


def get_existing_crypto_params(db_path: str) -> Optional[CryptoParams]:
    """Return crypto params if the DB exists and has meta; otherwise None."""
    if not os.path.exists(db_path):
        return None
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("SELECT salt, kdf_iters FROM meta WHERE id = ?", (META_ID,))
        row = cur.fetchone()
        if row is None:
            return None
        return CryptoParams(salt=row["salt"], kdf_iters=row["kdf_iters"])
    finally:
        conn.close()


@dataclass
class LogRow:
    """One row from the logs table (decrypted payload is separate)."""

    id: int
    ts: str
    event_type: str
    keysym: str
    keycode: int
    ciphertext: bytes


def insert_log(
    db_path: str,
    *,
    ts: str,
    event_type: str,
    keysym: str,
    keycode: int,
    ciphertext: bytes,
) -> None:
    """Append one encrypted log entry to the logs table."""
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO logs (ts, event_type, keysym, keycode, ciphertext)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ts, event_type, keysym, keycode, ciphertext),
        )
        conn.commit()
    finally:
        conn.close()


def fetch_logs(db_path: str, limit: Optional[int] = None) -> Iterable[LogRow]:
    """Yield log rows from the DB, newest first; optional limit."""
    if not os.path.exists(db_path):
        return []
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        sql = "SELECT id, ts, event_type, keysym, keycode, ciphertext FROM logs ORDER BY ts DESC"
        params: tuple[object, ...] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)
        cur.execute(sql, params)
        rows = [
            LogRow(
                id=row["id"],
                ts=row["ts"],
                event_type=row["event_type"],
                keysym=row["keysym"],
                keycode=row["keycode"],
                ciphertext=row["ciphertext"],
            )
            for row in cur.fetchall()
        ]
        return rows
    finally:
        conn.close()

