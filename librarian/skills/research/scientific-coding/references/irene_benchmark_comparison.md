# Irene SDP Benchmark Comparison Workflow

How to compare before/after numerical results when a code change affects
Irene's SDP relaxation pipeline (DSDP, mean certificates, ADE constraints,
KKT stationarity).

## Step 1: Snapshot old results

```bash
cd /home/YOUR-USER/Code/Python/Irene
cp ade_benchmark.json ade_benchmark_before_fix.json
cp dsdp_benchmark.json dsdp_benchmark_before_fix.json
cp dsdp_phase_d_results.json dsdp_phase_d_results_before_fix.json
```

## Step 2: Re-run benchmarks with fixed code

```bash
unset CONDA_SHLVL CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER CONDA_PYTHON_EXE
conda run -n sage python3 run_ade_benchmark.py
conda run -n sage python3 run_dsdp_benchmark.py
```

For long-running suites, use background + notify:
```
terminal(command="conda run -n sage python3 run_ade_benchmark.py",
         background=true, notify_on_complete=true, timeout=300)
```

## Step 3: Diff via execute_code

Use `execute_code` (not inline terminal jq) to load both JSON files and
produce a side-by-side comparison table. Key structure:

```python
import json

with open('ade_benchmark_before_fix.json') as f:
    before = json.load(f)
with open('ade_benchmark.json') as f:
    after = json.load(f)

before_by_name = {r['name']: r for r in before['results']}
after_by_name = {r['name']: r for r in after['results']}

for name in sorted(before_by_name.keys()):
    b = before_by_name[name]
    a = after_by_name.get(name, {})
    b_lb = b.get('lower_bound')
    a_lb = a.get('lower_bound')
    if b_lb is not None and a_lb is not None:
        delta = a_lb - b_lb
        if abs(delta) > 1e-10:
            print(f"\u26a0 CHANGED: {name}: {b_lb} \u2192 {a_lb} (\u0394={delta:.2e})")
        else:
            print(f"\u2713 SAME:    {name}: {b_lb}")
```

## Step 4: Update reports

### Pattern A: Fix changes outcomes

If the fix materially changes numerical results, update the relevant
sections of the main synthesis report with new tables and analysis.

### Pattern B: Fix does NOT change outcomes (postscript)

If the fix is mathematically necessary but doesn't change structural
results, **add a short postscript to the existing report** instead of
rewriting it. The postscript should contain:
1. One-paragraph description of the fix
2. Before/after comparison table
3. Verdict on impact

Example from `DSDP_Synthesis_Numerical_Experiments_2026-07-17.md`:

```
## Postscript: Eq Fix Numerical Rerun (2026-07-18)

A bug was discovered and fixed in DSDPRelaxations.add_ade_moment_constraint()
where self.AddConstraint(diff == 0) evaluated to a Python bool instead of
a SymPy Equality object... The fix was applied and all benchmarks re-run.

| Test Category | Before | After | Change |
|---|---|---|---|
| Trigonometric ADE | Near-exact | Near-exact | Unchanged |
| P7 torus-curve gap | 8.34% | 8.34% | Unchanged |
| P8 logarithmic gap | 10.73% | 10.73% | Unchanged |

Verdict: The Eq fix is mathematically necessary but does not resolve the
structural gaps (P7, P8, tan ADE).
```

### Hermes session reports

After every completed task, write a markdown session summary to:
`/home/YOUR-USER/Code/Python/Reports/[project]_[YYYY-MM-DD_HHMMSS].md`

Centralized Reports folder, not per-project subdirectories.

## Pitfall: KKT stationarity degrades bounds for boundary optima

When `DSDPKKTRelaxation.solve_kkt()` enforces `\u2207L = 0` as moment
equalities at low SDP order (d \u2264 2), problems whose true minimum lies
on the boundary of the box domain can experience **regression** \u2014 the
lower bound shifts away from the correct value toward 0.

Example: `min(x1*x2*x3)` on [-4, 4]\u00b3 (true min = -64):
- Without KKT (or with KKT silently dropped by `==` bug): LB \u2248 -64
- With KKT enforced at order 2: LB \u2248 0 (KKT requires Lagrange multipliers that order-2 relaxation can't resolve)

This is a known limitation documented in the baseline report
(DSDP_Synthesis_Numerical_Experiments_2026-07-17.md, Section 9):
"KKT+ADE instability: KKT degrades ADE bounds at d \u2264 3."

**Recommendation:** Do not use KKT stationarity at orders < 3 for
problems where the optimum lies on the boundary. The Eq(diff, 0) fix
is correct for mathematical rigor, but it exposes this pre-existing
KKT limitation.

## Affected code paths

The `add_ade_moment_constraint` method in `Irene/dsdp.py` (line 280)
is called from three places:
1. `DSDPRelaxations.solve()` \u2192 `_build_diff_kkt_moments()` (when `use_diff_kkt=True`)
2. `DSDPRelaxations.solve()` \u2192 `_build_mean_certificate_moments()` (when `use_mean_cert=True`)
3. `DSDPKKTRelaxation.solve_kkt()` \u2192 `_build_kkt_stationarity()`

Before the fix, `self.AddConstraint(diff == 0)` evaluated `diff == 0`
as a Python `bool`, which `AddConstraint` silently skips. After the
fix, `self.AddConstraint(Eq(diff, 0))` creates a symbolic `Equality`
object that is properly routed to localizing moment matrices.

## Irene benchmark scripts

| Script | What it tests | Affected by Eq fix? |
|--------|--------------|---------------------|
| `run_ade_benchmark.py` | 11 ADE tests: trig, exp, cosh, KKT | 3/11 tests (coupled_oscillator, tan_ade, trig_kkt) |
| `run_dsdp_benchmark.py` | 23 DSDP tests: mean certs, KKT | 1/23 tests (3D box product KKT) |
| `run_dsdp_suite.py` | Full pytest suite (56 tests) | None directly |
| Phase D scripts | Various experimental configs | Varies by config |
