#!/usr/bin/env python3
"""Vikunja task management CLI tool."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import requests


def _load_emv():
    """Load environment variables from .emv files in parent directories."""
    current = Path(__file__).resolve().parent
    while True:
        emv_path = current / ".emv"
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
                if not key:
                    continue
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                if key not in os.environ or not os.environ.get(key):
                    os.environ[key] = value
            break
        if current.parent == current:
            break
        current = current.parent


_load_emv()

URL = os.getenv("VIKUNJA_URL", "http://YOUR-HOST:3456")
ALT_URL = os.getenv("VIKUNJA_ALT_URL", "")
TOKEN = os.getenv("VIKUNJA_TOKEN", "")


class VikunjaError(RuntimeError):
    pass


ZERO_TIME_PREFIX = "0001-01-01T00:00:00"


def _parse_response(response):
    if not response.text:
        return {}
    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}


def _request(method, path, payload=None, params=None, dry_run=False):
    """Make HTTP request to Vikunja API with failover."""
    if dry_run:
        return {
            "dry_run": True,
            "method": method,
            "path": path,
            "payload": payload,
            "params": params,
            "attempt_urls": [f"{URL}{path}", f"{ALT_URL}{path}"],
        }

    if not TOKEN:
        raise VikunjaError("Missing Vikunja token. Set VIKUNJA_TOKEN.")

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }

    errors = []
    for base_url in (URL, ALT_URL):
        full_url = f"{base_url}{path}"
        try:
            response = requests.request(
                method,
                full_url,
                json=payload,
                params=params,
                headers=headers,
                timeout=10,
            )
        except requests.RequestException as exc:
            errors.append(f"{full_url}: {exc}")
            continue

        if 500 <= response.status_code <= 599:
            snippet = response.text.strip()[:300]
            errors.append(f"{full_url}: HTTP {response.status_code} {snippet}")
            continue

        if response.status_code >= 400:
            body = _parse_response(response)
            raise VikunjaError(
                f"Request failed at {full_url} with HTTP {response.status_code}: "
                f"{json.dumps(body, ensure_ascii=True)}"
            )

        return _parse_response(response)

    raise VikunjaError("Unable to reach Vikunja server. Tried URLs: " + " | ".join(errors))


def _extract_id(json_output):
    """Extract task ID from API response JSON (handles nested 'data' or direct)."""
    if not json_output:
        return None
    try:
        d = json.loads(json_output)
    except ValueError:
        return None
    # Try common patterns: {"data": {id: N}}, {id: N}, list[0]
    if isinstance(d, dict):
        inner = d.get("data", d)
        if isinstance(inner, dict):
            return inner.get("id")
    elif isinstance(d, list) and len(d) > 0:
        first = d[0]
        if isinstance(first, dict):
            return first.get("id")
    return None


def _get_parent_id(task_id_or_none):
    """Resolve parent_task_id CLI argument to numeric ID."""
    if task_id_or_none is None or str(task_id_or_none).strip() == "":
        return None
    try:
        return int(task_id_or_none)
    except (ValueError, TypeError):
        raise VikunjaError(f"Invalid parent-task-id: {task_id_or_none}")


# Project operations


def list_projects():
    return _request("GET", "/api/v1/projects")


def get_project(project_id):
    return _request("GET", f"/api/v1/projects/{project_id}")


def create_project(title, description=None, dry_run=False):
    payload = {"title": title}
    if description:
        payload["description"] = description
    return _request("PUT", "/api/v1/projects", payload=payload, dry_run=dry_run)


def update_project(project_id, title=None, description=None, dry_run=False):
    payload = {}
    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description

    if not payload:
        raise VikunjaError("No fields provided for project update.")

    return _request("POST", f"/api/v1/projects/{project_id}", payload=payload, dry_run=dry_run)


def search_projects(query):
    projects = list_projects()
    if not isinstance(projects, list):
        raise VikunjaError("Unexpected response while listing projects for search.")

    query_norm = query.lower()
    results = []
    for project in projects:
        haystack = " ".join([str(project.get("title", "")), str(project.get("description", "")), str(project.get("identifier", ""))]).lower()
        if query_norm in haystack:
            results.append(project)

    return results


def get_project_by_title(title, exact=False):
    projects = list_projects()
    if not isinstance(projects, list):
        raise VikunjaError("Unexpected response while listing projects for title lookup.")

    title_norm = title.lower()
    if exact:
        matches = [p for p in projects if str(p.get("title", "")).lower() == title_norm]
    else:
        matches = []
        for project in projects:
            project_title = str(project.get("title", "")).lower()
            if title_norm in project_title:
                matches.append(project)

    if not matches:
        raise VikunjaError(f"No project found for title: {title}")
    if len(matches) > 1:
        options = [{"id": p.get("id"), "title": p.get("title")} for p in matches]
        raise VikunjaError(
            "Multiple projects matched. Refine the title or use exact match: " + json.dumps(options, ensure_ascii=True)
        )

    return matches[0]


# Task operations


def list_tasks(project_id=None):
    if project_id is not None:
        return _request("GET", f"/api/v1/projects/{project_id}/tasks")
    return _request("GET", "/api/v1/tasks/all")


def get_task(task_id):
    return _request("GET", f"/api/v1/tasks/{task_id}")


def delete_task(task_id, dry_run=False):
    """Delete a task by ID."""
    if not isinstance(dry_run, bool):
        raise VikunjaError("dry_run must be True/False")

    return _request(
        "DELETE",
        f"/api/v1/tasks/{task_id}",
        dry_run=dry_run,
    )


def list_labels():
    return _request("GET", "/api/v1/labels")


def create_label(title, description=None, hex_color=None, dry_run=False):
    payload = {"title": title}
    if description:
        payload["description"] = description
    if hex_color:
        payload["hex_color"] = hex_color
    return _request("PUT", "/api/v1/labels", payload=payload, dry_run=dry_run)


def attach_label(task_id, label_id, dry_run=False):
    return _request(
        "PUT",
        f"/api/v1/tasks/{task_id}/labels",
        payload={"label_id": label_id},
        dry_run=dry_run,
    )


def create_task_relation(child_task_id, parent_task_id, relation_kind="subtask", dry_run=False):
    """Create a subtask relation: child is a subtask of parent."""
    if not isinstance(dry_run, bool):
        raise VikunjaError("dry_run must be True/False")

    return _request(
        "PUT",
        f"/api/v1/tasks/{child_task_id}/relations",
        payload={
            "task_id": child_task_id,
            "other_task_id": parent_task_id,
            "relation_kind": relation_kind,
        },
        dry_run=dry_run,
    )


def _normalize_due_date(due_date):
    if due_date is None:
        return None

    value = due_date.strip()
    if not value:
        return None

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return f"{value}T23:59:00Z"

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise VikunjaError(
            "Invalid due date. Use YYYY-MM-DD or an ISO-8601 datetime, "
            "for example 2026-03-22 or 2026-03-22T23:59:00Z."
        ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)

    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_existing_due_date(due_date):
    if not due_date or str(due_date).startswith(ZERO_TIME_PREFIX):
        return None
    return _normalize_due_date(str(due_date))


def _find_label_by_title(title):
    labels = list_labels()
    if not isinstance(labels, list):
        raise VikunjaError("Unexpected response while listing labels.")

    title_norm = title.strip().lower()
    for label in labels:
        if str(label.get("title", "")).strip().lower() == title_norm:
            return label

    return None


def _ensure_task_labels(task_id, labels, dry_run=False):
    """Create or find labels and attach them to a task."""
    if not labels:
        return []

    existing_titles = set()
    if not dry_run:
        task = get_task(task_id)
        if not isinstance(task, dict):
            raise VikunjaError("Unexpected response while reading task labels.")
        existing_titles = {str(label.get("title", "")).strip().lower() for label in (task.get("labels") or [])}

    # Normalize: if a comma-separated string was passed, split it into a list
    if isinstance(labels, str):
        labels = [l.strip() for l in labels.split(",") if l.strip()]

    created_or_found = []
    for raw_label in labels:
        title = raw_label.strip()
        if not title:
            continue
        title_norm = title.lower()

        if title_norm in existing_titles:
            continue

        label = _find_label_by_title(title)
        if label is None:
            label = create_label(title, dry_run=dry_run)

        attach_label(task_id, int(label["id"]), dry_run=dry_run)
        created_or_found.append(label)
        existing_titles.add(title_norm)

    return created_or_found


def create_task(
    project_id,
    title,
    description=None,
    due_date=None,
    priority=None,
    labels=None,
    parent_task_id=None,
    dry_run=False,
):
    """Create a task with optional subtask relation to parent."""
    payload = {"title": title}
    if description:
        payload["description"] = description
    if due_date:
        payload["due_date"] = _normalize_due_date(due_date)
    if priority is not None:
        payload["priority"] = priority

    created = _request(
        "PUT",
        f"/api/v1/projects/{project_id}/tasks",
        payload=payload,
        dry_run=dry_run,
    )

    # Attach subtask relation after creation
    if parent_task_id is not None:
        child_id = created.get("id") if isinstance(created, dict) else None
        if child_id is None:
            raise VikunjaError("Task was created but no task id was returned for relation attachment.")

        create_task_relation(int(child_id), int(parent_task_id), "subtask", dry_run=dry_run)

    # Attach labels after creation
    if labels:
        child_id = created.get("id") if isinstance(created, dict) else None
        if child_id is None:
            raise VikunjaError("Task was created but no task id was returned for label attachment.")

        _ensure_task_labels(child_id, labels, dry_run=dry_run)
        if not dry_run:
            created = get_task(child_id)

    return created


def update_task(
    task_id,
    title=None,
    description=None,
    done=None,
    due_date=None,
    project_id=None,
    priority=None,
    labels=None,
    dry_run=False,
):
    """Update a task's properties."""
    current = get_task(task_id)
    if not isinstance(current, dict):
        raise VikunjaError("Unexpected response while reading task before update.")

    payload = {
        "title": current.get("title", ""),
        "description": current.get("description") or "",
        "done": current.get("done", False),
        "project_id": current.get("project_id"),
        "priority": current.get("priority", 0),
    }

    current_due_date = _normalize_existing_due_date(current.get("due_date"))
    if current_due_date is not None:
        payload["due_date"] = current_due_date

    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description
    if done is not None:
        payload["done"] = done
    if due_date is not None:
        normalized_due_date = _normalize_due_date(due_date)
        if normalized_due_date is None:
            payload.pop("due_date", None)
        else:
            payload["due_date"] = normalized_due_date
    if project_id is not None:
        payload["project_id"] = project_id
    if priority is not None:
        payload["priority"] = priority

    if not payload:
        raise VikunjaError("No fields provided for task update.")

    updated = _request("POST", f"/api/v1/tasks/{task_id}", payload=payload, dry_run=dry_run)
    if labels:
        _ensure_task_labels(task_id, labels, dry_run=dry_run)
        if not dry_run:
            updated = get_task(task_id)
    return updated


