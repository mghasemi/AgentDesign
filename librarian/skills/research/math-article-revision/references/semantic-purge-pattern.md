# Semantic purge: a worked instance (MomentSheaf Galois descent)

Reviewer flagged: "$H^1(G,\mathcal M(K'))$ measures the failure of
descent for torsors" is too vague — no torsor has been constructed whose
obstruction is this group.

## The mistake

Batch 1 fixed the single cited location (the Definition, `def:galois_coh`)
and rephrased it correctly ("classifies $1$-cocycles modulo coboundaries").
A residual grep was run — but for the *literal math strings* the earlier
review rounds had used ($H^1(G,P$, $P_x$), all clean. The overstatement
in fact survived as **prose** in four other locations:

- theorem body `thm:coh_obst` item (2): "torsors under the $G$-set of
  representing measures"
- remark `rem:obst_vacuous`: "descent of families (torsors)"
- Example (quadratic extension): "$H^1(G,M)$ then measures the ambiguity
  of descending $G$-conjugate families"
- summary table: "$H^1$ … is a framework for families"

None contained the literal quoted math string, so the string grep missed
all four. The user's follow-up ("make sure the severe logical issues are
actually fixed") forced Batch 2, which purged all of them.

## The fix that worked

Grep for the claim's **meaning**, not its LaTeX spelling. Enumerate every
phrasing:

```bash
# semantic, not literal
grep -nE 'torsor|measures the ambiguity|failure of descent|obstruction class|controls the descent' paper.tex
```

Then fix every hit and re-verify absence with a pymupdf audit whose
`needles_absent` are *prose substrings*, not math-mode substrings
(extraction of superscripts/Greek is unreliable).

## Companion regression: summary-table overfull

The Batch 2 edit lengthened a `@{}ll@{}` summary-table row (no wrap),
producing a 765pt `Overfull \hbox`. Fixed by splitting the row into two
and switching the column spec to wrapping columns `p{4cm}p{9cm}`.
Lesson: any edit near a `tabular` requires a post-compile `grep Overfull`.

## Meta-lesson

"Already resolved" / "already fixed" is a claim, not a status. Deliver
proof-level evidence: the corrected statement, its hypotheses, and why
the proof is sound — never a string-absence report alone.
