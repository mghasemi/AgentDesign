# Manuscript Status Audit — 8-Step Checklist

Use this when asked "what's the status of X.tex?", "what remains?", or "audit this manuscript."
This is a lightweight alternative to the full Stage 6 Reflexion gate.

---

## Step 1: Read the full `.tex` file

- Use `read_file` with pagination (`offset`/`limit`) for files >500 lines.
- Do NOT skip sections — every section must be read.
- Note the total line count and whether `\end{document}` is present.

## Step 2: Compile (2+ passes)

```bash
cd /path/to/project
# First pass — expect undefined-reference warnings
pdflatex -interaction=nonstopmode paper.tex 2>&1 | grep -cE 'Error|Warning'
# Second pass — references should resolve
pdflatex -interaction=nonstopmode paper.tex 2>&1 | grep 'Warning' | grep -v 'rerun\|Rerun\|sorting'
```

- **0 errors** and only harmless warnings (hyperref Unicode, `rerun`) = ✅.
- Any `Reference ... undefined` after second pass = ❌.

## Step 3: Search for TODOs / placeholders / missing inputs

```bash
grep -n 'TODO\|FIXME\|XXX\|placeholder\|\\input{' paper.tex
```

Check every `\input{FILENAME}` — does the file exist? Is it a stub?

## Step 4: Verify citation completeness

```bash
# Extract all \cite{KEY} (strip optional [...] arguments first)
grep -oP '\\cite\{[^}]*\}' paper.tex | sort -u > /tmp/cited.txt
# Extract all \bibitem{KEY}
grep -oP '\\bibitem\{[^}]*\}' paper.tex | sort -u > /tmp/bibbed.txt
# Find cited but not bibbed
comm -23 <(sed 's/\\cite{//;s/}//' /tmp/cited.txt | sort -u) \
         <(sed 's/\\bibitem{//;s/}//' /tmp/bibbed.txt | sort -u)
# Find bibbed but never cited
comm -13 <(sed 's/\\cite{//;s/}//' /tmp/cited.txt | sort -u) \
         <(sed 's/\\bibitem{//;s/}//' /tmp/bibbed.txt | sort -u)
```

Also check for non-standard `\cite[...]{...}` syntax — commas inside optional
arguments can break LaTeX parsing.  Flag any instance like
`\cite[page 31 and Lemma 4.2.5, page 107]{MSc01}`.

## Step 5: Verify cross-references

After 2+ compilation passes, check the `.log` file:

```bash
grep -c 'Reference.*undefined' paper.log
```

0 hits = all `\ref`, `\eqref`, `\pageref` keys resolve.

## Step 6: Check supporting files

- If the manuscript claims formal verification (Lean4, Coq, etc.), locate the
  claimed file.
- Attempt to run the verifier:
  ```bash
  export PATH="$HOME/.hermes/profiles/math/home/.elan/bin:$PATH"
  lean verify_file.lean
  ```
- **Common pitfall**: `import Mathlib` requires a full Mathlib installation.
  The `elan` toolchain binary may exist but `lake` needs to fetch Mathlib
  (~1 GB download, can time out on slow connections).
- Flag as 🟡 if the verifier exists but can't be executed due to missing
  dependencies. Do NOT block on this — it's a supporting infrastructure
  issue, not a manuscript content issue.

## Step 7: Compare against progress reports

If `Progress/` or `Sources/` directories exist with stage/phase reports:

- Read the latest report (e.g., `stage_6_final_report.md`).
- Check for:
  - **Old file paths**: report references `.github/Sources/paper.tex` but
    the actual file is at `project/paper_combined.tex`.
  - **Outdated theoretical approaches**: e.g., a draft used a weaker
    preordering-based approach but the current `.tex` has the stronger
    direct proof.
  - **Resolved placeholders**: report lists a placeholder table as
    outstanding but the `.tex` now has it inline.
- Flag version drift explicitly — it wastes follow-up effort.

## Step 8: Categorize and report

Produce a table with columns:

| # | Location | Issue | Fix |

Group rows by severity:

- 🔴 **Text issues**: wrong claim counts, undefined symbols, missing
  cross-references, unused bib entries.
- 🟡 **Infrastructure**: unverifiable Lean4 files, missing toolchains,
  companion docs needing updates.
- 🟢 **Cosmetic**: non-standard citation formatting, vague references
  ("earlier draft" without `\ref{}`).

Precede the table with a one-line compilation verdict and any theoretical
correctness note (if version drift was detected between drafts and the
current file).
