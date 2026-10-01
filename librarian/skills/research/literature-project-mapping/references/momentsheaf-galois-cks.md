# MomentSheaf — Galois Descent & CKS 2008 Connection Map (2026-09-01)

Session snapshot for future MomentSheaf work. Manuscript: `MomentSheaf/manuscript/momentsheaf_article.tex`. Vikunja project #27. Phase 5 (#428–#432) and correspondence umbrella #712 are DONE; the open work lives in the correspondence tracks below.

## Manuscript §7 "Galois Descent and Cohomology" (tex lines ~1721–2230)
- Def 7.1 finite G-Galois algebra: A' f.g. projective A-module of rank |G|, (A')^G = A, normal-basis isomorphism (line 1740)
- Thm 7.4 Descent for real spectra: π: Sper(A') → Sper(A) continuous surjection under the formally-real-over-every-ordering hypothesis; fibers = G-orbits (Marshall Thm 3.4); Sper(A) ≅ Sper(A')/G (line 1778)
- Rem 7.5: formally-real hypothesis necessary — R ⊂ C fails (Sper(C) = ∅)
- Thm 7.6 Descent of moment functionals: P(K) ≅ P'(K')^G via L ↦ L∘(1/|G|)Tr, inverse L' ↦ L'|_A; requires every α ∈ K extends to a character of A' (line 1872)
- Cor 7.7 Measure descent: μ' descends iff G-invariant; μ = π*μ' (line 1996)
- Rem: descent is elementary (trace pairing), NOT quasi-coherent sheaf descent (line 2017)
- Thm 7.9 Descent of determinacy: unique G-invariant representing measure of L_Tr ⇒ L determinate (line 2056)
- Cor 7.10 Persistence of indeterminacy under finite extensions (line 2081); Rem 7.12 Stieltjes: no splitting field among finite extensions (line 2100)
- Def 7.11 Galois cohomology on SIGNED measures only: H^n(G, M(K')) = Ext^n_{Z[G]}(Z, M(K')); positive cones P'(K'), M_+(K') are NOT Z[G]-modules (line 2120)
- Rem: Hochschild–Serre spectral sequence = possible framework only, not asserted (line 2151)

## Open problems (sec:open, lines 2747–2849)
Galois-relevant: (1) infinite Galois extensions (profinite G, H^1_cont); (4) extension to Sper(A); (6) converse of determinacy / splitting fields (converse FALSE among finite extensions); (9) Hochschild–Serre invariants; (10) cohomological classification of families of representing measures; (11) positive Galois descent data — correct cohomological home for positivity-constrained data (candidates: non-abelian H^1 à la Giraud, cohomology of ordered G-modules, torsor descent for convex cones).

## Vikunja #27 correspondence structure (verified 2026-09-01)
- #712 Improvements from 2026-08-31 correspondence (done) → children: #713 (Track A), #719 (Track B), #723 (Track C), #727 (audit), #728 (literature)
- Track A #713 → #714–#718. A4 counterexample RESOLVED 2026-08-31: conjecture FALSE (βN free-ultrafilter); correct statement is the max-ideal criterion in B(X)
- Track B #719 → #720–#722: promote affine-slice determinacy formula M_L(K) = μ0 + (V ∩ (M_+(K) − μ0)) to a proposition; reframe §5.3
- Track C #723 → #724–#726: positive Galois descent — audit cone-not-module wording (C1), moment-problem vs descent parallel table (C2), open-problem formulation (C3)
- #727 final proof-level audit (Prop 6.3, Thm 7.6) before submission — has CKS positioning checklist item
- #728 Literature: Cimprič–Kuhlmann–Scheiderer 2008 — relation to §7 Galois descent (created 2026-09-01; full 6-connection analysis in its description)

## CKS 2008 connection (arXiv:0808.0034, math.AG, 2008-08-01)
Wiki entity: `entities/cimpric-kuhlmann-scheiderer-equivariant-moment-2008.md` (also updated 2026-09-01 with the MomentSheaf section). Six connections:
1. Same descent principle, dual direction: Thm 7.6(1) P(K) ≅ P'(K')^G vs CKS Thm 4.1 Q(T^G) = Q(T)^G — "G-invariant moment data on the big ring = moment data on the fixed subring". CKS = compact-reductive-group instance; MomentSheaf = finite-Galois-algebra instance.
2. Same averaging mechanism: CKS Prop 2.1 Haar-averages over compact G(R); MomentSheaf uses (1/|G|)Tr and the averaged measure formula (Cor 7.7(2)). Feeds Problem (1): profinite G is compact, Haar exists.
3. CKS §5 finite solvability (truncated conditions checked inside A^G) ↔ MomentSheaf K-frame {B_ω} / Thm 7.9 sufficiency side.
4. CKS Thm 4.1–4.2 = closest published positivity-descent results, but SINGLE-OBJECT certificate descent only — Problem (11) family/positivity-constrained classification stays open.
5. Hypothesis parallel: compact G(R) + Archimedean ↔ finite Galois + character-extension; failures parallel (non-compact ⇒ no averaging; R ⊂ C ⇒ π not surjective).
6. CKS is NOT Galois descent: A^G ⊂ A is a subring (Hilbert finite generation), not a finite extension with fixed ring A — "equivariant sibling" of §7, not a special case.

## Pending manuscript actions (staged in #728, NOT executed)
(a) cite CKS 2008 in §7 as related work + bibliography entry; (b) one sentence in Problem (11) naming CKS Thm 4.1–4.2 as the compact positive-descent precedent; (c) optional Thm 7.9 sufficiency remark via CKS §5; (d) make "CKS ≠ Galois descent" explicit. Each edit: user-latex-style pass + claims ledger update.
