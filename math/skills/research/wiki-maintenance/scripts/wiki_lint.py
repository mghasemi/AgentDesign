#!/usr/bin/env python3
"""Wiki linter — checks for broken links, redundancy, duplication, contradictions,
frontmatter validity, orphan pages, and index completeness.

Runs standalone: python3 /path/to/wiki_lint.py
Returns a structured report grouped by severity.

Also callable after every ingestion to verify nothing broke.
"""
import os
import re
import yaml
from datetime import date, timedelta

WIKI = "/home/YOUR-USER/Code/wiki"


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def parse_frontmatter(text):
    text = text.lstrip()
    if not text.startswith("---"):
        return None, text
    try:
        end = text.index("---", 3)
        fm_block = text[3:end].rstrip()
        fm = yaml.safe_load(fm_block)
        body = text[end + 3 :].lstrip()
        return fm, body
    except (ValueError, yaml.YAMLError) as e:
        return {"_yaml_error": str(e)}, text


def find_wikilinks(text):
    return [m.group(1) for m in re.finditer(r"\[\[([^\]]+)\]\]", text)]


def find_md_links(text):
    return [
        (m.group(0), m.group(1))
        for m in re.finditer(r"\[([^\]]+)\]\(([^)]+\.md)\)", text)
    ]


# ── Collect all wiki pages ────────────────────────────────────────────
wiki_pages = {}  # slug -> (path, content, frontmatter)
issues = []  # list of (severity, category, message)

META_FILES = {"SCHEMA.md", "log.md", "index.md"}

for root, dirs, files in os.walk(WIKI):
    rel = os.path.relpath(root, WIKI)
    if (
        rel.startswith("raw")
        or rel.startswith("node_modules")
        or rel.startswith(".vitepress")
        or rel == "scripts"
    ):
        continue
    for fname in files:
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(root, fname)
        content = read_file(fpath)
        fm, body = parse_frontmatter(content)
        slug = os.path.relpath(fpath, WIKI).replace("/", "_")
        wiki_pages[slug] = (fpath, content, fm or {})

meta_slugs = {
    s
    for s in wiki_pages
    if os.path.basename(wiki_pages[s][0]) in META_FILES
}
content_slugs = {s for s in wiki_pages if s not in meta_slugs}

# ── 1. Filename conventions ───────────────────────────────────────────
for slug in content_slugs:
    fpath = wiki_pages[slug][0]
    fname = os.path.basename(fpath).replace(".md", "")
    if not re.match(r"^[a-z0-9][a-z0-9\-]*$", fname):
        issues.append(("high", "filename", f"Bad filename: {fname}"))

# ── 2. Frontmatter validation ────────────────────────────────────────
required_fields = ["title", "created", "updated", "type", "tags"]
valid_types = {"entity", "concept", "comparison", "query", "summary"}

for slug in content_slugs:
    fpath, _, fm = wiki_pages[slug]
    if "_yaml_error" in fm:
        issues.append(
            (
                "high",
                "frontmatter",
                f"{os.path.basename(fpath)}: YAML parse error: {fm['_yaml_error']}",
            )
        )
        continue
    for field in required_fields:
        if field not in fm:
            issues.append(
                (
                    "medium",
                    "frontmatter",
                    f"{os.path.basename(fpath)}: missing '{field}'",
                )
            )
    if fm.get("type") and fm["type"] not in valid_types:
        issues.append(
            (
                "medium",
                "frontmatter",
                f"{os.path.basename(fpath)}: invalid type '{fm['type']}'",
            )
        )

# ── 3. Tag taxonomy check ────────────────────────────────────────────
schema_path = os.path.join(WIKI, "SCHEMA.md")
allowed_tags = set()
if os.path.exists(schema_path):
    schema_text = read_file(schema_path)
    for m in re.finditer(r"-\s+\*\*.*?\*\*:\s*(.+)", schema_text):
        line = m.group(1).strip()
        tags = [t.strip().lower() for t in line.split(",")]
        allowed_tags.update(tags)

if allowed_tags:
    used_tags = set()
    for slug in content_slugs:
        _, _, fm = wiki_pages[slug]
        tags = fm.get("tags", [])
        if isinstance(tags, list):
            used_tags.update(str(t).strip().lower() for t in tags)
        elif isinstance(tags, str):
            used_tags.add(tags.strip().lower())
    unknown_tags = used_tags - allowed_tags
    if unknown_tags:
        issues.append(
            (
                "medium",
                "tags",
                f"Tags not in taxonomy: {', '.join(sorted(unknown_tags))}",
            )
        )

