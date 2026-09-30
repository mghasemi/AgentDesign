# Paper Ingestion Example: Infinite-Dimensional Moment-SOS Hierarchy for PDEs

This is a worked example of the ingestion workflow applied to:
- **Paper:** Henrion, Infusino, Kuhlmann, Vinnikov — "Infinite-dimensional moment-SOS hierarchy for nonlinear partial differential equations" (arXiv:2305.18768)
- **Date ingested:** 2026-07-30
- **Resulting files:** `raw/articles/infinite-dimensional-moment-sos-hierarchy-nonlinear-pdes.md`, `entities/infinite-dimensional-moment-sos-hierarchy.md`

## Extraction Notes

- `pdftotext -layout` produced clean output (75.4 KB, 1279 lines). No pymupdf fallback needed.
- Layout cleanup applied: removed form feeds (`\f`), which appeared as page breaks. Condensed multi-line spacing.
- Equations in the raw article were simplified to plain-text approximations (e.g., `d^2 u/dx^2` instead of proper LaTeX) — the raw file is an archival reference, not a display format.

## Entity Page Structure

The entity page was structured with these sections:
1. **Summary** — orientations the reader (first systematic infinite-dimensional treatment)
2. **Three-Step Approach** — table mapping step → section → description
3. **Key Theoretical Results** — Theorem 1-4 with conditions
4. **Class of PDEs Handled** — mathematical setting in display LaTeX
5. **Moment Hierarchy: Truncation Degrees** — time/algebraic/harmonic
6. **Numerical Results** — table of SDP sizes, accuracy figures
7. **Relevance to DSDP Project** — 6 specific connections with section references
8. **Open Questions** — from the paper

## DSDP Relevance Mapping

| Paper concept | DSDP counterpart | Section in paper |
|---|---|---|
| Occupation measure $\mu_t = \delta_{u(t)}$ | Trajectory measures for ADEs | §3.1 |
| No relaxation gap (Assumption 2) | Flat extension caveat (DSDP §7.3.2) | §3.2 |
| Polynomial operator $F(h) = \sum F_s(h^{\otimes s})$ | ADE-constrained polynomial operators | §3.3 |
| Nuclear space moment problem (Theorem 3) | Differential KKT conditions foundation | §4 |
| Fourier moment truncation hierarchy | Multi-derivation truncation | §5–6 |
| Convergence rate: open problem | Same open problem in DSDP | §6 |

## Table Formatting Pitfall

The initial patch on `index.md` introduced double-pipe `||` artifacts at the start of table rows because the `old_string` included the preceding row's formatting. **Fix:** always check Markdown table rendering after patch edits. The fix was a second targeted patch replacing `||` rows with `|`.

## SHA256 Computation

The raw file frontmatter's `sha256` should hash only the body content (below the closing `---`), not the full file with frontmatter and not the PDF binary.
