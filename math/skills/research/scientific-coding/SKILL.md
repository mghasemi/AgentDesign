---
name: scientific-coding
description: "Use when running Python experiments, simulations, or data analyses in a secure resource-limited sandbox. Captures stdout, stderr, and execution metadata. Auto-logs results to SiYuan and records failure context in SimpleRAG project groups to prevent redundant re-runs."
metadata: {"clawdbot":{"emoji":"🧪","requires":{"bins":["python3"]},"config":{"env":{"SANDBOX_CPU_SECONDS":{"description":"CPU time limit per run in seconds","default":"30","required":false},"SANDBOX_MEM_MB":{"description":"Memory limit per run in megabytes","default":"512","required":false},"SIYUAN_URL":{"description":"SiYuan API URL for auto-logging results","default":"","required":false},"SIYUAN_TOKEN":{"description":"SiYuan API token","default":"","required":false}}}}}
---
# Scientific Coding Sandbox

Use this skill to execute Python code for empirical experimentation in a resource-limited, isolated environment. The sandbox prevents runaway processes and network access. Results are auto-logged to SiYuan; failures are recorded to SimpleRAG project groups to prevent redundant re-runs.

## When to Use

- Test a numerical algorithm or optimization heuristic.
- Generate statistical distributions, empirical data, or plots.
- Run a pytest suite against a newly generated module.
- Validate symbolic results from sympy-mcp or sagemath-mcp empirically.

## When Not to Use

- Do not use for symbolic computation — use sympy-mcp or sagemath-mcp.
- Do not use to compile LaTeX — use latex-manuscript.
- Do not use for tasks requiring network access (the sandbox blocks outbound connections).

## Commands

### Run inline code

```bash
python3 {baseDir}/scientific_coding_tool.py run --code "import math; print(math.factorial(20))"
python3 {baseDir}/scientific_coding_tool.py run --code "$(cat experiment.py)" --format json
```

### Run a script file

```bash
python3 {baseDir}/scientific_coding_tool.py run --file /path/to/experiment.py
python3 {baseDir}/scientific_coding_tool.py run --file /path/to/experiment.py --label "gradient-descent-v1"
```

### Run pytest in sandbox

```bash
python3 {baseDir}/scientific_coding_tool.py test --file /path/to/test_module.py
python3 {baseDir}/scientific_coding_tool.py test --file /path/to/test_module.py --format json
```

### Save last result to SiYuan

```bash
python3 {baseDir}/scientific_coding_tool.py save-to-siyuan --label "gradient-descent-v1" --notebook "MathAgent Experiments"
```

### Check failure log (what has already been tried)

```bash
python3 {baseDir}/scientific_coding_tool.py failures --recent 10
python3 {baseDir}/scientific_coding_tool.py failures --label "gradient-descent"
```

## Output

`run` returns:

```json
{
  "command": "run",
  "label": "gradient-descent-v1",
  "stdout": "Converged in 47 iterations. Loss: 0.00012",
  "stderr": "",
  "exit_code": 0,
  "cpu_seconds_used": 1.3,
  "memory_mb_peak": 24,
  "success": true,
  "siyuan_block_id": "20260425143200-abc123"
}
```

On resource limit exceeded:

```json
{
  "success": false,
  "error": "CPU time limit exceeded (30s)",
  "failure_logged": true
}
```

## Resource Limits

The sandbox enforces:
- CPU time: `SANDBOX_CPU_SECONDS` (default 30 s) via `resource.RLIMIT_CPU`.
- Virtual memory: `SANDBOX_MEM_MB` (default 512 MB) via `resource.RLIMIT_AS`.
- No outbound network: sandbox runs with `--network none` semantics (blocks socket creation).

## Pitfalls

### NumPy 2.x: `np.trapz` removed

NumPy ≥2.0 removed `np.trapz`. Use `np.trapezoid(y, x)` — identical signature.
If you get `AttributeError: module 'numpy' has no attribute 'trapz'`, check
the version before anything else. This is NOT a broken install.

### `solve_ivp` needs explicit `args=` for parameterized ODEs

```python
# WRONG — b never passed
solve_ivp(lambda t, y, b: f(t, y, b), [0, T], y0, t_eval=t)

# RIGHT
solve_ivp(lambda t, y, b: f(t, y, b), [0, T], y0,
          args=(beta,), t_eval=t)
```

Without `args=`, SciPy calls `fun(t, y)` only — `TypeError: missing 1 required positional argument`.

### `conda run` needs `CONDA_SHLVL` unset from terminal

The terminal session inherits `CONDA_SHLVL=1` which breaks `conda run`:

```bash
unset CONDA_SHLVL CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER CONDA_PYTHON_EXE
conda run -n sage python3 script.py
```

