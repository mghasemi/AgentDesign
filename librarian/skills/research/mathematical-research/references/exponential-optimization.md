# Exponential Optimization Analysis and Results

## Summary of Findings  
We analyzed the minimization problem for $f(x) = e^x - x^2$ on the interval $[-2, 2]$ considering auxiliary variables and constraints. The constraint system was found to be inconsistent, which led us to solve it as a standard optimization problem.

## Constraint System Analysis
The original constraint system:
1. $d_x(x) = 1$ - Trivial identity, always holds
2. $d_x(y) = y$ - Implies $dy/dx = y$, general solution: $y(x) = C \cdot e^x$
3. $d_y(y) = 1$ - Trivial identity when $y \neq 0$
4. $y \cdot d_y(x) = 1$ - Implies $dy/dx = 1/y$, which contradicts constraint 2

**CRITICAL OBSERVATION**: The system is inconsistent! Constraint 2 requires $dy/dx = y$ while constraint 4 requires $dy/dx = 1/y$. These can only both be true if $y^2 = 1$, which doesn't satisfy the exponential relationship for general x values.

**CONCLUSION**: The constraints do NOT uniquely identify $y = e^x$. We must treat this as a standard optimization problem without these constraints.

## Optimization Results
We used two numerical methods to find the minimum of $f(x) = e^x - x^2$ on $[-2, 2]$:

### Method 1: Bounded Minimization (Local Optimizer)
- **Optimal x**: $x^* \approx -1.9957$
- **Minimum value**: $f(x^*) \approx -3.8467$ 
- **Method Type**: Local optimizer with box constraints, good for unimodal functions

### Method 2: Differential Evolution (Global Optimizer)
- **Optimal x**: $x^* = -2.0000$
- **Minimum value**: $f(x^*) \approx -3.8647$ 
- **Method Type**: Global stochastic search, explores entire search space

### Key Observations:
1. The minimum occurs at the left endpoint of the interval ($x = -2$)
2. Both methods converge to similar results (difference ~0.018 in function value)
3. Differential evolution finds a slightly lower point but is more computationally intensive
4. The bounded minimization is sufficiently accurate for practical purposes