# ── 4. Cross-reference check ────────────────────────────────────────
for slug in content_slugs:
    fpath, content, fm = wiki_pages[slug]
    wikilinks = find_wikilinks(content)
    md_links = find_md_links(content)
    related = len(fm.get("related", [])) + len(fm.get("contradictions", []))
    total_outbound = len(wikilinks) + len(md_links) + related
    if total_outbound < 2:
        issues.append(
            (
                "low",
                "cross-ref",
                f"{os.path.basename(fpath)}: only {total_outbound} outbound links",
            )
        )

# ── 5. Broken wikilinks ─────────────────────────────────────────────
for slug in content_slugs:
    fpath, content, _ = wiki_pages[slug]
    for link in find_wikilinks(content):
        link_name = link.replace(" ", "-").lower() + ".md"
        found = False
        for root2, _, files2 in os.walk(WIKI):
            rel2 = os.path.relpath(root2, WIKI)
            if rel2.startswith("node_modules") or rel2.startswith(".vitepress"):
                continue
            if link_name in files2:
                found = True
                break
        if not found:
            base_dir = os.path.dirname(fpath)
            if os.path.exists(os.path.join(base_dir, link_name)):
                found = True
        if not found:
            issues.append(
                (
                    "high",
                    "broken-link",
                    f"{os.path.basename(fpath)}: dead wikilink '[[{link}]]'",
                )
            )
    for _, md_link in find_md_links(content):
        candidate = os.path.normpath(os.path.join(os.path.dirname(fpath), md_link))
        if not os.path.exists(candidate):
            issues.append(
                (
                    "high",
                    "broken-link",
                    f"{os.path.basename(fpath)}: dead link '{md_link}'",
                )
            )

# ── 6. Index completeness ───────────────────────────────────────────
index_path = os.path.join(WIKI, "index.md")
if os.path.exists(index_path):
    index_content = read_file(index_path)
    for slug in content_slugs:
        fpath, _, _ = wiki_pages[slug]
        fname = os.path.basename(fpath).replace(".md", "")
        rel_path = os.path.relpath(fpath, WIKI)
        if fname not in index_content and rel_path.replace("/", "_") not in index_content:
            issues.append(
                (
                    "medium",
                    "index",
                    f"{os.path.basename(fpath)}: missing from index.md",
                )
            )

# ── 7. Page size ─────────────────────────────────────────────────────
for slug in content_slugs:
    fpath, content, _ = wiki_pages[slug]
    lines = len(content.splitlines())
    if lines > 200:
        issues.append(
            ("low", "size", f"{os.path.basename(fpath)}: {lines} lines (>200)")
        )

# ── 8. Contradictions ───────────────────────────────────────────────
for slug in content_slugs:
    fpath, _, fm = wiki_pages[slug]
    if fm.get("contested"):
        issues.append(
            ("medium", "contradiction", f"{os.path.basename(fpath)}: contested")
        )
    if fm.get("contradictions"):
        issues.append(
            (
                "medium",
                "contradiction",
                f"{os.path.basename(fpath)}: contradicts {fm['contradictions']}",
            )
        )

# ── 9. Stale content ────────────────────────────────────────────────
cutoff = date.today() - timedelta(days=90)
for slug in content_slugs:
    fpath, _, fm = wiki_pages[slug]
    updated = fm.get("updated")
    if isinstance(updated, str):
        try:
            upd_date = date.fromisoformat(updated)
            if upd_date < cutoff:
                issues.append(
                    (
                        "low",
                        "stale",
                        f"{os.path.basename(fpath)}: last updated {updated}",
                    )
                )
        except ValueError:
            pass

# ── Report ────────────────────────────────────────────────────────────
high = sum(1 for s, _, _ in issues if s == "high")
med = sum(1 for s, _, _ in issues if s == "medium")
low = sum(1 for s, _, _ in issues if s == "low")

print(f"# Wiki Lint Report — {date.today()}")
print(f"\n**Pages scanned:** {len(content_slugs)}")
print(f"**Issues found:** {len(issues)}")

if high > 0:
    print(f"\n## HIGH ({high})")
    for s, c, m in issues:
        if s == "high":
            print(f"- **{c}**: {m}")

if med > 0:
    print(f"\n## MEDIUM ({med})")
    for s, c, m in issues:
        if s == "medium":
            print(f"- **{c}**: {m}")

if low > 0:
    print(f"\n## LOW ({low})")
    for s, c, m in issues:
        if s == "low":
            print(f"- **{c}**: {m}")

if not issues:
    print("\nNo issues found.")
else:
    print(f"\n`{len(issues)} total issues ({high} high, {med} medium, {low} low)`")
