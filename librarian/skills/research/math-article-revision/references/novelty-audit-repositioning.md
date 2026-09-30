# Novelty Audit Repositioning — Worked Instance (MomentSheaf, 2026-08-31)

Two-round novelty audit of `momentsheaf_article.tex` against published
prior art. Round 1: component-level audit ("the inverse-limit formulation
is already published"). Round 2: theorem-by-theorem audit with a 24-row
table. Both dispositioned; commits `10a3140` and `fa66cc6`.

## Metadata verification (rounds 1 + 2)

| Claim in audit | Verified via | Result |
|---|---|---|
| IKKM projective-limit paper | Crossref 10.1007/s00020-022-02692-6 | IEOT **94** (2022), no. 2, Art. 12; arXiv:1906.01691 — audit's data correct; existing `Infusino2022` bibitem accurate |
| Bishop–de Leeuw | Numdam 10.5802/aif.95 | Ann. Inst. Fourier **9** (1959), 305–331 — added as `BishopDeLeeuw1959` |
| Edwards | Numdam 10.5802/aif.133 | Ann. Inst. Fourier **13** (1963), no. 1, 111–121 — added as `Edwards1963` |
| CGIK | arXiv abs page | JOT **90** (2023), no. 2 — existing bibitem fine |

Tooling notes: arXiv API 503'd under load (one retry, then fall back to
`web_search`); Crossref over **https** (plain http fetch returned 0 bytes
under the security scanner); Numdam citation-export blocks give
ready-made volume/issue/pages/MR/Zbl — prefer it for AIF and other
French archives.

## Round 1 — the key distinction: attribution vs. positioning

The manuscript CITED IKKM 2022 correctly — once, buried inside failure-mode
(C1) of the non-compact section. Nothing in the abstract or introduction
acknowledged that the inverse-limit principle itself is published. The fix
was positional, not citational:

- Abstract honesty clause ("The inverse-limit principle itself is not
  new — ... — whereas the system studied here is the set-level inverse
  system of representing-measure sets of a fixed functional").
- Two intro positioning paragraphs: the space-level vs. set-level
  contrast (IKKM: projective limits of character spaces X(A) with
  Yamasaki/Prokhorov conditions; ours: inverse system {M(B_ω)} of compact
  convex subsets of the FIXED space M_+(K), where existence ↔ finite
  intersection property, determinacy ↔ cardinality of the limit).
- Classical-status paragraph: Richter, Bishop–de Leeuw/Edwards, Bredon
  measure-sheaf, Gelfand reduction — "we claim no credit".
- Original-source bibitems added where only textbook citations existed
  (Phelps → + Bishop–de Leeuw 1959, Edwards 1963).

## Round 2 — audit rows mostly already satisfied

The theorem-by-theorem audit targeted the post-round-1 version but several
rows were stale or already handled:

| Audit row | Actual state | Verdict |
|---|---|---|
| "state first countability in the theorem, not the proof" | Was already IN the statement; `rem:dirac_general` delimits the general case with the Dieudonné measure | already satisfied — proved by reading the statement |
| lim¹ kept to linearized system | Open Problem (7) + `rem:lim1role` already restrict correctly | already satisfied |
| H¹ for families "keep conjectural" | `thm:coh_obst`(2) already says framework-only | satisfied, but no dedicated open-problem item → added Problem (10) |
| Prop 3.6 (= `prop:localizing`) "Known" | Putinar cited for the key step but no blanket disclaimer | partial gap → added "standard Lasserre–Putinar–Schmüdgen theory ... claim no novelty" |
| "add Relation to previous work subsection" | absent | genuine gap → added §1.1 |
| three-tier novelty structure | absent | genuine gap → added |
| sharpened central claim | "casts the CGIK framework in the language of inverse limits" — weaker than the audit's proposed wording | replaced with audit's wording |

**Lesson:** for each audit row, produce proof-level evidence of
"already satisfied" (quote the statement + where the hypothesis lives),
the same standard the skill demands for "already resolved" reviewer
items. The round-2 disposition report
(Reports/MomentSheaf_novelty_audit_round2_2026-08-31.md) carries the full
verdict table.

## The three-tier classification (reusable template)

1. **Established foundations** — name every borrowed component WITH its
   citation: framework papers (CGIK), the closest prior work (IKKM),
   classical tools (Choquet: Phelps/BdL/Edwards; Richter; standard
   measure-sheaf theory; Gelfand reduction). Explicit phrase: "used as
   background and not claimed as new".
2. **New structural results** — numbered (i)–(v), each with its precise
   hypotheses and delimitation (e.g. stalk extreme-ray classification
   "under first countability at x"). These are the defensible claims.
3. **Open directions** — cross-referenced to numbered open problems, with
   the explicit sentence "formulated as questions and not as theorems"
   and "not a theorem of this paper" for each.

## Enumerate renumbering incident (round 2)

New Open Problem (10) inserted after (9). Five pre-existing `Problem~(9)`
references; semantically three targeted the families-descent question
(now (10)) and two targeted Hochschild–Serre invariants (still (9)).
Retargeted the three via atomic batch — one anchor failed on line-wrap,
rolling back its two siblings; diagnosed with `cat -A`, fixed the failed
anchor with a single `patch`, then REAPPLIED the two rolled-back edits.
Final verification: extract compiled PDF, regex item numbers against
open-problem titles, assert (7)=Derived invariants, (9)=Hochschild–Serre,
(10)=Cohomological classification of families; assert every
`Problem~(N)` reference in the source points at the semantically
correct compiled item.

## Verification checklist (both rounds)

- Atomic batches with `count(old)==1` asserts; NO partial application.
- 2-pass pdflatex: 0 undefined refs/citations, 0 multiply-defined labels.
- pymupdf render checks: hyphenation-tolerant needles (search squashed
  text for cross-line phrases; curly-apostrophe traps: "Richter's"
  extracts with U+2019 — use a shorter needle).
- Overfull-hbox regression check: count before vs. after (9 → 9; all
  <25pt cosmetic). `git stash` mid-build is dangerous when the PDF is
  tracked — the stash-pop collides with the rebuilt PDF; prefer
  `git show HEAD:file` for the baseline build or a separate worktree.
- Citation hygiene: cited-no-bib and bib-never-cited both empty.
- Disposition report in Reports/ + commit in the same batch as the .tex.
