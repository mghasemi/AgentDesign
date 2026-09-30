# Proof-Audit Worked Instance: MomentSheaf Flagship Claims (2026-08-31)

Two audit targets suggested by a reviewer's closing recommendation
("audit Prop 6.3 and Thm 7.6 before submission") — BOTH contained
genuine gaps the reviewer did not flag. The reviewer's 14 positioning
items, by contrast, were mostly already-satisfied or terminology fixes.
Lesson: the pre-submission audit of a paper's ORIGINAL mathematics is
where defects concentrate; reviewed-adjacent positioning claims have
usually been through several rounds already.

## Gap 1 — Prop 6.3 (stalk extreme rays): missing mixed-atom case

**Claim:** under first countability at $x$,
$\operatorname{ExtRay}(\mathcal M_{+,x}) = \mathbb R_{\ge0}[\delta_x]_x$.

**Hole:** the published proof only treated germs with $\mu(\{x\})=0$
(the annulus decomposition $E=\bigcup_n(W_{2n}\setminus W_{2n+1})$,
$\nu_1=\chi_E\mu$, $\nu_2=(1-\chi_E)\mu$). A germ with a NONTRIVIAL
atom $m>0$ at $x$ AND a nonzero residual germ was never shown
non-extreme.

**Repair (add before the atomless case):** decompose
$\mu = m\delta_x + \mu_0$ with $\mu_0(\{x\})=0$.
- If $m>0$ and $[\mu_0]_x \ne 0$: $[\mu]_x = m[\delta_x]_x + [\mu_0]_x$
  is a sum of two positive germs that are NOT proportional —
  $[\mu_0]_x = c\,[\delta_x]_x$ forces $0 = \mu_0(\{x\}) = c$, i.e.
  $[\mu_0]_x=0$, contradiction. Not extreme.
- If $[\mu_0]_x = 0$: $[\mu]_x = m[\delta_x]_x$, a positive multiple of
  the Dirac ray.
- Remaining case $\mu(\{x\})=0$: the existing annulus argument.

The case analysis is now exhaustive. Audit pattern: **enumerate the
cases the proof actually treats versus the cases the claim asserts** —
here "every germ" vs. the two implicitly assumed (pure-atom,
atomless).

## Gap 2 — Thm 7.6(2) (Galois descent correspondence): three silent holes

**Claim:** $\mu \mapsto \tilde\mu$ bijects $\mathcal M_L(K)$ with the
$G$-invariant representing measures of $L_{\mathrm{Tr}}$ on $K'$,
inverse $\mu' \mapsto \pi_*\mu'$.

**Holes and repairs:**

1. **Compactness of $K'$ silently used** ($C(K')$, Riesz, weak-$*$ on
   $\mathcal M(K')$ all require it) but never proved. Repair: $A'$ is a
   finite $A$-module (Galois algebra def), so every $b'\in A'$ satisfies
   a monic polynomial over $A$ (determinant trick); for
   $\alpha'\in K'$, $\alpha'(b')$ is a root of the coefficient-wise
   $\alpha$-evaluated polynomial, giving a uniform bound per $b'$;
   $K' = \pi^{-1}(K)$ is closed in $\mathbb R^{A'}$ and contained in a
   compact product of bounded intervals.
2. **Continuity of the averaged integrand unproved.** Repair: define
   $g_f(\alpha) = \frac1{|G|}\sum_\sigma f(\sigma\tilde\alpha)$
   (well-defined: fibers are single orbits by the fiber lemma);
   $\bar f(\alpha') = \frac1{|G|}\sum_\sigma f(\sigma\alpha')$ is
   continuous $G$-invariant on $K'$, and $K'/G \cong K$ is a
   HOMEOMORPHISM (continuous surjection between compact Hausdorff
   spaces with orbit fibers) — so $g_f$ descends continuously. Then
   $\int f\,d\tilde\mu := \int g_f\,d\mu$ defines $\tilde\mu$ by
   Riesz, and $\tilde\mu$ is $G$-invariant since $g_{f\circ\tau}=g_f$.
3. **Pushforward check applied the defining formula to $\chi_E$**
   (discontinuous — the formula is only valid for $f \in C(K')$).
   Repair: Radon measures on a compact space are equal iff they agree
   on $C(K)$; test $\pi_*\tilde\mu = \mu$ against $h \in C(K)$ via
   $g_{h\circ\pi} = h$ (each orbit point lies in the same fiber). The
   converse direction $\widetilde{\pi_*\mu'} = \mu'$ similarly runs
   through $\int f\,d\widetilde{\pi_*\mu'} = \int \bar f\,d\mu'
   = \int f\,d\mu'$ using $G$-invariance of $\mu'$.

Audit pattern (**construction used outside its defining hypotheses**):
list every object the proof constructs; for each, check whether the
place it is USED satisfies the hypotheses under which it was DEFINED.
Here the measure was defined by a continuous-$f$ formula and then
queried at a discontinuous $f$.

## Verification pattern

- Both repairs went into the SAME atomic edit batch as the review's
  14 positioning items (21 edits, assert-before-write; one anchor
  diagnosed via `sed -n | cat -A` after a line-wrap mismatch, then the
  whole batch re-run).
- Residual sweep false positive: "covariance distinction" contains
  "variance distinction" — use
  `re.findall(r'(?<!co)variance distinction', ...)` (see SKILL.md
  semantic-purge pitfall on substring-superset false positives).
- Environment demotion (thm:persistence theorem → corollary): prose
  refs retargeted in-batch; PDF probe
  `Corollary 7\.\d+ \(Persistence` confirmed the printed name.
- 3-pass pdflatex (inline bibliography), 0 warnings / 0 undefined,
  pymupdf positive+negative probes; disposition at
  `reports/Review_08_disposition_20260831.md` committed with the
  manuscript (MomentSheaf commit 7117213).
- Disposition convention for this project:
  `reports/Review_NN_disposition_YYYYMMDD.md`, per DOX.md rule 3.

## Generalizable rules

1. A "correspondence via an explicit formula" theorem needs: the host
   space's topology validated (compactness), the formula's domain
   respected (continuity), and BOTH directions proved inverse — not
   just asserted.
2. Case-based classifications ("exactly the germs such that...") must
   be checked against a complete case partition of the ambient object,
   not against the cases the existing proof happens to handle.
3. When a reviewer says "the rest is well-positioned; audit claims X
   and Y before submission" — treat X and Y as suspected-broken, not
   as rubber stamps. In this instance both were broken, in ways the
   reviewer's own report did not detect.
