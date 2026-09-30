# Lean4 Lake Project Workflow (When MCP Tools Fail)

## Problem

The `lean4_repl`, `lean4_prove`, and `lean4_search` MCP tools may fail with:
```
No such file or directory: PosixPath('/home/YOUR-USER/.cache/lean4_tool')
```
or return empty results (`"success": false`) when the scratch project is
missing or the toolchain path is broken.

## Workaround: Standalone Lake Project

Create a Lake project with Mathlib in the target directory:

```bash
HOME=/home/YOUR-USER lake init <project_name> math
```

Wait for Mathlib cache download (5-10 minutes, ~8 GB). Then write `.lean` files
and build:

```bash
HOME=/home/YOUR-USER cd <project_dir> && HOME=/home/YOUR-USER lake build
```

### Critical: `HOME` Fix

When running under Hermes profiles, `HOME` is set to the profile home
(e.g., `~/.hermes/profiles/math/home/`), which elan cannot find.
Always prefix `lake` and `lean` commands with `HOME=/home/YOUR-USER`:

```bash
HOME=/home/YOUR-USER elan show       # verify toolchain
HOME=/home/YOUR-USER lake build      # build project
```

Without this, `elan` reports `no default toolchain configured`.

## Current State (2026-07-25)

| Property | Value |
|----------|-------|
| Lean version | v4.31.0 |
| Mathlib revision | `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` |
| Working project | `/home/YOUR-USER/Code/Python/positivstellensatz/VerifySection4/` |
| Project type | `lake init verify_section4 math` — standalone Lake+Mathlib |

## Key Mathlib Lemmas Discovered

- `pow_arith_mean_le_arith_mean_pow_of_even` — power-mean inequality for even exponents (no nonnegativity constraint on zᵢ)
- `Even.convexOn_pow` — convexity of xⁿ on all ℝ when n is even
- Located in `Mathlib/Analysis/MeanInequalitiesPow.lean` and `Mathlib/Analysis/Convex/Mul.lean`

## Proving Nonnegativity via Power-Mean

For polynomials of the form `Avg(xᵢ⁴) − (Avg xᵢ)⁴`, use:

```lean
have h_ineq : (∑ i ∈ s, w i * z i) ^ 4 ≤ ∑ i ∈ s, w i * z i ^ 4 :=
  Real.pow_arith_mean_le_arith_mean_pow_of_even s w z hw_nonneg hw_sum h_even
```

where `h_even : Even 4` is proved by `use 2`.
