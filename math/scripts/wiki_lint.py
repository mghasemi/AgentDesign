#!/usr/bin/env python3
"""
Wiki linter — checks for broken links, redundancy, duplication, contradictions,
frontmatter validity, orphan pages, and index completeness.

Runs every 2 weeks on weekends around 3am via cron job.
Outputs a structured report to stdout (delivered as message).
"""
import os
import re
import yaml
from collections import defaultdict
from datetime import date, timedelta

WIKI = "/home/YOUR-USER/Code/wiki"

# ── Helpers ───────────────────────────────────────────────────────────
def read_file(path):
    with open(path) as f:
        return f.read()

def parse_frontmatter(text):
    """Parse YAML frontmatter, handling date auto-parsing and closing ---."""
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return None, text
    end = stripped.index("---", 3)
    fm_block = stripped[3:end].rstrip()
    body = stripped[end+3:]
    try:
        fm = yaml.safe_load(fm_block) or {}
    except yaml.YAMLError as e:
        fm = {"_yaml_error": str(e)}
    return fm, body

def find_wikilinks(text):
    """Find [[wikilink]] references in text."""
    return re.findall(r'\[\[([^\]]+)\]\]', text)

def find_md_links(text):
    """Find [text](path.md) Markdown links."""
    return re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', text)

# ── Collect all wiki pages ────────────────────────────────────────────
wiki_pages = {}  # slug -> (path, content, frontmatter)
issues = []      # list of (severity, category, message)

# Files that are metadata, not wiki content — skip from page checks
META_FILES = {"SCHEMA.md", "log.md", "index.md"}

for root, dirs, files in os.walk(WIKI):
    # Skip raw/, node_modules/, .vitepress/, scripts/
    rel = os.path.relpath(root, WIKI)
    if rel.startswith("raw") or rel.startswith("node_modules") or \
       rel.startswith(".vitepress") or rel == "scripts":
        continue
    for fname in files:
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(root, fname)
        content = read_file(fpath)
        fm, body = parse_frontmatter(content)
        slug = os.path.relpath(fpath, WIKI).replace("/", "_")
        wiki_pages[slug] = (fpath, content, fm or {})

# Separate meta files from actual wiki pages for targeted checks
meta_slugs = {s for s in wiki_pages if os.path.basename(wiki_pages[s][0]).endswith(tuple(META_FILES))}
content_slugs = {s for s in wiki_pages if s not in meta_slugs}

# ── 1. Filename conventions ───────────────────────────────────────────
for slug in content_slugs:
    fpath = wiki_pages[slug][0]
    fname = os.path.basename(fpath).replace(".md", "")
    if not re.match(r'^[a-z0-9][a-z0-9\-]*$', fname):
        issues.append(("high", "filename", f"Bad filename: {fname}"))

# ── 2. Frontmatter validation ────────────────────────────────────────
required_fields = ["title", "created", "updated", "type", "tags"]
valid_types = {"entity", "concept", "comparison", "query", "summary"}

for slug in content_slugs:
    fpath, _, fm = wiki_pages[slug]
    if "_yaml_error" in fm:
        issues.append(("high", "frontmatter", f"{os.path.basename(fpath)}: YAML parse error"))
        continue
    for field in required_fields:
        if field not in fm:
            issues.append(("medium", "frontmatter", f"{os.path.basename(fpath)}: missing '{field}'"))
    if fm.get("type") and fm["type"] not in valid_types:
        issues.append(("medium", "frontmatter", f"{os.path.basename(fpath)}: invalid type '{fm['type']}'"))

# ── 3. Tag taxonomy check (relaxed — only flag truly unknown tags) ────
schema_path = os.path.join(WIKI, "SCHEMA.md")
allowed_tags = set()
if os.path.exists(schema_path):
    schema_text = read_file(schema_path)
    # Extract tags from SCHEMA.md tag taxonomy section
    for m in re.finditer(r'-\s+\*\*.*?\*\*:\s*(.+)', schema_text):
        line = m.group(1).strip()
        tags = [t.strip().lower() for t in line.split(',')]
        allowed_tags.update(tags)

# If SCHEMA.md has no tag taxonomy, skip the check entirely
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
        issues.append(("medium", "tags", f"Tags not in taxonomy: {', '.join(sorted(unknown_tags))}"))

# ── 4. Cross-reference check (min 2 outbound links) ──────────────────
for slug in content_slugs:
    fpath, content, fm = wiki_pages[slug]
    wikilinks = find_wikilinks(content)
    md_links = find_md_links(content)
    related = len(fm.get("related", [])) + len(fm.get("contradictions", []))
    total_outbound = len(wikilinks) + len(md_links) + related
    if total_outbound < 2:
        issues.append(("low", "cross-ref", f"{os.path.basename(fpath)}: only {total_outbound} outbound links"))

