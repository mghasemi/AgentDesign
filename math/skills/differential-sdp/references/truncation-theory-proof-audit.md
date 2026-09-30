# DSDP Truncation Theory — Proof Audit & Correction (2026-08-14)

Authoritative record of the audit and rewrite of `positivstellensatz/dsdp_truncation_theory.tex`.
The companion audit report is `Reports/DSDP_Truncation_Theory_Proof_Audit.md`.
**This file supersedes the "Finite Truncation Theory" section of SKILL.md if they ever disagree.**

## 1. What was wrong (failure-mode taxonomy)

The first draft's Lemma 2.3 claimed a three-way equivalence; ALL THREE implications failed.
Six failure modes were found — use these as a checklist for any future DSDP proof:

| # | Failure mode | Detection question | Instance caught |
|---|---|---|---|
| 1 | Hypothesis mismatch | Does every assumption used in the proof appear in the statement? | (iii)⇒(i) used "compactness of K̃" which condition (iii) never stated |
| 2 | Ill-defined host object | Is the object the claim is about actually the right type? | "QM in B_d" where B_d was defined only as a span (vector space), not a ring |
| 3 | Unlinked data | Do all conditions involve the same objects, with the relation stated? | (i) used S, (ii) used only I_ADE, (iii) used K̃ — no stated relation |
| 4 | Citation content mismatch | Does the article's OWN description of a cited theorem match its use? | CGIK 3.1 used for "compact ⟹ Archimedean" but §1.4 described it as Tchakaloff |
| 5 | Missing converse | Does the argument show both inclusions, or just one? | "measures define functionals" showed moment cone ⊆ dual cone only |
| 6 | Internal contradiction | Does the claim contradict another result in the same article on a canonical example? | Lemma (i)⟺(ii) + Prop 2.5 (compact ⟹ embedding) + y'=y example ⟹ contradiction |

**Contradiction probe:** for differential results, test joint consistency on the ADE $y' = y$.
Two statements that jointly force a false conclusion mean at least one is false.

## 2. Corrected Lemma 2.3 (as now in the .tex)

**Machinery (§2.2):** truncation homomorphism $\tau_\nu : K\{\bar X\} \to K[\mathbf{X}^{(\nu)}]$
(annihilates derivatives of order $> \nu$; a ring hom, hence preserves SOS);
slice ideal $\mathcal{I}_{\text{ADE}}^{(\nu)} = \mathcal{I}_{\text{ADE}} \cap K\{\bar X\}_{\le\nu}$;
truncated quotient algebra $A^{(\nu)} = K[\mathbf{X}^{(\nu)}]/\mathcal{I}_{\text{ADE}}^{(\nu)}$;
projection $\pi_\nu : K[\mathbf{X}^{(\nu)}] \to A^{(\nu)}$;
$B_d^{(\nu)} = \pi_\nu(\operatorname{Span}_K\{X^\beta : |\beta| \le 2d\})$ (a subspace — only an algebra when it equals $A^{(\nu)}$).

**Lemma.** For fixed $\nu \ge d_S$, $d \ge 0$, the following are equivalent:
1. $\pi_\nu(T_S^{(\nu)}) \subseteq B_d^{(\nu)}$;
2. $B_d^{(\nu)} = A^{(\nu)}$;
3. $\dim_K A^{(\nu)} < \infty$ (finite colength of the slice ideal).

**Proof pattern:**
- (1)⇒(2): $T_S^{(\nu)}$ contains every square ($\sigma_0 = q^2$, $\sigma_i = 0$), so
  $\Sigma A^{(\nu)2} \subseteq \pi_\nu(T_S^{(\nu)})$. For $a \in A^{(\nu)}$ lift to $\tilde a$ and use
  $(a+1)^2-(a-1)^2 = 4a$ (char 0): both terms lie in $B_d^{(\nu)}$ by (1), so $a \in B_d^{(\nu)}$.
- (2)⇒(3): $B_d^{(\nu)}$ is spanned by finitely many monomial cosets.
- (3)⇒(2): pick monomial cosets forming a $K$-basis, take $2d \ge \max_j |\beta_j|$.

## 3. Corrected downstream chain (coherence fixes forced by the restructure)

- **Thm 2.4:** holonomic ⟹ $A^{(\nu)}$ finitely generated, generating degree $\delta(\nu)$
  polynomially bounded; fixed-$f$ certificate projects into $B_d^{(\nu)}$ iff $2d \ge D(f)$.
  *False claim removed:* "holonomic ⟹ $T_S^{(\nu(d))}\subseteq QM(B_d)$, linear $\nu(d)$" —
  $y'=y$ is holonomic but every slice quotient is a polynomial ring.
- **Prop 2.5 (Archimedean boxing):** quadratic boxes $r^2-(X_i^{(\alpha)})^2 \in S$ give
  $R^2 - \sum(X_i^{(\alpha)})^2 = \sum(r^2 - (X_i^{(\alpha)})^2) \in T_S^{(\nu)}$ directly
  (each summand is a generator with coefficient 1). **Key subtlety:** the module-form cone
  $\{\sigma_0 + \sum\sigma_i s_i\}$ does NOT contain products of generators, so linear boxes
  $\pm X + r$ only yield Archimedeanity for the preordering (product) form.
