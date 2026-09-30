# Source → Wiki → Manuscript Citation Bridge (worked instance)

Compound workflow: user hands a paper and asks both (a) ingest it into the
wiki and (b) check whether its results shed light on the manuscript's open
problems. Outcome: wiki pages + a `queries/` mapping page + (if relevant)
citation edits in the manuscript.

Worked instance below: **Alaghmandan–Ghasemi 2015** (arXiv:1510.00846,
"Seminormed ∗-subalgebras of ℓ∞(X)") → **MomentSheaf** manuscript.

## What the paper contributes (the load-bearing results)

- **Theorem 2.5 (density criterion):** for `ι: A → B_ρ(F^X)`, the image
  `ι*(X_ρ)` is dense in `sp_{ρ_ι}(A)` iff `∃D>0: ρ_ι(a) ≤ D·sup_{x∈X_ρ}|e_x(ιa)|`
  — i.e. X dense in the Gelfand spectrum ⟺ the seminorm is equivalent to
  the sup-norm on X.
- **§3 compactification ξ_ΣX:** Gelfand spectrum of bounded Σ-measurable
  functions M_b(X,Σ); totally disconnected compact Hausdorff, X open+dense.
- **Proposition 3.8/3.9 (lifting + support shift):** every positive measure
  on (X,Σ) lifts to ξ_ΣX, but `X ∩ supp(μ)` is at most countable — the
  support escapes X into the added points.
- **Remark 3.4 / Example 3.1:** ξ_ΣX non-metrizable; X = ω₁+1 first
  countability fails exactly at ω₁ — the spaces where the stalk theorem's
  first-countability hypothesis is genuinely needed.
- **Halos h(x) + Theorem 3.12:** Robinson's-theorem analogue (compact iff
  Ỹ ⊆ ∪ h(y)); nonstandard model of the "points at infinity".

## Mapping to MomentSheaf open problems

| Paper result | MomentSheaf target |
|---|---|
| Thm 2.5 | Open Problem (5) constructible density; breaking phenomena (i),(ii) |
| Cor 2.3 / Rem 2.4 | breaking phenomenon (iv) non-compact spectrum |
| §3 ξ_ΣX | (iv) — canonical compactification |
| Prop 3.8 + 3.9 | Open Problem (8) local moment constraints; rem:momentconstraint |
| Cor 3.10 | prop:stalkcone germ criterion |
| Rem 3.4 + Ex 3.1 | prop:dirac_extreme first-countability hypothesis |
| halos + Thm 3.12 | Open Problem (4) real-spectrum extension |

**Negative mapping (what it does NOT address):** Galois/cohomological
problems (1,6,7,9); non-commutative (2); computational (3); the real
spectrum Sper(A) directly (works with characters X(A)/sp_ρ(A), not orderings).

## The key heuristic — check for uncited self-work FIRST

Before doing anything else, grep the manuscript for the author surname and
arXiv id. Alaghmandan–Ghasemi 2015 is Ghasemi's OWN paper, and the MomentSheaf
manuscript (which poses exactly the density question Thm 2.5 answers, and
exactly the support-shift subtlety Prop 3.9 describes) did not cite it. That
is a low-risk, high-value citation: the author's own prior work, directly on
topic, provably relevant. This is a recurring pattern in this user's corpus —
many of their own papers (Ghasemi–Kuhlmann–Marshall, Ghasemi–Marshall, etc.)
form a chain that later manuscripts should cross-cite.

## Citation edits made (three sites + bib entry)

1. Bibliography: `\bibitem{AlaghmandanGhasemi2015}` (alphabetically first),
   "M. Alaghmandan and M. Ghasemi, *Seminormed ∗-subalgebras of ℓ∞(X)*,
   arXiv:1510.00846." — note arXiv-only, no journal venue (verified by search;
   do NOT fabricate a journal).
2. §8 `subsec:beyond_setup`: density criterion with `\cite[Thm.~2.5]{...}`,
   replacing the looser "separating seminorm" sentence.
3. §5 `rem:momentconstraint`: support-shift warning with
   `\cite[Prop.~3.9]{...}`.
4. §9 Problem (8): flag support-shift as the concrete obstruction, cite
   `Prop.~3.9`.

## Verification sequence that worked

- 3-pass pdflatex → grep `Reference.*undefined`/`Citation.*undefined`/
  `multiply.defined` all 0; `Label(s) may have changed` 0 on pass 3.
- pymupdf: check bib entry present, "equivalent to the sup-norm" present,
  "at most countable set" present. Use prose substrings, not math-mode
  needles (the `^[raw/...]`-style provenance and `^*` superscripts extract
  unreliably).

## Reusable rule of thumb

For this user, "ingest X and check it against my open problems" almost always
means: X is their own or a close collaborator's paper, and the expected
outcome is a `queries/` mapping page plus 2–4 concrete `\cite[Thm N.M]`
edits — not a vague "relevant, see also" note. Deliver the specific numbered
citations, and state the negative mapping so the user can see you did not
over-claim.
