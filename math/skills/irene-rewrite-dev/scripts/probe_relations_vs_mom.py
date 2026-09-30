"""Probe: equality constraint encoded as `relations=` vs as a moment constraint.

Run (any cwd) with Irene's venv interpreter:

    cd /home/YOUR-USER/Code/Python/Irene && \
        .venv/bin/python3 <skill_dir>/scripts/probe_relations_vs_mom.py

Model: min x + y  s.t.  x*y = 1   (true optimum = 2 at (1,1), AM-GM).

What this demonstrates (and what it deliberately does NOT):

* `relations=[xy-1]` measures against the quotient algebra R[x,y]/<xy-1>:
  the reduced monomial basis is strictly smaller than the un-reduced one.
* `MomentConstraint(Mom(xy-1)==0)` only records the scalar moment condition
  E[xy] = 1 in `MomConst` (split into rhs -/+ ErrorTolerance) and leaves the
  full monomial basis in place.
* Do NOT expect a wrong *bound* from the moment route: the moment-matrix PSD
  already encodes the Jensen / Cauchy-Schwarz inequalities that hold on the
  variety, so naive bound-gap examples come out coincidentally tight.
  Structural accounting is the reliable discriminator -- basis size,
  localizing-block count, moment-constraint count, solver status.

Observed (order-2 relaxation, CVXOPT): basis 9 / nLoc 0 / nMom 0 for the
relations route vs basis 15 / nLoc 0 / nMom 2 for the moment route.
Status note: this particular model family reported 'Infeasible' for every
route at orders 1 and 2, although min x+y over the hyperbola is 2 -- treat
'Infeasible' on quotient-algebra relaxations as UN-DIAGNOSED rather than as
proof of infeasibility, and sanity-check against a known feasible point.
"""
import warnings

from sympy import symbols

from Irene.relaxations import Mom, SDPRelaxations

x, y = symbols("x y")


def run(tag, use_relations, use_mom, order):
    try:
        rlx = (SDPRelaxations([x, y], relations=[x * y - 1]) if use_relations
               else SDPRelaxations([x, y]))
        rlx.SetObjective(x + y)
        if use_mom:
            rlx.MomentConstraint(Mom(x * y - 1) == 0)
        rlx.MomentsOrd(order)
        rlx.InitSDP()
        rlx.Minimize()
        out = rlx.Info.get("min")
        basis = rlx.ReducedMonomialBase(2 * order)
        print(f"{tag:36s} f_min={out!r:24s} status={rlx.Info.get('status')!r:12s} "
              f"basis({2 * order})={len(basis):3d} nLoc={len(rlx.Constraints)} "
              f"nMom={len(rlx.MomConst)}")
        return out, len(basis), len(rlx.MomConst)
    except Exception as exc:  # noqa: BLE001
        print(f"{tag:36s} EXCEPTION {type(exc).__name__}: {exc}")
        return None


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    print("TRUE optimum = 2.0\n")
    for order in (1, 2):
        print(f"--- moment order {order} ---")
        run("A: relations=[xy-1]", True, False, order)
        run("B: MomentConstraint(Mom(xy-1)==0)", False, True, order)
        run("C: no constraint at all", False, False, order)