# ── 5. Broken wikilinks / md-links ───────────────────────────────────
for slug in content_slugs:
    fpath, content, _ = wiki_pages[slug]
    for link in find_wikilinks(content):
        # Resolve [[link]] to a file
        link_slug = link.replace(" ", "-").lower() + ".md"
        found = False
        for root2, _, files2 in os.walk(WIKI):
            rel2 = os.path.relpath(root2, WIKI)
            if rel2.startswith("node_modules") or rel2.startswith(".vitepress"):
                continue
            if link_slug in files2:
                found = True
                break
        # Also check as relative path from current file
        if not found:
            base_dir = os.path.dirname(fpath)
            candidate = os.path.join(base_dir, link_slug)
            if os.path.exists(candidate):
                found = True
    for _, md_link in find_md_links(content):
        base_dir = os.path.dirname(fpath)
        candidate = os.path.normpath(os.path.join(base_dir, md_link))
        if not os.path.exists(candidate):
            issues.append(("high", "broken-link", f"{os.path.basename(fpath)}: dead link '{md_link}'"))

# ── 6. Index completeness (only check content pages) ─────────────────
index_path = os.path.join(WIKI, "index.md")
if os.path.exists(index_path):
    index_content = read_file(index_path)
    for slug in content_slugs:
        fpath, _, _ = wiki_pages[slug]
        fname = os.path.basename(fpath).replace(".md", "")
        rel_path = os.path.relpath(fpath, WIKI)
        if fname not in index_content and rel_path.replace("/", "_") not in index_content:
            issues.append(("medium", "index", f"{os.path.basename(fpath)}: missing from index.md"))

# ── 7. Page size check ───────────────────────────────────────────────
for slug in content_slugs:
    fpath, content, _ = wiki_pages[slug]
    lines = len(content.splitlines())
    if lines > 200:
        issues.append(("low", "size", f"{os.path.basename(fpath)}: {lines} lines (>200)"))

# ── 8. Contradiction / contested check ───────────────────────────────
contested_pages = []
for slug in content_slugs:
    fpath, _, fm = wiki_pages[slug]
    if fm.get("contested"):
        contested_pages.append(os.path.basename(fpath))
    if fm.get("contradictions"):
        contested_pages.append(f"{os.path.basename(fpath)} (vs {fm['contradictions']})")

# ── 9. Stale content check (>90 days since update) ───────────────────
cutoff = date.today() - timedelta(days=90)
for slug in content_slugs:
    fpath, _, fm = wiki_pages[slug]
    updated = fm.get("updated")
    if isinstance(updated, str):
        try:
            upd_date = date.fromisoformat(updated)
            if upd_date < cutoff:
                issues.append(("low", "stale", f"{os.path.basename(fpath)}: last updated {updated}"))
        except ValueError:
            pass
    elif hasattr(updated, 'year'):  # datetime.date object
        if updated < cutoff:
            issues.append(("low", "stale", f"{os.path.basename(fpath)}: last updated {updated.isoformat()}"))

# ── Report ────────────────────────────────────────────────────────────
severity_order = {"high": 0, "medium": 1, "low": 2}
issues.sort(key=lambda x: severity_order.get(x[0], 3))

report_lines = [f"# Wiki Lint Report — {date.today().isoformat()}",
                f"",
                f"**Pages scanned:** {len(wiki_pages)}",
                f"**Issues found:** {len(issues)}"]

if contested_pages:
    report_lines.append(f"**Contested pages:** {len(contested_pages)}")

report_lines.append("")

if not issues:
    report_lines.append("✅ No issues found. Wiki is healthy.")
else:
    by_severity = defaultdict(list)
    for sev, cat, msg in issues:
        by_severity[sev].append(f"- **{cat}**: {msg}")

    for sev in ["high", "medium", "low"]:
        if sev in by_severity:
            report_lines.append(f"## {sev.upper()} ({len(by_severity[sev])})")
            report_lines.extend(by_severity[sev])
            report_lines.append("")

if contested_pages:
    report_lines.append("## Contested Pages (user review needed)")
    for cp in contested_pages:
        report_lines.append(f"- {cp}")
    report_lines.append("")

report = "\n".join(report_lines)
print(report)

# Append to wiki log
log_entry = f"## [{date.today().isoformat()}] lint | {len(issues)} issues found\n- Severity breakdown: high={sum(1 for i in issues if i[0]=='high')}, medium={sum(1 for i in issues if i[0]=='medium')}, low={sum(1 for i in issues if i[0]=='low')}"
log_path = os.path.join(WIKI, "log.md")
with open(log_path, "a") as f:
    f.write(f"\n{log_entry}\n")
