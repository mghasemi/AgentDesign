# Replacing SDP-Based Claims with Formal Proofs in Manuscripts

## Pattern
When a manuscript claims "X is SOS — confirmed by SDP decomposition (Irene)",
there are three tiers of replacement:

### Tier 1: Explicit Rational SOS (best)
If an explicit SOS decomposition with rational coefficients is known,
replace the entire SDP paragraph with the identity + verification method.

Example (M_{4,2}):
```
Old: "SDP decomposition using Irene produces a 15×15 Gram matrix of rank 3..."
New:  "We provide an explicit SOS decomposition:
       M_{4,2} = 1/16 Σ_{i<j} (X_i² - X_j²)²,
       verified by direct expansion. The identity has been formally proved
       in Lean 4 (ancillary file)."
```

### Tier 2: Formal Nonnegativity Proof + SDP Caveat
If nonnegativity follows from a known inequality but no explicit SOS is known,
lead with the inequality proof, then note the SDP confirmation as secondary.

Example (M_{4,1}):
```
Old: "SDP decomposition using Irene confirms M_{4,1} is SOS..."
New:  "Nonnegativity follows from the power-mean inequality:
       (Avg X_i)^4 ≤ Avg(X_i^4) by Jensen (t⁴ convex for even n).
       SOS membership is further confirmed by SDP (Irene) yielding
       a rank-3 Gram matrix; an explicit rational SOS remains open."
```

### Tier 3: Computational Evidence (when nothing else is available)
When neither an explicit SOS nor a formal inequality proof is available,
downgrade the claim from "confirmed" to "verified computationally" and
add an explicit caveat.

Example (d=3 cases):
```
Old: "confirmed to be SOS via SDP decomposition using Irene"
New:  "SOS membership verified computationally via SDP decomposition (Irene).
       Unlike the d=2 case, explicit rational SOS decompositions are not yet
       known for d=3; the results rest on numerical SDP evidence."
```

## LaTeX Implementation Notes

- When adding `\newtheorem{example}{Example}`, verify it's in the preamble
  (`grep '\\\\newtheorem' paper.tex`) before inserting any example env.
- For Lean 4 lemma names in `\texttt{}`, break long names across lines
  with `\\\\` to avoid 70pt overfull hbox warnings.
- After replacing SDP claims: verify via pymupdf that the new terms
  ("power-mean", "Jensen", "explicit SOS") appear in the extracted PDF text.
- Two-pass pdflatex is sufficient for inline-bibliography manuscripts
  (no bibtex needed when using `\begin{thebibliography}`).

## Verification Checklist

- [ ] `\newtheorem{example}` in preamble before first `\begin{example}`
- [ ] No unescaped `_` in `\texttt{}` content (use `\_`)
- [ ] pymupdf confirms new terms in PDF text
- [ ] Lean 4 ancillary file builds with `lake build` (0 errors)
- [ ] All `\cite{GMIr}` references to Irene correctly describe SDP as
      computational evidence (not formal proof) where applicable
