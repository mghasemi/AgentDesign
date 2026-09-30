---
name: differential-sdp
version: 1.2.0
# CHANGELOG v1.3.0 (2026-08-12):
#   - Project realigned to 4-phase research plan: "Differential-Algebraic Extensions of the Moment-SOS Hierarchy"
#   - Phase I: Theoretical formalization with Ritt-Raudenbush guarantees and differential Archimedean boxing
#   - Phase II: AST compilation engine for automatic ADE generation from transcendental expressions
#   - Phase III: Hybrid monoid-graph dimensionality reduction (inner quotienting + outer chordal decomposition)
#   - Phase IV: Irene integration + numerical validation via Curto-Fialkow extraction
#   - Previous barrier taxonomy preserved as Phase IV validation targets
# CHANGELOG v1.2.0 (2026-07-19):
#   - CGIK (Curto, Ghasemi, Infusino, Kuhlmann 2023) established as PRIMARY theoretical foundation
#   - Semigroup algebra approach documented as the mathematical setting, not just implementation
#   - Brouette CODF repositioned as certificate side (secondary), CGIK as measure-theoretic side (primary)
#   - New DSDP article added: positivstellensatz/dsdp_article.tex + dsdp_article_refs.bib
#   - Core Mathematical Framework restructured around CGIK Theorems 2.7/2.8/4.2
# CHANGELOG v1.1.0 (2026-07-17):
#   - Added Phase C/D findings: function class dominance map, hybrid routing, exponential ADE structural failure
#   - Added Final Barrier Taxonomy with status (cured/partially cured/open)
#   - Added Recommended Strategies per Problem Type (current best configs)
#   - Added Known Dead Ends (approaches confirmed to fail)
#   - Added reference to 2026-07-17 synthesis reports
category: mathematical-research
language: en
input_variables:
- name: focus_topic
  description: Primary research topic of interest (e.g., torus-curve gap, logarithmic ADE encoding)
- name: constraints
  description: Key theoretical constraints to verify
- name: solver_behavior
  description: Specific solver behaviors to analyze and report
triggers:
- /research-differential-sdp
- /dsdp-framework-analysis
description: >
  Orchestrates end-to-end differential-algebraic SDP research sessions by integrating LightRAG, SearXNG, experimental data synthesis,
  theoretical analysis of Putinar's Positivstellensatz extensions to ADE constraints, and mathematical framework documentation.
  Focuses on identifying convergence barriers (Groebner complexity, dynamic range, torus-curve gap) and developing
  novel theoretical extensions for transcendental optimization problems. Configured with user preferences:
    - Full detail preserved for focus topics (Lasserre SDP extension to ADE)
    - Non-focus content summarized aggressively or omitted
    - No API keys/tokens/credentials preserved in outputs
system_prompt_addendum: >
  You are a mathematical research assistant specializing in differential-algebraic SDP relaxations.
  Your primary goal is to synthesize theoretical frameworks for extending Lasserre's hierarchy to transcendental optimization problems via Algebraic Differential Equation (ADE) lifting. Adhere strictly to the following:
    - When analyzing ADE-constrained SDP relaxation barriers, always prioritize the focus topic and preserve full detail
    - For non-focus topics, provide concise summaries or omit details unless explicitly requested by user
    - Never include API keys, tokens, or credentials in any form of output
    - Structure all mathematical proofs and frameworks using formal LaTeX notation with display equations ($$...$$) for standalone formulas
    - When documenting research findings, use clear, precise terminology: 'quotient ring', 'semigroup differential algebras'
  Workflow steps (4-Phase Research Plan):
    **Phase I — Theoretical Formalization:**
      1. Initialize LightRAG queries on differential ring foundations (Ritt-Woodin, Kolchin topology, CGIK framework)
      2. Execute SearXNG searches for differential Positivstellensatz and Archimedean boxing conditions
      3. Formalize the partial differential ring $\mathcal{R} = \mathbb{R}\{x\}$ with commuting derivations $\Delta$
      4. Establish ADE ideal generation, Ritt-Raudenbush finite-generation guarantees, and initial-value symmetry breaking

    **Phase II — Algorithmic Pipeline Architecture:**
      5. Design AST traversal engine for transcendental node identification
      6. Implement variable adjunction with holonomic Lie prolongation (bounded-degree ADE systems)
      7. Auto-lift algebraic invariants (e.g., $u^2+v^2-1$ for trigonometric functions)
      8. Generate point-evaluation initial conditions at regular points

    **Phase III — Dimensionality Reduction:**
      9. Implement inner-step monoid quotient pruning via admissible term orderings on $\Theta$
     10. Compute minimal quotient basis $B_d = \text{supp}(\mathbb{R}[S]/\mathcal{I}_{\le 2d})$
     11. Construct correlative sparsity graph $G=(V,E)$ and perform chordal completion
     12. Block-diagonalize global PSD moment matrix into clique-localized matrices

    **Phase IV — Implementation & Validation:**
     13. Integrate pipeline with Irene's semigroup engine (`grouprings.py`)
     14. Interface block-diagonalized matrices with MOSEK/CVXOPT/SDPA solvers
     15. Extract certified solutions via Curto-Fialkow flat extension theorem
     16. Validate against barrier taxonomy from Phases 1–15 (Groebner complexity, dynamic range, torus-curve gap)
toolset:
- terminal
- skill_view
- search_files
- web_extract
- mcp_lightrag_search
- read_file
- write_file
timeout: 3600
---
# Differential SDP Research Workflow

## Objective
Orchestrate end-to-end research for the **"Differential-Algebraic Extensions of the Moment-SOS Hierarchy"** project. The goal is to generalize Lasserre's SDP hierarchy to transcendental and dynamical systems by:

**Phase I — Differential Ring Formalization:** Embed non-polynomial problems into partial differential rings $\mathcal{R} = \mathbb{R}\{x\}$ with commuting derivations, replacing transcendental functions with ADE-governed auxiliary variables. Enforce the Ritt-Raudenbush guarantee (finite generation of radical differential ideals) and the Differential Archimedean boxing condition for convergence.

**Phase II — AST Compilation Engine:** Build a symbolic engine that parses optimization problem ASTs, identifies transcendental nodes, performs variable adjunction, applies holonomic Lie prolongation to generate bounded-degree ADE systems, lifts algebraic invariants, and auto-generates initial-condition point evaluations.

