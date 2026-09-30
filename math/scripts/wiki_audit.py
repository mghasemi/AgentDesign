#!/usr/bin/env python3
"""Bi-weekly wiki audit: duplicate detection + index completeness."""
import os, re
from pathlib import Path

wiki_root = Path("/home/YOUR-USER/Code/wiki")

# Collect content .md files (exclude raw/, node_modules/, .vitepress/, log.md, SCHEMA.md)
content_files = []
for md in wiki_root.rglob("*.md"):
    rel = md.relative_to(wiki_root)
    parts = rel.parts
    if "raw" in parts or "node_modules" in parts or ".vitepress" in parts:
        continue
    if rel.name in ("log.md", "SCHEMA.md"):
        continue
    content_files.append(rel)

print(f"Content files to scan: {len(content_files)}")

# Read each file, strip frontmatter, extract sentences
def read_body(path):
    text = path.read_text(errors="replace")
    if text.startswith("---"):
        end = text.find("\n---", 4)
        if end != -1:
            text = text[end+4:]
    return text.strip()

def sentences(text):
    raw = re.split(r'(?<=[.!?])\s+', text)
    return {s.strip().lower() for s in raw if len(s.strip()) > 15}

file_sentences = {}
for rel in content_files:
    body = read_body(wiki_root / rel)
    sents = sentences(body)
    file_sentences[rel] = sents

# Pairwise Jaccard similarity
threshold = 0.8
duplicates = []
n = len(file_sentences)
items = list(file_sentences.items())
for i in range(n):
    for j in range(i+1, n):
        (pi, si), (pj, sj) = items[i], items[j]
        if not si or not sj:
            continue
        union = len(si | sj)
        if union == 0:
            continue
        intersection = len(si & sj)
        jaccard = intersection / union
        if jaccard >= threshold:
            duplicates.append((pi, pj, round(jaccard, 3)))

print(f"\nPotential duplicates (Jaccard >= {threshold}):")
if duplicates:
    for a, b, sim in sorted(duplicates, key=lambda x: -x[2]):
        print(f"  {a} <-> {b}  (similarity={sim})")
else:
    print("  none found")

# Index completeness check
index_path = wiki_root / "index.md"
index_text = index_path.read_text()

linked_paths = set(re.findall(r'\]\(([^)]+)\)', index_text))
print(f"\nPaths linked in index.md: {len(linked_paths)}")

missing_from_index = []
for rel in content_files:
    stem = str(rel)
    if stem not in linked_paths and "./" + stem not in linked_paths:
        missing_from_index.append(stem)

print(f"\nContent pages NOT in index.md:")
if missing_from_index:
    for p in sorted(missing_from_index):
        print(f"  {p}")
else:
    print("  none — all content pages are indexed")

# Check for broken links (linked but file doesn't exist)
broken = []
for lp in linked_paths:
    if lp.startswith("http"):
        continue
    clean = lp.lstrip("./")
    full = wiki_root / clean
    if not full.exists():
        broken.append(clean)

print(f"\nBroken links (in index.md but file missing):")
if broken:
    for b in sorted(broken):
        print(f"  {b}")
else:
    print("  none — all linked files exist")
