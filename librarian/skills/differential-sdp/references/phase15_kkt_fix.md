# Phase 15: KKT Space Mismatch — Code Trace and Fix

## Bug Summary
`_build_diff_kkt_moments()` in `dsdp.py` silently returns 0 differential KKT constraints because it differentiates `self.RedObjective` (AuxSym space) instead of `self.Objective` (generator space).

## Architecture Background
`SDPRelaxations` (parent class) maintains two representations of the objective:

| Attribute | Space | Set By | Example |
|-----------|-------|--------|---------|
| `self.Objective` | Original generators | `SetObjective()` at `relaxations.py:261` | `x - u` |
| `self.RedObjective` | AuxSyms (X1, X2, ...) | Same, via `self.ReduceExp()` | `X1 - X2` |

Similarly for constraints:

| Attribute | Space | Set By |
|-----------|-------|--------|
| `self.OrgConst` | Original generators | `AddConstraint()` at `relaxations.py:275` |
| `self.Constraints` | AuxSyms | Same, via `self.ReduceExp()` |

## Derivation Map Registration
`set_derivation(diff_map)` at `dsdp.py:122` validates that all keys are in `self.Generators`:
```python
for key, val in diff_map.items():
    assert key in self.Generators, f"Derivation key {key} not in generators"
```

## Root Cause Chain
1. `_build_diff_kkt_moments()` (line 235) calls `self.differentiate(self.RedObjective, sym)`
2. `differentiate()` delegates to `_leibniz_diff(expr, var)` (line 160)
3. `_leibniz_diff` checks `if expr in self.diff_map` — but `expr` is `X1 - X2` (AuxSym), not `x - u` (generator)
4. Falls through to `expr.diff(var)` (line 203) which returns 0 because AuxSyms are independent symbols
5. Result: `diff_term == 0` for all generators → no KKT constraints added

## Fix Applied
In `dsdp.py` `_build_diff_kkt_moments()`:
- Line 235: `self.differentiate(self.RedObjective)` → `self.differentiate(self.Objective)`
- Line 240: `self.differentiate(self.RedObjective, sym)` → `self.differentiate(self.Objective, sym)`
- Line 249: `self.differentiate(cnst, sym)` → `self.differentiate(self.OrgConst[i], sym)`

After differentiation, `self.ReduceExp()` still brings results to AuxSym space for moment matrix construction.

## Verification
After fix, `_build_diff_kkt_moments()` returns non-zero constraint count when `diff_map` is properly registered and the objective/constraints are non-constant in the differentiation variables.
