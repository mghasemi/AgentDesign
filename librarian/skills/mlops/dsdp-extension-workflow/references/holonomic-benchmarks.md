# Holonomic Benchmark Patterns

Concrete configurations for testing DSDP multi-derivation on P7/P8-class problems.

## P7 Polynomial Shortcut

When the objective is monotone in a lifted function, use the argument directly:

```python
# min e^{xt} on [-4,4]² ≡ min(xt)
dsdp = DSDPRelaxations([x, t], relations=[],
    q=1, p=0, depth=1, archimedean=True, box_size=4, verbosity=0, Parallel=True)
dsdp.SetObjective(x * t)
lb = dsdp.solve(order=2)  # exact: -16.0
```

## P7 Multi-Derivation ADE Lift

```python
x, t, y = Symbol('x'), Symbol('t'), Symbol('y')
tmp = DSDPRelaxations([x, t, y])
dx_syms, dx_rels, _ = tmp.build_ade_relations({x:1, t:0, y:t*y}, wrt='x')
dt_syms, dt_rels, _ = tmp.build_ade_relations({x:0, t:1, y:x*y}, wrt='t')
all_gens = list(dx_syms.values()) + list(dt_syms.values()) + [x, t, y]
all_rels = dx_rels + dt_rels

dsdp = DSDPRelaxations(all_gens, relations=all_rels,
    q=1, p=0, depth=1,
    diff_maps={'x': {x:1,t:0,y:t*y}, 't': {x:0,t:1,y:x*y}},
    original_gens=[x,t,y],
    archimedean=True, box_size=4, verbosity=0, Parallel=True)
dsdp.SetObjective(y)
lb = dsdp.solve(order=d)
# LB ≈ -4.0 (loose — no positivity invariant for exp)
```

## P8 Minimal Algebraic (7 gens, 2 invariants)

The largest practical Groebner configuration for the current engine:

```python
x,y,s,c,L,v,w = Symbol('x'),Symbol('y'),Symbol('s'),Symbol('c'),Symbol('L'),Symbol('v'),Symbol('w')
gens = [x,y,s,c,L,v,w]
rels = [s**2+c**2-1, y*v-1]  # invariants only, no derivative symbols
obj = x*L - y*s*w

dsdp = DSDPRelaxations(gens, relations=rels,
    q=1, p=0, depth=1, archimedean=True, box_size=8, verbosity=0, Parallel=True)
dsdp.SetObjective(obj)
dsdp.AddConstraint(2-x>=0); dsdp.AddConstraint(x+2>=0)
dsdp.AddConstraint(2-y>=0); dsdp.AddConstraint(y-Rational(1,2)>=0)
lb = dsdp.solve(order=d)
# LB ≈ -32.0, 947% gap (independent of d — relaxation saturated)
```

## P8 KKT Injection — THE REMEDY

Use `diff_maps` with `use_diff_kkt=True` to add differential stationarity constraints
as moment constraints **without adding derivative symbols to the generator list**.
This avoids Groebner explosion entirely while tightening bounds dramatically.

### D_x only (617% gap)

```python
dm_x = {x:1, s:pi*c, c:-pi*s, w:w}
dsdp = DSDPRelaxations([x,y,s,c,L,v,w],
    relations=[s**2+c**2-1, y*v-1],
    diff_map=dm_x, use_diff_kkt=True,
    q=1, p=0, depth=1, archimedean=True, box_size=8, verbosity=0, Parallel=True)
dsdp.SetObjective(x*L - y*s*w)
dsdp.AddConstraint(2-x>=0); dsdp.AddConstraint(x+2>=0)
dsdp.AddConstraint(2-y>=0); dsdp.AddConstraint(y-Rational(1,2)>=0)
lb = dsdp.solve(order=1)
# LB ≈ -21.92, 617% gap (was 947% without KKT)
```

### D_x + D_y (100% gap)

```python
dm_xy = {
    'x': {x:1, s:pi*c, c:-pi*s, w:w},
    'y': {y:1, L:v, v:-v**2}
}
dsdp = DSDPRelaxations([x,y,s,c,L,v,w],
    relations=[s**2+c**2-1, y*v-1],
    diff_maps=dm_xy, use_diff_kkt=True,
    q=1, p=0, depth=1, archimedean=True, box_size=8, verbosity=0, Parallel=True)
dsdp.SetObjective(x*L - y*s*w)
dsdp.AddConstraint(2-x>=0); dsdp.AddConstraint(x+2>=0)
dsdp.AddConstraint(2-y>=0); dsdp.AddConstraint(y-Rational(1,2)>=0)
lb = dsdp.solve(order=1)
# LB ≈ 0.0, 100% gap (was 947%, then 617% with D_x only)
```

### KKT constraints added

- **D_x(obj)** = L − y·w·(πc + s) = 0  (degree 3)
- **D_y(obj)** = x·v − s·w = 0          (degree 2)

Both are added as moment constraints via `add_ade_moment_constraint()`.
The `solve()` method iterates all `diff_maps` keys automatically (v1.3+).

### Why this works

The KKT constraints encode the differential relationships between lifted variables
(sin/cos/exp/log) **without adding derivative symbols as generators**. This avoids
the 14-generator Groebner explosion while still constraining the feasible moment set.

## P8 Full ADE (14 gens) — TIMEOUT >180s

```python
# Build D_x ADE: {x:1, s:πc, c:-πs, w:w}
tmp_x = DSDPRelaxations([x,s,c,w])
dx_syms, dx_rels, _ = tmp_x.build_ade_relations(
    {x:1, s:Pi*c, c:-Pi*s, w:w}, wrt='x')

# Build D_y ADE: {y:1, L:v, v:-v²}
tmp_y = DSDPRelaxations([y, L, v])
dy_syms, dy_rels, _ = tmp_y.build_ade_relations(
    {y:1, L:v, v:-v**2}, wrt='y')

# Merge — 14 generators, 9 relations → Groebner timeout >180s
all_gens = list(dx_syms.values())+list(dy_syms.values())+[x,y,s,c,L,v,w]
all_rels = dx_rels + dy_rels + [s**2+c**2-1, y*v-1]
```

## Gap Reporting Convention

```python
GT = -3.057836140573  # ground truth
gap = abs(float(lb) - GT) if lb else None
rel_gap = gap / abs(GT) * 100 if gap else None
print(f"LB={float(lb):.8f}, gap={gap:.4f}, rel={rel_gap:.1f}%, {elapsed:.1f}s")
```

## Benchmark Summary (2026-07-18)

| Config | Gens | Rels | d=1 LB | d=1 Gap | d=2 LB | d=2 Gap |
|---|---|---|---|---|---|---|
| P7 polynomial shortcut | 2 | 0 | dual infeas | — | **-16.00** | **0.00%** |
| P7 multi-deriv ADE | 9 | 6 | -4.00 | 3.5×10⁹% | -4.00 | 3.5×10⁹% |
| P8 no KKT | 7 | 2 | -32.00 | 946.5% | -32.00 | 946.5% |
| P8 D_x KKT only | 7 | 2 | -21.92 | 616.9% | -21.92 | 616.9% |
| P8 D_x + D_y KKT | 7 | 2 | **≈0.00** | **100.0%** | **≈0.00** | **100.0%** |
| P8 full ADE | 14 | 9 | timeout | — | timeout | — |
