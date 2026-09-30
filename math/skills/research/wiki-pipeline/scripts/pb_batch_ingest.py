#!/usr/bin/env python3
"""Batch-add local PDFs to PocketBase wiki_ingestion queue.

Usage:
    python3 pb_batch_ingest.py /path/to/file1.pdf /path/to/file2.pdf ...
    python3 pb_batch_ingest.py --type webpage https://example.com/paper.pdf ...

Title is derived from the actual filename (minus .pdf extension).
"""
import urllib.request, json, sys, os, argparse
from datetime import date

def main():
    parser = argparse.ArgumentParser(description='Batch-add files to PB wiki_ingestion')
    parser.add_argument('files', nargs='+', help='Local PDF paths or URLs')
    parser.add_argument('--type', dest='source_type', default='pdf',
                        choices=['pdf', 'arxiv', 'webpage', 'other'],
                        help='Source type (default: pdf)')
    args = parser.parse_args()

    # Load token
    with open('/home/YOUR-USER/.hermes/profiles/math/home/YOUR-USER.txt') as f:
        token = f.read().strip()

    PB_HOST = "YOUR-HOST"
    PB_URL = f"http://{PB_HOST}:8090"

    # Health check
    print("Health check...", end=" ")
    try:
        urllib.request.urlopen(f"{PB_URL}/api/health", timeout=10)
        print("OK")
    except Exception as e:
        print(f"FATAL: {e}")
        sys.exit(1)

    # Auth check
    print("Auth check...", end=" ")
    try:
        urllib.request.urlopen(
            f"{PB_URL}/api/collections/wiki_ingestion/records",
            headers={'Authorization': f'Bearer {token}'}, timeout=10)
        print("OK")
    except Exception as e:
        print(f"FATAL: {e}")
        sys.exit(1)

    # Derive title from filename (actual name, minus .pdf extension)
    def title_from_path(p):
        base = os.path.basename(p.split('?')[0])  # strip query params for URLs
        if base.endswith('.pdf'):
            base = base[:-4]
        return base

    today = date.today().isoformat()
    ok, fail = 0, 0
    for fpath in args.files:
        title = title_from_path(fpath)
        data = {
            'source_url': fpath,
            'source_type': args.source_type,
            'title': title,
            'date_added': today,
            'ingested': False,
        }
        req = urllib.request.Request(
            f"{PB_URL}/api/collections/wiki_ingestion/records",
            data=json.dumps(data).encode(),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        try:
            resp = urllib.request.urlopen(req, timeout=15)
            j = json.loads(resp.read())
            print(f"  [+] '{title}' -> ID={j['id']}")
            ok += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"  [-] '{title}' FAILED ({e.code}): {body}")
            fail += 1
        except Exception as e:
            print(f"  [-] '{title}' ERROR: {e}")
            fail += 1

    print(f"\nDone: {ok} ok, {fail} failed.")
    sys.exit(1 if fail else 0)

if __name__ == '__main__':
    main()
