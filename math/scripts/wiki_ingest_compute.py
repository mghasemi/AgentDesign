#!/usr/bin/env python3
"""Compute sha256 of extracted content for raw wiki file."""
import hashlib, json

# Read the cached web extract
with open("/home/YOUR-USER/.hermes/profiles/math/cache/web/oa.upm.es-8675d9c996.md") as f:
    content = f.read()

sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
print(f"SHA256: {sha}")
print(f"Content length: {len(content)} chars, {len(content)//1024} KB")
