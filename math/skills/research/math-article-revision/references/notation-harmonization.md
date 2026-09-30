# Notation Harmonization When Merging .md Proofs into LaTeX Manuscripts

When inserting a theorem + proof from a standalone `.md` note into an
existing LaTeX manuscript, the note will almost certainly use different
notation (variable names, math alphabets, degree conventions) than the
target manuscript. Audit and adapt these four aspects BEFORE the first
compile.

## 1. Variable Names

The `.md` note may use $x_i$ while the manuscript uses $Y_i$, $X_i$, or
$y_a$. Check the manuscript's Section 2 (preliminaries) for the canonical
variable naming convention and adopt it consistently throughout the
inserted block.

## 2. Math Alphabets

The most dangerous clash: a `.md` note may use $M_{q,p}$ for one form
while the manuscript already reserves $M_{q,p}$ (or $\mathcal{M}_{q,p}$)
for a different but related form. Do not blindly carry the note's
notation into the manuscript.

**Resolution pattern**: If the forms are scalar multiples of each other
(e.g., unnormalized vs. normalized power sums), relate them explicitly
in a transitional sentence:
> $\Phi_{q,q-1} = W^q \cdot M_{q,q-1}$

Then assign a distinct alphabetic variant that won't collide:
$\Phi$, $\mathscr{M}$, $\mathfrak{M}$, $\mathbf{M}$, etc.

## 3. Cross-References

The `.md` note won't have any `\label` / `\ref` at all. After insertion:
- Add `\label{thm:...}` to the new theorem
- Add `\label{lem:...}` to any internal lemmas
- Wire `\ref` back to related existing results (e.g., `\ref{rem:open-questions}`)
- Add a connecting remark that situates the new result within the manuscript

## 4. Environment Names

Verify the manuscript preamble (`\newtheorem` declarations) supports all
environment types used in the proof (e.g., `lemma`, `corollary`). Missing
declarations cause `! LaTeX Error: Environment lemma undefined.` — a
trivial error that breaks compilation.

Check with:
```bash
grep -n '\\newtheorem' paper.tex
```

## 5. Degree / Exponent Conventions

The manuscript may normalize exponents differently than the note.
For example, the note may define $P_k = \sum w_i x_i^k$ (raw power sum)
while the manuscript uses $M_p(Y,w) = (\sum w_i Y_i^p / \sum w_i)^{1/p}$
(normalized power mean). Both are related by a factor of $W^k$ or
$W^{-k/p}$, and this scaling affects the form's degree and
homogeneity. Verify the degree matches the manuscript's conventions
before asserting the form belongs to a specific cone ($\mathcal{P}_{n,2d}$,
$\Sigma_{n,2d}$, etc.).

## Example: Merging MeanTheorem.md into mean_polynomials_combined_v2.tex

The note defined:
$$M_{q,q-1}(x) = W \cdot P_q(x)^{q-1} - P_{q-1}(x)^q$$

The manuscript already uses $M_{q,p}(Y,w)$ for the normalized mean polynomial form.
Resolution: rename to $\Phi_{q,q-1}(Y,w)$, state the relationship
$\Phi_{q,q-1} = W^q \cdot M_{q,q-1}$, and use manuscript variables $Y_i$.
