# Manuscript Readiness Audit Workflow

Systematic checklist for auditing a LaTeX manuscript before submission or after
merging new sections. Complements the `compile`, `ast-check`, and `notation-audit`
tools with human-directed semantic checks.

## When to Use

- After merging multiple `.tex` source files into a combined manuscript
- Before submission to ensure cross-reference and citation hygiene
- When a collaborator reports that certain claims or cross-references feel off
- After major content restructure (new sections added, theorems reordered)

## Workflow (6 Steps)

### Step 1: Read the complete file

Read the entire `.tex` file (not just the diff or changed sections). Use
`read_file` with high `limit` or multiple offset-based reads. This catches
issues invisible from diffs: inconsistent notation across sections,
duplicate definitions, remaining "earlier draft" references.

### Step 2: Compile with 2 passes

```bash
pdflatex -interaction=nonstopmode <file>.tex 2>&1 | grep -E 'Error|Output written|! '
pdflatex -interaction=nonstopmode <file>.tex 2>&1 | grep -c 'Warning'
```

First pass: expect many undefined reference/citation warnings (normal).
Second pass: warnings should drop to near-zero. Any lingering `Reference/Citation
undefined` on second pass indicates a real problem.

Filter out harmless warnings:
- `hyperref` Unicode bookmark warnings (PDF strings from math in section titles)
- `rerun` / `Rerun to get cross-references` (LaTeX internal)

### Step 3: Search for TODOs, placeholders, and unresolved references

```bash
grep -n -i 'TODO\|FIXME\|XXX\|placeholder\|??' <file>.tex
grep -n 'earlier draft\|prior version\|TBD' <file>.tex
```

Vague phrases like "stated in the earlier draft" or "the three open problems"
may refer to content that no longer exists or whose count has changed during
revision. Verify each one against the actual current content.

### Step 4: Verify cross-reference integrity

```bash
# List all \ref{} targets
grep -oP '\\ref\{[^}]+\}' <file>.tex | sort | uniq -c

# List all \label{} definitions
grep -oP '\\label\{[^}]+\}' <file>.tex | sort | uniq -c
```

Every `\ref{...}` must have a corresponding `\label{...}`. Mismatches indicate
deleted or renamed sections/theorems/equations. Also scan for undefined symbols
cross-referenced in prose (e.g., "the exponent-interiority margin $\Delta$"
without a definition).

### Step 5: Audit the bibliography

```bash
# Count citations and bib entries
grep -c '\\bibitem{' <file>.tex
grep -oP '\\cite(\[[^\]]*\])?\{[^}]+\}' <file>.tex | sort | uniq -c
```

Checklist:
- [ ] Every `\cite{key}` has a `\bibitem{key}` (and vice versa — no unused entries)
- [ ] Entries ordered alphabetically by first author last name
- [ ] No duplicate entries (e.g., `Marshall99` unpublished + `Marshall02` published
      for the same paper — keep only the canonical version)
- [ ] Citation formatting uses standard LaTeX: `\cite[p.~31]{key}`, not
      `\cite[page 31]{key}` (and never `\pno` which is `biblatex`-only)

### Step 6: Check for semantic issues specific to math manuscripts

- **Claim inflation**: Claims like "formally verified" or "proved" should be
  backed by actual tool output. If a Lean4 verification file exists but Mathlib
  isn't installed, either install it or qualify the claim.
- **Definition-use ordering**: Every notation/term used in a proof should be
  defined earlier. Check for symbols introduced in prose without `\def` or
  equation blocks.
- **Theorem-proof pairing**: Every `\begin{theorem}` should have a
  `\begin{proof}` or an explicit note about why no proof is given.
- **Abstract accuracy**: The abstract's claims should match the actual content
  of the paper. After merging new sections, old abstracts often go stale.

## Output

The audit produces a severity-graded issue list:

| Priority | Category | Examples |
|----------|----------|---------|
| 🔴 Critical | Undefined symbols, missing proof, claim inflation | `Δ_support(d,p)` never defined |
| 🟡 Medium | Infrastructure gaps | Lean4 verification file exists but can't be checked |
| 🟢 Minor | Formatting, bib ordering, unused entries | `Marshall99` never cited |
