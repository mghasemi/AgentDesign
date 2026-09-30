# Convex/Concave Envelopes & Piecewise Polynomial Branch-and-Bound

**Session:** 2026-07-16 | **Status:** Research complete, proof-of-concept recommended

## Motivation

Non-POP SDP (Chebyshev degree 5) shows ~0.75 approximation error for trigonometric test cases, dominating the hierarchy gap (~0.0004) by 4+ orders of magnitude. Convex envelopes on partitioned domains can reduce this error to O(h^2) per subinterval.

## Convex Envelope Theory

For f: D -> R on compact convex domain D:
- **Convex envelope** conv_D(f) = sup {g : g convex, g <= f on D} (tightest convex underestimator)
- **Concave envelope** cav_D(f) = inf {g : g concave, g >= f on D} (tightest concave overestimator)
- For any convex relaxation g: conv_D(f) <= g <= f, so lb_convex >= lb_any_relaxation >= f*

## Known Convex Envelopes for Test Functions

| Function | Domain | Convex Envelope | Notes |
|----------|--------|-----------------|-------|
| sin x | [0, pi] | Chord: (2/pi)x | Linear, exact at endpoints |
| sin x | [0, pi/2] | Chord (concave) | sin'' = -sin <= 0 |
| cos x | [0, pi/2] | Self (concave) | cos'' = -cos <= 0 |
| cos x | [0, pi] | Chord: -(2/pi)x + 1 | Concave on full interval |
| e^x | Any interval | Self (strictly convex) | e'' = e > 0 |
| tan x | [-1, 1] | Self (convex for x >= 0) | tan'' = 2sec^2 tan |
| sin x + cos x | [0, pi/2] | Requires composition rules | McCormick-style or partitioning |

**Critical:** For e^x and tan^2 x on convex subdomains, envelope = function itself. Exact relaxation, zero approximation error.

## AlphaBB Methodology (Adjiman, Androulakis, Floudas 1998)

Constructs convex underestimators via interval Hessian analysis:
```
f_under(x) = f(x) + sum(alpha_i * (x^U - x)(x - x^L))
```
where alpha_i >= 0 chosen so Hessian + diag(2*alpha) is PSD on domain.

**For transcendental functions:** Hessian involves transcendental derivatives. Interval arithmetic is well-defined but conservative.

## Piecewise McCormick Relaxation (Castro 2015)

Divides domain into n partitions, applies tighter convex relaxations per subinterval. Gap converges as O(1/n^2) for bilinear terms; same rate applies to bounded second-derivative functions.

## Spatial Branch-and-Bound Algorithm

```
1. Initialize: single region S, tolerance epsilon, best solution U = inf
2. Choose region S_j from active set
3. Lower bound: solve convex relaxed SDP on S_j -> l_j
4. Upper bound: solve local NLP on S_j -> u_j
5. Prune: discard regions where l_j > U + epsilon
6. Check: if u_j - l_j <= epsilon, accept as local optimum
7. Branch: split S_j into subregions, return to step 2
```

## Computational Complexity

| Component | Complexity | Notes |
|-----------|------------|-------|
| Domain partitioning | O(n) | Linear in subintervals |
| Local convexity check | O(n * cost(f'')) | Symbolic or interval arithmetic |
| AlphaBB construction | O(n * d^2) | d = polynomial degree for SDP |
| SDP solve per subinterval | O(n * d^3 * log(1/epsilon)) | Moment matrix size ~d^2 |
| Total | O(n * d^3 * log(1/epsilon)) | Linear in n, cubic in d |

For 1D with n=10, d=2: manageable. For multivariate with n=100, d=4: expensive.

## Expected Tightness Improvement

- **Trig test (sin x + cos x on [0, pi/2]):** Chebyshev error ~0.75 -> convex envelope with n=10 -> ~0.024 (30x improvement)
- **Exp test (e^x + e^-x on [-1, 1]):** Envelope is exact -> zero error
- **Tan test (tan^2 x + x^2 on [-1, 1]):** Envelope is exact -> zero error

## Integration Challenges with Irene

### Moment Matrix Construction
Irene's SDPRelaxations expects polynomial objectives. Convex envelopes are piecewise-defined, requiring:
1. Separate SDP per subinterval (simpler, aligns with current architecture)
2. Global SDP with partition constraints (more complex, single solve)

**Recommendation:** Approach 1 — each subinterval becomes separate OptimizationProblem with box constraints.

### AlphaBB Underestimator Implementation
Two-level approximation needed:
1. Polynomial approximation of f (Chebyshev/Taylor)
2. AlphaBB convexification of polynomial approximation

**Alternative:** Apply alphaBB directly to transcendental f, then approximate the underestimator by polynomial. Preserves convexity but introduces approximation error.

### Branch-and-Bound Loop
Requires new class BranchAndBoundSDP wrapping SDPRelaxations:
- Manage partition tree
- Node selection (lowest lower bound)
- Pruning (LB > UB + tolerance)
- Branching (split subinterval if gap > tolerance)
- Upper bounding via scipy.optimize.minimize

## Comparison Matrix

| Metric | DSDP-ADE | Convex Envelope sBB | Non-POP SDP (Chebyshev) |
|--------|----------|---------------------|------------------------|
| Approximation error | 0 (exact) | O(h^2) per subinterval | ~0.75 (degree 5) |
| Hierarchy gap | ~0.0004 | ~0.0004 (same SDP) | ~0.0004 |
| Total gap | ~0.0004 | O(h^2) + 0.0004 | ~0.75 |
| Computational cost | High (differential algebra) | Moderate (n * SDP solves) | Low (single SDP) |
| Scalability to multivariate | Poor (curse of dimensionality) | Moderate (partition grid grows exponentially) | Good (single SDP) |
| Rigorous bounds | Yes | Yes (convergence proof) | No (approximation error unbounded) |

## Recommendations

### Short-Term (Proof of Concept)
1. Implement piecewise convex envelope for 1D trig test case
2. Partition [0, pi/2] into n=5 subintervals
3. Compute convex envelope per subinterval (chord or self)
4. Replace sin x + cos x with piecewise linear underestimator
5. Solve SDP relaxation per subinterval using SDPRelaxations
6. Compare lower bounds against current Chebyshev approach
7. Expected: approximation error drops from ~0.75 to ~0.05

### Medium-Term (Full sBB Implementation)
1. Develop BranchAndBoundSDP class in Irene
2. Add alphaBB underestimator support
3. Integrate with SDPRelaxations for lower bounding
4. Use local NLP solver for upper bounding

### Long-Term (Multivariate Extension)
1. Adapt partitioning to multivariate domains (hyperrectangles)
2. Implement adaptive refinement based on local gap estimates
3. Handle curse of dimensionality via sparse grids or lattice partitions
4. Integrate with DSDP-ADE (hybrid: exact symbolic + numerical relaxation)

## Key References

1. Adjiman et al. (1998) - alphaBB methodology for global optimization
2. Castro (2015) - Tightening piecewise McCormick relaxations
3. Floudas (1995) - Deterministic Global Optimization
4. McCormick (1976) - Convex underestimating problems
5. Skjäl & Westerlund (2014) - New methods for alphaBB-type underestimators
6. Liberti (2008) - Introduction to global optimization (Ecole Polytechnique)
