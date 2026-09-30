# Stale Review Targeting the Wrong File — Worked Instance

**Session:** MomentSheaf Review-07, 2026-08-30 (`momentsheaf_article.tex`, 36 pp.)

## Failure mode

A review praised the current version accurately ("stalks as Prop 6.2–6.3,
Choquet as Theorem 6.9") yet its four highest-priority items — a local
indeterminacy index iota(x), Theorem 6.11 via "continuity of sections",
Corollary 6.12's projlim^1 M(B_omega) equivalence, a "cokernel of
Delta" argument — existed only in `moment_sheaf_unified.tex`, an early
merged draft still tracked in `manuscript/`.

## Diagnosis procedure

1. `.aux` mapping first (`grep -oE 'newlabel\{[^}]+\}\{\{[0-9.]+' paper.aux`):
   Section 6 ends at Remark 6.10 — no Thm 6.11, no Crl 6.12; the numbering
   the review praised matches exactly.
2. Grep the canonical file for the flagged math — 0 hits for every pattern.
3. `git log -S '<flagged phrase>' -- <canonical>.tex` — empty output PROVES
   the content never existed in that file's history (a present-day grep
   can't distinguish "removed last week" from "never there").
4. Sweep sibling `.tex` files in the directory to locate the superseded
   draft the review actually targets.

## Verdict discipline

A stale review is NOT all-or-nothing: here 4 of its 15 items were still
valid live fixes (function-system phrasing, normalization remark,
first-countability qualifiers, A/J claim scoping). Verify every item
independently; never dismiss a whole review as stale.

## Root-cause fix

```bash
mkdir -p archive/superseded
git mv manuscript/<old-draft>.{tex,pdf} archive/superseded/
rm -f manuscript/<old-draft>.{aux,log,out,toc,brf,fls,fdb_latexmk}
```

Update the project README's directory tree in the SAME commit — a README
still listing superseded drafts as current is part of the root cause.

## Gotchas

- `git mv` to a sibling tree outside the repo fails; archive INSIDE the
  repo to keep history as tracked renames.
- `rm -f` of many build artifacts trips an auto-approved security-scan
  CRITICAL flag; harmless for regenerable files, verify `git status` after.
- Atomic-batch anchor failure: `sed -n 'N,Mp' file | cat -A` reveals the
  real line wrapping that broke the match; fix that one anchor and re-run
  the WHOLE batch (assert-before-write leaves the file untouched on any
  failure — never hand-patch the successful subset).