def search_tasks(query, project_id=None):
    """Search tasks by title or description."""
    tasks = list_tasks(project_id)
    if not isinstance(tasks, list):
        raise VikunjaError("Unexpected response while listing tasks for search.")

    query_norm = query.lower()
    results = []
    for task in tasks:
        haystack = " ".join([str(task.get("title", "")), str(task.get("description", "")), str(task.get("identifier", ""))]).lower()
        if query_norm in haystack:
            results.append(task)

    return results


def list_overdue_tasks(project_id=None):
    """List tasks with due dates in the past that are not done."""
    tasks = list_tasks(project_id)
    if not isinstance(tasks, list):
        raise VikunjaError("Unexpected response while listing tasks.")

    now = datetime.now(timezone.utc)
    overdue = []
    for task in tasks:
        if task.get("done", False):
            continue

        due_at = _parse_due_date_value(task.get("due_date"))
        if due_at is None:
            continue

        if due_at < now:
            overdue.append(task)

    return overdue


def complete_task(task_id, dry_run=False):
    """Mark a task as done."""
    return update_task(task_id, done=True, dry_run=dry_run)


# CLI parsing and dispatch


def _parse_bool(value):
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("Boolean value expected: true/false")


def _parse_priority(value):
    try:
        priority = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Priority must be an integer between 0 and 5.") from exc

    if priority < 0 or priority > 5:
        raise argparse.ArgumentTypeError("Priority must be an integer between 0 and 5.")
    return priority


