# GPkit Gotchas and Patterns

GPkit is a Python package for geometric programming. Several non-obvious behaviors
cause silent failures or confusing errors. This reference documents patterns discovered
during the SONC-GP and mean-polynomial hierarchy implementations.

## Variable bounds

GPkit requires EVERY variable appearing in the objective to have a lower bound
(expressed as a constraint). The `bounds=` kwarg on `Variable(...)` does NOT
create a GP constraint — it only marks metadata.

**Wrong:**
```python
a = Variable('a', bounds=(1e-6, None))  # no actual constraint
b = Variable('b', value=2.0, bounds=(1e-6, None))
```

**Right:**
```python
a = Variable('a')
b = Variable('b')
constraints = [1e-6/a <= 1.0, 1e-6/b <= 1.0]  # explicit lower bounds
```

## Constant terms

`Posynomial({(): value})` creates a phantom VARIABLE named `\fbox{0}`, not a constant.
This causes "has no lower bound" errors. Use `Monomial({}, value)` instead.

**Wrong:**
```python
obj = Posynomial({(): 3.0})  # Creates a variable named "0"
```

**Right:**
```python
obj = Monomial({}, 3.0)  # Proper constant monomial
```

## Zero-coefficient monomials

GPkit rejects monomials with coefficient 0 ("each c must be positive").
Use conditional construction:

```python
obj = None  # sentinel
for term in possible_terms:
    t = Monomial({}, coeff) if isinstance(coeff, float) else coeff * term
    obj = t if obj is None else obj + t
```

## Constraint format

All constraints must be `posynomial ≤ monomial` (or `≤ 1`).
Use `1/x ≤ 1` instead of `x ≥ 1`.

```python
constraints.append(G_beta / b[beta] <= 1.0)  # good
constraints.append(b[beta] >= G_beta)          # may cause issues
```

## SignomialsEnabled context

When constraints involve posynomial ≤ posynomial (not posynomial ≤ monomial),
use `SignomialsEnabled()`. This requires `localsolve()` instead of `solve()`.

```python
with SignomialsEnabled():
    cns = (lhs + g_minus) <= g_plus
```

## Model construction

Build constraints list first, then construct Model. Do not try to `solve()`
a model with no constraints — it will raise `UnboundedGP`.
