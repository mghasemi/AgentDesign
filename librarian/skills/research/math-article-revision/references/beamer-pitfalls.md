# Beamer-Specific LaTeX Pitfalls

## `\coloneqq` Requires `mathtools`

`\coloneqq` is not part of `amsmath` — it requires `mathtools`.
A beamer deck that loads only `amsmath` and uses `\coloneqq` fails with:

```
! Undefined control sequence.
\beamer@doifinframe ...\coloneqq
```

**Fix:** Add `\usepackage{mathtools}` to the preamble.
`mathtools` loads and extends `amsmath`, so it can sit alongside or replace it.

## `\newcommand` Double-Subscript Errors

When a `\newcommand` definition already contains a subscript — e.g.,
`\newcommand{\Tmean}{T_{\mathrm{mean}}}` — using it with a further
subscript produces a double-subscript error:

```latex
\newcommand{\Tmean}{T_{\mathrm{mean}}}
...
\Tmean_r           % ERROR: expands to T_{\mathrm{mean}}_r → double subscript!
```

The error looks like:
```
! Double subscript.
\beamer@doifinframe ...- \lambda \;\in\; \Tmean _
                                                  r + ...
```

**Fix A (recommended):** Wrap the macro in braces before adding subscripts:
```latex
{\Tmean}_{,r}        % correct
{\Tmean}^{(1)}       % also correct for superscripts
```

**Fix B:** Redefine the macro to not include subscript braces (less common):
```latex
\newcommand{\Tmean}{T_{\mathrm{mean}}}  % still has subscript internally
% Use: {\Tmean}_r  — still needs braces
```

How to audit a beamer deck for this:
```bash
# Find all \newcommand lines that contain subscripts
grep -n '\\newcommand.*_.*{' beamer.tex

# Find usages that add subscripts to those macros
grep -n '\\Tmean_\|\\Mcal_\|\\Pcal_' beamer.tex
```

The fix pattern `{\Tmean}_{,r}` works for any macro, so when in doubt, brace it.

## Beamer Build Cycle

Beamer decks use 2-pass pdflatex (no bibtex, no `\cite` usually):

```bash
pdflatex -interaction=nonstopmode -halt-on-error deck.tex
pdflatex -interaction=nonstopmode -halt-on-error deck.tex
grep -c '^!' deck.log     # must be 0
```

If the first pass produces no PDF (fatal error), fix errors before the second pass.

## Common Beamer Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Double subscript` | `\cmd_r` where `\cmd` has a `_{...}` | `{\cmd}_r` |
| `Undefined control sequence: \coloneqq` | Missing `mathtools` | `\usepackage{mathtools}` |
| `Environment ... undefined` | Missing `\newtheorem` in preamble | Add declaration |
| `Missing $ inserted` | Math outside math mode in frame | Wrap in `$...$` or `\[...\]` |
