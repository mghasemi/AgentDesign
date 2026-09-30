# Table Overflow Fixes in LaTeX

## Problem

Tables with 5+ columns or wide math content overflow the page margin.
This is common in research articles with experimental result tables.

## Fix: Font Size Reduction

Apply `\small` or `\footnotesize` immediately before `\begin{tabular}`:

```latex
\begin{table}[htbp]
  \centering
  \caption{...}
  \label{tab:...}
  \footnotesize            % ← add this line
  \begin{tabular}{@{}lcccc@{}}
  ...
```

**Guidelines:**
- `\small`: 5-column tables, moderate-width content
- `\footnotesize`: 6-column tables, or 5-column with long math in cells
- 3-column tables and solver-config tables usually don't need shrinking

## Batch Fix with execute_code

When fixing many tables, use `execute_code` with `patch`:

```python
from hermes_tools import patch

tables = ['tab:phase4', 'tab:phase12', 'tab:phase7', ...]
for label in tables:
    old = f'  \\label{{{label}}}\n  \\begin{{tabular}}'
    new = f'  \\label{{{label}}}\n  \\small\n  \\begin{{tabular}}'
    patch('paper.tex', old, new)
```

This matches the pattern `\label{tab:XXX}\n  \begin{tabular}` and inserts the
font size command between them. Same approach works for `\footnotesize` on
the widest tables.

## Verification After Fix

Rebuild with `scripts/latex-verify.sh paper` and visually inspect the PDF
for any remaining overflow. Tables that still overflow may need column-width
specifiers (e.g., `p{3cm}`) or abbreviated column headers.
