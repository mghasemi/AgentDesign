# Verified Citations — Choquet Theory & Truncated Moment Problems

Bank of citations verified against actual sources during the MomentSheaf
review passes (2026-08-28). Reuse directly; re-verify only if the claim
being cited changes.

## Phelps, Lectures on Choquet's Theorem (2nd ed., LNM 1757, Springer 2001)

Chapter map verified against the book's table of contents (Google Books
snippet, `books.google.com/books?id=CxXcWPyHMkwC`):

| Chapter | Title | Cite for |
|---|---|---|
| 1 | Introduction: the Krein–Milman theorem as an integral representation theorem | KM framing |
| 2 | Application to completely monotonic functions | — |
| 3 | The metrizable case | early maximality-criterion material |
| 4 | The Choquet–Bishop–de Leeuw existence theorem | existence of maximal measures; barycenter representation on non-metrizable compact convex sets |
| 5 | Applications to Rainwater's and Haydon's theorems | — |
| 6 | **The Choquet boundary** | function-system Choquet boundary ∂A; the maximum principle (maximal measures annihilate continuous f with f\|∂A = 0) |
| 15 | Orderings and dilations of measures | the maximality criterion: μ ∈ M_x(K) is maximal in the Choquet order ⟺ μ is an extreme point of M_x(K) |

- **Common miscitation to avoid:** the Choquet boundary is **Ch. 6**, not
  Ch. 10 (a wrong `[Ch. 10]` pin-cite was caught and fixed in review pass 5).
- The Wikipedia "Choquet theory" page gives correct statements of Choquet's
  theorem (compact convex **metrizable** ⇒ representing probability measure
  supported on ext C) and Choquet–Bishop–de Leeuw (non-metrizable ⇒ measure
  vanishing on Baire sets containing no extreme points); Bishop–de Leeuw,
  Ann. Inst. Fourier 9 (1959), 305–331.

## Richter's theorem (truncated moment problems)

- **H. Richter, "Parameterfreie Abschätzung und Realisierung von
  Erwartungswerten", Blätter der Deutschen Gesellschaft für
  Versicherungsmathematik (DGVFM) 3 (1957), 147–162.**
  Verified via Springer link (`link.springer.com/article/10.1007/BF02808864`)
  and multiple citing papers.
- First Richter theorem (finitely-atomic EXISTENCE for solvable truncated
  problems): stated as Thm 2.23 in the Leipzig thesis "The Truncated Moment
  Problem" (Qucosa, `ul.qucosa.de/api/qucosa%3A21536`).
- Second Richter theorem (extreme points are finitely atomic with ≤ N
  atoms, N = number of moment conditions): **provable inline** in ~15 lines,
  so prove it rather than leaning on the citation:
  - atomless part μ₀ ≠ 0 ⇒ non-extreme: the map f ↦ (∫ b̂ f dμ₀)_{b∈B},
    L¹(μ₀) → ℝ^N has infinite-dimensional kernel; η ≪ μ₀ with zero moments
    gives μ ± εη ∈ M(B);
  - > N atoms ⇒ non-extreme: the N × k matrix (b̂(x_i)) has nonzero kernel;
    perturb weights.
  - Mass constraint (1 ∈ B) is already one of the N equations — the bound
    does NOT drop to N−1.

## Curto–Fialkow (secondary reference for the finite-atomic results)

- **R. E. Curto and L. A. Fialkow, "Truncated K-moment problems in several
  variables", J. Operator Theory 54 (2005), no. 1, 189–226.**
  Verified via arXiv:math/0507067 and the journal archive (theta.ro JOT).
- **FABRICATED entry caught:** "Curto & Fialkow, Truncated moment problems:
  an introductory survey, in *The Moment Problem* (G. B. Folland, ed.),
  Springer, 2019" — no such volume exists. Fialkow's real survey is "The
  truncated K-moment problem: a survey" (see `cs.newpaltz.edu/~fialkowl/`);
  when you need the survey, cite it from that preprint rather than
  inventing a venue.

## Tchakaloff

- **V. Tchakaloff, "Formules de cubatures mécaniques à coefficients non
  négatifs", Bull. Sci. Math. 81 (1957), 123–134.** Verified via the
  Encyclopedia of Mathematics entry on the truncated complex moment problem.

## Verification techniques that worked

- Book chapter numbers: Google Books TOC snippet search
  (`books.google.ps/books?id=...`) exposes the full contents listing.
- Journal entries: the journal's own archive (JOT: theta.ro) or arXiv
  metadata (e.g., arXiv:math/0507067 states "J. Operator Theory 54 (2005)").
- Original German-language papers: Springer's archive
  (`link.springer.com/article/10.1007/BF02808864`) confirms exact page
  ranges and journal names.
- Chapter-level citations (`[Ch. 6]{Key}`) are the honest precision level
  when you have verified the TOC but not read the whole book; avoid
  inventing theorem numbers inside chapters.
