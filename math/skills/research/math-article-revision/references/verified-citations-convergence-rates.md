# Verified Citations: Lasserre-Hierarchy Convergence Rates

Session-verified bibliography entries (2026-08-14, primary sources checked via
search + publisher pages) for remarks about convergence rates of the moment-SOS /
Lasserre hierarchy — the cluster most often cited when refining worst-case
Nie--Schweighofer bounds in DSDP / polynomial-optimization manuscripts.

## Citation map (what each paper actually proves)

| Reference | Result | Conditions |
|---|---|---|
| Nie, Math. Program. 146 (2014), 97--121 (arXiv:1206.0319) | FINITE convergence of Lasserre's hierarchy | Archimedean + LICQ + strict complementarity + second-order sufficiency at every global minimizer |
| Fang--Fawzi, Math. Program. 190 (2021), 331--360 (arXiv:1908.05155) | Algebraic rate $f_{\min}-f_d = O(1/d)$ | Homogeneous polynomial optimization on the sphere |
| Gribling--de Klerk--Vera, arXiv:2505.00544 (2025) | Algebraic rate $O(1/d)$ | Polynomial optimization on the hypercube $[-1,1]^n$ — the relevant geometry when box constraints box the lifted set |
| Nie--Schweighofer, J. Complexity 23 (2007), 135--150 | Worst-case bound $D(c)=O(\exp(c_1(f_{\min}-c)^{-c_2}))$ | Archimedean quadratic module, Putinar module form |
| Schweighofer, J. Complexity 20 (2004), 529--543 | Worst-case bound, Schmuedgen form | Preordering form |
| Burer--Monteiro, Math. Program. 95(2) (2003), 329--357 | Low-rank factorization $X = RR^\top$ for SDPs | $r$ = target rank (the flat rank in moment problems) |
| Golubitsky--Kondratieva--Ovchinnikov--Szanto, J. Algebra 322(11) (2009), 3852--3877 (arXiv:0803.0160) | Order bound for differential Nullstellensatz / differential elimination | Expressed via the Jacobi number of the generating system |

## Name-collision trap

A reviewer recommendation cited "Nie, Fang, and Fawcett". There is NO
Fang--Fawcett paper; "Fawcett" is a typo for **Fawzi** (Hamza Fawzi, Cambridge,
SOS hierarchy / quantum information). Always verify reviewer-named authors
before inserting bib entries; correct silently in the manuscript and mention
the correction in the session summary.

## LaTeX-ready entries (manual thebibliography style)

    \bibitem{nie14}
    J.~Nie,
    \emph{Optimality conditions and finite convergence of Lasserre's hierarchy},
    Math. Program. \textbf{146} (2014), 97--121.

    \bibitem{fang-fawzi}
    K.~Fang and H.~Fawzi,
    \emph{The sum-of-squares hierarchy on the sphere and applications in quantum information theory},
    Math. Program. \textbf{190} (2021), 331--360.

    \bibitem{gkv}
    S.~Gribling, E.~de Klerk, and J.~C. Vera,
    \emph{Revisiting the convergence rate of the Lasserre hierarchy for polynomial optimization over the hypercube},
    preprint, arXiv:2505.00544 (2025).

    \bibitem{burer-monteiro}
    S.~Burer and R.~D.~C. Monteiro,
    \emph{A nonlinear programming algorithm for solving semidefinite programs via low-rank factorization},
    Math. Program. \textbf{95}(2) (2003), 329--357.

    \bibitem{gkos}
    O.~Golubitsky, M.~Kondratieva, A.~Ovchinnikov, and A.~Sz\'ant\'o,
    \emph{A bound for orders in differential Nullstellensatz},
    J.~Algebra \textbf{322}(11) (2009), 3852--3877.

## Remark-writing pattern that worked

- Insert a new regularity/rate remark AFTER the theorem's `\end{proof}` and
  before the next `\subsection` — downstream numbering shifts, which is safe
  in a fully `\ref`-based manuscript.
- Structure: worst-case bound is pathological (governed by Lojasiewicz-type
  exponents) → Nie gives finite convergence under regularity → Fang--Fawzi /
  Gribling give algebraic rates → the boxed lifted set makes the hypercube
  result the directly relevant one.
- Reviewer asked for "polynomial rate under Strict Complementarity, SOSC,
  LICQ" — the accurate, stronger statement is: Nie = finite convergence under
  those conditions; Fang--Fawzi + Gribling--de Klerk--Vera = unconditional
  algebraic rates on sphere/hypercube.
