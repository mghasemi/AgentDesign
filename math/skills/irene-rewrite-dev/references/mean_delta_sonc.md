# MeanDeltaSONC — Mean Polynomial vs SONC Gap Analysis

Created 2026-08-11. Project at `/home/YOUR-USER/Code/Python/MeanDeltaSONC/`.
Reports: `/home/YOUR-USER/Code/Python/Reports/MeanDeltaSONC_2026-08-11*.md`.

## Research Question

Find mean polynomials $M_{q,p}(Y,w)$ (monomial generators $Y$, positive weights $w$)
that are nonnegative but **not SONC**.

## Key Findings

### Corrected: $M_{4,2}((x,x^3),(1,1))$ IS a Circuit Polynomial

After mathematical analysis, this polynomial IS a circuit polynomial (hence SONC):

$$M_{4,2}((x, x^3), (1,1)) = 4x^4 - 8x^8 + 4x^{12}$$

- Support: $\{4, 8, 12\}$ — three points in $\mathbb{R}^1$ = circuit ($n+2 = 3$)
- Affine relation: $8 = \frac{1}{2} \cdot 4 + \frac{1}{2} \cdot 12$, so $\lambda_4 = \lambda_{12} = \frac{1}{2} > 0$
- AM-GM condition: $|c_8| = 8 \leq (4/0.5)^{0.5} \cdot (4/0.5)^{0.5} = 8$ — **holds with equality**

The earlier SONC GP infeasibility was a **false negative** — the GP solver cannot handle
the exact AM-GM boundary numerically. See pitfall below.

### Collinear-Support Theorem (genuine non-SONC proof)

**Theorem**: If a nonnegative polynomial $f \in \mathbb{R}[x_1,\ldots,x_n]$ has Newton
polytope of dimension $d < n$, and $f$ has $> d+2$ terms, then $f$ is NOT SONC.

