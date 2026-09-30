"""Backend API for the Wiki Browser desktop plugin.

Manages the VitePress dev server lifecycle (start / stop / restart / status)
for the math research wiki at /home/YOUR-USER/Code/wiki (port 5173).

Process-management notes
------------------------
* ``npm run dev`` spawns ``npm -> sh -> node``; killing the npm PID alone
  orphans the actual listener. We therefore spawn with
  ``start_new_session=True`` (own process group) and signal the whole group
  via ``os.killpg``.
* Servers started outside the plugin (manual ``npm run dev``) have no PID
  file; :func:`stop` falls back to discovering the listener PID(s) on the
  port via ``ss -tlnp``.
* Server output goes to a log file (never PIPE) — an undrained pipe fills up
  and blocks the child.
"""

import asyncio
import os
import re
import signal
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

WIKI_DIR = Path(os.environ.get("WIKI_DIR", "/home/YOUR-USER/Code/wiki"))
WIKI_PORT = 5173
VITEPRESS_DIR = WIKI_DIR / ".vitepress"
PID_FILE = VITEPRESS_DIR / ".wiki-dev-server.pid"
LOG_FILE = VITEPRESS_DIR / "wiki-dev-server.log"
START_TIMEOUT_S = 20
STOP_TIMEOUT_S = 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _check_server() -> bool:
    """Return True if a server is responding on WIKI_PORT."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("localhost", WIKI_PORT), timeout=2.0
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False


async def _read_pid_file():
    """Read and validate the stored PID (may be None)."""
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return pid
    except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
        return None


async def _write_pid_file(pid: int) -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid))


async def _remove_pid_file() -> None:
    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass


async def _find_port_pids() -> list:
    """Discover PIDs listening on WIKI_PORT via ``ss -tlnp``.

    Handles servers started outside the plugin (no PID file): the port is the
    source of truth for what is actually serving the wiki.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "ss", "-tlnp",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
    except Exception:
        return []
    pids = []
    for line in out.decode(errors="replace").splitlines():
        if f":{WIKI_PORT}" not in line:
            continue
        for m in re.finditer(r"pid=(\d+)", line):
            pids.append(int(m.group(1)))
    return pids


def _tail_log(n_bytes: int = 400) -> str:
    """Return the tail of the dev-server log (for error diagnostics)."""
    try:
        data = LOG_FILE.read_bytes()[-n_bytes:]
        return data.decode(errors="replace").strip()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/status")
async def status():
    """Check whether the wiki dev server is running."""
    running = await _check_server()
    pid = await _read_pid_file()
    if not pid:
        pids = await _find_port_pids()
        pid = pids[0] if pids else None
    return {"running": running, "port": WIKI_PORT, "pid": pid, "dir": str(WIKI_DIR)}


@router.post("/start")
async def start():
    """Start ``npm run dev`` in the wiki dir unless it is already running."""
    if await _check_server():
        return {
            "ok": True,
            "message": "Server already running",
            "running": True,
            "pid": await _read_pid_file(),
        }

    if not WIKI_DIR.is_dir() or not (WIKI_DIR / "package.json").exists():
        return {"ok": False, "error": f"Wiki dir not found: {WIKI_DIR}"}
    if not (WIKI_DIR / "node_modules").is_dir():
        return {"ok": False, "error": "node_modules missing — run `npm install` first"}

    VITEPRESS_DIR.mkdir(parents=True, exist_ok=True)
    log_handle = open(LOG_FILE, "ab")
    try:
        proc = await asyncio.create_subprocess_exec(
            "npm", "run", "dev",
            cwd=str(WIKI_DIR),
            stdout=log_handle,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
        )
    except FileNotFoundError:
        log_handle.close()
        return {"ok": False, "error": "npm not found in PATH"}
    except Exception as exc:
        log_handle.close()
        return {"ok": False, "error": str(exc)}

    # The child inherited the log fd — safe to close our copy now.
    log_handle.close()

    pid = proc.pid
    await _write_pid_file(pid)

    for _ in range(START_TIMEOUT_S * 2):
        if await _check_server():
            return {
                "ok": True,
                "message": f"Wiki dev server started (PID {pid})",
                "running": True,
                "pid": pid,
            }
        if proc.returncode is not None:
            await _remove_pid_file()
            return {
                "ok": False,
                "error": f"npm exited with code {proc.returncode}: {_tail_log()}",
            }
        await asyncio.sleep(0.5)

    return {
        "ok": True,
        "message": f"Server starting (PID {pid}) — first boot may take longer",
        "running": await _check_server(),
        "pid": pid,
    }


@router.post("/stop")
async def stop():
    """Stop the wiki dev server (own process group, then port-based fallback)."""
    if not await _check_server():
        await _remove_pid_file()
        return {"ok": True, "message": "Server was not running", "running": False}

    killed = False

    # 1) Kill the process group we spawned (covers npm -> sh -> node tree).
    pid = await _read_pid_file()
    if pid:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            killed = True
        except (ProcessLookupError, PermissionError):
            pass

    # 2) Port-based fallback: anything else actually bound to the port.
    for p in await _find_port_pids():
        try:
            os.kill(p, signal.SIGTERM)
            killed = True
        except (ProcessLookupError, PermissionError):
            pass

    await _remove_pid_file()

    # Wait for the port to free.
    for _ in range(STOP_TIMEOUT_S * 2):
        if not await _check_server():
            return {"ok": True, "message": "Server stopped", "running": False}
        await asyncio.sleep(0.5)

    # Escalate: SIGKILL anything still bound.
    for p in await _find_port_pids():
        try:
            os.kill(p, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    await asyncio.sleep(0.5)

    running = await _check_server()
    return {
        "ok": not running,
        "message": "Server stopped" if not running else "Could not stop server",
        "running": running,
    }


@router.post("/restart")
async def restart():
    """Stop then start the wiki dev server."""
    await stop()
    return await start()