- **Remark 2.6:** $y'=y$ ⟹ $A^{(\nu)} \cong K[x^{(0)},\dots,x^{(\nu)},y]$ — infinite-dimensional
  at EVERY order, independent of boxing. Compactness gives the certificate in the infinite
  algebra; no single $B_d^{(\nu)}$ contains the full cone. Non-truncability is a property of
  the full cone, not of individual certificates.
- **Thm 3.1:** project certificates via $\tau_\nu \circ \pi_\nu$ — truncation as a RING
  HOMOMORPHISM applied to the whole identity. *Never* "truncate each SOS term to order ν":
  term-wise truncation does not preserve SOS. Hypothesis must be $\bar f > 0$ on the
  truncated lifted set $\tilde K^{(\nu)}$ — positivity on the full lifted variety does NOT
  transfer (points of $\tilde K^{(\nu)}$ need not extend to points of $\tilde K$).
  Step 3 split: finite-order lower bound (CGIK 3.1) vs asymptotic convergence (CGIK 4.2,
  Curto–Fialkow flat extension). Brouette's differential certificate and the truncated
  Schmüdgen certificate coincide after projection; the SDP side is classical Schmüdgen/Jacobi–Putinar.
- **Lemma 4.2:** reverse inclusion via lifting along surjective $\pi_\nu$: lift each
  $q_{j,m}$ to $\tilde q_{j,m}$, set $\tilde\sigma_j = \sum_m \tilde q_{j,m}^2$.
- **Thm 4.5:** no finite-order iff — one-directional implications + asymptotic convergence.

## 4. Brouette citation facts (verified 2026-08-14, final)

