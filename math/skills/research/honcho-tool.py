#!/usr/bin/env python3
"""Honcho memory and social cognition API tool for Hermes."""

import argparse
import json
import os
import sys
from pathlib import Path
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

BASE_URL = os.getenv("HONCHO_BASE_URL", "http://YOUR-HOST:8008/")
WORKSPACE_ID = os.getenv("HONCHO_WORKSPACE", "hermes")


class HonchoError(RuntimeError):
    pass


def _request(method, path, payload=None):
    """Make HTTP request to Honcho API."""
    if not WORKSPACE_ID or WORKSPACE_ID == "":
        raise HonchoError("Missing HONCHO_WORKSPACE. Set it in environment.")

    url = f"{BASE_URL}{path}".replace("{workspace_id}", WORKSPACE_ID)

    try:
        response = requests.request(method, url, json=payload, timeout=20)
        if response.status_code == 401 or (response.status_code >= 400 and "Feature is disabled" not in response.text):
            raise HonchoError(f"Honcho API error {response.status_code}: {response.text[:200]}")
        return response.json() if response.text else {}
    except requests.exceptions.ConnectionError:
        raise HonchoError("Cannot connect to Honcho at " + BASE_URL)
    except Exception as e:
        raise HonchoError(f"Honcho API error: {str(e)}")


def list_peers():
    """List all peers in the workspace."""
    data = _request("POST", "/v3/workspaces/{workspace_id}/peers/list")
    return {"peers": data.get("items", [])}


def get_peer(peer_id):
    """Get specific peer details."""
    path = f"/v3/workspaces/{WORKSPACE_ID}/peers/{peer_id}"
    data = _request("GET", path)
    return {"peer": data}


def create_peer(name, **metadata):
    """Create a new peer."""
    payload = {
        "name": name,
        "workspace_id": WORKSPACE_ID,
        "metadata": metadata
    }
    data = _request("POST", "/v3/workspaces/{workspace_id}/peers", payload)
    return {"created_peer": data.get("item", data)}


def update_peer(peer_id, **updates):
    """Update peer details."""
    path = f"/v3/workspaces/{WORKSPACE_ID}/peers/{peer_id}"
    data = _request("PUT", path, updates)
    return {"updated_peer": data}


def delete_peer(peer_id):
    """Delete a peer."""
    path = f"/v3/workspaces/{WORKSPACE_ID}/peers/{peer_id}"
    data = _request("DELETE", path)
    return {"deleted_peer_id": peer_id, "success": True}


def get_card(peer_id):
    """Get peer card (curated facts)."""
    path = f"/v3/workspaces/{WORKSPACE_ID}/peers/{peer_id}/card"
    data = _request("GET", path)
    return {"card": data.get("item", [])}


def update_card(peer_id, add=None, remove=None):
    """Update peer card with facts."""
    payload = {}
    if add:
        payload["add"] = [f"{fact}" for fact in add] if isinstance(add, list) else [str(add)]
    if remove:
        payload["remove"] = [f"{fact}" for fact in remove] if isinstance(remove, list) else [str(remove)]

    path = f"/v3/workspaces/{WORKSPACE_ID}/peers/{peer_id}/card"
    data = _request("PUT", path, payload)
    return {"updated_card": data}


def get_representation(peer_id):
    """Get peer representation."""
    path = f"/v3/workspaces/{WORKSPACE_ID}/peers/{peer_id}/representation"
    data = _request("POST", path)
    return {"representation": data.get("item", [])}


def update_representation(peer_id, **updates):
    """Update peer representation."""
    payload = updates.copy() if updates else {}
    path = f"/v3/workspaces/{WORKSPACE_ID}/peers/{peer_id}/representation"
    data = _request("POST", path, payload)
    return {"updated_representation": data}


def get_context(peer_id):
    """Get full context for a peer."""
    path = f"/v3/workspaces/{WORKSPACE_ID}/peers/{peer_id}/context"
    data = _request("GET", path)
    return {"context": data.get("item", [])}


def search_peer(peer_id, query):
    """Search across peer observations."""
    payload = {
        "query": query,
        "max_tokens": 1000
    }
    path = f"/v3/workspaces/{WORKSPACE_ID}/peers/{peer_id}/search"
    data = _request("POST", path, payload)
    return {"results": data.get("items", [])}


def get_conclusions(peer_id):
    """List conclusions for a peer."""
    path = f"/v3/workspaces/{WORKSPACE_ID}/conclusions/list"
    # Note: This endpoint requires workspace_id in URL, not peer-specific
    data = _request("POST", path)
    return {"conclusions": data.get("items", [])}


def create_conclusion(peer_id, conclusion_text):
    """Create a new conclusion for a peer."""
    payload = {
        "peer_id": peer_id,
        "text": conclusion_text
    }
    path = f"/v3/workspaces/{WORKSPACE_ID}/conclusions"
    data = _request("POST", path, payload)
    return {"created_conclusion": data.get("item", data)}


def delete_conclusion(conclusion_id):
    """Delete a conclusion."""
    path = f"/v3/workspaces/{WORKSPACE_ID}/conclusions/{conclusion_id}"
    data = _request("DELETE", path)
    return {"deleted_conclusion_id": conclusion_id, "success": True}


