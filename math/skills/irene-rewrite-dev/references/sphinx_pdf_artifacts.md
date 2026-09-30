# Sphinx → LaTeX → PDF Rendering Artifacts Catalog

Documented during IreneRewrite v1.3.0–v1.3.1 documentation review cycle (2026-08-09).

## Principle

When a reviewer reports errors in the compiled PDF that cannot be found in the
RST source files, the issue is a Sphinx → LaTeX → pdflatex pipeline artifact.
**Do not modify correct RST source.** Fix pipeline issues via `doc/conf.py` or
LaTeX preamble packages, not by editing the source.

## Catalog of Known Artifacts

| Source (RST) | Rendered in PDF | Cause |
|---|---|---|
| `\text{pruned}` | "pnined" | Sans-serif admonition font ligature: "ru" → "ni" |
| `\operatorname{New}(F)` | "771 New(F)" | Font encoding fallback for `\operatorname` |
| `\prec` | missing symbol (blank) | LaTeX Unicode math symbol fallback |
| `-4` (verbatim code) | `4` (minus dropped) | Verbatim-to-LaTeX conversion loses unary minus |
| `\neq` (in `:math:`) | literal "eq" | Missing backslash — `eq` interpreted as literal text |
| `$$\min...$$` (raw LaTeX) | raw unrendered `$$...$$` text | Sphinx requires `.. math::`, not raw `$$` |
| `▼` (U+25BC, literal block) | `! LaTeX Error: Unicode character ▼` | pdflatex can't handle non-ASCII in literal blocks |
| `│` (U+2502, preformatted) | LaTeX crash | Same as above — must use ASCII `|` and `v` |
| `2**2**y**4` (in PDF only) | appears as garbled product | Verbatim conversion corrupts `*` sequences |
| `1.\emptyset/3.0` (in PDF only) | OCR-like glyph artifact | Font substitution for `0` or `/` in code blocks |

## Real Source Bugs (Not Artifacts)

These WERE in the RST source and WERE fixed:

| File | Line | Bug | Fix |
|---|---|---|---|
| `sdp.rst` | 8 | Raw `$$...$$` instead of `.. math::` | Converted to `.. math::` block |
| `optim.rst` | 77 | `eq` instead of `\neq` in inline math | Added backslash: `\neq` |

## Diagnostic Workflow

1. Read the RST source with `read_file` to confirm content
2. Check the PDF with pymupdf to see what actually rendered
3. If source is correct but PDF is wrong → pipeline artifact → do NOT modify RST
4. If source has the bug → fix the source
5. Rebuild with `make latexpdf` and verify with pymupdf

## Mitigation Options (For Conf.py)

### Approach A: pdflatex with improved preamble — ✅ WORKS (182pp, 0 errors)

This is the pragmatic approach that actually compiled successfully.
xelatex and lualatex timed out or produced empty PDFs due to font
configuration complexity (Latin Modern system fonts not installed;
lualatex font loading hung on 182-page document).

```python
# In doc/conf.py — NO latex_engine setting (defaults to pdflatex)
latex_elements = {
    'preamble': r'''
\usepackage{mathrsfs}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}        # Latin Modern — fixes "pruned" → "pnined" ligature
\usepackage{textcomp}       # Extra text symbols — fixes minus signs in code
\usepackage{upquote}        # Straight quotes in verbatim — prevents quote corruption
''',
}
```

Key fixes provided by each package:
- `lmodern`: Replaces CM fonts with Latin Modern in T1 encoding, eliminating
  the "ru"→"ni" sans-serif ligature that made `\text{pruned}` render as "pnined"
- `textcomp`: Provides \textminus and other text companion symbols, fixing
  dropped minus signs in code blocks
- `upquote`: Forces straight quotes in verbatim environments, preventing
  Sphinx's code-block-to-LaTeX conversion from corrupting quote characters

### Approach B: xelatex/lualatex — ⚠️ ATTEMPTED, NOT WORKING

Switching to `latex_engine = 'xelatex'` or `'lualatex'` would eliminate
most Unicode and font-substitution artifacts natively.  However, both
engines failed in practice:

- **xelatex**: Produced 0-page PDF — Latin Modern fonts not available as
  system OTF/TTF (only as TeX Live Type1 fonts).  `fontspec` can find some
  fonts via TeX Live search but the bold mono variant was missing, causing
  silent content drop.
- **lualatex**: Hung/timeout during compilation of 182-page document —
  font loading was extremely slow through luaotfload on this system.

**If system fonts are later installed**, the working preamble would be:
```python
latex_engine = 'xelatex'
latex_elements = {
    'preamble': r'''
\usepackage{mathrsfs}
\usepackage{fontspec}
\usepackage{amsmath,amssymb}
''',
}
```