- **Ad-hoc verification scripts**: For custom verification, use `python3 -c "import sys; sys.path.append('PATH'); from MODULE import FUNCTION; VERIFY()"` to avoid file cleanup issues. Create temporary files only when absolutely necessary.

Piping a heredoc into `conda run -n sage python3` silently produces nothing.
Write to a `.py` file first, then execute it.

### SageMath MCP fallback

When `mcp_sagemath_sage_run_script` returns empty output or times out
repeatedly, fall back to `terminal` with `conda run -n sage python3`.
The MCP can stall on long-running numerical work; the conda path via
terminal is more reliable. Always use the `unset` preamble above.

### Irene SDP benchmark comparison

**ALWAYS use Irene's dedicated venv for SDP tasks** — do NOT use the sage conda
environment:

```bash
cd /home/YOUR-USER/Code/Python/Irene
# If Irene not installed in venv (ModuleNotFoundError):
/home/YOUR-USER/Code/Python/Irene/.venv/bin/pip install -e .
# Then run:
/home/YOUR-USER/Code/Python/Irene/.venv/bin/python3 script.py
```

The dsdp_benchmark.json environment confirms `independent_from_sage: true`.

When verifying Irene code changes that affect the SDP relaxation pipeline
(DSDP, ADE constraints, KKT stationarity), use the benchmark comparison
workflow in `references/irene_benchmark_comparison.md` — snapshot old
JSON, re-run with venv, diff via execute_code. That reference also
documents the KKT boundary-optimum regression pitfall (KKT at order ≤ 2
degrades bounds for problems whose optimum lies on the domain boundary).

### DSDP / ADE+SDP attack vectors

When investigating numerical improvements for the Differential SDP
framework, consult `references/ade_sdp_attack_vectors.md` — a ranked
taxonomy of attack vectors (differential exponential ADE, Fourier moment
matching, log-polynomial hierarchy, initial condition encoding) with
feasibility scores, expected gaps, concrete experiment scripts, and
literature references (Choi et al. 2026, Bach 2022).

For formal ADE definitions (sinh/cosh, log, Bessel, Airy — first-order
systems, differential ideals, invariants, initial conditions, and
compactification notes), see `references/ade_sdp_formal_definitions.md`.

### DSDP / ADE+SDP attack vector status

Status updates based on experimental runs: `references/ade_sdp_attack_vector_status.md`.
Records confirmed DEAD ENDS (derivative-coupled ADE, P7 d=3 timeout) and
verified NEW mechanisms (dual-ADE technique, 55%→9.4% for exp-x²).

### Dual-ADE technique (NEW — verified 2026-07-18)

A Groebner-constrained derivative encoding that tightened exponential ADE
bounds 6× (55% → 9.4%). See `references/ade_sdp_dual_ade_technique.md` for
the full recipe, mechanism explanation, working/not-working table, and the
critical `AddConstraint`-vs-`relations` distinction. Key insight: put
derivative relations in Groebner (to constrain moment matrix) but the
algebraic reciprocal in `AddConstraint` (to keep the auxiliary variable as
a generator, NOT Groebner-eliminated). **Parallel=True is mandatory for
d≥3** (sequential times out at 300s with 6+ generators).

### Rational parameterization for non-compact varieties (NEW — verified 2026-07-18)

Compaction technique that cures the hyperbolic function gap (sinh/cosh:
2857% → 0.00005% at d=1). See `references/ade_sdp_rational_parameterization.md`
for the full recipe. Uses stereographic projection to map the hyperbola
$z^2-y^2=1$ to a compact bounded-parameter variety via $t = \\tanh(x/2)$.

