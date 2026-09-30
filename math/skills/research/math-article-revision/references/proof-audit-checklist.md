# Proof Audit for Merged Manuscripts

Checklist for verifying mathematical correctness when a manuscript was
assembled from multiple sources (markdown note series, earlier partial
drafts, multi-author contributions).

## When to Use

- After merging sections from different drafts into a single `.tex`
- When proofs cite references that haven't been individually verified
- Before submission of a manuscript assembled from research-phase notes

## Workflow

### 1. Verify Lemma Claims Against Cited References

Every lemma/theorem that cites an external reference must have its claim
checked against what the reference ACTUALLY proves. Common traps:

- **Existence vs. universal extendability:** A theorem proving existence
  of a representing measure does NOT imply that every restricted measure
  extends uniquely. E.g., CGIK Theorem 2.7 guarantees existence, not
  that restriction maps are surjective.
- **Compactness ⇒ Mittag-Leffler:** Not true in general. Compactness of
  individual spaces does not imply the inverse system satisfies
  Mittag-Leffler.
- **"By standard arguments"** hiding a nontrivial gap — the most dangerous
  phrase in merged manuscripts.

### 2. Notation-Type Mismatches

Check that notation semantics match the object type:

| Wrong | Why | Fix |
|-------|-----|-----|
| `M_d(L)\|_U ⪰ 0` | Matrix entries don't depend on open set U | `M_d(L) ⪰ 0` |
| `\rho_{β,α}(μ_β)` where `ρ` is set inclusion | Inclusion doesn't need function notation | Use `⊆` directly |
| Restriction notation on algebraic objects | `\|_U` only makes sense for functions | Use set-theoretic notation |

### 3. Project-Language Residue

A manuscript for standalone publication must not reference its
development history. Scan for and remove:

- `Phase 1/2/3/...` references → replace with section numbers
- `Summary of Phase N` → `Summary: Topic Name`
- Internal flow diagrams (`Phase 1 → Phase 2 → ...`) → natural prose
- "As part of this research program" / "The five phases form" → remove

### 4. Duplicate Words and Simple Typos

The `[Sketch]` proof environment won't catch:
- "and and" (double conjunction)
- "semidefinite semidefinite" (duplicate after line wrap)
- Missing spaces after `\cite{...}` commands

```bash
# Find duplicated adjacent words
grep -n -E '\b([a-zA-Z]+) \1\b' manuscript.tex
```

### 5. Summary Table Hygiene

Wide summary tables overflow page margins. Fix pattern:

```latex
\begin{center}
\small                    % ← prevents overflow on 6-row tables
\begin{tabular}{@{}ll@{}}
  \toprule
  ...
  \bottomrule
\end{tabular}
\end{center}
```

### 6. External Reviewer Critiques: Disposition Before Editing

A detailed review arriving as numbered critiques must NOT be applied wholesale —
parts of such reviews are themselves wrong. Workflow (worked instance: DSDP
truncation theory pass 5, 2026-08-14):

1. **Verify each critique against the CURRENT file text.** Reviews are often
   written against an older draft or mis-number results (reviewer's "Prop 3.3/3.5"
   vs current numbering) — map before acting.
2. **Produce a disposition table** (accepted / accepted-but-reason-wrong /
   rejected-with-rebuttal) and record it in the audit file so later sessions
   know why a point was NOT applied.
3. **A rebuttal needs a positive counter-argument:**
   - *Strawman detection*: the critique attacks a claim the article never makes.
     Instance: "τ-projection invalid because τ(∂^α P_j) ∉ I^{(ν)}" — but the
     certificate is an identity IN the differential ring (not modulo the ideal),
     so applying the ring homomorphism τ is legitimate; the article never claims
     τ(I) ⊆ I^{(ν)}. Adopt the constructive remedy anyway when it improves
     clarity (lead with Putinar on the lift; demote τ to a consistency remark).
   - *Wrong-reason-right-conclusion*: accept the fix, correct the justification.
     Instance: reviewer claimed ord(fg) = max(ord f, ord g) — FALSE; orders are
     additive under products (ord(y'·y') = 2 = 1+1), max holds for SUMS. The
     division formula was still wrong, for the correct reason (need ν − ord(s_j)).
4. **Reviewers' invoked lemmas can be false too** — verify each against sources
   before quoting (order arithmetic, "every CODF model is non-Archimedean",
   Ritt's basis theorem statement, etc.).

### 7. Audit-Report Hygiene Across Fix Passes

An audit report that accumulates fix passes most often fails by
SELF-CONTRADICTION: stale verdicts and superseded analyses presented next to
"✅ Fixed" resolutions read as an invalid document (user flagged this twice in
one session). After EVERY pass, sweep for:

- **Verdict lines** — "Verdict (current): ✅ ... — *(historical: ❌/⚠️ ...)*";
  a bare ❌ under a ✅ resolution contradicts.
- **Historical quarantine** — superseded implication tables under an explicit
  "Historical analysis (superseded) — retained for provenance only" header that
  states its (i)–(iii) labels refer to the OLD conditions; the CURRENT proof's
  directions get their own ✅ table.
- **Duplicate rows** — repeated patches to the same table (bibliography flags)
  leave both the old ❌ row and the new ✅ row for one item; grep per key after
  each patch batch.
- **Derived tables** — executive-summary severity counts, deliverable-status
  tables, and priority lists must be re-synced when items close.
- **Superseded resolutions** — a later pass can invalidate an earlier pass's own
  resolution text; add a "Correction (pass N) — supersedes the resolution above"
  line (e.g., pass-3 said "rate supplied by CGIK 4.2"; pass-4 discovered 4.2 is
  the Stochel-type theorem).
- **Stale metadata** — page counts, "remaining work" lines, and notation claims
  (grep to confirm "0 occurrences of ν*(d)").