**Proof (n=2, d=1 case — all exponents on a line)**:
1. A 2D circuit polynomial requires 3 affinely independent vertices (non-degenerate triangle).
2. If all exponents of $f$ are collinear, any circuit in a SONC decomposition must
   include at least 1 vertex OFF the line (otherwise 3 collinear vertices don't form a simplex).
3. Each circuit's vertex coefficients are strictly **positive**.
4. Off-line vertex contributions from different circuits are all positive → **cannot cancel**
   to zero (as required, since $f$ has zero coefficient at off-line exponents).
5. Contradiction → no SONC decomposition exists. ∎

**Application**: $M_{q,q-1}((x,y),(1,1))$ for even $q \geq 4$:
- All exponents lie on $e_x + e_y = \deg(M)$ (collinear)
- Number of terms $= 2q-1 \geq 7 > 3$ (too many for single circuit)
- Therefore provably NOT SONC.

Generalizes to $n$ dimensions: support in $(n-1)$-dim hyperplane + terms $> n+1$ → non-SONC.

### Global Nonnegativity Domain Restriction

$M_{q,p}$ is **globally** nonnegative (on all of $\mathbb{R}^n$) only when BOTH
$c/p$ is even AND $q$ is even. Otherwise it's only nonnegative on $\mathbb{R}_{\geq 0}^n$.

| $(q,p)$ | $c/p$ | $q$ even? | Globally NN? | Verified (1000 pts) |
|---------|-------|-----------|-------------|---------------------|
| (2,1) | 2 (even) | ✓ | ✓ | 0 neg |
| (3,2) | 3 (odd) | ✗ | ✗ | 284 neg |
| (4,3) | 4 (even) | ✓ | ✓ | 0 neg |
| (5,4) | 5 (odd) | ✗ | ✗ | 216 neg |
| (6,5) | 6 (even) | ✓ | ✓ | 0 neg |

**Implication**: For SONC membership, non-globally-NN cases ($M_{3,2}$, $M_{5,4}$) are
trivially non-SONC (all SONC polynomials must be globally nonnegative). Only globally-NN
cases need the collinear-support analysis.

### Computational Sweep Results

| $(q,p)$ | Terms | Collinear | Globally NN | SONC GP | Verdict |
|---------|-------|-----------|-------------|---------|---------|
| (2,1) | 3 | ✓ | ✓ | Feasible | SONC (circuit $(x-y)^2$) |
| (3,2) | 5 | ✓ | ✗ | Infeasible | Trivially non-SONC (not globally NN) |
| (4,3) | 7 | ✓ | ✓ | Infeasible | **Provably non-SONC** (collinear theorem) |
| (5,4) | 9 | ✓ | ✗ | Infeasible | Trivially non-SONC (not globally NN) |
| (6,5) | 11 | ✓ | ✓ | Infeasible | **Provably non-SONC** (collinear theorem) |

### General Pattern

| Condition | SONC? | Reason |
|-----------|-------|--------|
| $q=2$, any monomials with 3-term expansion | ✓ | Single circuit polynomial |
| $q$ even, $q \geq 4$, 2+ variables | ✗ | Collinear-support theorem |
| $q$ odd, any $p$ | ✗ | Not globally nonnegative → trivially non-SONC |
| $(q,p)$ with $|q-p| \geq 2$, simple monomials | ✗ | Too many expansion terms |

**Monomial parity is NOT the driver** — both odd and even monomials can produce
SONC-feasible or SONC-infeasible forms. The key determinants are:
1. Support dimension (collinear/coplanar vs full-dimensional)
2. Number of expansion terms (circuit requires exactly $n+2$)
3. Global nonnegativity domain (evenness of $q$ and $c/p$)

---

## Mean-SOS Conjecture (2026-08-11)

### Computational Evidence

$M_{q,q-1}(x_1,\ldots,x_n)$ with even $q$ is SOS for all tested configurations.
All SDP relaxations are feasible at order $\lceil \deg/2 \rceil$ with gap $< 10^{-8}$.

| $M_{q,p}$ | $n$ | deg | Globally NN? | SOS? | SONC? |
|-----------|-----|-----|-------------|------|-------|
| $M_{2,1}$ | 2 | 2 | ✓ | ✓ | ✓ |
| $M_{4,3}$ | 2 | 12 | ✓ | ✓ | ✗ |
| $M_{6,5}$ | 2 | 30 | ✓ | ✓ | ✗ |
| $M_{2,1}$ | 3 | 2 | ✓ | ✓ | ✓ |
| $M_{4,1}$ | 3 | 4 | ✓ | ✓ | ✓ |
| $M_{6,1}$ | 3 | 6 | ✓ | ✓ | ✗ |
| $M_{8,1}$ | 3 | 8 | ✓ | ✓ | ✗ |
| $M_{4,3}$ | 3 | 12 | ✓ | ✓ | ✗ |
| $M_{4,3}$ | 4 | 12 | ✓ | ✓ | ✗ |
| $M_{4,3}$ (1,2,3) | 3 | 12 | ✓ | ✓ | ✗ |
| $M_{4,3}$ (1,10,1) | 3 | 12 | ✓ | ✓ | ✗ |

### Key Observations

1. **2 variables**: PSD = SOS (Hilbert). All globally NN mean polynomials in 2 vars are SOS.
2. **3+ variables**: All tested globally NN mean polynomials are SOS at the first
   Lasserre relaxation order — including degree 30, non-uniform weights up to ratio 10:1.
3. **No PSD-but-not-SOS found**: The search for non-SOS candidates must continue
   (higher degrees, non-power-mean monomials, or it may be a theorem that all such
   $M_{q,p}$ are SOS).

### Proof Sketch (5 parts)

Full formalization: `MeanDeltaSONC/notes/mean_sos_theorem_proof_sketch.md`.

**§1 — General Definition**

$M_{q,p}(x) = W^{\,c/p - c/q} \cdot P_q(x)^{c/q} - P_p(x)^{c/p}$ where
$c = \operatorname{lcm}(q,p)$, $W = \sum w_i$, $P_k(x) = \sum w_i x_i^k$.

For $p=q-1$: simplifies to $M_{q,q-1} = W \cdot P_q^{q-1} - P_{q-1}^q$.

**§2 — $q=2$ (PROVED)**

$M_{2,1} = \sum_{i<j} w_i w_j (x_i - x_j)^2$ — explicit SOS with $\binom{n}{2}$ squares.

**§3 — $n=2$ (PROVED)**

$M_{q,q-1}(x_1,x_2)$ is a nonnegative binary form → SOS by Hilbert's theorem.

**§4 — Conjectural Lemma 2 (OPEN)**

There exist SOS forms $R_{ij}(x)$ such that:

$$M_{q,q-1} = \sum_{i<j} w_i w_j \cdot (x_i^{q-1} - x_j^{q-1})^2 \cdot R_{ij}(x)$$

For $q=2$, $R_{ij} \equiv 1$. For $n=2$, the quotient $M/(x_1^{q-1}-x_2^{q-1})^2$ is SOS.
For $n \geq 3$, the challenge is to resolve overlap between pairs into a consistent
global decomposition. This is the **unique remaining gap**.

---

## PITFALL — SONC GP false negatives at AM-GM boundary

The SONC geometric program can return **infeasible** for polynomials that ARE
actually circuit polynomials (hence SONC). This occurs when the AM-GM condition
holds with **equality** at the boundary.

**Example**: $M_{4,2}((x,x^3),(1,1)) = 4x^4 - 8x^8 + 4x^{12}$ is provably a circuit
polynomial ($|c_8| = 8$, AM-GM bound = $8$), but the GP reports `'a_0_2 + 8 ≤ 1e-10'
is infeasible by 8e+12%` — numerical failure at the exact boundary.

**Consequence**: Do NOT conclude "not SONC" from GP infeasibility alone. Always
check whether the polynomial could be a circuit polynomial by verifying:
1. Does support form a circuit (size = $n+2$, minimally affinely dependent)?
2. Does the AM-GM condition hold (possibly at boundary)?
3. Is GP infeasibility just a boundary artifact?

When the polynomial IS a circuit polynomial but the GP is infeasible, the
polynomial IS SONC — the GP result is a false negative.

## Normalization Bug in Irene's DSDP

`DSDPMeanRelaxation._build_mean_pair()` at `Irene/dsdp.py:358-405` originally
did **no** normalization by $\sum w_i$, producing forms that can be negative:

```python
# BUG (original): unnormalized form
Q = expand(weighted_q_sum ** q_exp)      # (∑ w_i y_i^q)^{c/q}
P = expand(weighted_p_sum ** p_exp)      # (∑ w_i y_i^p)^{c/p}
```

**Iteration 1 (wrong — over-scaled by $W^c$)**: applied separate $W^{c-c/q}$ and
$W^{c-c/p}$ factors to Q and P, producing $W^c \cdot M$ instead of $M$ — e.g.,
$M_{4,3}((x,y))$ came out as $256x^{12} + \dots$ instead of $x^{12} + \dots$.
User caught this: "$M_{4,3}((x,y)) = 256(x-y)^2$ can't be correct."

**Iteration 2 (correct — minimal integer-coefficient form)**: multiply the power-mean
inequality by $W^{\max(c/q, c/p)} = W^{c/p}$ (since $q > p \implies c/q < c/p$).
Only the Q term gets a $W$ factor:

$$M_{q,p} = W^{\,c/p - c/q} \left(\sum w_i y_i^q\right)^{c/q}
          - \left(\sum w_i y_i^p\right)^{c/p}$$

For $p=0$, the arithmetic-mean certificate ($P=1$) is left unchanged.

Applied 2026-08-11 at `Irene/dsdp.py:358-429` and
`MeanDeltaSONC/mean_polynomial/core.py:127-193`.
Verification: all 12 `test_dsdp_mean.py` tests pass.

## Library Structure

```
MeanDeltaSONC/
├── mean_polynomial/
│   ├── __init__.py    ← Public API
│   ├── core.py        ← MeanPolynomial class (correct normalization)
│   ├── tests.py       ← SOS/SONC/nonnegativity via IreneRewrite
│   └── utils.py       ← Monomial generation, weight helpers
└── experiments/
    ├── exp01_odd_monomials.py
    └── exp02_multivariate.py
```

### SONC Membership Testing Pattern (via IreneRewrite)

```python
from sympy import Poly, expand
from Irene.grouprings import CommutativeSemigroup, SemigroupAlgebra
from Irene.program import OptimizationProblem
from Irene.sonc import SONCRelaxations

def sympy_to_optimization_problem(expr, var_symbols):
    """Convert sympy polynomial to Irene OptimizationProblem.

    PITFALL: SemigroupAlgebra is NOT callable — do NOT use SA(0), SA(coeff).
    Instead, use SA['name'] ** exp with float arithmetic.
    PITFALL: expr.subs(subs_dict) fails because sympy.Pow tries sympify
    AtomicSGElement. Use Poly.as_dict() to extract monomials instead.
    """
    var_names = [str(v) for v in var_symbols]
    SG = CommutativeSemigroup(var_names)
    SA = SemigroupAlgebra(SG)

    poly = Poly(expand(expr), *var_symbols)
    result = None
    for monom, coeff in poly.as_dict().items():
        mono_term = float(coeff)
        for var_idx, exp in enumerate(monom):
            if exp > 0:
                mono_term = mono_term * (SA[var_names[var_idx]] ** exp)
        result = mono_term if result is None else result + mono_term

    optim = OptimizationProblem(SA)
    optim.set_objective(result if result is not None else 0.0)
    return optim
```

### SONC Feasibility vs Membership

`SONCRelaxations.solve()` returns a lower bound on the minimum. Interpreting results:

| GP Status | Lower bound | Interpretation |
|-----------|-------------|----------------|
| Feasible | lb ≥ 0 | Polynomial IS SONC (certificate proves nonnegativity) |
| Feasible | lb < 0 | SONC certificate found but loose; does NOT prove non-SONC |
| Infeasible | — | Strong evidence of non-SONC, BUT check for AM-GM boundary false negative first |
| Solver error | — | Indeterminate — numerical issue, not proof of non-SONC |

**For gap detection**: prefer GP-infeasible cases **after ruling out** the
AM-GM boundary false negative pitfall (above).

## SageMath Integration

For symbolic circuit analysis, use SageMath via conda:

```bash
unset CONDA_SHLVL CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER CONDA_PYTHON_EXE
conda run -n sage sage script.py
```

**PITFALL — SageMath ETuple vs Python tuple**: SageMath polynomial `.dict()` keys
are `ETuple`, not Python `tuple`. When checking `e in some_list`, cast to `tuple(e)` first.

**PITFALL — SageMath Rational format strings**: Use `int(coeff)` or `float(coeff)`
instead of raw Rational in f-strings — Rational doesn't support `:+d` format.

**PITFALL — SageMath uses `**`, not `^`**: Sage polynomials use `x**4`, not `x^4`
(unlike the Sage REPL preparser). Scripts run with the standard Python parser.
