#!/usr/bin/env python3
"""Sanitize the extracted profile data with the same rules the pack builder uses.

Keeps the structural evidence (keys, shapes, counts) and replaces every credential,
endpoint, hostname, local path and personal identifier with a placeholder, so the
whole project folder is safe to distribute alongside the profile packs.

Usage: python3 references/sanitize_extracted_data.py
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_patterns():
    spec = importlib.util.spec_from_file_location(
        "build_profile_packs", ROOT / "references" / "build_profile_packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PATTERNS


def main():
    patterns = load_patterns()
    target = ROOT / "data" / "profile_comparison.json"
    text = target.read_text()
    for rx, repl in patterns:
        text = rx.sub(repl, text)
    json.loads(text)                      # refuse to write invalid JSON
    target.write_text(text)
    print(f"sanitized {target.relative_to(ROOT)} ({len(text)} chars)")


if __name__ == "__main__":
    main()
