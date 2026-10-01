---
name: user-latex-style
description: Use when writing, editing, or compiling any LaTeX manuscript for YOUR-USER User. Encodes document class, theorem styles, macro conventions, bibliography format, and refined prose tone.
---

# User LaTeX Style Guide

## 1. Document Class & Preamble

```latex
\documentclass{amsart}
\usepackage{amsmath, amssymb, mathrsfs, verbatim}
```

**Additional packages** as needed: `amsthm`, `xifthen`, `color`, `multirow`, `\usepackage[arrow, matrix]{xy}` for commutative diagrams.

### Hyperref — colored links (standard for all documents)

```latex
\definecolor{DarkBlue}{rgb}{0,0.2,0.6}
\definecolor{PinkPurple}{rgb}{0.8,0.3,0.3}

\usepackage[pdftex,
  pdfauthor={...},
  pdftitle={...},
  pdfsubject={...},
  pdfkeywords={...},
  linkcolor=DarkBlue,
  citecolor=PinkPurple,
  colorlinks=true]{hyperref}
```

Always include PDF metadata and colored links. Drop `\mathsym`/`\unicode` no-ops — they are SageMath export artifacts.

---

## 2. Theorem Environments

```latex
\newtheorem{thm}{Theorem}[section]
\newtheorem{lemma}[thm]{Lemma}
\newtheorem{prop}[thm]{Proposition}
\newtheorem{crl}[thm]{Corollary}

\theoremstyle{definition}
\newtheorem{dfn}[thm]{Definition}
\newtheorem{exm}[thm]{Example}
\newtheorem{qus}[thm]{Question}
\newtheorem{rem}[thm]{Remark}

\numberwithin{equation}{section}
```

Remarks are upright (`\theoremstyle{definition}`), not italic. Names are short: `thm` not `theorem`, `exm` not `example`, `crl` not `corollary`.

---

## 3. Macro Hierarchy

### Number fields (universal)
```latex
\newcommand{\reals}{\mathbb{R}}
\newcommand{\naturals}{\mathbb{N}}
\newcommand{\integers}{\mathbb{Z}}
\newcommand{\cplx}{\mathbb{C}}
\newcommand{\rationals}{\mathbb{Q}}
```

### Polynomial rings & SOS
```latex
\newcommand{\ux}{\underline{X}}
\newcommand{\sgr}[2]{#1[#2]}
\newcommand{\rx}{\sgr{\mathbb{R}}{\ux}}
\newcommand{\fps}[2]{#1\lsem #2\rsem}
\newcommand{\rfps}{\fps{\mathbb{R}}{\underline{X}}}
\newcommand{\sos}{\sum\mathbb{R}[\underline{X}]^2}
\newcommand{\ringsos}[1]{\sum #1^2}
\newcommand{\ringsop}[2]{\sum #1^{#2}}
```

### Structural
```latex
\newcommand{\pos}[1]{\mbox{Pos}(#1)}
\newcommand{\K}[1]{\mathcal{K}_{#1}}
\newcommand{\supp}{\text{supp}}
\newcommand{\spn}{\text{Span}}
\newcommand{\la}{\langle} \newcommand{\ra}{\rangle}
\newcommand{\cl}[2]{\overline{#2}^{\ifthenelse{\isempty{#1}}{}{#1}}}
\newcommand{\norm}[2]{\|\ifthenelse{\isempty{#2}}{\cdot}{#2}\|_{#1}}
```

---

## 4. Bibliography — Manual `thebibliography`

```latex
\begin{thebibliography}{99}

\bibitem{gha-mar2}
M. Ghasemi, M. Marshall,
\emph{Lower bounds for polynomials using geometric programming},
SIAM J. Optim. \textbf{22}(2) (2012), 460--473.

\end{thebibliography}
```

- Authors: initials first, "and" before last author. Title in `\emph{...}`. Volume in `\textbf{...}`.
- Citation keys: short alphanumeric — `{FK}`, `{gha-mar1}`, `{lasserre1}`. Own papers: `gha-*` prefix.
- In-text: `\cite{key}`, `\cite[Theorem 3.1]{key}`. No BibTeX, no `.bib` files.
- Use semantic `\emph{}` / `\textbf{}` — never `{\em ...}` or `{\bf ...}`.

