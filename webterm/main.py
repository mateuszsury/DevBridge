"""
DevBridge - AI Terminal Launcher
Author: Mateusz Sury
Python 3.13+

Continue your local AI coding sessions from anywhere.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from fastapi import Depends, FastAPI, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .db import DB
from .settings import env
from .security import (
    Principal,
    get_effective_settings,
    hash_password,
    make_session_token,
    require_admin,
    require_principal,
    verify_password,
    parse_session_token,
)
from .terminal_manager import TerminalManager

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="WebTerm")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "webterm" / "static")), name="static")

db = DB(str(BASE_DIR / env.DB_PATH))
tm = TerminalManager(db)


def tpl(name: str) -> str:
    return (BASE_DIR / "webterm_templates" / name).read_text(encoding="utf-8")


@app.on_event("startup")
async def startup() -> None:
    # Bootstrap admin jeśli brak użytkowników
    if db.count_users() == 0:
        db.create_user(
            username=env.BOOTSTRAP_ADMIN_USERNAME,
            password_hash=hash_password(env.BOOTSTRAP_ADMIN_PASSWORD),
            is_admin=True,
        )

    # Oznacz running z DB jako stale (bo nie wznawiamy procesów)
    await tm.mark_db_sessions_stale_on_start()
    await tm.load_sessions_from_db()


@app.get("/login", response_class=HTMLResponse)
def login_page() -> str:
    return tpl("login.html")


@app.post("/login")
def login(username: str = Form(), password: str = Form()) -> RedirectResponse:
    user = db.get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        return RedirectResponse(url="/login?err=1", status_code=302)

    token = make_session_token(username)
    resp = RedirectResponse(url="/", status_code=302)
    cfg = get_effective_settings(db)
    resp.set_cookie(
        env.SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,  # ustaw True za HTTPS
    )
    return resp


@app.post("/logout")
def logout() -> RedirectResponse:
    resp = RedirectResponse(url="/", status_code=302)
    resp.delete_cookie(env.SESSION_COOKIE)
    return resp


@app.get("/", response_class=HTMLResponse)
def index(_: Principal = Depends(lambda: require_principal(db))) -> str:
    return tpl("index.html")


# ---------- API: settings ----------
@app.get("/api/settings")
def api_get_settings(p: Principal = Depends(lambda: require_principal(db))) -> dict:
    cfg = get_effective_settings(db)
    return {"settings": cfg, "principal": {"username": p.username, "is_admin": p.is_admin}}


@app.put("/api/settings")
def api_put_settings(body: dict, p: Principal = Depends(lambda: require_principal(db))) -> dict:
    # jeśli auth_required=True to tylko admin może zmieniać
    cfg = get_effective_settings(db)
    if bool(cfg.get("auth_required", False)):
        require_admin(p)

    # whitelist kluczy
    allowed_keys = {
        "auth_required",
        "allow_anonymous_terminal",
        "max_sessions",
        "idle_ttl_seconds",
        "scrollback_limit_chars",
        "default_unix_shell",
        "default_windows_shell",
    }

    for k, v in body.items():
        if k not in allowed_keys:
            continue
        db.set_setting(k, v)

    return {"ok": True, "settings": get_effective_settings(db)}


# ---------- API: users ----------
@app.get("/api/users")
def api_list_users(p: Principal = Depends(lambda: require_principal(db))) -> dict:
    cfg = get_effective_settings(db)
    if bool(cfg.get("auth_required", False)):
        require_admin(p)

    users = []
    for r in db.list_users():
        users.append(
            {
                "id": int(r["id"]),
                "username": r["username"],
                "is_admin": bool(r["is_admin"]),
                "created_at": float(r["created_at"]),
            }
        )
    return {"users": users}


@app.post("/api/users")
def api_create_user(body: dict, p: Principal = Depends(lambda: require_principal(db))) -> dict:
    cfg = get_effective_settings(db)
    if bool(cfg.get("auth_required", False)):
        require_admin(p)

    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    is_admin = bool(body.get("is_admin", False))

    if not username or len(username) < 3:
        raise HTTPException(status_code=400, detail="Username too short")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password too short")

    if db.get_user_by_username(username):
        raise HTTPException(status_code=400, detail="User exists")

    db.create_user(username=username, password_hash=hash_password(password), is_admin=is_admin)
    return {"ok": True}


@app.put("/api/users/{user_id}")
def api_update_user(
    user_id: int,
    body: dict,
    p: Principal = Depends(lambda: require_principal(db)),
) -> dict:
    cfg = get_effective_settings(db)
    if bool(cfg.get("auth_required", False)):
        require_admin(p)

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Not found")

    if "is_admin" in body:
        db.set_user_admin(user_id, bool(body["is_admin"]))

    if "password" in body and body["password"]:
        pw = str(body["password"])
        if len(pw) < 6:
            raise HTTPException(status_code=400, detail="Password too short")
        db.set_user_password(user_id, hash_password(pw))

    return {"ok": True}


@app.delete("/api/users/{user_id}")
def api_delete_user(user_id: int, p: Principal = Depends(lambda: require_principal(db))) -> dict:
    cfg = get_effective_settings(db)
    if bool(cfg.get("auth_required", False)):
        require_admin(p)

    user = db.get_user_by_id(user_id)
    if not user:
        return {"ok": True}

    db.delete_user(user_id)
    return {"ok": True}


# ---------- API: sessions ----------
@app.get("/api/sessions")
async def api_list_sessions(_: Principal = Depends(lambda: require_principal(db))) -> dict:
    return {"sessions": await tm.list_sessions()}


@app.post("/api/sessions")
async def api_create_session(body: dict, p: Principal = Depends(lambda: require_principal(db))) -> dict:
    cfg = get_effective_settings(db)
    if bool(cfg.get("auth_required", False)):
        # logged users only; principal already verified
        pass
    else:
        # anon mode: jeśli allow_anonymous_terminal = false, blokuj tworzenie
        if not bool(cfg.get("allow_anonymous_terminal", True)) and p.username is None:
            raise HTTPException(status_code=403, detail="Anonymous terminal disabled")

    cwd = body.get("cwd")
    shell = body.get("shell")
    cols = int(body.get("cols", 120))
    rows = int(body.get("rows", 30))
    return await tm.create_session(cwd=cwd, shell=shell, cols=cols, rows=rows)


@app.delete("/api/sessions/{sid}")
async def api_kill_session(sid: str, _: Principal = Depends(lambda: require_principal(db))) -> dict:
    await tm.kill_session(sid)
    return {"ok": True}


# ---------- API: projects ----------
@app.get("/api/projects")
async def api_list_projects(path: str, _: Principal = Depends(lambda: require_principal(db))) -> dict:
    """List all subdirectories in the given path as projects."""
    import os
    from pathlib import Path as PathLib

    try:
        base_path = PathLib(path).expanduser().resolve()

        if not base_path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")

        if not base_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

        projects = []

        # List all subdirectories
        try:
            for item in base_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if has .git directory
                    has_git = (item / '.git').exists()

                    projects.append({
                        'name': item.name,
                        'path': str(item),
                        'hasGit': has_git
                    })
        except PermissionError:
            raise HTTPException(status_code=403, detail=f"Permission denied: {path}")

        # Sort by name
        projects.sort(key=lambda x: x['name'].lower())

        return {"projects": projects}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))


# ---------- API: quick actions ----------
@app.post("/api/quick-action/execute")
async def api_execute_quick_action(body: dict, _: Principal = Depends(lambda: require_principal(db))) -> dict:
    """Execute a quick action command in the background and return the result."""
    import asyncio
    import subprocess

    command = body.get("command", "").strip()
    cwd = body.get("cwd", "").strip()

    if not command:
        raise HTTPException(status_code=400, detail="Command is required")

    if not cwd or not os.path.isdir(cwd):
        raise HTTPException(status_code=400, detail="Invalid working directory")

    try:
        # Determine shell based on OS
        if os.name == "nt":
            # Windows
            shell_cmd = ["powershell.exe", "-Command", command]
        else:
            # Unix/Linux
            shell_cmd = ["/bin/bash", "-c", command]

        # Execute command in background with timeout
        process = await asyncio.create_subprocess_exec(
            *shell_cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            # Wait for command to complete with 60 second timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60.0
            )

            output = stdout.decode("utf-8", errors="ignore")
            error_output = stderr.decode("utf-8", errors="ignore")

            # Combine output
            combined_output = output
            if error_output:
                combined_output += "\n" + error_output

            success = process.returncode == 0

            return {
                "success": success,
                "exit_code": process.returncode,
                "output": combined_output.strip(),
                "error": error_output.strip() if not success else None
            }

        except asyncio.TimeoutError:
            # Kill process if it times out
            try:
                process.kill()
                await process.wait()
            except Exception:
                pass

            return {
                "success": False,
                "exit_code": -1,
                "output": "",
                "error": "Command timed out after 60 seconds"
            }

    except Exception as e:
        return {
            "success": False,
            "exit_code": -1,
            "output": "",
            "error": str(e)
        }


# ---------- WebSocket: terminal ----------
@app.websocket("/ws/terminal/{sid}")
async def ws_terminal(ws: WebSocket, sid: str) -> None:
    cfg = get_effective_settings(db)
    auth_required = bool(cfg.get("auth_required", False))

    if auth_required:
        cookie = ws.cookies.get(env.SESSION_COOKIE)
        username = parse_session_token(cookie) if cookie else None
        if not username or not db.get_user_by_username(username):
            await ws.close(code=4401)
            return
    else:
        # anon mode
        if not bool(cfg.get("allow_anonymous_terminal", True)):
            await ws.close(code=4403)
            return

    await ws.accept()

    scrollback = await tm.get_scrollback(sid)
    if scrollback:
        await ws.send_text(json.dumps({"type": "replay", "data": scrollback}))

    q = await tm.subscribe(sid)

    async def sender() -> None:
        while True:
            chunk = await q.get()
            await ws.send_text(json.dumps({"type": "output", "data": chunk}))

    async def receiver() -> None:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            t = msg.get("type")
            if t == "input":
                data = msg.get("data", "")
                await tm.write(sid, data.encode("utf-8", errors="ignore"))
            elif t == "resize":
                await tm.resize(sid, int(msg.get("cols", 120)), int(msg.get("rows", 30)))

    import asyncio

    st = asyncio.create_task(sender())
    rt = asyncio.create_task(receiver())

    try:
        done, pending = await asyncio.wait({st, rt}, return_when=asyncio.FIRST_EXCEPTION)
        for d in done:
            _ = d.result()
    except WebSocketDisconnect:
        pass
    finally:
        for t in (st, rt):
            t.cancel()
        await tm.unsubscribe(sid, q)