- Author: **Quentin** Brouette (UMons). **PhD thesis "Differential algebra, ordered fields and model theory", Université de Mons, September 2015** (verified from thesis title page; https://agif.umons.ac.be/Brouette/Thesis.pdf). Ch. 2 "Stellensätze": §2.4 Positivstellensatz (topological 2.4.1 / algebraic 2.4.2), §2.5 Schmüdgen's theorem. Earlier published paper: "A nullstellensatz and a positivstellensatz for ordered differential fields", Math. Log. Quart. 59(3) (2013) 247–254.
- **CODF was introduced by SINGER** (J. Symbolic Logic 43(1) 1978, 82–91) — NOT Marker. The m-commuting-derivations theory (m-CODF) is **Cédric Rivière**, C. R. Math. Acad. Sci. Paris 343(3) (2006) 151–154.
- **Algebraic P-satz (Thm 2.4.17):** $f \ge 0$ on $W_S$ ⟺ $\exists m, p, q \in T: f^{2m} + p = qf$,
  under a $T$-convex proper differential ideal hypothesis. NOT compactness, NOT $f > 0$.
- **Topological P-satz (Thm 2.4.3):** $f\cdot g = f^{2m} + h$, $g, h \in T_S$.
- **Schmüdgen-type (Thm 2.5.4):** compact $W_S^*$ + $f > q$ ⟹ $f \in T_E$, $E = S \cup$ boxes.
- **Density of differential points (Cor 2.4.2):** in CODF models the set of differential points is dense in the truncated space — the tool for soundness/asymptotic exactness of the lift.
- Do NOT mix these forms in one theorem; they have different hypotheses.

## 5. Bibliography flags (web-verified 2026-08-14) — ALL RESOLVED in passes 3–4

| Entry | Verdict | Final action |
|---|---|---|
| `poldrop` "D. Póldrop, A note on Pólya's theorem" | FABRICATED — no such author/paper | **Deleted** (bibitem + its only citation, the old Thm 4.3 proof). Replaced by Nie–Schweighofer (J. Complexity 23(1) 2007, 135–150) and Schweighofer (J. Complexity 20(4) 2004, 529–543) — both real, added. |
| `jp` "Jarnicki & Pólak" Bull. Acad. Polon. 31 (1983) | No trace | **Deleted**; Archimedean ⟺ compactness now cited to Wörmann via Marshall + Schmüdgen |
| `woodin` "W. C. Woodin, J. Algebra 1 (1964) 278–297" | No such paper; W. H. Woodin (b. 1955) is a set theorist | **Deleted**; §1.1 now cites Ritt/Kolchin/Marker. "Ritt–Woodin" no longer appears anywhere in the file |
| `brouette17` "S. Brouette, JSL 82(3) (2017)" | Initial wrong, venue unconfirmed | **Corrected** to Q. Brouette PhD thesis, UMons (Sept 2015); pin-cites (Def 2.3.1, Thm 2.5.4, Rem 2.5.5, Cor 2.4.2) match thesis chapter structure |
| `brouette20` "Ann. Mat. Pura Appl. 199 (2020)" | Unverifiable | **Deleted**; m-CODF cited to Rivière CRAS 343(3) (2006) 151–154 |
| `marker` "IHES Publ. Math. 62 (1985) 85–104" | Venue wrong | **Corrected** to Model Theory of Fields, Lecture Notes in Logic 5, 2nd ed., A K Peters (2006); `singer` (JSL 43(1) 1978) added for CODF |
| Kolchin "Thm II.1.3 / Cor II.2.5", Prestel "Thm 3.4" pin-cites | Fabricated pin-cites | Removed with the Lemma 2.3 rewrite (pass 2); both books re-cited legitimately in pass 4 (Kolchin §1.1, Prestel §1.3) |
| CGIK pin-cites (2.7/3.1/4.2) | Verified against arXiv:2009.05115 | **Thm 3.1 = generalized Tchakaloff** (correct usage); **Thm 2.7 = compactness/representation criterion** (correct); **Thm 4.2 = Stochel-type truncated-K-frame theorem — NOT a convergence rate** (the old §1.4/Thm 4.3 attribution was wrong; Thm 4.3 re-proved). Bibitem fixed: "The truncated moment problem for unital commutative R-algebras", J. Operator Theory 90(1) (2023), 223–261; co-author "S. Kuhlmann" |

## 6. Verification workflow that worked (LaTeX rewrite)

1. Ordered multi-edit via `execute_code` + `hermes_tools.patch` (sequential, deterministic).
2. Two-pass `pdflatex -interaction=nonstopmode -halt-on-error`; grep log for
   `undefined|multiply defined` refs — must be empty.
3. pymupdf spot-check: probe for NEW theorem text in the PDF (not just error count).
4. Stale-notation sweep with `search_files`: **regex escaping** — a literal backslash needs
   `\\` in the pattern; `\p` is a Unicode-property class in Rust regex (silent zero-hit trap).
   Always include a known-positive control probe to validate the pattern.
5. `execute_code` sandbox cwd ≠ session cwd — use ABSOLUTE paths for `fitz.open`/file ops
   (search_files resolves relative to session cwd, but Python stdlib does not).

## 7. Passes 3–4 (2026-08-14): all open items CLOSED

- **Prop 3.2 (fixed):** $\nu^* = \max(d_S, d_f, \nu_{\max})$ — constant in $d$; $\tau_{\nu^*}$ is a ring hom on ALL of $K\{\bar X\}$, annihilates higher jets, so no certificate term forces a larger order. Pipeline = "lift once, then run Lasserre". Old formula $2d\cdot\nu_{\max}+d_S$ deleted.
- **Prop 3.4 (fixed by reframing):** the SDP certificate is a CLASSICAL Archimedean-P-satz certificate in $K[\mathbf{X}^{(\nu^*)}]$ — degree bookkeeping never came from Brouette's proof (why no bound could be extracted). Qualitative $D(f)$ from Jacobi–Putinar; quantitative via Nie–Schweighofer (module form) / Schweighofer (Schmüdgen form). The fabricated $k \le 2^{|E|}(d_f+1)(\delta_f+1)$ deleted.
- **Thm 4.3 (fixed):** $p_d \uparrow f_{\min}$ via the Archimedean P-satz + $D(c)$; CGIK 4.2 correctly identified as the Stochel-type theorem (NOT a rate). Invented $\alpha$ and the Pólya/`poldrop` justification deleted.
- **§4.2:** $\dim M_d = \binom{N_{\nu^*}+d}{d}$, $N_{\nu^*} = n\cdot\#\{\alpha : |\alpha| \le \nu^*\}$; stale conditions $k\cdot d_f \le \nu$, $k\cdot\delta_f \le d$ removed; semigroup-algebra identification + reduction-phase pointer (monoid pruning/chordal, `gha-dsdp`) added.
- **Prop `prop:soundness` (Soundness of the ADE Lift, §3):** jets embed into $\tilde K^{(\nu^*)}$; $\min_{\tilde K^{(\nu^*)}} \bar f \le f_{\min}$; $p_d \le \min_{\tilde K^{(\nu^*)}} \bar f \le f_{\min}$; asymptotic exactness via Brouette Cor 2.4.2 (density of differential points). Thm 3.1 now points to it.
- **§5 worked example (harmonic oscillator):** $y_1'=-y_2$, $y_2'=y_1$, invariant $y_1^2+y_2^2=1$; $\nu^*=1$; moment matrix $M_1(y)$ displayed; $p_1 = 0 = f_{\min}$ exact by flat extension; atom $(1,0,0,1)$ = jet of $(\cos,\sin)$ at 0. Numerically verified (candidate $M_1$ eigenvalues $[0,0,2]$; 50k-point feasibility search confirms $a \le 1$).

**Numerical-verification note:** the execute_code sandbox interpreter may lack a working numpy (version mismatch); run numeric checks via `terminal` with the project venv (`Irene/.venv/bin/python3`) instead.

**Remaining (optional only):** numerical validation at scale through Irene's DSDP pipeline; a 2-derivation worked example; quantitative refinement of the density/exactness argument.
