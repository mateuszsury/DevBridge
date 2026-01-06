from __future__ import annotations

import base64
import hashlib
import hmac
import time
from dataclasses import dataclass
import bcrypt
from fastapi import Cookie, HTTPException
from .settings import env
from .db import DB


def hash_password(pw: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw.encode('utf-8'), salt).decode('utf-8')


def verify_password(pw: str, pw_hash: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(pw.encode('utf-8'), pw_hash.encode('utf-8'))


def _sign(data: bytes) -> str:
    mac = hmac.new(env.SESSION_SECRET.encode("utf-8"), data, hashlib.sha256)
    return mac.hexdigest()


def make_session_token(username: str, ttl_seconds: int = 7 * 24 * 3600) -> str:
    exp = int(time.time()) + ttl_seconds
    payload = f"{username}:{exp}".encode("utf-8")
    b64 = base64.urlsafe_b64encode(payload).decode("ascii")
    sig = _sign(payload)
    return f"{b64}.{sig}"


def parse_session_token(token: str) -> str | None:
    try:
        b64, sig = token.split(".", 1)
        payload = base64.urlsafe_b64decode(b64.encode("ascii"))
        if not hmac.compare_digest(_sign(payload), sig):
            return None
        username, exp_s = payload.decode("utf-8").split(":", 1)
        if int(exp_s) < int(time.time()):
            return None
        return username
    except Exception:
        return None


@dataclass
class Principal:
    username: str | None
    is_admin: bool


def get_effective_settings(db: DB) -> dict:
    # Domyślne ustawienia aplikacji (nadpisywane przez SQLite)
    defaults = {
        "auth_required": False,
        "allow_anonymous_terminal": True,  # gdy auth_required=False
        "max_sessions": 50,
        "idle_ttl_seconds": 0,
        "scrollback_limit_chars": 200_000,
        "default_unix_shell": "/bin/bash",
        "default_windows_shell": "powershell.exe",
    }
    stored = db.get_all_settings()
    defaults.update(stored)
    return defaults


def require_principal(
    db: DB,
    session: str | None = Cookie(default=None, alias=env.SESSION_COOKIE),
) -> Principal:
    cfg = get_effective_settings(db)
    auth_required = bool(cfg.get("auth_required", False))

    if not auth_required:
        # anon OK
        return Principal(username=None, is_admin=True)

    if not session:
        raise HTTPException(status_code=401, detail="Not logged in")

    username = parse_session_token(session)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = db.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="Unknown user")

    return Principal(username=username, is_admin=bool(user["is_admin"]))


def require_admin(principal: Principal) -> None:
    if not principal.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")