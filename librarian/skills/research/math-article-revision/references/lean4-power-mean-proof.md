# Lean 4 + Mathlib: Power-Mean Inequality Proof Pattern

Complete recipe for proving polynomial nonnegativity via the power-mean inequality
for even exponents. Cross-cutting knowledge: useful during both manuscript revision
and formal verification stages.

## Lemma Chain

`Even.convexOn_pow` → `map_sum_le` → `pow_arith_mean_le_arith_mean_pow_of_even`

Files:
- `Mathlib/Analysis/Convex/Mul.lean` — `Even.convexOn_pow` (even `n` ⇒ `x ↦ xⁿ` convex on ℝ)
- `Mathlib/Analysis/MeanInequalitiesPow.lean` — the final lemma

## Exact Lemma Signature

```lean
Real.pow_arith_mean_le_arith_mean_pow_of_even (s : Finset ι) (w z : ι → ℝ)
    (hw : ∀ i ∈ s, 0 ≤ w i) (hw' : ∑ i ∈ s, w i = 1) {n : ℕ} (hn : Even n) :
    (∑ i ∈ s, w i * z i) ^ n ≤ ∑ i ∈ s, w i * z i ^ n
```

**Critical**: `s` is a **section variable** — must be passed explicitly.

## GOTCHA: `s` is an explicit binder

```lean
-- WRONG: type mismatch
Real.pow_arith_mean_le_arith_mean_pow_of_even w z hw_nonneg hw_sum h_even

-- RIGHT: pass s explicitly
Real.pow_arith_mean_le_arith_mean_pow_of_even s w z hw_nonneg hw_sum h_even
```

## Complete Proof Template (4-variable case)

```lean
import Mathlib
open Finset

example (x1 x2 x3 x4 : ℝ) : (x1^4+x2^4+x3^4+x4^4)/4 - ((x1+x2+x3+x4)/4)^4 ≥ 0 := by
  have h_even : Even 4 := by use 2
  let s : Finset ℕ := {0,1,2,3}
  let w : ℕ → ℝ := fun _ => 1/4
  let z : ℕ → ℝ := fun i => if i=0 then x1 else if i=1 then x2 else if i=2 then x3 else x4
  have hw_nonneg : ∀ i ∈ s, 0 ≤ w i := by intro i hi; unfold w; positivity
  have hw_sum : ∑ i ∈ s, w i = 1 := by unfold w s; norm_num
  have hz_sum : ∑ i ∈ s, w i * z i = (x1+x2+x3+x4)/4 := by
    unfold w z s; norm_num; ring
  have hz4_sum : ∑ i ∈ s, w i * z i ^ 4 = (x1^4+x2^4+x3^4+x4^4)/4 := by
    unfold w z s; norm_num; ring
  have h_ineq : (∑ i ∈ s, w i * z i) ^ 4 ≤ ∑ i ∈ s, w i * z i ^ 4 :=
    Real.pow_arith_mean_le_arith_mean_pow_of_even s w z hw_nonneg hw_sum h_even
  rw [hz_sum, hz4_sum] at h_ineq
  linarith
```

## Computing Small Explicit Finset Sums

`Fin.sum_univ_four` does NOT exist. Use `norm_num` + `ring`:

```lean
unfold w z s; norm_num; ring
```

## Even n Proof Gotcha

```lean
have h_even : Even 4 := by
  use 2
-- 4 = 2*2 is rfl; do NOT add `ring` after `use 2`
```

`use 2; ring` produces: `error: No goals to be solved`

## Lake Project Setup

Two options exist:

### Option A: In-Repo Lake Project (recommended)

```bash
mkdir MyVerify && cd MyVerify
HOME=/home/YOUR-USER lake init my_verify math       # creates project + Mathlib dependency
HOME=/home/YOUR-USER lake exe cache get             # download prebuilt oleans (~5659 files, ~2-5 min)
HOME=/home/YOUR-USER lake build                     # ~2 min after cache, more on first build
```

This is more reliable than the scratch project because:
- Mathlib is a proper Lake dependency (not a cached singleton)
- Incremental rebuilds are fast (~2s for a single file)
- The `.lake` directory lives alongside your `.lean` files for inspection

Timeout: set at least 300s for `cache get`, 300s for first `build`.

### Option B: MCP Scratch Project (used by MCP tools)

The MCP tools (`lean4_repl`, `lean4_search`, `lean4_prove`) auto-create a scratch
project at `~/.cache/lean4_tool/`. When this directory is missing, they fail with
`No such file or directory: PosixPath('/home/YOUR-USER/.cache/lean4_tool')`.

Fix:
```bash
HOME=/home/YOUR-USER mkdir -p ~/.cache/lean4_tool
cd ~/.cache/lean4_tool
HOME=/home/YOUR-USER lake init scratch math
HOME=/home/YOUR-USER lake exe cache get
```

## Explicit SOS: $M_{4,2}$

$$M_{4,2} = \frac{1}{16}\sum_{i<j}(x_i^2 - x_j^2)^2$$

Lean proof = single `ring` on the expanded identity.

## $M_{4,1}$: SOS via SDP only

Nonnegativity provable via power-mean lemma. No explicit rational SOS decomposition
known — SDP finds rank-3 Gram matrix with algebraic-number entries.
