# Bibliography Management in LaTeX Revisions

## Sorting by First-Author Surname

When a reviewer asks to sort the bibliography alphabetically, follow this procedure
for manuscripts with inline (`\begin{thebibliography}`) bibliographies:

### Procedure

1. Read the bibliography block with `read_file` (note the line range).
2. Extract all `\bibitem{KEY}` entries and determine the correct sort order:
   - **Primary key**: first author's surname (case-insensitive).
   - **Secondary key**: publication year (ascending within the same first author).
   - **Tertiary key**: bibitem key itself (for tie-breaking).
3. Reconstruct the sorted block and replace it with `patch` `mode='replace'`.
4. Run a verification script to confirm the sort order.

### Accented Names

Accented surnames (Schmüdgen, Pólya, G\"ardenfors) sort as their base letter.
When using Python for sort logic, normalize:
```python
import unicodedata
def normalize_surname(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
```

### Multi-word Surnames

"de Wolff" sorts under D, not W. "De Wolff" and "de Wolff" both sort under D.

## Verification Script (Sort Order)

```python
"""Verify bibliography sort order after reordering"""
import re

TEX = "paper.tex"
with open(TEX) as f:
    tex = f.read()

bib = re.search(r'\\begin\{thebibliography\}.*?\\end\{thebibliography\}', tex, re.DOTALL)
keys = [m.group(1) for m in re.finditer(r'\\bibitem\{(\w+)\}', bib.group(0))]

# Expected order: define per-paper
expected = ['Curto2023', 'Dressler2017', 'Dressler2019', ...]

is_sorted = keys == expected
for i, (actual, expect) in enumerate(zip(keys, expected)):
    print(f"  {'OK' if actual == expect else '!!'} [{i+1}] {actual}")

print(f"\nSorted: {is_sorted}")
```

## Verification Script (Comprehensive Post-Edit)

After applying multiple reviewer-requested edits across a manuscript, use a
focused assertion-based check. Pattern:

```python
"""Post-revision content verification"""
import re, os, subprocess

TEX = "/path/to/paper.tex"
with open(TEX) as f:
    tex = f.read()

# Source checks: each edit should leave a trace
checks = [
    (r'\section*{Acknowledgments}', "acknowledgments section added"),
    ('BIRS',                        "acknowledgment content"),
    ('to clarify',                  "word replacement applied"),
    (r'\cite[Chapter~II]{HLP52}',  "new citation inserted"),
    (r'($\Leftarrow$) Sufficiency', "proof direction signpost"),
]

passed = 0
for pat, desc in checks:
    ok = pat in tex
    print(f"  {'OK' if ok else 'FAIL'}: {desc}")
    if ok:
        passed += 1

# Build check
os.chdir(os.path.dirname(TEX))
for _ in range(2):
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
        os.path.basename(TEX)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

log_path = TEX.replace('.tex', '.log')
errs = open(log_path).read().count('\n!')
print(f"\nLaTeX errors: {errs}")
print(f"Source: {passed}/{len(checks)} passed")
```

## Hermes Verify Naming Convention

When creating temporary verification scripts, use the naming pattern
`/tmp/hermes-verify-<topic>.py` (or `.sh`). The system recognizes this
prefix for ad-hoc verification evidence. Clean up after verification
with `rm -f /tmp/hermes-verify-*.py`.
