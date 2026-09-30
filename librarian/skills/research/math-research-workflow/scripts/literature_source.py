#!/usr/bin/env python3
"""literature_source.py — check-before-download + store source copies.

Dedup helper for the Verified-Sources Registry (references/verified-sources-registry.md).
Two jobs:
  1) SHOW:  is this source already verified / already stored locally?
  2) FETCH: download a file into <project>/Sources/ and print the path for the
            registry row (does NOT itself verify citation metadata — run the
            Citation Verification Gate separately).

Usage (stdlib only):
  python3 literature_source.py show  <project_dir> [<key>|<arxiv_id>|<doi>|title-word]
      -> grep the project's literature/verified_sources.md and print matches +
         any Sources/ files whose name contains the query.
      Exit 0 if a verified row exists, 1 if none.

  python3 literature_source.py fetch <project_dir> <url> <filename> [sources_subdir]
      -> download <url> to <project>/<sources_subdir|Sources>/<filename>, skipping
         the download if that file already exists. Prints the saved path.

  python3 literature_source.py link  <project_dir> <Sources-relative-path>
      -> print the one registry row pattern to paste (Key left blank).

Example:
  python3 .../literature_source.py fetch positivstellensatz \
      https://arxiv.org/pdf/1109.0048 GMW2014.pdf
  => /home/YOUR-USER/Code/Python/positivstellensatz/Sources/GMW2014.pdf (or 'exists')
"""

import os
import sys
import urllib.request


def _registry_path(project_dir):
    p = os.path.join(project_dir, "literature", "verified_sources.md")
    return p if os.path.isfile(p) else None


def _sources_files(project_dir):
    out = []
    for d in ("Sources", "sources", "literature"):
        full = os.path.join(project_dir, d)
        if os.path.isdir(full):
            for fn in os.listdir(full):
                f = os.path.join(full, fn)
                if os.path.isfile(f):
                    out.append(f)
    return out


def cmd_show(project_dir, query):
    found = False
    rp = _registry_path(project_dir)
    if rp:
        print(f"# registry: {rp}")
        with open(rp, encoding="utf-8") as fh:
            for line in fh:
                if query.lower() in line.lower():
                    found = True
                    print(line.rstrip())
    if query:
        for f in _sources_files(project_dir):
            if query.lower() in os.path.basename(f).lower():
                found = True
                print(f"# local file: {f}")
    if not found and rp:
        print("# (no matching verified row or stored copy)")
    return 0 if found else 1


def cmd_fetch(project_dir, url, filename, subdir="Sources"):
    target_dir = os.path.join(project_dir, subdir)
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, filename)
    if os.path.isfile(path):
        print(f"exists: {path}")
        return 0
    req = urllib.request.Request(url, headers={"User-Agent": "hermes-math/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(path, "wb") as out:
        out.write(resp.read())
    print(path)
    return 0


def cmd_link(project_dir, src_rel_path):
    print("Registry row to paste (fill Key/verified columns):")
    print(f"| [TBD] | <verified citation> | <arXiv|DOI> | YYYY-MM-DD | <Method> | {src_rel_path} | |")
    return 0


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, project_dir = argv[0], argv[1]
    if not os.path.isdir(project_dir):
        print(f"error: not a directory: {project_dir}", file=sys.stderr)
        return 2
    if cmd == "show":
        return cmd_show(project_dir, argv[2] if len(argv) > 2 else "")
    if cmd == "fetch":
        if len(argv) < 4:
            print("fetch needs <project_dir> <url> <filename> [sources_subdir]", file=sys.stderr)
            return 2
        return cmd_fetch(project_dir, argv[2], argv[3], argv[4] if len(argv) > 4 else "Sources")
    if cmd == "link":
        if len(argv) < 3:
            return 2
        return cmd_link(project_dir, argv[2])
    print(f"error: unknown command {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
