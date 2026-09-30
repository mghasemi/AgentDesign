"""Backend API for the Vikunja Desktop Plugin.

Provides REST endpoints to interact with the Vikunja Kanban server
for viewing and managing projects and tasks.
"""

import os
from pathlib import Path
from fastapi import APIRouter
import requests

router = APIRouter()

# Load .emv file if it exists (similar to vikunja_tool.py)
_current = Path(__file__).resolve().parent
while True:
    emv_path = _current / ".emv"
    if emv_path.is_file():
        for raw_line in emv_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            if key not in os.environ or not os.environ.get(key):
                os.environ[key] = value
        break
    if _current.parent == _current:
        break
    _current = _current.parent

# Vikunja API configuration
VIKUNJA_URL = os.environ.get("VIKUNJA_URL", "http://YOUR-HOST:3456")
VIKUNJA_TOKEN = os.environ.get("VIKUNJA_TOKEN", "")


def _request(method: str, path: str, payload=None, params=None):
    """Make an authenticated request to the Vikunja API."""
    if not VIKUNJA_TOKEN:
        return {"error": "Missing VIKUNJA_TOKEN environment variable. Please set it in your .emv file or profile config."}

    headers = {
        "Authorization": f"Bearer {VIKUNJA_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.request(
            method,
            f"{VIKUNJA_URL}{path}",
            json=payload,
            params=params,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


@router.get("/projects")
def list_projects():
    """List all Vikunja projects."""
    return _request("GET", "/api/v1/projects")


@router.get("/projects/{project_id}/tasks")
def list_project_tasks(project_id: int):
    """List all tasks for a specific project."""
    return _request("GET", f"/api/v1/projects/{project_id}/tasks")


@router.get("/tasks")
def list_all_tasks():
    """List all tasks across all projects."""
    return _request("GET", "/api/v1/tasks/all")


@router.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Get a specific task by ID."""
    return _request("GET", f"/api/v1/tasks/{task_id}")


@router.post("/tasks/{task_id}")
def update_task(task_id: int):
    """Get current task state and toggle done status."""
    # First get the current task
    task = _request("GET", f"/api/v1/tasks/{task_id}")
    if "error" in task:
        return task
    
    # Toggle done status
    return _request("POST", f"/api/v1/tasks/{task_id}", payload={
        "title": task.get("title", ""),
        "description": task.get("description") or "",
        "done": not task.get("done", False),
        "project_id": task.get("project_id")
    })