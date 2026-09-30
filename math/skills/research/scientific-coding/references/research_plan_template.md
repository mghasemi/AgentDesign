# Research Plan Template

For experimental research tasks (like ADE+SDP numerical improvement),
use this plan structure. It's distinct from the software-engineering
plan in the `plan` skill — this is for *research exploration*, not
*implementation*.

## Structure

### 0. Gap Map
List each barrier with current gap and dominant cause, e.g.:
```
| P7 Torus-Curve | 8.34% | S¹×S¹ torus ≠ 1D curve at d=2 |
| P8 Logarithmic | 10.73% | log(y) has no polynomial invariant |
```

### 1–N. Research Directions
Per barrier, one section containing:
- **Inspiration:** paper, theorem, or technique being adapted
- **Core idea:** one-paragraph description
- **Expected outcome:** quantitative gap reduction target
- **Feasibility:** High / Medium / Low with justification
- **Risk:** Low / Medium / High with failure modes
- **Priority:** star rating
- **Concrete experiment script** (when feasible)

### Priority Matrix
Table ranking all directions by feasibility × expected impact.

### Recommended First Experiment
The one direction with highest (feasibility × impact) — justify the choice.

### Open Questions
Unresolved theoretical blockers that the experiments may illuminate.

### Implementation Timeline
Week-by-week plan with deliverables.

## Pitfalls

- **Don't propose without testing.** Every attack vector in the plan
  should have a concrete, runnable experiment script. Vague directions
  are noise.
- **Document dead ends immediately.** When an experiment fails, record
  the failure in the skill reference before moving on. Otherwise the
  next session re-explores the same dead end.
- **Literature search first, then experiment.** Check arXiv/Google
  Scholar before implementing — you may find an existing approach that
  either validates or invalidates your idea.

## Reference

See `scientific-coding/references/ade_sdp_attack_vectors.md` for the
canonical taxonomy. See `ade_sdp_dead_ends_and_pitfalls.md` for what's
been eliminated.
