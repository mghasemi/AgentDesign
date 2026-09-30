---
name: latex-manuscript
description: "Use when compiling LaTeX documents, applying AST-aware diff patches, auditing mathematical notation for consistency, generating a \\newcommand glossary from a .tex file, or detecting undefined macros and unmatched braces."
metadata: {"clawdbot":{"emoji":"📄","requires":{"bins":["python3"]},"optional_bins":["pdflatex","lualatex"],"config":{"env":{"LATEX_COMPILER":{"description":"LaTeX compiler binary: pdflatex or lualatex","default":"pdflatex","required":false},"LATEX_GLOSSARY_GROUP":{"description":"SimpleRAG group name for the master notation glossary","default":"math-notation-glossary","required":false},"SIMPLERAG_URL":{"description":"SimpleRAG API base URL for glossary retrieval","default":"http://YOUR-HOST:7000","required":false}}}}}
related_skills: [ghasemi-latex-style]
---

**Prerequisite**: When writing or editing `.tex` content, ALWAYS load `ghasemi-latex-style` first. It defines the authoritative document conventions — `amsart` class, theorem environments (`thm`/`lemma`/`prop`/`crl`/`exm`/`rem`/`dfn`), macro hierarchy (`\reals`, `\sos`, `\rx`, `\sgr`, `\fps`), colored hyperlinks (DarkBlue/PinkPurple), manual `thebibliography`, and prose tone.
# LaTeX Manuscript Skill

Use this skill to compile, audit, and patch LaTeX manuscripts. It prevents the "execution illusion" — documents that look correct but fail to compile — and enforces notation consistency across long documents.

## When to Use

- Compile a `.tex` file and capture structured error output.
- Check a `.tex` file for unmatched braces, undefined macros, or notation drift.
- Apply a diff-based patch to a `.tex` source without manual editing.
- Auto-generate a `\newcommand` preamble from recurring symbols in a document.
- Audit all math-mode variables against the master glossary stored in SimpleRAG.

## When Not to Use

- Do not use for symbolic computation — use sympy-mcp or sagemath-mcp.
- Do not use for bibliography management — use zotero.

## Pitfalls

### `\DeclareMathOperator` and TeX Primitives

Never use `\DeclareMathOperator` with a name that is a TeX primitive.
The most common offender is `\sp` (TeX's superscript primitive, equivalent to `^`).
Even though `\DeclareMathOperator{\sp}{sp}` appears valid in the preamble,
`\sp_{\rho_K}` is parsed as `^{\rho_K}` by TeX, producing "Missing { inserted"
errors at lines that look syntactically correct in source.

**Fix:** Use a non-primitive name instead (e.g. `\gspec` for Gelfand spectrum).
Other primitives to avoid: `\sb` (subscript), `\it` (italic), `\bf` (bold), `\sl` (slanted).

### Multi-Pass Build Verification

For full verification after BibTeX changes, use a 3-pass clean build:
```bash
rm -f *.aux *.bbl *.blg *.out *.log
pdflatex -interaction=nonstopmode paper.tex
bibtex paper
pdflatex -interaction=nonstopmode paper.tex
pdflatex -interaction=nonstopmode paper.tex
```

Then audit with:
```bash
grep -c 'Reference.*undefined' paper.log   # must be 0
grep -c 'Citation.*undefined' paper.log    # must be 0
grep -c 'Warning' paper.blg                # must be 0
grep -c '^!' paper.log                     # must be 0
```

A standalone script is available at `scripts/latex-verify.sh`:
```bash
bash {baseDir}/scripts/latex-verify.sh path/to/paper
```
### Table Overflow

Tables with 5+ columns or wide math cells commonly overflow page margins.
See `references/table-overflow-fix.md` for the `\small`/`\footnotesize`
pattern and batch-fix approach via `execute_code`.

## Manuscript Readiness Audit

For a systematic checklist to audit a manuscript before submission or after
merging sections, see `references/manuscript-readiness-audit.md`. This
covers cross-reference hygiene, bibliography completeness and ordering,
claim inflation checks, and placeholder detection.

## Commands

### Compile

```bash
python3 {baseDir}/latex_tool.py compile /path/to/paper.tex
python3 {baseDir}/latex_tool.py compile /path/to/paper.tex --compiler lualatex --format json
```

### AST structural check (no compilation required)

```bash
python3 {baseDir}/latex_tool.py ast-check /path/to/paper.tex
python3 {baseDir}/latex_tool.py ast-check /path/to/paper.tex --format json
```

### Notation audit against master glossary

```bash
python3 {baseDir}/latex_tool.py notation-audit /path/to/paper.tex
python3 {baseDir}/latex_tool.py notation-audit /path/to/paper.tex --glossary-group math-notation-glossary --format json
```

### Auto-generate \newcommand glossary preamble

```bash
python3 {baseDir}/latex_tool.py auto-glossary /path/to/paper.tex
python3 {baseDir}/latex_tool.py auto-glossary /path/to/paper.tex --output /path/to/preamble.tex
```

### Apply diff patch

```bash
python3 {baseDir}/latex_tool.py diff-patch /path/to/paper.tex --patch /path/to/changes.diff
python3 {baseDir}/latex_tool.py diff-patch /path/to/paper.tex --old "\\alpha" --new "\\theta" --scope "section:3"
```

## Output

`compile` returns:

```json
{
  "command": "compile",
  "file": "/path/to/paper.tex",
  "success": false,
  "errors": [
    {"line": 47, "message": "Undefined control sequence \\myfunc"},
    {"line": 103, "message": "Missing $ inserted"}
  ],
  "warnings": [],
  "output_pdf": null
}
```

`notation-audit` returns a list of drift events:

```json
{
  "drifts": [
    {"symbol": "\\alpha", "first_use": "section:1", "redefined_as": "\\theta", "section": "section:3"}
  ]
}
```

## Configuration

- `LATEX_COMPILER`: `pdflatex` (default) or `lualatex`.
- `LATEX_GLOSSARY_GROUP`: SimpleRAG group holding the master notation glossary. Default: `math-notation-glossary`.
- `SIMPLERAG_URL`: SimpleRAG endpoint for glossary retrieval.
