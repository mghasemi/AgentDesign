# Citation Merge Workflow

When a reference (e.g., an unpublished manuscript, an intermediate tech note,
or a self-citation to an incomplete work) needs to be absorbed into the
main article and removed from the bibliography entirely.

## Steps

### 1. Locate all citation sites
```bash
grep -n "cite{RefKey}" article.tex
```

### 2. Replace each citation with self-contained content
Use `execute_code` with Python raw strings for safe backslash handling:

```python
with open("article.tex", "r") as f:
    content = f.read()

# Each replacement absorbs the cited content inline
edits = [
    (r"old text~\cite{RefKey} trailing", r"new self-contained text"),
    # ... one per citation site
]
for old, new in edits:
    assert old in content, f"Not found: {old[:60]}..."
    content = content.replace(old, new)

with open("article.tex", "w") as f:
    f.write(content)
```

### 3. Optionally enrich with implementation detail
If the reference contained algorithmic or implementation content not
already in the article, add it at the appropriate section:

- **ADE encoding details** → add to the ADE Encoding section (§3.2)
- **Multi-derivation implementation** → add to the Multi-Derivation section (§4.5)
- **Solver routing logic** → add to the Pipeline or Experiments section

Example: The `build_ade_relations` insight (derivative symbols must be
prepended to the generator list for Groebner leading terms) fits naturally
after the definition of the ADE lifted algebra.

### 4. Remove the bib entry
```python
bib_path = "article_refs.bib"
with open(bib_path, "r") as f:
    bib = f.read()

old_entry = """@misc{RefKey,
  author  = {...},
  title   = {...},
  year    = {20XX},
  note    = {Manuscript in preparation}
}
"""
assert old_entry in bib, "Bib entry not found!"
bib = bib.replace(old_entry, "")
with open(bib_path, "w") as f:
    f.write(bib)
```

### 5. Verify
- `grep -c "RefKey" article.tex article_refs.bib` → must be 0
- Full 3-pass pdflatex + bibtex compile → 0 undefined citations
- pymupdf content check for key terms from the absorbed material
- Verify all remaining cited keys exist in bib:
```python
import re
cites = set(re.findall(r'\\cite\{([^}]+)\}', tex_content))
bib_keys = set(re.findall(r'@\w+\{([^,]+),', bib_content))
missing = cites - bib_keys  # must be empty
```
