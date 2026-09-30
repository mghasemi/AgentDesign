# PDF Content Verification Script (pymupdf)

Use instead of ad-hoc grep after compilation. Verifies that specific LaTeX changes
(e.g., new theorems, renamed sections, added citations, replaced matrices) actually
rendered in the output PDF.

## Pattern

```python
import pymupdf, re, os, subprocess, sys

PAPER_DIR = '/path/to/project'
PAPER_TEX = 'paper.tex'

# 1. Two-pass compile
for pas in (1, 2):
    r = subprocess.run(
        ['pdflatex', '-interaction=nonstopmode', '-halt-on-error', PAPER_TEX],
        cwd=PAPER_DIR, capture_output=True, text=True, timeout=120
    )
    # Save log for inspection if needed:
    # with open(f'/tmp/tex-pass{pas}.log', 'w') as f: f.write(r.stdout + r.stderr)

pdf_path = os.path.join(PAPER_DIR, PAPER_TEX.replace('.tex', '.pdf'))

# 2. PDF integrity check
doc = pymupdf.Document(pdf_path)
pages = doc.page_count
text = ''.join(doc[i].get_text() for i in range(pages))
doc.close()

# 3. Content assertions — adapt these per session
checks = {
    'example_present':   'Example' in text and 'linear polynomial' in text,
    'gram_fixed':        'rank' in text and 'Gram matrix' in text,
    'signomial_clear':   'signomial constraint' in text and 'non-convex' in text,
    'citation_present':  'DIdW02' in text,
}

all_pass = all(checks.values())
print(f'all_pass: {all_pass}')
for k, v in checks.items():
    print(f'{k}: {v}')

sys.exit(0 if all_pass else 1)
```

## Ligature / Font Caveats

LaTeX ligatures (ff, fi, fl) and subscripts may not extract cleanly. Use shorter
substrings and be tolerant: search for `signomial` not `signomial constraint`.

For stubborn cases, use font-aware extraction:

```python
page = doc[pg]
blocks = page.get_text("dict")["blocks"]
for block in blocks:
    if "lines" in block:
        for line in block["lines"]:
            line_text = "".join(span["text"] for span in line["spans"])
            if "target" in line_text.lower():
                print(f"Found: {line_text}")
```

## Full 5-Check Verification Pattern

For insertions of new theorems/sections into an existing manuscript, use
this comprehensive 5-check pattern (beyond pymupdf content-only checks):

```python
import subprocess, sys, re
from pathlib import Path

PROJ = Path("/path/to/project")
TEX = PROJ / "paper.tex"
AUX = PROJ / "paper.aux"
PDF = PROJ / "paper.pdf"
errors = []

# 1. Compile: two-pass
for _ in range(2):
    r = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", TEX.name],
        capture_output=True, text=True, timeout=60, cwd=PROJ
    )
    if r.returncode != 0:
        errors.append(f"pdflatex exited {r.returncode}")

# 2. Check .aux for new labels
aux_txt = AUX.read_text()
for lbl in ["thm:new_result", "lem:supporting"]:
    if f"\\newlabel{{{lbl}}}" not in aux_txt:
        errors.append(f"Label {lbl} missing from .aux")

# 3. Check PDF contains key phrases (pymupdf)
import fitz
doc = fitz.open(PDF)
pdf_text = "".join(page.get_text() for page in doc)
doc.close()
for phrase in ["New Theorem Title", "key notation", "Lemma"]:
    if phrase not in pdf_text:
        errors.append(f"Phrase '{phrase}' not found in PDF")

# 4. Check LaTeX source for structural integrity
tex = TEX.read_text()
for needle in [
    r"\begin{theorem}\label{thm:new_result}",
    r"\end{proof}",
    r"\section{Next Section}",
]:
    if needle not in tex:
        errors.append(f"Source missing: {needle[:60]}...")

# 5. Verify positioning relative to existing landmarks
idx_old = tex.find(r"\label{thm:existing}")
idx_new = tex.find(r"\label{thm:new_result}")
if idx_old == -1 or idx_new == -1 or idx_new <= idx_old:
    errors.append("New theorem not positioned after existing one")

if errors:
    print("FAIL:", *errors, sep="\n  ")
    sys.exit(1)
print("PASS: All 5 checks passed")
```

The `.aux` label check (step 2) is particularly valuable — it catches
broken cross-references before they silently produce `??` in the PDF.
The positioning check (step 5) catches insertion-at-wrong-location errors
that are invisible to both the compiler and content extraction.
