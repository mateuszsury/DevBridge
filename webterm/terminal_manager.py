from __future__ import annotations

import asyncio
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .db import DB
from .security import get_effective_settings

IS_WINDOWS = os.name == "nt"
if IS_WINDOWS:
    from .pty_windows import WindowsPty, spawn_windows
else:
    from .pty_unix import UnixPty, spawn_unix


@dataclass
class Session:
    id: str
    cwd: str
    shell: str
    cols: int
    rows: int
    created_at: float
    last_activity_at: float
    status: str  # running/exited/killed/stale
    scrollback: str
    pty: Any | None
    output_task: asyncio.Task | None


class TerminalManager:
    def __init__(self, db: DB) -> None:
        self.db = db
        self.sessions: dict[str, Session] = {}
        self.subscribers: dict[str, set[asyncio.Queue[str]]] = {}
        self._lock = asyncio.Lock()

    def _truncate_scrollback(self, s: str, limit: int) -> str:
        if len(s) <= limit:
            return s
        return s[-limit:]

    def _default_shell(self, cfg: dict) -> str:
        if IS_WINDOWS:
            return str(cfg.get("default_windows_shell") or "powershell.exe")
        return str(cfg.get("default_unix_shell") or "/bin/bash")

    async def mark_db_sessions_stale_on_start(self) -> None:
        # Po restarcie nie wznawiamy procesów, więc to co było "running"
        # oznaczamy jako "stale" (historyczne).
        rows = self.db.list_sessions()
        for r in rows:
            if r["status"] == "running":
                self.db.upsert_session(
                    session_id=r["id"],
                    cwd=r["cwd"],
                    shell=r["shell"],
                    pid=r["pid"],
                    status="stale",
                    created_at=float(r["created_at"]),
                    last_activity_at=float(r["last_activity_at"]),
                    cols=int(r["cols"]),
                    rows=int(r["rows"]),
                    scrollback=r["scrollback"] or "",
                )

    async def load_sessions_from_db(self) -> None:
        rows = self.db.list_sessions()
        async with self._lock:
            for r in rows:
                sid = r["id"]
                if sid in self.sessions:
                    continue
                self.sessions[sid] = Session(
                    id=sid,
                    cwd=r["cwd"],
                    shell=r["shell"],
                    cols=int(r["cols"]),
                    rows=int(r["rows"]),
                    created_at=float(r["created_at"]),
                    last_activity_at=float(r["last_activity_at"]),
                    status=r["status"],
                    scrollback=r["scrollback"] or "",
                    pty=None,
                    output_task=None,
                )

    async def list_sessions(self) -> list[dict]:
        async with self._lock:
            items = []
            for s in sorted(self.sessions.values(), key=lambda x: x.created_at, reverse=True):
                # Only return active (running) sessions
                if s.status not in ["running"]:
                    continue

                # Get PID properly
                pid = None
                if s.pty:
                    try:
                        pid = s.pty.pid
                    except Exception:
                        pass

                items.append(
                    {
                        "id": s.id,
                        "cwd": s.cwd,
                        "shell": s.shell,
                        "pid": pid,
                        "status": s.status,
                        "created_at": s.created_at,
                        "last_activity_at": s.last_activity_at,
                    }
                )
            return items

    async def create_session(self, cwd: str | None, shell: str | None, cols: int, rows: int) -> dict:
        cfg = get_effective_settings(self.db)

        max_sessions = int(cfg.get("max_sessions", 50))
        idle_ttl = int(cfg.get("idle_ttl_seconds", 0))
        scrollback_limit = int(cfg.get("scrollback_limit_chars", 200_000))

        if cwd is None or not os.path.isdir(cwd):
            cwd = os.path.expanduser("~")

        shell = (shell or "").strip() or self._default_shell(cfg)

        # WSL helper: pozwól na wpisanie np. "wsl" lub "wsl.exe"
        # oraz zostaw dowolne parametry jeśli user poda pełną komendę.
        if IS_WINDOWS and shell.lower() in {"wsl", "wsl.exe"}:
            shell = "wsl.exe"

        async with self._lock:
            running = sum(1 for s in self.sessions.values() if s.status == "running")
            if running >= max_sessions:
                raise RuntimeError("Max running sessions reached")

            sid = uuid.uuid4().hex
            now = time.time()

            if IS_WINDOWS:
                pty_obj = spawn_windows(shell=shell, cwd=cwd, cols=cols, rows=rows)
                pid = pty_obj.pid
            else:
                pty_obj = spawn_unix(shell=shell, cwd=cwd, cols=cols, rows=rows)
                pid = pty_obj.pid

            sess = Session(
                id=sid,
                cwd=cwd,
                shell=shell,
                cols=cols,
                rows=rows,
                created_at=now,
                last_activity_at=now,
                status="running",
                scrollback="",
                pty=pty_obj,
                output_task=None,
            )

            self.sessions[sid] = sess
            self.subscribers.setdefault(sid, set())

            self.db.upsert_session(
                session_id=sid,
                cwd=cwd,
                shell=shell,
                pid=pid,
                status=sess.status,
                created_at=now,
                last_activity_at=now,
                cols=cols,
                rows=rows,
                scrollback=sess.scrollback,
            )

            sess.output_task = asyncio.create_task(
                self._pump_output(sess, scrollback_limit, idle_ttl),
            )
            return {"id": sid}

    async def kill_session(self, sid: str) -> None:
        async with self._lock:
            sess = self.sessions.get(sid)
            if not sess:
                return

            # Cancel output task first
            if sess.output_task:
                sess.output_task.cancel()
                try:
                    await sess.output_task
                except asyncio.CancelledError:
                    pass
                except Exception:
                    pass

            # Terminate PTY
            if sess.pty:
                try:
                    sess.pty.terminate()
                except Exception as e:
                    print(f"Error terminating PTY {sid}: {e}")

            sess.status = "killed"
            sess.last_activity_at = time.time()
            sess.pty = None

            # Update database
            self.db.upsert_session(
                session_id=sess.id,
                cwd=sess.cwd,
                shell=sess.shell,
                pid=None,
                status=sess.status,
                created_at=sess.created_at,
                last_activity_at=sess.last_activity_at,
                cols=sess.cols,
                rows=sess.rows,
                scrollback=sess.scrollback,
            )

            # Remove from active sessions after a delay
            # This allows cleanup to complete
            await asyncio.sleep(0.1)
            if sid in self.sessions:
                del self.sessions[sid]

    async def write(self, sid: str, data: bytes) -> None:
        async with self._lock:
            sess = self.sessions.get(sid)
            if not sess or sess.status != "running" or not sess.pty:
                return
            try:
                sess.pty.write(data)
                sess.last_activity_at = time.time()
            except Exception as e:
                print(f"Error writing to PTY {sid}: {e}")
                # Mark session as exited if write fails
                sess.status = "exited"

    async def resize(self, sid: str, cols: int, rows: int) -> None:
        async with self._lock:
            sess = self.sessions.get(sid)
            if not sess or sess.status != "running" or not sess.pty:
                return
            try:
                sess.cols = cols
                sess.rows = rows
                sess.pty.resize(cols=cols, rows=rows)
                sess.last_activity_at = time.time()
            except Exception as e:
                print(f"Error resizing PTY {sid}: {e}")

    async def get_scrollback(self, sid: str) -> str:
        async with self._lock:
            sess = self.sessions.get(sid)
            return sess.scrollback if sess else ""

    async def subscribe(self, sid: str) -> asyncio.Queue[str]:
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=300)
        async with self._lock:
            self.subscribers.setdefault(sid, set()).add(q)
        return q

    async def unsubscribe(self, sid: str, q: asyncio.Queue[str]) -> None:
        async with self._lock:
            subs = self.subscribers.get(sid)
            if subs and q in subs:
                subs.remove(q)

    async def _broadcast(self, sid: str, chunk: str) -> None:
        async with self._lock:
            subs = list(self.subscribers.get(sid, set()))
        for q in subs:
            try:
                q.put_nowait(chunk)
            except asyncio.QueueFull:
                pass

    async def _pump_output(self, sess: Session, scrollback_limit: int, idle_ttl: int) -> None:
        last_flush = 0.0
        flush_every = 0.5
        loop = asyncio.get_event_loop()

        try:
            while True:
                if not sess.pty or sess.status != "running":
                    return

                # Run blocking I/O in executor to prevent freezing
                try:
                    out = await loop.run_in_executor(None, sess.pty.read, 4096)
                except Exception as e:
                    # PTY closed or error
                    print(f"Error reading from PTY {sess.id}: {e}")
                    await self.kill_session(sess.id)
                    return

                if out:
                    text = out.decode("utf-8", errors="ignore")
                    sess.scrollback = self._truncate_scrollback(
                        sess.scrollback + text,
                        scrollback_limit,
                    )
                    sess.last_activity_at = time.time()
                    await self._broadcast(sess.id, text)

                now = time.time()
                if now - last_flush >= flush_every:
                    last_flush = now
                    # Get PID properly
                    pid = None
                    if sess.pty:
                        try:
                            pid = sess.pty.pid
                        except Exception:
                            pass

                    self.db.upsert_session(
                        session_id=sess.id,
                        cwd=sess.cwd,
                        shell=sess.shell,
                        pid=pid,
                        status=sess.status,
                        created_at=sess.created_at,
                        last_activity_at=sess.last_activity_at,
                        cols=sess.cols,
                        rows=sess.rows,
                        scrollback=sess.scrollback,
                    )

                if idle_ttl and (time.time() - sess.last_activity_at) > idle_ttl:
                    await self.kill_session(sess.id)
                    return

                await asyncio.sleep(0.02)
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"Unexpected error in _pump_output for {sess.id}: {e}")
            return
        except Exception:
            sess.status = "exited"
            sess.last_activity_at = time.time()
            self.db.upsert_session(
                session_id=sess.id,
                cwd=sess.cwd,
                shell=sess.shell,
                pid=getattr(sess.pty, "pid", None) if sess.pty else None,
                status=sess.status,
                created_at=sess.created_at,
                last_activity_at=sess.last_activity_at,
                cols=sess.cols,
                rows=sess.rows,
                scrollback=sess.scrollback,
            )