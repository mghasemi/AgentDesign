# Truncation Theory — Pass 5: External Reviewer Disposition (2026-08-14)

Follow-up to `truncation-theory-proof-audit.md` (passes 1–4). A detailed external
review arrived with 9 numbered critiques. Disposition: **7 accepted, 1 rebutted,
1 accepted-with-corrected-reason.** Article after pass 5: 14 pp, compiles clean.

## Disposition table (full record in Reports/DSDP_Truncation_Theory_Proof_Audit.md)

| # | Critique | Verdict |
|---|----------|---------|
| I.1 | τ-projection invalid (prolongations ∂^α P_j) | ⚠️ **Strawman** — see rebuttal below; constructive remedy adopted anyway |
| I.2 | ord(fg)=max makes the division formula wrong | ✅ Right conclusion, **wrong stated reason** |
| I.3 | Ritt's basis theorem false as stated (needs radical) | ✅ Correct |
| I.4 | Slice ideal needs differential elimination (Janet/Rosenfeld–Gröbner) | ✅ Correct |
| II.1 | Lemma 2.3 is an obstruction theorem | ✅ Accepted (framing added) |
| II.2 | CODF models non-Archimedean; R ⊭ CODF | ✅ Correct (Remark rem:codf-vs-real added) |
| II.3 | §5 drops x → domain relaxation to full S¹ | ✅ Correct (caveat + remedy added) |
| III.1 | D(c) = O(exp(c₁ ε^{−c₂})) via Nie–Schweighofer | ✅ Accepted (Thm 4.3 updated) |
| III.2 | ν*(d) notation vs fixed ν* | ✅ Accepted (0 occurrences of ν*(d) remain) |

## Rebuttal I.1 (strawman — do not "fix" this by removing τ)

Brouette's Positivstellensatz (thesis Thm 2.4.17: f·g = f^{2m}+h with g,h ∈ T) is
an **identity in the differential polynomial ring K{X}**, NOT an identity modulo
I_ADE. Prolongation terms ∂^α P_j appear only in certificates valid modulo the
ideal. Applying the ring homomorphism τ_{ν*} to a ring identity is therefore
legitimate; the reviewer's computation τ_1(y''−y') = −y' ∉ (y'−y) is correct but
attacks a claim the article never makes (τ(I) ⊆ I^{(ν)} is explicitly disclaimed).
What WAS adopted: Step 2 now states the ring-identity status explicitly, includes
the ADE generators ±P_j in E (noting they vanish in A^{(ν*)}), and **leads with
Putinar/Jacobi directly on the compact lifted set** — the τ-projection is demoted
to a consistency statement.

## Correction I.2 (reviewer's lemma false, conclusion right)

Reviewer claimed ord(fg) = max(ord f, ord g). **FALSE** — differential orders are
additive under products: ord(y'·y') = 2 = 1+1; the max rule holds for SUMS. The
division formula ⌊ν/ord(s_j)⌋ was still wrong for the correct reason: the needed
bound is ord σ_j ≤ ν − ord(s_j) (division under-constrains and at ν = d_j admits
products of order > ν). Def 2.1 now carries the additive rule.

## Durable domain facts verified this pass

- **"Ritt–Woodin" is a fabricated attribution.** No W. Woodin differential-algebra
  paper exists (J. Algebra 1 (1964) 278–297 is not real; W. H. Woodin, b. 1955, is
  a set theorist). Use "Ritt–Raudenbush" (radical differential ideals) / Ritt/Kolchin.
- Ritt's basis theorem: only RADICAL differential ideals are finitely generated;
  K{X} is not differentially Noetherian. Non-radical example: [y²].
- ord(fg) = ord f + ord g; ord(f+g) ≤ max. ord(∂f) = ord f + 1.
- CODF models are non-Archimedean ordered fields; R with standard derivations is
  not a model. CODF's role in the article = soundness of the ADE lift only.
- CGIK Thm 4.2 = Stochel-type (truncated K-frames), NOT a convergence-rate result.
- Nie–Schweighofer's complexity bound is exponential: O(exp(c₁ ε^{−c₂})).