**Phase III — Hybrid Dimensionality Reduction:** Implement two-stage reduction: (inner) monoid quotient pruning via admissible term orderings on the operator semigroup $\Theta$, yielding minimal basis $B_d = \text{supp}(\mathbb{R}[S]/\mathcal{I}_{\le 2d})$; (outer) correlative sparsity decomposition with chordal completion, block-diagonalizing the global PSD moment matrix into clique-localized matrices.

**Phase IV — Implementation & Validation:** Integrate with Irene's semigroup engine (`grouprings.py`), interface with MOSEK/CVXOPT/SDPA solvers, and extract certified solutions via Curto-Fialkow flat extension. Validate against the barrier taxonomy from Phases 1–15.

## Core Mathematical Framework

### CGIK — Truncated Moment Problem for Commutative Algebras (PRIMARY)

The CGIK paper (Curto, Ghasemi, Infusino, Kuhlmann, J. Operator Theory 90(2), 2023,
arXiv:2009.05115) solves the truncated moment problem for **arbitrary unital commutative
$\mathbb{R}$-algebras** — not just polynomial rings. This is the primary theoretical
foundation for DSDP. Two central theorems:

- **Theorem 2.7 (compact $K$):** If $K \subseteq X(A)$ is compact and the truncated
  subspace $B$ contains a function strictly positive on $K$, then every $K$-positive
  linear functional on $B$ admits a $K$-representing measure.
- **Theorem 2.8 (non-compact $K$):** Requires a weight function $p \in A \setminus B$
  with $\sup |\hat{b}|/\hat{p} < \infty$ and a $K$-positive extension to $B_p$.
  Guarantees a representing measure with support in $K$.

**DSDP application:** The ADE lifted algebra $A/\mathcal{I}$ is a unital commutative
$\mathbb{R}$-algebra. Its character space $X(A/\mathcal{I}) \cong V_{\mathbb{R}}(\mathcal{I})$
is the ADE variety. The CGIK theorems applied to $A/\mathcal{I}$ directly justify the
SDP relaxation: the $K$-positivity condition IS $M_d(y) \succeq 0$. The weight function
$p$ in Theorem 2.8 is the Archimedean polynomial $R^2 - \|x\|^2 - \sum (y_j)^2$.

**Convergence:** CGIK Theorem 4.2 (Stochel analogue) guarantees that solving the
truncated problem on each frame element solves the full moment problem. Increasing
truncation order $d \to \infty$ yields $\tilde{f}^{(d)} \to f^*$.

### Semigroup Algebras and ADE Lifting

The Irene `grouprings.py` module provides commutative semigroup algebras with derivation
support. This is NOT just an implementation detail — it is the mathematical setting:
- $A = \mathbb{R}[x_1,\ldots,x_n]\langle y_1,\ldots,y_m \rangle$ is a semigroup algebra
- ADE relations generate an ideal $\mathcal{I} \subset A$
- The quotient $A/\mathcal{I}$ is the domain for CGIK theorems
- Compactness of $V_{\mathbb{R}}(\mathcal{I})$ determines CGIK Theorem 2.7 vs 2.8 applicability

See the DSDP article: `positivstellensatz/dsdp_article.tex` (25 pages, 2026-07-19).

### Brouette CODF Positivstellensatz (CERTIFICATE SIDE — Secondary)

