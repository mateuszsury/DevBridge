from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

_SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  is_admin INTEGER NOT NULL DEFAULT 0,
  created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  cwd TEXT NOT NULL,
  shell TEXT NOT NULL,
  pid INTEGER,
  status TEXT NOT NULL, -- running/exited/killed/stale
  created_at REAL NOT NULL,
  last_activity_at REAL NOT NULL,
  cols INTEGER NOT NULL,
  rows INTEGER NOT NULL,
  scrollback TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at REAL NOT NULL
);
"""


class DB:
    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = threading.Lock()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._lock:
            conn = self._conn()
            try:
                conn.executescript(_SCHEMA)
                conn.commit()
            finally:
                conn.close()

    def exec(self, sql: str, params: tuple = ()) -> None:
        with self._lock:
            conn = self._conn()
            try:
                conn.execute(sql, params)
                conn.commit()
            finally:
                conn.close()

    def fetchone(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        with self._lock:
            conn = self._conn()
            try:
                cur = conn.execute(sql, params)
                return cur.fetchone()
            finally:
                conn.close()

    def fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            conn = self._conn()
            try:
                cur = conn.execute(sql, params)
                return cur.fetchall()
            finally:
                conn.close()

    # ----- settings -----
    def set_setting(self, key: str, value: Any) -> None:
        self.exec(
            """
            INSERT INTO app_settings(key,value,updated_at)
            VALUES(?,?,?)
            ON CONFLICT(key) DO UPDATE SET
              value=excluded.value,
              updated_at=excluded.updated_at
            """,
            (key, json.dumps(value), time.time()),
        )

    def get_setting(self, key: str) -> Any | None:
        row = self.fetchone("SELECT value FROM app_settings WHERE key = ?", (key,))
        if not row:
            return None
        return json.loads(row["value"])

    def get_all_settings(self) -> dict[str, Any]:
        rows = self.fetchall("SELECT key,value FROM app_settings")
        out: dict[str, Any] = {}
        for r in rows:
            out[r["key"]] = json.loads(r["value"])
        return out

    # ----- users -----
    def count_users(self) -> int:
        row = self.fetchone("SELECT COUNT(*) AS c FROM users")
        return int(row["c"]) if row else 0

    def create_user(
        self,
        username: str,
        password_hash: str,
        is_admin: bool = False,
    ) -> None:
        self.exec(
            """
            INSERT INTO users(username,password_hash,is_admin,created_at)
            VALUES(?,?,?,?)
            """,
            (username, password_hash, 1 if is_admin else 0, time.time()),
        )

    def list_users(self) -> list[sqlite3.Row]:
        return self.fetchall(
            "SELECT id,username,is_admin,created_at FROM users ORDER BY created_at DESC",
        )

    def get_user_by_username(self, username: str) -> sqlite3.Row | None:
        return self.fetchone("SELECT * FROM users WHERE username = ?", (username,))

    def get_user_by_id(self, user_id: int) -> sqlite3.Row | None:
        return self.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))

    def delete_user(self, user_id: int) -> None:
        self.exec("DELETE FROM users WHERE id = ?", (user_id,))

    def set_user_password(self, user_id: int, password_hash: str) -> None:
        self.exec(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user_id),
        )

    def set_user_admin(self, user_id: int, is_admin: bool) -> None:
        self.exec(
            "UPDATE users SET is_admin = ? WHERE id = ?",
            (1 if is_admin else 0, user_id),
        )

    # ----- sessions -----
    def upsert_session(
        self,
        session_id: str,
        cwd: str,
        shell: str,
        pid: int | None,
        status: str,
        created_at: float,
        last_activity_at: float,
        cols: int,
        rows: int,
        scrollback: str,
    ) -> None:
        self.exec(
            """
            INSERT INTO sessions(id,cwd,shell,pid,status,created_at,last_activity_at,cols,rows,scrollback)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
              cwd=excluded.cwd,
              shell=excluded.shell,
              pid=excluded.pid,
              status=excluded.status,
              last_activity_at=excluded.last_activity_at,
              cols=excluded.cols,
              rows=excluded.rows,
              scrollback=excluded.scrollback
            """,
            (
                session_id,
                cwd,
                shell,
                pid,
                status,
                created_at,
                last_activity_at,
                cols,
                rows,
                scrollback,
            ),
        )

    def list_sessions(self) -> list[sqlite3.Row]:
        return self.fetchall("SELECT * FROM sessions ORDER BY created_at DESC")

    def get_session(self, session_id: str) -> sqlite3.Row | None:
        return self.fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))