def _parse_labels(value):
    labels = [label.strip() for label in value.split(",") if label.strip()]
    if not labels:
        raise argparse.ArgumentTypeError("Labels must be a comma-separated list like theory,review.")
    return labels


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Read/create/update Vikunja projects and tasks with URL failover."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview write requests without sending them to the server.")

    subparsers = parser.add_subparsers(dest="resource", required=True)

    # Project operations
    projects = subparsers.add_parser("projects", help="Project operations")
    project_sub = projects.add_subparsers(dest="action", required=True)

    project_list = project_sub.add_parser("list", help="List all projects")

    project_search = project_sub.add_parser("search", help="Search projects")
    project_search.add_argument("--query", required=True)

    project_get_by_title = project_sub.add_parser("get-by-title", help="Get one project by title")
    project_get_by_title.add_argument("--title", required=True)
    project_get_by_title.add_argument("--exact", action="store_true", help="Require exact title match instead of substring match.")

    project_get = project_sub.add_parser("get", help="Get one project")
    project_get.add_argument("project_id", type=int)

    project_create = project_sub.add_parser("create", help="Create a project")
    project_create.add_argument("--title", required=True)
    project_create.add_argument("--description")

    project_update = project_sub.add_parser("update", help="Update a project")
    project_update.add_argument("project_id", type=int)
    project_update.add_argument("--title")
    project_update.add_argument("--description")

    # Task operations
    tasks = subparsers.add_parser("tasks", help="Task operations")
    task_sub = tasks.add_subparsers(dest="action", required=True)

    task_list = task_sub.add_parser("list", help="List tasks")
    task_list.add_argument("--project-id", type=int)

    task_overdue = task_sub.add_parser("overdue", help="List all overdue open tasks")
    task_overdue.add_argument("--project-id", type=int)

    task_search = task_sub.add_parser("search", help="Search tasks")
    task_search.add_argument("--query", required=True)
    task_search.add_argument("--project-id", type=int)

    task_get = task_sub.add_parser("get", help="Get one task")
    task_get.add_argument("task_id", type=int)

    task_delete = task_sub.add_parser("delete", help="Delete a task by ID")
    task_delete.add_argument("task_id", type=int)

    task_create = task_sub.add_parser("create", help="Create a task")
    task_create.add_argument("--project-id", type=int, required=True)
    task_create.add_argument("--title", required=True)
    task_create.add_argument("--description")
    task_create.add_argument("--due-date")
    task_create.add_argument("--priority", type=_parse_priority)
    task_create.add_argument("--labels", type=_parse_labels)
    task_create.add_argument("--parent-task-id", type=int, help="Parent task ID (creates subtask relation)")

    task_log = task_sub.add_parser("log", help="Log a task (alias of create)")
    task_log.add_argument("--project-id", type=int, required=True)
    task_log.add_argument("--title", required=True)
    task_log.add_argument("--description")
    task_log.add_argument("--due-date")
    task_log.add_argument("--priority", type=_parse_priority)
    task_log.add_argument("--labels", type=_parse_labels)
    task_log.add_argument("--parent-task-id", type=int, help="Parent task ID (creates subtask relation)")

    task_update = task_sub.add_parser("update", help="Update a task")
    task_update.add_argument("task_id", type=int)
    task_update.add_argument("--title")
    task_update.add_argument("--description")
    task_update.add_argument("--done", type=_parse_bool)
    task_update.add_argument("--due-date")
    task_update.add_argument("--project-id", type=int)
    task_update.add_argument("--priority", type=_parse_priority)
    task_update.add_argument("--labels", type=_parse_labels)

    task_complete = task_sub.add_parser("complete", help="Mark a task as done")
    task_complete.add_argument("task_id", type=int)

    return parser