Brouette (2015) provides existence of differential SOS certificates via CODF theory.
This is the **certificate side** (explicit algebraic representation of positivity),
complementing CGIK's **measure-theoretic side** (existence of representing measures).
The certificate-to-SDP mapping requires degree bounds — resolved 2026-08-14 (the bounds come from the CLASSICAL Archimedean P-satz after the lift, not from Brouette's proof; see the Finite Truncation Theory section below).

### Classical Polynomial Case (Tertiary Reference)
- **Truncated Moment Problem (TMP):** Curto-Fialkow flat extension theorem.

## Key Theoretical Gaps & Research Directions
### 1. Differential Positivstellensatz — Brouette (2015) — RESOLVED (Existence) / Open (Degree Bounds)

**Status:** Existence of differential SOS certificates is **proved** (Brouette 2015, UMONS PhD thesis). Explicit degree bounds remain **open**.

**Key reference:** Quentin Brouette, *"Differential Algebra, Ordered Fields and Model Theory"*, 2015. [Thesis: `https://agif.umons.ac.be/Brouette/Thesis.pdf`] [CIRM slides: `https://www.cirm-math.fr/ProgWeebly/Renc1155/Brouette.pdf`]

Brouette establishes three variants of a Positivstellensatz for **Closed Ordered Differential Fields (CODF)** — the model completion of ordered differential fields (Singer 1978). Each provides a different certificate form for non-negativity of differential polynomials on ADE-constrained sets:

- **Topological (Thm 2.4.3):** If $O \\subseteq W_S^* \\subseteq \\operatorname{cl}(O)$, then $f(\\bar{x}) \\geq 0$ on $W_S \\iff \\exists m, g, h \\in T_S : f \\cdot g = f^{2m} + h$. Transfers Stengle via density of differential tuples.
- **Algebraic (Thm 2.4.17):** If $\\exists$ $T$-convex proper differential ideal, then $f(\\bar{x}) \\geq 0$ on $W_S \\iff \\exists m, p, q \\in T : f^{2m} + p = q f$. Model-completeness proof.
- **Schm\\"udgen (Thm 2.5.4):** If $W_S^*$ compact + $f > q$, then $f \\in T_E$ with $E = S \\cup \\{\\pm X_i^{(j)} + r\\}$ — **finitely generated cone**. This is the certificate that maps to SDP truncation.

**DSDP relevance (7-link chain):** Algebraic variant → existence of certificate [3]→[4]. Topological variant → transfer to lifted space. Schm\\"udgen variant → finite SOS truncation [4]→[5].

**Critical pitfall (Brouette Remark 2.5.5):** $W_S^*$ compact $\\implies W_S$ $d$-differentially bounded, but the **converse fails**: e.g. $S = \\{X, -X, X'+1\\}$ yields $W_S = \\{0\\}$ (bounded) but $W_S^* = \\{0\\} \\times [1, \\infty[$ (non-compact). Always verify $W_S^*$, not just $W_S$.

**Remaining open:** Effective degree bounds for Brouette's own (differential) certificates — his proof gives existence but no quantification. **Resolved for the SDP pipeline (2026-08-14):** the degree bookkeeping does NOT come from Brouette — after the lift at $\nu^* = \max(d_S, d_f, \nu_{\max})$ the certificate is a CLASSICAL Archimedean-Positivstellensatz certificate in $K[\mathbf{X}^{(\nu^*)}]$; quantitative bounds from Nie–Schweighofer (J. Complexity 23(1) 2007) and Schweighofer (J. Complexity 20(4) 2004). Brouette's role: soundness of the ADE lift + certificate existence in the differential ring.

**Verbatim theorems:** See `Reports/DSDP_Rigorous_Argument_Synthesis_2026-07-17.md` §2.3–2.4.

#### Finite Truncation Theory (2026-08-14, audited & corrected same day) — Resolution of Item 2

**Status:** Fully audited and corrected across 4 passes (2026-08-14). Article: `positivstellensatz/dsdp_truncation_theory.tex` (13 pp, compiles clean). **The first draft's key results below were REFUTED by audit — do not cite them.** Corrected architecture:

- **Lemma 2.3 (QM Embedding, corrected):** for fixed $\nu \ge d_S$, $d \ge 0$: $\pi_\nu(T_S^{(\nu)}) \subseteq B_d^{(\nu)} \iff B_d^{(\nu)} = A^{(\nu)} \iff \dim_K A^{(\nu)} < \infty$. *(The draft's "finite Betti numbers in Kolchin topology" condition was fabricated and deleted; proof via the squares-span identity $(a+1)^2-(a-1)^2=4a$.)*
- **Prop 3.2 (corrected):** truncation order is **constant in $d$**: $\nu^* = \max(d_S, d_f, \nu_{\max})$ — lift once, run Lasserre on $K[\mathbf{X}^{(\nu^*)}]$. *(The draft's $\nu^*(d) \le 2d\cdot\nu_{\max}+d_S$ conflated monomial degree with derivative order.)*
- **Thm 2.4 (corrected):** holonomic ⟹ $A^{(\nu)}$ finitely generated with polynomially bounded generating degree; fixed-$f$ certificates project for $2d \ge D(f)$. *(The draft's "holonomic ⟹ truncable, linear $\nu(d)$" is FALSE — $y'=y$ is holonomic yet every slice quotient is a polynomial ring.)*
- **Prop 2.5:** Archimedeanity from **quadratic** boxes $r^2-(X_i^{(\alpha)})^2 \in S$ (direct sum-of-generators computation). Linear boxes $\pm X + r$ only work for the preordering (product) form.
- **Prop 3.4 (corrected):** degree bound $D(f)$ for the projected certificate comes from the **classical** Archimedean P-satz — Nie–Schweighofer (J. Complexity 23(1) 2007), Schweighofer (J. Complexity 20(4) 2004) — NOT from Brouette's proof. *(The draft's $k \le 2^{|E|}(d_f+1)(\delta_f+1)$ was fabricated.)*
- **Thm 4.3 (corrected):** $p_d \uparrow f_{\min}$ via Archimedean P-satz + degree bound $D(c)$; **CGIK Thm 4.2 is the Stochel-type theorem (truncated K-frames), NOT a convergence-rate result.** *(The draft's $\alpha = 2/(n(\nu^*+1)+2)$ "via Pólya" was invented; the `poldrop` reference is fabricated and was deleted.)*
- **Prop (Soundness of the ADE Lift):** solution jets embed into $\tilde K^{(\nu^*)}$; $p_d \le \min_{\tilde K^{(\nu^*)}} \bar f \le f_{\min}$; asymptotic exactness via Brouette's density corollary (thesis Cor 2.4.2).
- **§5 worked example:** harmonic oscillator ($y_1'=-y_2$, $y_2'=y_1$, invariant $y_1^2+y_2^2=1$); $p_1 = 0 = f_{\min}$ exact by flat extension; extracted atom = jet of $(\cos,\sin)$ at 0. Numerically verified.
- **Verified citations:** Brouette = Q. Brouette PhD thesis UMons **Sept 2015**; CODF due to **Singer** (JSL 43(1) 1978); m derivations = **Rivière** (CRAS 343(3) 2006); CGIK = "The truncated moment problem for unital commutative R-algebras", JOT 90:1 (2023) 223–261. Fabricated entries removed: `poldrop`, `jp`, `woodin`, `brouette20`.

**Full failure-mode taxonomy, corrected proofs, and bibliography resolutions:** `references/truncation-theory-proof-audit.md`.

**Vikunja tracking:** Parent task #512, subtasks #513–#516 under project #29.

### 2. Torus-Curve Gap Mitigation
**Goal:** Develop constraints that force SDP moment matrices to concentrate on parametric curves within product manifolds.
- **Kernel Enforcement:** Add constraints based on vanishing ideals of curves (Section 3.1)
- **Moment Conditions:** Enforce known integrals as linear constraints on moments

### 3. Logarithmic ADE Encoding
**Challenge:** Convert differential constraint $y \cdot d_y u = 1$ into polynomial invariant.
- **Approach 1 (Resultant Elimination):** Compute resultant to eliminate derivative generators
- **Approach 2 (Infinite Series Truncation):** Use series approximation with degree truncation

### 4. Extreme Dynamic Range & Log-Monotone Reduction (Phase 9 — Cured)
**Challenge:** When the ADE solution $y = e^{p(x)}$ spans $[e^{-B^2}, e^{B^2}]$ (ratio $e^{2B^2} \sim 10^{14}$ for $B=4$), neither direct ADE lifting nor rescaling by $V_{\max}$ cures the ill-conditioning.
- **Cure:** Log-monotone reduction — when $y$ is a monotone exponential of a polynomial, $\min y \equiv \min \log y = \min p(x)$ collapses to a pure polynomial SDP. Gap $1.6 \times 10^{-7}$ at $d=2$.
- **Boundary KKT:** For $\min p(x)$ with linear partials, KKT stationarity is degree-1 (no Groebner bottleneck). Contrast with degree-3 KKT in Phases 5/7/8.
- **When to apply:** $y = e^{p(x)}$ and objective is monotone in $y$. **When NOT:** $y$ is not exponential-of-polynomial, or objective is not monotone in $y$.

## Experimental Validation Process
### Phase Analysis Protocol:
For each experimental phase (e.g., torus-curve gap, logarithmic ADE encoding, extreme dynamic range):
1. Identify theoretical barriers using LightRAG and web research
2. Formulate novel mathematical extensions based on identified gaps
3. Document findings with formal LaTeX notation for equations
4. Preserve full detail only for focus topics; summarize non-focus content
5. Verify against experimental results from DSDP Phase 1–9

### Known Barriers (as of DSDP Improvement Analysis, 2026-07-16):
1. **Compact-vs-Non-Compact Variety Gap** (ADE Benchmark): Algebraic relations defining **compact** varieties (e.g., $f^2+g^2=1$ for trig) yield near-exact SDP bounds at order 2 (gap ~$10^{-8}$). Relations defining **non-compact** varieties (e.g., $yz=1$ for exponential/hyperbolic lifts) produce loose bounds (55%+ gap) at the same order. Increasing mean certificate depth ($d=1\to2$) does NOT close this gap — the relaxation order $o$ is the bottleneck, not certificate depth. Root cause: the SDP relaxation treats lifted variables as independent subject to algebraic relations, allowing it to explore regions of the variety far from the true function graph. See `references/ade_benchmark_2026-07-15.md`.
2. **Groebner bottleneck** (Phases 5, 7, 8): Degree-3+ KKT in 7+ generators. Cured by coupled oscillatory lift (Phase 8) or log-reduction (Phase 9).
   **Concrete performance boundary (verified Phase 7–8, 2026-07-13):**
   | Config | Result | Time |
   |--------|--------|------|
   | 7g + 1 rel, d=1 | ✅ Success | ~1.0s |
   | 7g + 3 rels, d=1 | ✅ Success | ~2.3s |
   | 7g + 2 rels, d=2 | ✅ Success (slow) | ~103s |
   | 6g + 2 rels, d=2 | ✅ Success | ~37s |
   | 6g + 3 rels, d=2 | ❌ Infeasible (over-constrained) | ~30s |
   | 6g + 1 rel, d=3 | ❌ Hang (>20s) | — |
   | 6g + 3 rels, d=3 | ❌ Hang (>20s) | — |
   **Rule:** `d=2` is the practical ceiling for 6+ generators. 3+ relations at d=2 over-constrains the relaxation. Always start with 6g + 2 rels at d=2 as the baseline viable config.
2. **Dynamic range** (Phase 6): One-sided range $\cosh \in [1, V_{\max}]$. Cured by rescaling.
3. **Torus-curve gap** (Phase 7): Product manifold $\neq$ parametric curve. **Partially cured** — explicit moment fixing on problem variables (x, y) reduces gap from 88.04% → 8.34% at d=2 (exp4-MOM-B). The remaining 8.34% is structural at d=2; requires d=3 to close further.
4. **Logarithmic gap** (Phase 8): $\log(y)$ has no polynomial invariant. **Open.**
5. **Extreme dynamic range** (Phase 9): Two-sided range $e^{2B^2} \sim 10^{14}$. **Cured via log-monotone reduction.**
6. **Manifold-vs-Curve Gap for tan(x)** (Phase 15): Trig encoding $u\cdot c-s=0, s^2+c^2=1$ defines a 3D manifold in $\mathbb{R}^4$ but cannot enforce parametric coupling $u=\tan(x)$ at $d\leq 2$. LB hits box bound, gap >480%. Structural, not numerical — no order increase closes it. Direct ADE encoding ($u' = 1+u^2$) also fails — KKT stationarity is inapplicable when optimum is boundary-constrained.
7. **No Polynomial Invariant for Airy** (Phase 15): $\operatorname{Ai}(x)$ satisfies $y''-xy=0$ but has no algebraic invariant. Lifted variables are free, SDP returns box bound. Gap ~87%. Fundamental limitation for functions without polynomial invariants.
8. **P8 Gap Floor** (Phase 8, 2026-07-16): The 10.73% gap at d=2 with R1+K2 relations is **structural and robust** across all tested strategies: moment fixing, KKT injection, cross-product constraints, monomial ordering, and parallel mode all fail to improve it. Tighter bounds worsen it (54.22%) by clipping the feasible region. Breaking this floor requires d=3 (computationally prohibitive at 300s) or additional ADE-derived algebraic relations.
9. **Exponential ADE Structural Failure** (Phase C/D, 2026-07-17): The ADE $D_x(y) = y$ for $e^x$ creates a quotient algebra that admits spurious points ($y \approx 0, x \approx 10$) even with coupling $yz=1$. Gap 2484% persists at $d = 3, 4$ — this is a **depth-independent structural failure**, not a depth limitation. Cosh ($y+z$ with $yz=1$) is cured at $d \geq 2$ (gap $2.44 \times 10^{-9}$) because the symmetric objective is algebraically well-conditioned. Exp-x² ($y - x^2$) is not — the asymmetric objective allows the relaxation to exploit the non-compact variety.
10. **KKT+ADE Irreducible Instability** (Phase D3, 2026-07-17): Trig KKT ($x^2 + \sin x$) produces 330% underestimates at ALL configurations ($d=1,2,3$, with/without KKT, with/without tight bounds). The ADE quotient algebra itself admits spurious stationary points — this is NOT a KKT+ADE interaction issue. Removing KKT doesn't help.
11. **Manifold-vs-Curve Gap for tan(x)** (Phase D4, 2026-07-17): ADE $D_x(u)=1+u^2$ defines a 2D manifold; true graph $\tan(x)$ is 1D. At $d \leq 4$, LB = -25.0 regardless of ADE relations. NonPOP Chebyshev is the workaround ($\text{gap} \sim 10^{-9}$). Fix requires initial condition encoding $u(0)=0$ as moment constraint.

### Phase C/D: NonPOPSDP vs DSDP-ADE Comparison (2026-07-17)
**Function Class Dominance Map:**

| Function Class | DSDP-ADE | NonPOP SDP | Winner |
|---------------|----------|------------|--------|
| Trigonometric (compact variety) | Excellent ($10^{-7}\\%$) | Poor (400% gap) | **DSDP-ADE** |
| Exponential (non-compact) | Failed (0 optimal) | Good (0.52% gap) | **NonPOP SDP** |
| Algebraic constraints | Excellent ($10^{-9}$) | Excellent ($10^{-9}$) | **Tie** |
| KKT + ADE combined | Poor (330%) | Moderate (7.54%) | **NonPOP SDP** |
| $\tan(x)$ (manifold-vs-curve) | Catastrophic ($10^{17}\\%$) | Excellent ($10^{-9}$) | **NonPOP SDP** |
| Coupled trig+exp | Good (10.73%) | Moderate | **DSDP-ADE** |

**Key Phase D findings:**
- **D1 (Depth extension):** FAILS — increasing $d$ to 3,4 does NOT fix Exp-x² (2484% gap persists). Cosh fails with `1/X2` generator error at all depths (rational objective bug).
- **D2 (Coupled ADE):** CURES Cosh at $d \geq 2$ ($yz=1$ coupling, gap $2.44\times10^{-9}$). Does NOT cure Exp-x².
- **D3 (KKT stabilization):** FAILS — removing KKT or increasing to $d=3$ doesn't fix Trig KKT (330% gap at all configs). ADE constraints themselves produce the underestimate.
- **D4 (Manifold-vs-curve):** UNFIXED — tan ADE returns LB = -25.0 regardless of config. NonPOP also underestimates.
- **D5 (Hybrid routing):** PARTIALLY viable — trig → DSDP-ADE works ($10^{-6}\\%$). Exp → NonPOP works but looser than Phase C (39.33% vs 0.52% — parameter drift issue).

### Infeasibility Triggers (2026-07-16, exp1–exp8):
| Trigger | Severity | Notes |
|---------|----------|-------|
| K1 + K2 combination | **CRITICAL** | Always causes rank/feasibility failure. Never combine. |
| DSDP with diff_map (no algebraic relations) | **HIGH** | Numerical divergence (costs → 10^15). Requires at least one relation to stabilize. |
| d=3 with 7 generators | **MEDIUM** | Timeout at 300s. Reduce generators before attempting d=3. |
| Overly tight bounds on P8 | **LOW** | Clips feasible region, worsens gap from 10.73% → 74.14%. |

### Gap Reduction Strategies (ranked by effectiveness, exp1–exp8):
1. **Explicit moment fixing on (x,y)** — P7: 88% → 8.34% (exp4-MOM-B). Single most effective strategy.
2. **Tighter variable bounds** — P7: 88% → 12.14% (exp1). Harmful for P8 (clips boundary optimum).
3. **Generator reduction** — 5 gens vs 7 gens: 3× speedup with identical solution quality (exp8).
4. **Parallel=True** — 3–4× speedup across all configs (exp8). Always use for $d \geq 2$, 5+ generators.
5. **KKT injection** — Requires tight bounds to be effective alone. No standalone benefit.
6. **Cross-product constraints** — No improvement over baseline (SDP captures implicitly).
7. **Monomial ordering** — Zero impact on solution quality (lex/grlex/grevlex identical).

### Recommended Current-Best Strategies (as of 2026-07-17)
**Per Problem Type — use these as defaults:**
| Problem | Config | Gap | Time | Notes |
|---------|--------|-----|------|-------|
| Pure trigonometric | DSDP-ADE R1+R2+R5, $d=2$ | $10^{-7}$ | 5.6s | Near-exact |
| Pure exponential | NonPOP Chebyshev $d=6$ | 0.52% | 0.14s | Valid LB, fast |
| Cosh/Cosh-x² | Coupled ADE $yz=1$, $d=2$ | $2.44\times10^{-9}$ | 0.55s | Near-exact |
| Log + coupled exp-trig (P8) | R1+K2, $d=2$, original bounds | 10.73% | 4.3s | Structural floor |
| Trig + rational hyp (P7) | exp4-MOM-B: tight bounds + moments on x,y | 8.34% | 8.7s | Best after moment fixing |
| Exponential $e^{P(x)}$, monotone obj | Log-monotone reduction (polynomial SDP) | $1.6\times10^{-7}$ | 0.2s | Always try first |
| Boundary box-vertex optima | Log-reduction + degree-1 KKT | $4.8\times10^{-7}$ | 0.4s | No Groebner bottleneck |
| Coupled oscillator (algebraic) | Both methods (DSDP-ADE or NonPOP) | $10^{-9}$ | <1s | Structurally simple |

### Known Dead Ends (do NOT re-attempt)
| Approach | Why It Fails | Evidence |
|----------|-------------|----------|
| Taylor approximation for global optimization | Local validity fails at domain boundary | All Taylor tests primal-infeasible |
| K1+K2 combination for P8 | Always causes rank/feasibility failure | 5+ independent configs |
| $d=3$ with 7 generators + Parallel=True | Timeout at 300s; file descriptor limits | exp6 consistently times out |
| Direct ADE lift for $y = e^{xt}$ with $B=4$ | Dynamic range $10^{14}$ destroys moment matrix | S1 infeasible at all orders |
| DSDP with diff_map, no algebraic relations | Numerical divergence, costs → $10^{15}$ | exp7 consistently diverges |
| Differential-algebraic elimination for torus-curve | No algebraic relation exists between $\sin t$ and $\operatorname{sech} t$ | Transcendental functions are algebraically independent |
| Removing KKT to fix Trig KKT underestimates | ADE quotient algebra itself produces the underestimate | D3: -KKT configs still give 330% gap |

### Mean Certificate Implementation Pitfalls (Phase 1–4, Q12):
- **Mean cert disabled by default (Q12 fix):** `use_mean_cert=False` is the default. The old `_build_mean_certificate_moments()` enforced `E[Q-P]=0` (moment equality) instead of `Q-P ∈ SOS` (PSD constraint), which over-constrained the relaxation and degraded bounds. A proper PSD fix requires arbitrary PSD blocks on the moment matrix — beyond current `SDPRelaxations`. Keep disabled until Irene supports it. User must opt in explicitly via `DSDPRelaxations(..., use_mean_cert=True)`.
- **PSD guard clause:** $M_{q,p}$ is PSD **iff** $q > p$ (Prop. 2.1). The guard must be `if self.q <= self.p: return []` — NOT `self.p >= self.q`. An inverted guard accepts indefinite parameters and rejects valid PSD certificates.
- **power_ratio type:** `(self.q - self.p) / self.q` produces a float even when mathematically integer (e.g., `1.0`). `expand(expr ** 1.0)` → non-integer exponents → `KeyError` in sympy's `Poly`. **Fix:** `power_ratio = int(round(power_ratio))` must execute unconditionally, not just inside a non-integer conditional.
- **DSDP API:** `DSDPMeanRelaxation` inherits from `SDPRelaxations` — use `dsdp.SetObjective(expr)` with raw sympy expressions. Do NOT use `OptimizationProblem.set_objective()` which requires `SemigroupAlgebraElement`.
- **Valid test parameters:** $q=1,p=0$ (Choi-Lam/SONC path), $q=2,p=1$ (Lemma 6.1, square recovery). Both are integer pairs with $q > p$.
- **AuxSyms vs Generators (Phase 3 pitfall):** `_build_mean_pair(q, p)` returns expressions in `self.AuxSyms` (X1, X2, ...), NOT the original generators (x, y). When verifying mean pair degrees or expanding certificates manually, use `Poly(expr, *dsdp.AuxSyms)` — NOT `Poly(expr, x, y)`. This caused a false assertion failure during Phase 3 verification where Q1, P1 appeared degree-0 because they were checked against wrong variables.
- **Depth hierarchy (Phase 3):** `depth=d` generates $d$ mean pairs $(q+k, p+k)$ for $k=0,\dots,d-1$, then expands $\prod_{k=1}^d (Q_k - P_k)$ into $2^d$ alternating-sign terms. Constraint growth is superlinear: d=1→1, d=2→3, d=3→9 constraints (2 vars). Default `depth=1` preserves Phase 2 behavior.
- **Solver routing (Phase 4):** `_is_posynomial()` and `_is_mixed_sign()` MUST use `cert.free_symbols` for `Poly()` construction, NOT `self.AuxSyms`. The certificate argument may be in original generator space (x, y) or AuxSyms space (X1, X2) depending on caller. Using `self.AuxSyms` unconditionally causes `Poly` to treat the expression as degree-0 constants. **Fix:** `gens = list(cert.free_symbols) or self.AuxSyms` with fallback.
- **GP/SONC backend gap (Phase 4):** `SONCRelaxations` and `GPRelaxations` operate on `SemigroupAlgebraElement` via `OptimizationProblem`, while DSDP uses sympy. There is no `OptimizationProblem.from_sympy()` method. **Current workaround:** GP/SONC routing logs the selection and delegates to SDP. True GP/SONC dispatch requires a sympy→semigroup algebra bridge.
- **Solver routing constants:** `SOLVER_SDP`, `SOLVER_GP`, `SOLVER_SONC` are exported from `Irene.dsdp` for testability. Depth ≥ 2 always routes to SDP regardless of sign pattern (alternating expansion terms).
- **KKT Space Mismatch (Phase 15 bug — FIXED):** `_build_diff_kkt_moments()` returned 0 constraints because `RedObjective` lived in AuxSym space (`X1 - X2`) while `diff_map` keys were original generators (`{x, u, s, c}`). `_leibniz_diff(expr, var)` checks `if expr in self.diff_map` — AuxSyms are never found, so it falls through to `expr.diff(var)` which returns 0 for symbolic AuxSyms. All stationarity conditions were silently dropped. **Fix applied:** (a) Differentiate BEFORE reduction — `_build_diff_kkt_moments()` now calls `self.differentiate(self.Objective)` instead of `self.differentiate(self.RedObjective)`, and iterates `self.OrgConst` instead of `self.Constraints`. (b) Auto-register derivation on `__init__` when `diff_map` is passed via kwargs. VERIFIED: 56/56 tests pass, KKT now returns 2 constraints for tan(x), 3 for Airy.
  **Fix (concrete):** In `dsdp.py` `_build_diff_kkt_moments()` (line ~235–254):
  - Replace `self.differentiate(self.RedObjective, sym)` with `self.differentiate(self.Objective, sym)` — differentiate the original objective BEFORE reduction.
  - Replace `self.differentiate(cnst, sym)` with `self.differentiate(self.OrgConst[i], sym)` — differentiate original constraints, not reduced `self.Constraints`.
  - After differentiation, call `self.ReduceExp(diff_term)` to bring results back to AuxSym space.
  - `self.Objective` (original generator-space expression) is set by `SetObjective()` at `relaxations.py:261`.
  - `self.OrgConst` (original constraint expressions) is populated by `AddConstraint()` at `relaxations.py:275`.
  - See `references/phase15_kkt_fix.md` for code trace and verification.

### ADE-as-Relation: Quotient Ring Encoding (Q12, 2026-07-13)
**Problem:** Legacy DSDP encodes ADE constraints (e.g., $d_x(u) = 1+u^2$) as numerical KKT moment conditions. This produces loose bounds (box bound) because the differential equation is only enforced numerically, not algebraically.

**Solution:** Encode ADE as algebraic relations in the quotient ring. For each generator $g$ with derivative $d_x(g) = \text{expr}$, introduce a fresh symbol $d\_g$ and add relation $d\_g - \text{expr} = 0$ to the Groebner basis.

**Critical pitfall — Groebner variable ordering:** Derivative symbols MUST be prepended to the generator list. Lex-ordered Groebner bases place leading terms first — if state variables precede derivative symbols, `ReduceExp()` cannot substitute derivatives back to polynomial expressions. Verified: `ReduceExp(d_u) = u² + 1` only works when `d_u` is `X1` or `X2` (first in lex order).

**Critical pitfall — Derivative boxing artifact (Q12 fix):** When using `build_ade_relations()`, the expanded generator list includes derivative symbols. If archimedean boxing applies to ALL generators, boxing $d\_u \in [-B, B]$ with ADE $d\_u = 1+u^2$ implicitly forces $u^2 \leq B-1$, a box artifact that destroys bound quality. **Fix:** Pass `original_gens=[x, u]` (domain variables only) to `DSDPRelaxations()` so `_add_archimedean_boxing()` boxes only originals. Without this override, `box_size=4` on tan(x) yields LB=-5.732 (artifact) instead of LB=-3.0 (correct).

**API — `build_ade_relations()`:** Added to `DSDPRelaxations` (L140 of `dsdp.py`). Auto-generates derivative symbols, relations, and reordered generator list from any `diff_map`:
```python
# Correct workflow — box only [x, u], not [d_x, d_u]
tmp = DSDPRelaxations([x, u], diff_map={x: 1, u: 1 + u**2}, verbosity=0)
dsyms, rels, gens = tmp.build_ade_relations({x: 1, u: 1 + u**2})
dsdp = DSDPRelaxations(gens, relations=rels, original_gens=[x, u],
                       archimedean=True, box_size=4.0, verbosity=0)
```

**Benchmark (tan(x), minimize $x - u$ on $[-\pi/3, \pi/3]$):**
| Method | LB | Notes |
|--------|-----|-------|
| Legacy KKT | -4.000 | Box bound (no tightening) |
| ADE-as-relation | -3.000 | 25% improvement, 0 KKT constraints needed |
| ADE-as-relation + KKT | -3.000 | KKT adds no value when ADE is in quotient ring |
| ADE-as-relation, box all gens | -5.732 | **Boxing artifact** — derivative symbols boxed |

**When to use:** Any ADE where the derivative expression is polynomial in the generators (e.g., $\tan(x)$, $\exp(x)$, coupled oscillators). **When NOT to use:** ADEs with non-polynomial derivative expressions (e.g., $\log(y)$, Airy $y'' - xy = 0$ with no algebraic invariant).

### Multi-Derivation Framework (implemented 2026-07-18)

`DSDPRelaxations` now supports multiple independent derivation operators ($D_x$, $D_y$, etc.) for holonomic systems where different generators satisfy different ADEs under different derivations. Key use case: P8 where $D_x$ applies to trig/exp lifts and $D_y$ applies to $\log(y)$'s $y \cdot d_yu = 1$.

**Architecture:** `self.diff_maps: dict[str, dict]` replaces the old `self.diff_map` singleton. Keys are `wrt` strings (`'x'`, `'y'`), values are derivation maps.

**Backward compat (zero breakage):** Single `diff_map={x:1, y:y}` kwarg auto-routes to `diff_maps[first_generator_name]`. All 55 existing tests pass unchanged.

**API:**
```python
# Single derivation (backward compat — unchanged behavior)
dsdp = DSDPRelaxations([x, y], diff_map={x: 1, y: y})

# Multi-derivation via kwarg
dsdp = DSDPRelaxations([x, y], diff_maps={
    'x': {x: 1, y: y},   # D_x: dx/dx=1, dy/dx=y
    'y': {x: x, y: 1},   # D_y: dx/dy=x, dy/dy=1
})
dsdp.set_derivation({u: 1, v: v}, wrt='u')  # register D_u

# build_ade_relations with wrt — symbols prefixed by derivation
dsyms_x, rels_x, gens = dsdp.build_ade_relations({x:1, s:pi*c}, wrt='x')
# → symbols: dx_x, dx_s  (NOT dx_ prefix that would collide)
dsyms_y, rels_y, gens = dsdp.build_ade_relations({y:1, L:v}, wrt='y')
# → symbols: dy_y, dy_L  (no collision with dx_ symbols)

# differentiate respects wrt
dsdp.differentiate(v, u, wrt='u')  # D_u(v) using diff_maps['u']
dsdp.differentiate(u, v, wrt='v')  # D_v(u) using diff_maps['v']
```

**Modified methods** (all new `wrt=None` parameter defaults to first registered derivation):
- `set_derivation(diff_map, wrt=None)` — stores in `diff_maps[wrt]`
- `build_ade_relations(diff_map, prefix="d", wrt=None)` — symbol prefix encodes derivation (`dx_x` vs `dy_x`)
- `differentiate(expr, var=None, wrt=None)` — selects `diff_maps[wrt]`
- `_leibniz_diff(expr, var, dm=None)` — takes explicit `dm` dict parameter
- `_build_diff_kkt_moments(wrt=None)` — passes `wrt` to `differentiate`
- `DSDPKKTRelaxation._build_kkt_stationarity(wrt=None)` — same

**Verification:** `tests/test_dsdp_mean.py` — 55/55 pass. Ad-hoc: 23/23 pass (backward compat, multi-derivation builds, wrt-aware differentiation, product rule, sympy fallback, KKT compat). See `Reports/DSDP_MultiDerivation_Impl_2026-07-18.md`.

**When to use:** Problems with multiple independent derivations (e.g., P8 with $D_x$ for trig/exp and $D_y$ for $\log(y)$). **When NOT:** Single-derivation systems — backward compat path is simpler and tested.

### Adaptive Parallelism Controller (Improvement A, 2026-07-12)
`SDPRelaxations` includes an adaptive controller that replaces manual `Parallel=True/False` tuning:

- **`AdaptiveParallel = True`** enables automatic parallel/serial dispatch based on a scoring heuristic. Default is `False` (backward-compatible).
- **Heuristic scoring** maps problem signals to a decision:
  - Generators ≥ 7: score −2.0 (Groebner overhead per worker)
  - Generators ≥ 5: score −1.0
  - Generators < 5: score +0.5
  - Relations present: score −1.0 (Groebner cost)
  - Estimated basis ≥ 25: score +2.5 (C_α dominates)
  - Estimated basis ≥ 15: score +1.5
  - Max half-degree ≥ 3: score +1.5
  - **Decision:** score ≥ 0 → parallel, score < 0 → serial
- **Timeout fallback:** `SIGALRM` alarm (default 120s) degrades parallel → serial if `pInitSDP()` exceeds `AdaptiveTimeout`.
- **JSON telemetry:** Set `AdaptiveLogPath = "/path/to/log.json"` to record decisions for future tuning.
- **5-gen tuning fix:** Initial heuristic routed 5-gen problems serial (score=−0.5) causing 27× slowdown. Thresholds adjusted so basis bonus (+1.5 for basis≥15) outweighs gen penalty (−1.0 for 5 gens).

**Legacy note:** `Parallel = True` still works when `AdaptiveParallel = False` (default). Never batch-run multiple `Parallel=True` scripts concurrently — CPU saturation slows all of them. Run sequentially with `timeout 600`.

See session report `Reports/improvementA_adaptive_parallelism_2026-07-12_*.md` for benchmark data.

### NonPOPSDP: Approximation-Based Non-Polynomial SDP (2026-07-16)
**Module:** `Irene/nonpopsdp.py` — approximates transcendental functions via Taylor/Chebyshev polynomials, then delegates to `SDPRelaxations` for Lasserre hierarchy solving.

**API:**
```python
from Irene.nonpopsdp import NonPOPSDP, TranscendentalApproximator, taylor_approx, chebyshev_approx
from sympy import Symbol
from math import sin, cos

x = Symbol("x")
approx_map = {
    "sin": {"func": sin, "method": "chebyshev", "domain": (-3.14, 3.14), "degree": 6},
    "cos": {"func": cos, "method": "chebyshev", "domain": (-3.14, 3.14), "degree": 6},
}
npop = NonPOPSDP(x, approx_map, relax_order=2, ball_radius=4.0, parallel=True, verbosity=0)
npop.set_objective(Symbol("sin") + Symbol("cos"))  # CRITICAL: use set_objective(), not direct assignment
lb = npop.solve()
```

**Benchmark: NonPOPSDP vs DSDP-ADE (7 shared test cases):**
| Test | DSDP-ADE gap | NonPOP Chebyshev gap | Verdict |
|------|-------------|---------------------|---------|
| Trig min(sin+cos) | 1.0×10⁻⁸ | 53.6% | DSDP-ADE exact |
| Trig identity | 2.0×10⁻⁸ | Infeasible | DSDP-ADE wins |
| Trig product | 2.0×10⁻⁸ | 12.8% | DSDP-ADE exact |
| Exp lift | -2.14 (underestimate) | +1.52 (39.3%) | NonPOP valid but loose |
| Cosh lift | -4.5 (underestimate) | +1.30 | NonPOP valid but loose |
| tan²-x² | -1.0 (underestimate) | -1.0 (underestimate) | Both fail |
| Trig+KKT | -0.77 (underestimate) | +0.25 (107%) | NonPOP valid but loose |

**Gap decomposition formula:**
$$\text{Non-POP gap} = \underbrace{(\text{lb}_{\text{approx}} - f^*)}_{\text{≈0.75 dominant}} + \underbrace{(\text{lb}_{\text{SDP}} - \text{lb}_{\text{approx}})}_{\text{≈0.0004 negligible}}$$

Approximation error dominates hierarchy gap by 4+ orders of magnitude.

**Critical findings:**
1. DSDP-ADE dominates for trigonometric problems (compact varieties: gap ≤ 2×10⁻⁸)
2. NonPOP SDP bottleneck is approximation error, not hierarchy gap
3. Taylor approximations are unusable — all Taylor tests return primal infeasibility (local series diverge on global domains)
4. NonPOP SDP is 4× faster (mean 0.14s vs 0.59s) — useful as quick fallback
5. Both methods underestimate for exp/cosh/tan (non-compact varieties)

**When to use NonPOPSDP:** Quick lower bounds on non-polynomial problems where DSDP-ADE is unavailable or too slow. **When NOT to use:** When tight bounds matter, or for trigonometric problems (DSDP-ADE is exact).

**Pitfalls:**
- `set_objective()` is required before `solve()` — direct assignment to `objective_expr` raises RuntimeError
- `ball_radius=None` auto-infers from approximation domains (usually sufficient)
- `verbosity=0` suppresses SDP solver output; `verbosity=1` shows hierarchy details

See `references/nonpopsdp_benchmark_2026-07-16.md` for raw data and full comparison tables.

### Focus Topic Priority:
- **Focus Topics (Full Detail):** Lasserre SDP extension to ADE, semigroup-algebra computations, Groebner bases, Phase C/D function class comparison, barrier taxonomy
- **Non-Focus Content:** Summarized aggressively or omitted unless requested by user
- **Reference files:** `references/phase_cd_findings.md` — Phase C/D function class dominance map, D1–D5 results, hybrid routing logic

## Technical Constraints & Preference Handling
- **Credential Preservation:** Never output API keys, tokens, or credentials in any form
- **LaTeX Formatting:** Use formal display math ($$...$$) for all standalone mathematical formulas
- **Terminology:** Employ precise terminology: 'quotient ring', 'semigroup differential algebras'
- **Session Management:** Focus content receives priority; non-focus material summarized aggressively or omitted

## Synthesis Reports (2026-07-17 Archive)

After completing Phases 1–15, exp1–exp8, Phase C/D, and the ADE Benchmark, the DSDP source files were archived to `/home/YOUR-USER/Code/Python/Archive/DSDP/` and three comprehensive synthesis reports were generated:

| Report | Path | Content |
|--------|------|---------|
| Theory & Methodology | `Reports/DSDP_Synthesis_Theory_Methodology_2026-07-17.md` | ADE lifting, Ritt-Woodin, Kolchin, Positivstellensatz, quotient rings, KKT, coupled oscillatory lift, log-monotone reduction, NonPOPSDP comparison, differential-algebraic Positivstellensatz |
| Numerical Experiments | `Reports/DSDP_Synthesis_Numerical_Experiments_2026-07-17.md` | All 15 phases, ADE Benchmark, Phase C/D, exp1–exp8, barrier taxonomy, performance benchmarks, recommended strategies |
| Forward Plan | `Reports/DSDP_Forward_Plan_2026-07-17.md` | 3 open barriers with attack vectors, 4 untested phases, 3 theoretical problems, 8 code TODOs, tiered timeline, 9 open questions, 7 dead ends |
| **Brouette CODF Rigorous Arguments** | `Reports/DSDP_Rigorous_Argument_Synthesis_2026-07-17.md` | Full literature sweep + verbatim Brouette Positivstellensatz theorems (6 variants), 7-link ADE→SDP chain, certificate mapping table, gap analysis |
| **CGIK-Centered DSDP Article** | `positivstellensatz/dsdp_article.tex` | 25-page LaTeX article (2026-07-19). CGIK framework as primary theoretical backbone, semigroup algebra approach, convergence guarantees, 15-phase experiments, barrier taxonomy, function class dominance map. Bibliography: `dsdp_article_refs.bib` (45 entries). |

**When working on DSDP tasks, load these reports first** — they are the authoritative snapshot of project status as of 2026-07-19.
