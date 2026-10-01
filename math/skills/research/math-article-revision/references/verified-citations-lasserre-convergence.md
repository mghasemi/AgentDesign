# Verified citations: Lasserre convergence rates & differential Nullstellensatz

All entries verified against publisher pages on 2026-08-14 (truncation-theory
revision). Paste the bibitem forms verbatim; they follow the user-latex-style
manual `thebibliography` conventions.

## Finite convergence under regularity conditions

- **J. Nie, "Optimality conditions and finite convergence of Lasserre's hierarchy", Math. Program. 146 (2014), 97--121.** (arXiv:1206.0319)
  If the Archimedean condition holds and, at every global minimizer, the linear
  independence constraint qualification, strict complementarity, and second-order
  sufficiency hold, then Lasserre's hierarchy has finite convergence ($p_d = f_{\min}$).

```latex
\bibitem{nie14}
J.~Nie,
\emph{Optimality conditions and finite convergence of Lasserre's hierarchy},
Math. Program. \textbf{146} (2014), 97--121.
```

## Algebraic rate O(1/d) on specific compact sets

- **K. Fang, H. Fawzi, "The sum-of-squares hierarchy on the sphere and applications in quantum information theory", Math. Program. 190 (2021), 331--360.** (arXiv:1908.05155)
  SOS-hierarchy rate $O(1/r)$ for homogeneous polynomial optimization on the sphere.
  **Mis-citation trap:** frequently written "Fawcett" in reviewer feedback — no such paper.

```latex
\bibitem{fang-fawzi}
K.~Fang and H.~Fawzi,
\emph{The sum-of-squares hierarchy on the sphere and applications in quantum information theory},
Math. Program. \textbf{190} (2021), 331--360.
```

- **S. Gribling, E. de Klerk, J. C. Vera, "Revisiting the convergence rate of the Lasserre hierarchy for polynomial optimization over the hypercube", arXiv:2505.00544 (2025)**; also published in *Optimization* (2026), DOI 10.1080/02331934.2026.2641624.
  Same $O(1/r)$ rate on $[-1,1]^n$ — the relevant geometry when box constraints place the feasible set inside a hypercube.

```latex
\bibitem{gkv}
S.~Gribling, E.~de Klerk, and J.~C. Vera,
\emph{Revisiting the convergence rate of the Lasserre hierarchy for polynomial optimization over the hypercube},
preprint, arXiv:2505.00544 (2025).
```

## Effective differential Nullstellensatz (prolongation order bounds)

- **O. Golubitsky, M. Kondratieva, A. Ovchinnikov, A. Szántó, "A bound for orders in differential Nullstellensatz", J. Algebra 322(11) (2009), 3852--3877.** (arXiv:0803.0160)
  Order bounds for differential elimination expressed through the Jacobi number of
  the generating system; for linear first-order ADE systems the Jacobi number is at
  most the number of state variables, so the bound is small and explicit.

```latex
\bibitem{gkos}
O.~Golubitsky, M.~Kondratieva, A.~Ovchinnikov, and A.~Sz\'ant\'o,
\emph{A bound for orders in differential Nullstellensatz},
J.~Algebra \textbf{322}(11) (2009), 3852--3877.
```

## Worst-case (logarithmic) baseline

- **J. Nie, M. Schweighofer, "On the complexity of Putinar's Positivstellensatz", J. Complexity 23(1) (2007), 135--150.**
  $D(c) = O(\exp(c_1 (f_{\min}-c)^{-c_2}))$ — the pessimistic bound the regular/domain-specific rates above improve upon.