---

## 5. Prose Tone — Refined

### Core register
The voice is that of a senior mathematician addressing peers: authoritative, economical, and precise. Every sentence earns its place.

### Sentence-level patterns

**Opening a section** — define the objects, state the goal immediately:
> Fix $f \in \mathbb{R}[\mathbf{x}]$ of degree $2d$. We determine a lower bound for $f$ on $K_{\mathbf{g}}$ computable by geometric programming.

**Stating a result** — front-load the claim, then provide conditions:
> Theorem 3.1 establishes that $f_{\operatorname{gp}}$ is a lower bound for $f$ on $\mathbb{R}^n$, provided the feasible set of (3.1) is nonempty.

**Signposting structure** — brief, embedded in the narrative, not a bullet list:
> The proof proceeds in three steps. We first reduce to the case $m=0$, then apply Theorem 2.1, and finally verify the inequality constraints are tight.

**Handling edge cases** — dismiss trivialities quickly, name the interesting regime:
> If $\deg(f) < d$ then either $\Delta(f) = \emptyset$ and $f_{\operatorname{gp}} = f(0)$, or $\Delta(f) \neq \emptyset$ and $f_{\operatorname{gp}} = -\infty$. The case of interest is $\deg(f) = d$.

**Comparing results** — direct, no hedging:
> The bound obtained is typically weaker than the SDP bound, but the computation is orders of magnitude faster.

### What to avoid
- **Passive indirection**: "It can be shown that..." → "We prove that..."
- **Hedging**: "One might argue..." / "It seems plausible..." → Assert or qualify explicitly.
- **Throat-clearing**: "In this section we will consider..." → Start the mathematics.
- **Over-enumeration**: Don't number every paragraph or use bullet lists in prose — embed the structure in sentences.
- **Colloquial filler**: "basically", "essentially", "kind of", "pretty much".

### Acknowledgements
```latex
\section*{Acknowledgements}
The authors thank the anonymous referees for comments that improved the clarity of the presentation.
```
Use `\section*{Acknowledgements}`, not inline `\noindent \bf ... \rm`.

---

## 6. Title Block

```latex
\title[Short title]{Full Title}
\date{}
\author{Names}        % or \author[short]{Names$^1$, Names$^2$}
\address{$^1$Department, \\ University, \\ City, Country}
\email{emails}
\keywords{kw1, kw2, kw3}
\subjclass[2010]{Primary XX XXX Secondary XX XXX}
\begin{abstract} ... \end{abstract}
\maketitle
```

---

## 7. Sections & Cross-References

- Section titles lowercase in source: `\section{introduction}`, `\section{the main result}`
- Labels: `\label{thm:main}`, `\ref{thm:main}`. Never hard-code numbers.
- Display math: `\[...\]` or `\begin{equation}...\end{equation}` with `\label{eq:name}`.

---

## 8. Non-Negotiables

- `\documentclass{amsart}` — never `article`/`report`
- Remarks upright via `\theoremstyle{definition}` — never italic
- Manual `thebibliography` — no BibTeX/biblatex
- First person plural ("we") throughout — never "I" in body text
- Semantic font commands (`\emph`, `\textbf`) — never `{\em}`, `{\bf}`, `{\rm}`, `{\it}`
- Colored hyperlinks with full PDF metadata — never bare `\usepackage{hyperref}`

---

## 9. AI-Generated Anti-Patterns (never use)

The following structures appear in AI-generated `.tex` files but are absent from all 15 of your published manuscripts. Treat as forbidden.