**⚠️ PITFALL — false positive risk (2026-07-18):** The rational
parameterization can produce false positives if the box_size on `s`
(where $s = 1/(1-t^2)$) is too tight. When `box_size` constrains $|s| \\leq B$
but $s \\in [1, 1/(1-B^2)] \\gg B$, the SDP returns artificially tight bounds
because the feasible set is over-restricted. **Fix:** exclude `s` from
`original_gens` (so it's not boxed) and add explicit bounds
`AddConstraint(s >= 1.0)`, `AddConstraint(s <= s_max)` with
$s_{\\max} = 1/(1-t_{\\max}^2)$. With correct bounds, d=2 and d=3 become
numerically infeasible (primal/dual gap explosion → $10^{10}$) —
the rational coupling $s(1-t^2)=1$ creates ill-conditioned moment
matrices. **d=1 is already near-exact; higher orders are unnecessary.**

### Tan via Sin/Cos encoding (NEW — verified 2026-07-18) ✅

The tan ADE $d_x(y)=1+y^2$ is too weak at d≤2 without an invariant.
Instead, encode $\\tan(x) = \\sin(x)/\\cos(x) = f/g$ with the compact
circle invariant $f^2+g^2=1$ and use the polynomial objective
$(f-xg)^2 \\approx (\\tan(x)-x)^2$. This achieves **near-exact bounds
at d=1** (gap ~5×10⁻⁹). See `references/ade_sdp_tan_sincos.md`.

### P7 Holonomic encoding (NEW — verified 2026-07-18) ✅

The user-provided holonomic encoding uses $(z, u, v, w, s, r)$ with
invariants $u^2+v^2=1$, $w^2-s^2=1$, $wr=1$, and $z=xu+yr$. This
achieved **5.98% gap at d=1** (versus best-known 8.34% from exp4-MOM-B).
See `references/ade_sdp_p7_holonomic.md`.

### The Invariant Principle (confirmed 2026-07-18)

The Lasserre hierarchy at d≤2 produces tight bounds **only when** a compact
polynomial invariant couples the generators. Without one, ALL ADE encoding
techniques (standard, dual, compactified, factorized) return the box bound.
- ✅ ADE + compact invariant → tight (sin²+cos²=1, yu=1, rational param.)
- ❌ ADE + non-compact invariant → loose (z²-y²=1 hyperbola)
- ❌ ADE only (no invariant) → box bound (tan, Airy, log)

**DEAD ENDS confirmed experimentally (2026-07-18):** See
`references/ade_sdp_dead_ends_and_pitfalls.md` for attack vectors that
were tested and FAILED:
- Derivative-coupled exponential ADE (build_ade_relations adds zero info
  beyond yz=1 — the derivative symbols are Groebner-eliminated)
- P7 d=3 (6 gens times out at 300s; file descriptor limits under
  Parallel=True)
- Tight box bounds on lifted variables (causes SDP primal infeasibility
  when combined with circle invariants)
- Tan ADE compactification (M²-y²≥0 doesn't help at d≤2 — manifold-vs-curve
  gap persists; SDP bound is just the box bound)
- Sinh/cosh invariant (z²-y²=1 is non-compact; SDP extracts loose bounds
  by exploring unbounded hyperbola within the box)
- Log-polynomial hierarchy for P8 (framework requires max Σ a_i log(p_i(x))
  with a_i>0 constants; P8 has variable coefficient x on log term)

Also documents the benchmark-rerun-with-snapshot workflow and the
research plan template used to discover these results.

### Research plan template

When embarking on experimental research (not software implementation),
use the structure in `references/research_plan_template.md`: gap map →
literature search → attack vector matrix with feasibility/impact →
concrete experiment scripts → tight feedback loop. Always document
dead ends before moving to the next direction.

### Report postscript pattern

When a code fix does NOT change the main numerical results but you still
need to document the verification, **add a short postscript to the
existing report** instead of rewriting it. The postscript should contain:
a one-paragraph description of the fix, a before/after comparison table,
and a verdict. This preserves the original report's integrity while
adding the verification evidence.

Example: the `Eq(diff, 0)` fix had no effect on structural gaps (P7, P8,
tan ADE) but needed documentation. Added a "Postscript: Eq Fix Numerical
Rerun" section to `DSDP_Synthesis_Numerical_Experiments_2026-07-17.md`.

### Hermes session reports

After every completed task, write a markdown session summary to
`/home/YOUR-USER/Code/Python/Reports/[project]_[YYYY-MM-DD_HHMMSS].md`.
Centralized Reports folder, not per-project subdirectories. Use the
project codename (e.g., "DSDP", "Irene", "MP") as the prefix.

### `scipy.optimize.linprog`: variables are NON-NEGATIVE by default

`linprog` applies bounds `(0, None)` to every variable unless told otherwise.
A Farkas/duality feasibility problem such as "find `y` with `A y ≤ b` and
`y·m ≤ -1`" is therefore reported **infeasible** even when a negative-`y`
solution exists (a valid certificate silently comes back `None`).

```python
res = linprog(np.zeros(n), A_ub=A_ub, b_ub=b_ub, method="highs",
              bounds=[(None, None)] * n)   # free variables — REQUIRED here
```

Always sanity-check a returned certificate by re-evaluating its margins; a
`None` certificate on a problem you can solve by hand means the LP setup is
wrong, not that infeasibility is genuine.

### A numeric 0.0 can be float UNDERFLOW, not an exact zero

In a search for annihilators / kernels, a reported exact `0.0` (or `inf` from
`0 ** (-1/n)`, or `nan`) usually means the quantity left the representable
range: `t ** 2**33` underflows, `(1/3) ** 798` underflows, `exp(1800)`
overflows. Restrict the probe to the representable range and say so in the
output — never report underflow as a mathematical exactness result. Compute
in log space (`exp(-log(m) / (2n))`) wherever the exponent is large.

### Moment/moment-matrix conventions: match the GENERATOR, not a habit

For a real generator `x` on `[0,1]` the positivity object is the sum-index
Hankel `H[i,j] = μ(x^{α_i+α_j})`. For a **complex** generator `z` it is NOT:
`|p(z)|²` is not a polynomial in `z`, and the sum-index Hankel need not be
PSD (verified counterexample: `½δ_{e^{±iπ/3}}` gives eigenvalues
`(-1.5, 0, 0, 2.5)`). The correct truncation-level object is the Gram matrix
in the quotient basis forced by the relation on the support (`z z̄ = 1` on
`∂D`), i.e. the Toeplitz form `T[k,l] = ν(z^{k−l})` over differences `a−b`.
Sanity rule: if a "PSD check" prints a clearly negative eigenvalue while the
script claims PSD, the convention is wrong — fix the object, not the print.

### A finite point set cannot model a Peak ⊊ Choquet strictness example

When modelling a uniform algebra with a discretised skeleton, check
separation first: if the generators take distinct value pairs at every point
of a finite `K`, then (Stone–Weierstrass) they generate all of `C(K)`, so
every point is a peak point and `Peak(A) = Ch(A) = K`. Any "separation"
certificate found there is a **support-location** certificate, not a
Peak/Ch strict-inclusion witness. Assert the separation check numerically in
the script and print it next to the claim.

### Müntz–Szász approximation: use Szász (1916) L²→sup-norm bridge, never direct sup-norm

Müntz bases $\{x^{\lambda_k}\}$ are **provably ill-conditioned** for most
practical exponent sets. Trefethen (2022): approximating $f(x)=x$ in the
even-powers basis to accuracy $\varepsilon=10^{-6}$ requires degrees larger
than $x^{280,000}$ with coefficients exceeding $10^{107,000}$. Condition
number grows as

$$\kappa_{2n} \approx (1+\sqrt{2})^{2n} \approx 100.766^n.$$

**Protocol — never attempt direct sup-norm approximation** (no Chebyshev
grids, no Remez algorithm). Instead, reduce everything to L² and invoke the
Szász bridge:

1. **Differentiate analytically**: $f \to f'$. The derivative lives in a
   shifted Müntz space $\{x^{\lambda_k-1}\}$.
2. **Build L² Gram matrix** on the shifted basis:
   $$G_{ij} = \int_0^1 x^{\lambda_i + \lambda_j - 2} dx = \frac{1}{\lambda_i + \lambda_j - 1}.$$
3. **Regularized solve**: $(G + \varepsilon I)c = b$ where $b_j = \langle f', x^{\lambda_j-1}\rangle_{L^2}$ (numerical quadrature). Always print the condition number; warn when $\kappa > 10^{10}$.
4. **Integrate back**: $p(x) = \sum c_k x^{\lambda_k}$ is the sup-norm approximant.
5. **Bound error via Szász (1916)**:
   $$\|f - p\|_{C[0,1]} \leq \sqrt{q} \cdot \|f' - p'\|_{L^2[0,1]},$$
   where $q$ is the degree of the target monomial (or use a uniform constant for general $f$).

The error bound is the **deliverable** — it's a certificate, not just an
approximation. For your research (MeasuresAndAlgebras), this connects to the
Borwein–Erdélyi explicit L² error formula:
$$E(x^q, \Pi(\Lambda_n))_2 = \frac{1}{\sqrt{2q+1}} \prod_{k=0}^n \left|\frac{q-\lambda_k}{q+\lambda_k+1}\right|.$$

**Trade-off**: larger $\varepsilon$ → smaller coefficients but worse L²
residual → looser sup-norm bound. Always report both $\kappa$ and the Szász
bound together.

### SymPy `==` is NOT symbolic equality — use `Eq()` instead

In SymPy, `expr == 0` is **Python's structural equality** — it returns
a `bool` (`True`/`False`), not a symbolic `Equality` object. This is a
silent killer when passing constraints to frameworks that dispatch on
`isinstance(cnstr, Equality)`:

```python
# WRONG — evaluates to Python bool, silently ignored by AddConstraint()
self.AddConstraint(diff == 0)

# RIGHT — creates a symbolic Equality object
from sympy import Eq
self.AddConstraint(Eq(diff, 0))
```

If your constraint handler expects `sympy.core.relational.Equality`,
`GreaterThan`, or `LessThan` instances, `==` will never match — it
produces `bool`, which the handler skips. Use `Eq(lhs, rhs)` or
`Equality(lhs, rhs)` for symbolic equality. Note: `>=` / `<=` DO work
as symbolic inequalities in SymPy (they produce `GreaterThan`/`LessThan`).

## Auto-Logging

- On **success**: result is posted to SiYuan if `SIYUAN_URL` and `SIYUAN_TOKEN` are set.
- On **failure**: error + code snippet are stored in SimpleRAG (for example `project-<slug>-failures`). The orchestrator queries this memory before re-running to avoid identical failed attempts.
