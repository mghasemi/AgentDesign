---
name: scientific-coding
description: "Use when running Python experiments, simulations, or data analyses in a secure resource-limited sandbox. Captures stdout, stderr, and execution metadata. Auto-logs results to SiYuan and records failure context in the per-problem failure scratchpad to prevent redundant re-runs."
metadata: {"clawdbot":{"emoji":"🧪","requires":{"bins":["python3"]},"config":{"env":{"SANDBOX_CPU_SECONDS":{"description":"CPU time limit per run in seconds","default":"30","required":false},"SANDBOX_MEM_MB":{"description":"Memory limit per run in megabytes","default":"512","required":false},"SIYUAN_URL":{"description":"SiYuan API URL for auto-logging results","default":"","required":false},"SIYUAN_TOKEN":{"description":"SiYuan API token","default":"","required":false}}}}}
---
# Scientific Coding Sandbox

Use this skill to execute Python code for empirical experimentation in a resource-limited, isolated environment. The sandbox prevents runaway processes and network access. Results are auto-logged to SiYuan; failures are recorded to the per-problem failure scratchpad to prevent redundant re-runs.

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

Example: a symbolic-equality fix that changed no numerical result still needed
documenting, so the verification was recorded as a short postscript to the
existing report rather than as a rewrite.

### Hermes session reports

After every completed task, write a markdown session summary to
`/home/YOUR-USER/Code/Python/Reports/[project]_[YYYY-MM-DD_HHMMSS].md`.
Centralized Reports folder, not per-project subdirectories. Use the
project codename as the prefix.

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
- On **failure**: the error and the code snippet are appended to the project's failure log. The orchestrator queries this memory before re-running to avoid identical failed attempts.