### Preamble violations
| Anti-pattern | Fix |
|---|---|
| `\documentclass{article}` or `\documentclass[12pt]{article}` | `\documentclass{amsart}` |
| `\usepackage{amsfonts}` | Never used — drop it |
| `\usepackage{booktabs}` | Never used — drop it; use plain `\hline` in tables |
| `\usepackage{graphicx}` | Never used in your math papers |
| `\usepackage[left=3cm,...]{geometry}` | Let `amsart` handle margins |
| `\bibliographystyle{plain}` + `\bibliography{...}` | BibTeX — never. Use manual `\begin{thebibliography}` |
| `\setcounter{MaxMatrixCols}{20}` | Never used |

### Theorem environment violations
| Anti-pattern | Fix |
|---|---|
| `\newtheorem{theorem}{Theorem}` (long name, no shared counter) | `\newtheorem{thm}{Theorem}[section]` |
| `\newtheorem{proposition}[theorem]{Proposition}` (shares `theorem` counter) | `\newtheorem{prop}[thm]{Proposition}` |
| `\newtheorem{conjecture}{Conjecture}` | Never used in your work — drop it |
| `\theoremstyle{remark}` + `\newtheorem{remark}{Remark}` | `\theoremstyle{definition}` + `\newtheorem{rem}[thm]{Remark}` |
| `\newtheorem*{notation}{Notation}` (starred env) | Never used |
| `\DeclareMathOperator{\Pos}{Pos}` blocks | Use `\operatorname{Pos}` inline or `\mbox{Pos}`; only declare if used 5+ times |

### Section & structure violations
| Anti-pattern | Fix |
|---|---|
| `\section{Introduction}` (capitalized in source) | `\section{introduction}` (lowercase; amsart handles display) |
| `\section{The CGIK Truncated Moment Problem}` (long, capitalized) | `\section{the cgik truncated moment problem}` or shorter lowercase titles |
| `\subsection{...}`, `\subsubsection{...}` deep nesting | Flatten to sections + inline headings if needed |
| `\subsection*{Structure of the Paper}` with bullet lists | Embed structure in a short narrative paragraph — never a bulleted outline |
| `\label{sec:cgik-noncompact}` (long structured labels) | `\label{cgik}` or `\label{noncompact}` — short, no colons |
| `\appendix` + `\section{...}` inside | Appendices are extremely rare in your work; use only if genuinely needed |

### Prose & formatting violations
| Anti-pattern | Fix |
|---|---|
| `\textbf{Phase~1: Rational Lifting}` (inline bold headings with colons) | Use theorem/remark environments; never bold inline headings |
| `\medskip\noindent\textbf{...}` | If it needs a heading, it's a Remark or a paragraph in a proof |
| `\S\ref{s02}` | `Section~\ref{s02}` or `\S\ref{s02}` if space is tight — but prefer spelled-out |
| `\textsuperscript{th}` | `$r$th` or just `$r$-th` |
| `\texttt{CommutativeSemigroup}` (typewriter for code) | Never used in math papers — use italics or just the name |
| Multi-line titles with `\\` in `\title{}` | Keep the title one line; use `[short title]` option |
| `\thanks{...}` for affiliation | `\address{...}` and `\email{...}` |
| `\date{\today}` | `\date{}` for drafts |
| Unicode box-drawing comment separators (`% ═══════`) | `%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%` or nothing |
| `\toprule`/`\midrule`/`\bottomrule` (booktabs) | `\hline` only |
| `\begin{proof}[Proof sketch]` (custom proof name) | `\begin{proof}` only; embed "Proof sketch" in first sentence if needed |

### Over-verbose prose patterns (AI tells)
- **Survey-style intros**: "The certification of nonnegativity for multivariate polynomials is a central problem in real algebraic geometry with significant applications..." → Start with the specific problem and your contribution.
- **Roadmap paragraphs**: "The remainder of this paper is organized as follows. In \S\ref{s02}, we provide... In \S\ref{s03}, we revisit..." → One sentence max, or omit entirely.
- **Motivational throat-clearing**: "The polynomial restriction, however, excludes a vast class..." → Just state the gap and your solution.
- **Bulleted paper outlines**: `\begin{itemize} \item In \S2...` → Embed in prose or drop.
- **Over-explained methodology**: "The fundamental building block of the whole theory is a simple algebraic identity showing that..." → State the lemma; the proof speaks for itself.

