---
# Differential-Algebraic Optimization Findings

## Key Theoretical Insights from Curto et al. Paper

### 1. **Moment Matrix Exactness Condition (Theorem 2.3)**
In a unital commutative real algebra, the moment sequence $\gamma$ has a representing measure if and only if its associated Hankel matrix is positive semi-definite ($M(n) \succeq 0$) and satisfies:
$$\text{rank}(M(k)) = \text{rank}(M(k+1)), \quad \forall k \geq n,$$
in the flat extension sense. This provides a **necessary and sufficient condition** for our lifted SDP relaxations to be exact.

### 2. **Numerical Rank Test (Algorithm 3.5)**
A practical test for exactness is whether the moment matrix satisfies:
$$\kappa(M_{d+1}) \approx \kappa(M_d) $$
in relative condition number, where $\kappa$ is spectral or Frobenius condition number.

### 3. **Finite Support Measures (Theorem 4.1)**
If the optimal measure is supported at finitely many points, then $\exists d$ such that $p_d^{mom} = f^*$. This explains why Phase 2 achieved gap ~10⁻⁵.

## Applied to DSDP Barriers

### Torus-Curve Gap (Section 4.3)
**Theoretical Insight:** For unital commutative real algebras, the kernel of the moment matrix must satisfy:
$$\ker(M_k(w^*)) = \left\{ p \in \mathbb{R}[x,y]_{2k}: L(p) = 0, L(g_j y) = 0 \right\}$$
This means we can enforce parametric curve structure by adding constraints that the moment matrix lies in kernel subspaces.

### Dynamic Range Problem (Section 4.2)
**Numerical Flat Extension Test:** Practical method to verify exactness:
$$\frac{\|M_{d+1} - M_d \otimes I\|_F}{\|M_d\|_F} < \epsilon,$$
in Frobenius norm, which works in ill-conditioned cases.

## Verification Protocol for SDP Results
When analyzing DSDP experimental results:
- Use Theorem 2.3 conditions to certify exactness
- Apply numerical tests when matrices are ill-conditioned
- Preserve full detail only for focus topics (Lasserre extension)
- Summarize non-focus content aggressively or omit unless requested