def list_sessions():
    """List all sessions in the workspace."""
    data = _request("POST", "/v3/workspaces/{workspace_id}/sessions/list")
    return {"sessions": data.get("items", [])}


def get_session_context(session_id):
    """Get context for a specific session."""
    path = f"/v3/workspaces/{WORKSPACE_ID}/sessions/{session_id}/context"
    data = _request("GET", path)
    return {"session_context": data.get("item", [])}


def get_session_summaries(session_id):
    """Get summaries for a session."""
    path = f"/v3/workspaces/{WORKSPACE_ID}/sessions/{session_id}/summaries"
    data = _request("GET", path)
    return {"summaries": data.get("items", [])}


def search_session(session_id, query):
    """Search within a session."""
    payload = {
        "query": query,
        "max_tokens": 1000
    }
    path = f"/v3/workspaces/{WORKSPACE_ID}/sessions/{session_id}/search"
    data = _request("POST", path, payload)
    return {"results": data.get("items", [])}


def build_parser():
    parser = argparse.ArgumentParser(description="Honcho API tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Peer commands
    peers_list_parser = subparsers.add_parser("list-peers", help="List all peers")
    get_peer_parser = subparsers.add_parser("get-peer", help="Get peer details")
    get_peer_parser.add_argument("peer_id")

    create_peer_parser = subparsers.add_parser("create-peer", help="Create new peer")
    create_peer_parser.add_argument("name")

    update_peer_parser = subparsers.add_parser("update-peer", help="Update peer")
    update_peer_parser.add_argument("peer_id")

    delete_peer_parser = subparsers.add_parser("delete-peer", help="Delete peer")
    delete_peer_parser.add_argument("peer_id")

    # Card commands
    card_parser = subparsers.add_parser("get-card", help="Get peer card")
    card_parser.add_argument("peer_id")

    update_card_parser = subparsers.add_parser("update-card", help="Update peer card")
    update_card_parser.add_argument("peer_id")
    update_card_parser.add_argument("--add", nargs="+", help="Add facts")
    update_card_parser.add_argument("--remove", nargs="+", help="Remove facts")

    # Representation commands
    rep_parser = subparsers.add_parser("get-representation", help="Get peer representation")
    rep_parser.add_argument("peer_id")

    # Context commands
    context_parser = subparsers.add_parser("get-context", help="Get peer context")
    context_parser.add_argument("peer_id")

    search_parser = subparsers.add_parser("search-peer", help="Search peer observations")
    search_parser.add_argument("peer_id")
    search_parser.add_argument("query")

    # Conclusion commands
    conclusions_parser = subparsers.add_parser("get-conclusions", help="List peer conclusions")
    conclusions_parser.add_argument("peer_id")

    create_conclusion_parser = subparsers.add_parser("create-conclusion", help="Create peer conclusion")
    create_conclusion_parser.add_argument("peer_id")
    create_conclusion_parser.add_argument("text")

    delete_conclusion_parser = subparsers.add_parser("delete-conclusion", help="Delete peer conclusion")
    delete_conclusion_parser.add_argument("conclusion_id")

    # Session commands
    sessions_list_parser = subparsers.add_parser("list-sessions", help="List all sessions")

    session_context_parser = subparsers.add_parser("get-session-context", help="Get session context")
    session_context_parser.add_argument("session_id")

    session_summaries_parser = subparsers.add_parser("get-session-summaries", help="Get session summaries")
    session_summaries_parser.add_argument("session_id")

    session_search_parser = subparsers.add_parser("search-session", help="Search in session")
    session_search_parser.add_argument("session_id")
    session_search_parser.add_argument("query")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "list-peers":
            result = list_peers()
        elif args.command == "get-peer":
            result = get_peer(args.peer_id)
        elif args.command == "create-peer":
            result = create_peer(args.name)
        elif args.command == "update-peer":
            result = update_peer(args.peer_id)
        elif args.command == "delete-peer":
            result = delete_peer(args.peer_id)
        elif args.command == "get-card":
            result = get_card(args.peer_id)
        elif args.command == "update-card":
            result = update_card(args.peer_id, add=args.add, remove=args.remove)
        elif args.command == "get-representation":
            result = get_representation(args.peer_id)
        elif args.command == "get-context":
            result = get_context(args.peer_id)
        elif args.command == "search-peer":
            result = search_peer(args.peer_id, args.query)
        elif args.command == "get-conclusions":
            result = get_conclusions(args.peer_id)
        elif args.command == "create-conclusion":
            result = create_conclusion(args.peer_id, args.text)
        elif args.command == "delete-conclusion":
            result = delete_conclusion(args.conclusion_id)
        elif args.command == "list-sessions":
            result = list_sessions()
        elif args.command == "get-session-context":
            result = get_session_context(args.session_id)
        elif args.command == "get-session-summaries":
            result = get_session_summaries(args.session_id)
        elif args.command == "search-session":
            result = search_session(args.session_id, args.query)
        else:
            parser.print_help()
            sys.exit(1)

        print(json.dumps(result, indent=2))
    except HonchoError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
