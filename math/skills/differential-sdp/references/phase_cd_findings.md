# Phase C/D Findings — NonPOPSDP vs DSDP-ADE (2026-07-17)

## Function Class Dominance Map

| Function Class | DSDP-ADE | NonPOP SDP | Winner |
|---------------|----------|------------|--------|
| Trigonometric (compact variety, $f^2+g^2=1$) | Excellent ($10^{-7}$%) | Poor (400% gap) | **DSDP-ADE** |
| Exponential (non-compact, $yz=1$) | Failed (0 optimal runs) | Good (0.52% gap) | **NonPOP SDP** |
| Algebraic constraints | Excellent ($10^{-9}$) | Excellent ($10^{-9}$) | **Tie** |
| KKT + ADE combined | Poor (330% underestimate) | Moderate (7.54% underestimate) | **NonPOP SDP** |
| $\tan(x)$ (manifold-vs-curve) | Catastrophic ($10^{17}$%) | Excellent (gap ≤ $10^{-9}$) | **NonPOP SDP** |
| Coupled trig + exponential | Good (10.73% gap floor) | Moderate | **DSDP-ADE** |

## Aggregate Statistics

| Method | Optimal Rate | Success Rate | Valid LB Rate |
|--------|-------------|-------------|---------------|
| NonPOP SDP | 28/28 (100%) | 100% | 66.7% |
| DSDP-ADE | 8/14 (57.1%) | 57.1% | 50.0% |

## Phase D: Five Experimental Tracks

| Track | Goal | Result | Verdict |
|-------|------|--------|---------|
| D1: Depth extension ($d=3,4$) | Fix Exp-x²/Cosh | 2484% gap persists at $d=3,4$; Cosh `1/X2` error | **FAILS** |
| D2: Coupled ADE ($yz=1$) | Fix Cosh and Exp-x² | Cosh: $2.44\times10^{-9}$ ✅; Exp-x²: 2484% persists ❌ | **CURES Cosh only** |
| D3: KKT stabilization | Fix Trig KKT | 330% gap at ALL configs ($d=1,2,3$, ±KKT) | **FAILS** |
| D4: Manifold-vs-curve | Fix tan ADE | LB = -25.0 regardless; NonPOP underestimates | **UNFIXED** |
| D5: Hybrid routing | Auto-select method | Trig → DSDP-ADE ✅; Exp → NonPOP ⚠️ (39% vs 0.52% Phase C) | **PARTIALLY viable** |

## Key Root Causes

1. **Exponential ADE structural failure:** $D_x(y) = y$ is algebraically correct but numerically insufficient — the quotient algebra admits $y \to 0, x \to \infty$ while $yz \approx 1$ holds numerically. Depth-independent — persists at $d=4$.

2. **KKT+ADE irreducible instability:** ADE quotient algebra itself admits spurious stationary points of $x^2 + \sin x$. Removing KKT doesn't help — the ADE constraints are the root cause, not KKT interaction.

3. **tan manifold-vs-curve:** $D_x(u) = 1+u^2$ defines a 2D manifold in $(x,u)$ space. True graph $\tan(x)$ is a 1D curve. The moment hierarchy at $d \leq 4$ cannot distinguish them. Fix: encode initial condition $u(0)=0$.

## Recommended Hybrid Routing Logic

```python
def route_method(objective, constraints):
    """Route to DSDP-ADE or NonPOP based on function class."""
    if has_trigonometric_compact_variety(constraints):
        return "dsdp_ade"  # Near-exact
    if has_exponential_without_coupling(constraints):
        return "nonpop"    # Valid LB, 0.52% gap
    if has_tan_or_manifold_curve(constraints):
        return "nonpop"    # DSDP-ADE catastrophic
    if has_logarithmic(constraints):
        return "dsdp_ade"  # K2 provides 40× tightening
    return "dsdp_ade"      # Default
```
