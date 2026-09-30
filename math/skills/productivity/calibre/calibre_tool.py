import os
import pathlib
import requests
import sys
import json


def _load_emv() -> None:
    current = pathlib.Path(__file__).resolve().parent
    for _ in range(10):
        candidate = current / ".emv"
        if candidate.is_file():
            with candidate.open() as fh:
                for raw in fh:
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    if key not in os.environ or not os.environ.get(key):
                        os.environ[key] = value
            break
        if current.parent == current:
            break
        current = current.parent


_load_emv()


BASE_URL = os.environ.get("CALIBRE_URL", "http://YOUR-HOST:6060")
ALT_BASE_URL = os.environ.get("CALIBRE_ALT_URL", "")

def search_calibre(query):
    errors = []
    data = None
    urls = [u for u in (BASE_URL, ALT_BASE_URL) if u]
    for base_url in urls:
        try:
            # Fetch the initial metadata payload, then fall back to alternate server if needed.
            response = requests.get(f"{base_url}/interface-data/books-init", timeout=10)
            response.raise_for_status()
            data = response.json()
            break
        except (requests.RequestException, ValueError) as exc:
            errors.append(f"{base_url}: {exc}")

    if data is None:
        return {"error": "Unable to reach Calibre server. Tried URLs: " + " | ".join(errors)}

    metadata = data.get("metadata", {})
    results = []
    query = query.lower()

    for bid, meta in metadata.items():
        title = meta.get("title", "").lower()
        authors = " ".join(meta.get("authors", [])).lower()

        if query in title or query in authors:
            results.append({
                "id": bid,
                "title": meta.get("title"),
                "authors": ", ".join(meta.get("authors", [])),
                "formats": meta.get("formats", [])
            })
    return results

if __name__ == "__main__":
    query_str = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    print(json.dumps(search_calibre(query_str), indent=2))