def _dispatch(args):
    if args.resource == "projects":
        if args.action == "list":
            return list_projects()
        if args.action == "search":
            return search_projects(args.query)
        if args.action == "get-by-title":
            return get_project_by_title(args.title, exact=args.exact)
        if args.action == "get":
            return get_project(args.project_id)
        if args.action == "create":
            return create_project(args.title, args.description, dry_run=args.dry_run)
        if args.action == "update":
            return update_project(
                args.project_id, title=args.title, description=args.description, dry_run=args.dry_run
            )

    elif args.resource == "tasks":
        if args.action == "list":
            return list_tasks(args.project_id)
        if args.action == "overdue":
            return list_overdue_tasks(args.project_id)
        if args.action == "search":
            return search_tasks(args.query, args.project_id)
        if args.action == "get":
            return get_task(args.task_id)
        if args.action == "delete":
            return delete_task(args.task_id, dry_run=args.dry_run)
        if args.action in {"create", "log"}:
            return create_task(
                project_id=args.project_id,
                title=args.title,
                description=args.description,
                due_date=args.due_date,
                priority=args.priority,
                labels=args.labels,
                parent_task_id=_get_parent_id(args.parent_task_id),
                dry_run=args.dry_run,
            )
        if args.action == "update":
            return update_task(
                task_id=args.task_id,
                title=args.title,
                description=args.description,
                done=args.done,
                due_date=args.due_date,
                project_id=args.project_id,
                priority=args.priority,
                labels=args.labels,
                dry_run=args.dry_run,
            )
        if args.action == "complete":
            return complete_task(args.task_id, dry_run=args.dry_run)

    raise VikunjaError("Unsupported command")


def main():
    parser = _build_parser()
    args = parser.parse_args()

    try:
        result = _dispatch(args)
        print(json.dumps(result, indent=2, ensure_ascii=True))
    except VikunjaError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True))
        sys.exit(1)


if __name__ == "__main__":
    main()
