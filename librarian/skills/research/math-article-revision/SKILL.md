---
name: math-article-revision
description: "Use when revising math LaTeX articles. Multi-edit workflow."
related_skills: [user-latex-style, latex-manuscript]
---

**Prerequisite**: Load `user-latex-style` before any content edits. It defines the authoritative conventions — `amsart` class, theorem environment names, macro hierarchy, colored hyperlinks, and prose tone. When adding new theorems, environments, or bibliography entries, follow that skill's patterns exactly.

# Math Article Revision

Use when revising mathematical articles in LaTeX — applying reviewer feedback,
merging content from subsidiary references, restructuring sections, or making
multi-edit changes with a compile-then-verify workflow.

## When to Use

- Applying reviewer/advisor feedback that spans multiple sections
- Merging content from a subsidiary manuscript or note into a main article
- Restructuring sections (renaming, reordering, promoting/demoting subsections)
- Batch-editing LaTeX with citation/bib management side effects
- Verifying that LaTeX changes actually appear correctly in the compiled PDF

## When Not to Use

- Initial composition or first-draft writing — use `latex-manuscript`
- Single-line fixes (typos, one broken reference) — use `patch` directly
- Bibliography-only changes — use `project-bib` or `zotero`

## Core Workflow

### 1. Locate and Read

Use `terminal` with `grep -n` and `sed -n` to read the article's current state.
The `read_file` tool can fail on files with complex paths; `sed` via terminal
is the reliable fallback:

```bash
grep -n "pattern" paper.tex          # find line numbers
sed -n '100,150p' paper.tex          # read specific range
grep -n "\\cite{" paper.tex        # find all citations
```

### 2. Edit with `patch` (preferred) or Python

**Primary approach: `patch` with `mode='replace'`.** The `patch` tool works
correctly for LaTeX when using `mode='replace'` — backslashes are NOT
doubled. Batch independent edits (different file regions) in parallel calls
for efficiency.

**Line-wrap pitfall with `patch`:** if a `mode='replace'` patch fails with
"Could not find a match", the usual cause is a wrong guess about where the
source wraps lines (e.g., you wrote `in\n  \cite{...}` when the file has
`in \cite{...}` on one line). Fuzzy matching does NOT rescue a wrong
line-wrap guess inside math/`\cite` runs. Re-read the exact region with
`read_file` and match the file's actual wrapping — or shrink the anchor to
a short unique fragment that fits on one source line. Do not retry the same
patch with re-guessed wrapping more than twice.

**Fallback: `execute_code` with Python.** When `execute_code` is available
and you need complex multi-edit logic (loops, conditionals, replace-between),
use Python string operations with raw strings (`r"..."`).

**Fallback: `terminal` with Python heredoc.** When `execute_code` is blocked
(cron/background mode), pipe a Python script via:
```bash
python3 /dev/stdin << 'PYEOF'
... Python edits ...
PYEOF
```
Caution: the terminal tool's hardline parser blocks large inline payloads
that combine a heredoc with command substitution (`$(...)`) and pipes. If a
command comes back `BLOCKED (hardline)`, do not retry it inline — write the
script to a file with `write_file` and run `python3 script.py` (the file
path is echoed in the block message for review). Small single-purpose
heredocs usually pass (auto-approved); the block fires on oversized/compound
payloads.

Three patterns cover most editing needs:

**Pattern A: Simple replacement** (for edits matching a single unique anchor)
```python
with open("paper.tex", "r") as f:
    content = f.read()

old = r"""\subsection{Old Title}\label{sec:old}
Some paragraph text that uniquely identifies this location."""

new = r"""\subsection{New Title}\label{sec:new}
Replacement text with $\alpha$ and \textbf{bold} and \cite{Key}."""

assert old in content, "ANCHOR NOT FOUND — check whitespace/line endings"
content = content.replace(old, new)

with open("paper.tex", "w") as f:
    f.write(content)
```

**Pattern B: Replace-between** (for edits that replace everything between
a start marker and an end marker — preferred when the edit target spans many
lines where matching the entire old text would be fragile)
```python
def replace_between(content, start_marker, end_marker, new_text):
    """Replace content from start_marker (inclusive) through end_marker
    (inclusive). Returns None if either marker is not found."""
    s = content.find(start_marker)
    if s == -1:
        return None
    e = content.find(end_marker, s + len(start_marker))
    if e == -1:
        return None
    return content[:s] + new_text + content[e + len(end_marker):]

# Usage — markers are kept in new_text so they survive the replacement
content = replace_between(content,
    r"""\subsection{Old Title}""",
    r"""(\S\ref{sec:next}).""",
    r"""\subsection{New Title}
...replacement content spanning multiple paragraphs...
(\S\ref{sec:next}).""")
assert content is not None, "Replace-between failed — marker not found"
```

**Multi-edit batching**: When a session needs edits across multiple
non-contiguous sections, batch all changes into one `execute_code` block —
read the file once, apply all replacements, write once. This avoids the
`read_file` dedup issue and is faster than separate `execute_code` calls.
For a large review disposition (10–20 items), make the batch *atomic*:
assert `content.count(old) == 1` for each `(name, old, new)` triple, collect
failures into a `failed` list (a count of 0 means the anchor drifted, >1
means it is ambiguous — fix before writing), and only `f.write` the file if
every edit matched exactly once. A count of 2 on an anchor that looked
unique is usually a preamble duplicate: in the ghasemi-style preamble the
`\keywords{...}` line shares its text with the hyperref `pdfkeywords={...}`
option (and titles mirror `pdftitle`), so a substring of the keyword list
matches twice. Anchor the full line including the leading command
(`\keywords{...}`), then re-run the WHOLE batch — never patch the single
failed anchor alone. When one anchor fails, the file is left
untouched (assert-before-write) — diagnose the failed anchor by printing
the exact source region with `sed -n 'N,Mp' file | cat -A` (the `-A` reveals
the actual line wrapping and trailing spaces that broke the match) rather
than re-guessing the wrap, then re-run the whole batch. Never fix a single
failed anchor with a standalone edit: partial application defeats the
atomicity that makes review-disposition batches auditable. After writing, run a residual
`re.findall` sweep for the forbidden patterns (e.g. `H^n(G,\Pcal`,
"Choquet boundary measures") to confirm none survive, then a final `grep`
on the .tex — a source-level grep is more reliable than pymupdf for
confirming a forbidden *math-mode* pattern is gone (superscripts/Greek
fail to extract).

**Wholesale section replacement (line-splice)**: When a review demands
rewriting ~50% of the manuscript (remove false theorems, replace whole
sections with corrected constructions), anchor-based `patch` on 300-line
blocks is brittle. Use a deterministic line-splice script instead:
fragments as `r'''...'''` raw strings, spliced bottom-up by exact 1-based
line ranges (descending start line keeps all indices valid), then a
stale-label `\ref{}` grep over every removed label. Commit a
pre-restructure checkpoint first, and re-check ±2 lines around every
splice boundary — a stale sentence can survive just outside the range,
and a `\label` can be silently deleted inside it. After compiling, grep
the log for `multiply` (reused labels) as well as `undefined`. Full
recipe + content-audit pattern + PDF-extraction normalization pitfalls:
`references/line-splice-restructure.md`.

**Many-item review pass (10–20 local replacements):** do not batch these as
`str.replace` of guessed multi-line anchors — wrapping inside math/`\cite`
will fail the unique-count assert and the mixed `\\` / `\\\\` in one Python
file will silently write the wrong LaTeX. Dump each range from disk first
(`python3` printing `i|{lines[i-1]}` for every `(start,end)`), then splice
with a `startswith(head)` check on the *live* first line of that range.
Replacement bodies are `r'''...'''` with single TeX backslashes, identical
to source. Apply bottom-up. Recipe: `references/line-splice-restructure.md`
(§ Many small splices).

**Critical**: Use raw strings (`r"..."`) for all LaTeX content. Python's `\b`,
`\t`, `\n` in non-raw strings corrupt `\textbf`, `\tilde`, `\begin`, etc.

### 3. Compile Full Cycle

```bash
cd project_dir
rm -f *.aux *.bbl *.blg *.out
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
grep -c 'Reference.*undefined' paper.log   # must be 0
grep -c 'Citation.*undefined' paper.log    # must be 0
```

### 4. Verify Content in PDF (pymupdf)

Don't trust a clean log — verify new content actually rendered:

```python
import pymupdf
doc = pymupdf.open("paper.pdf")
full_text = "".join(doc[i].get_text() for i in range(doc.page_count))
for phrase in ["Ostrowski", "Fundamental Limitations"]:
    assert phrase in full_text, f"'{phrase}' NOT in PDF!"
doc.close()
```

### 5. Bibliography Sorting

When asked to sort the bibliography by first-author surname (a common
revision request), extract the `\bibitem` keys, determine the sort order,
and rewrite the entire `\begin{thebibliography}...\end{thebibliography}`
block as one `patch` replacement:

1. Read the bibliography range with `read_file`.
2. Determine sort order: alphabetically by first author surname; within
   same first author, sort chronologically by year.
3. Replace the entire block (from `\begin{thebibliography}` through
   `\end{thebibliography}`) with the sorted entries.
4. Verify with a small Python script that checks adjacent-key ordering.

For inline bibliographies, sorting is a pure TeX edit. For BibTeX-based
projects, sort the `.bib` file entries instead.

See `references/bibliography-management.md` for verification scripts and
edge cases (accented names, multi-word surnames).

### 5b. Splitting One Manuscript into Two Standalone Papers

Use when a monolithic article must become two independently compilable papers.

Procedure (in order):

1. **Map the structure.** Grep `\section`/`\subsection` with line numbers; pin each paper's body as a union of contiguous line ranges from section boundaries, not prose guesses. Record exact boundary lines in a probe file.
2. **Audit cross-references fresh** — do NOT trust any prior-session label or ref inventory (it may contain fabricated entries). Write an audit script to /tmp that enumerates every `\label` definition with its line range, classifies each `\ref`/`\eqref` site as A→B, B→A, or intra-paper, and lists distinct target labels per direction. Run it twice into two outputs and `diff -q`; only byte-identical output on an md5-pinned source counts as ground truth (see hermes-tool-edge-cases → references/multi-session-manuscript-continuation.md).
3. **Compute the transitive closure of the mirror set, then realize it.** For each cross-paper target label, follow the refs INSIDE its statement block: a mirrored theorem that itself `\ref`s another A-only label needs that label too — the distinct-label count grows after closure, and the naive count undercounts what a self-contained recap actually needs. Then realize the closed set as a `\section{Recap of Part I}` whose `\subsection`s carry the mirrored *section* labels (so `\ref{sec:presheaves}` resolves) and whose bodies restate each mirrored statement verbatim, keeping the original `\label` on every restated environment so `\ref`s renumber against the recap. Strip proofs (`\begin{proof}...\end{proof}` → "(Proof omitted.)"): a recap carries statements, not proofs. Order statements by logical topic under the matching subsection, not by original line order. When a section label is referenced as "Section~\ref{sec:X}", the recap's `\subsection\label{sec:X}` is what makes it resolve — do not leave section labels dangling.
4. **Reword, don't delete.** Cross-paper ref sites become prose pointers to the companion part ("Part II, Section ...") instead of `\ref`s; capture ±3 lines of context verbatim first so rewordings stay grammatical.
5. **Per-paper front matter + bibliography subset.** For inline `thebibliography`: keep only cited keys (cite sets from step 2); shared keys appear in both papers' bibs. No hardcoded section numbers — let each paper auto-number independently.
6. **Audit the assembled .tex before compiling** — undefined-ref / undefined-cite / orphan-bibitem are found faster at source level than by log-grepping, and they catch assembly bugs (e.g. a bad bibliography slice) before the first compile. Then the **compile gate per paper:** two pdflatex passes; audit the FINAL log for undefined references/citations (must be zero). After a clean compile, grep the `.aux` `\newlabel` lines to confirm the recap's section labels resolved to the intended subsection numbers (e.g. `sec:presheaves` → recap subsection 1.1, `sec:galois` → the renumbered Galois section), then verify rendered text.

Pitfalls:
- The naive distinct-label count undercounts what a self-contained recap or mirror actually needs; always close the set transitively before writing it.
- A prior session's derived artifact is untrusted input: any label with zero `\label` hits in the current source is fabricated — grep each one before building on the file.
- **Edit the assembled body by unique-substring replace, not remembered line index.** When a paper is built by slicing source line ranges and then edited, a single multi-line replacement shifts every later line index — an edit aimed at "line 206" lands on the wrong line after an earlier 8-line→3-line swap. Apply edits to the joined body text as `body.count(old)==1`-asserted substring replacements, or splice the source ranges bottom-up (descending start line keeps all indices valid).
- **The last `\bibitem` swallows `\end{thebibliography}`.** Extracting `\bibitem` blocks by walking forward to the next `\bibitem` leaves the final entry's walk unbounded, so it captures `\end{thebibliography}` and the paper fails with "Lonely \item". Slice the bibliography to exclude the `\end{thebibliography}` line, and verify the final bibitem block does not contain it.

### 6. Citation Hygiene

After adding/removing `\cite` references:
```python
import re
cites = set(re.findall(r'\\cite(?:\[[^\]]*\])?\{([^}]+)\}', tex))
bib_keys = set(re.findall(r'@\w+\{([^,]+),', bib))
assert not (cites - bib_keys), f"Missing: {cites - bib_keys}"
```

For manuscripts with an inline `\begin{thebibliography}` (no `.bib`), the
audit variant is:
```python
bib_keys = set(re.findall(r'\\bibitem\{([^}]+)\}', tex))
cites = {k.strip() for m in re.finditer(r'\\cite(?:\[[^\]]*\])?\{([^}]+)\}', tex)
         for k in m.group(1).split(',')}
print("cited, no bib entry:", sorted(cites - bib_keys) or "none")
print("bib entry, never cited:", sorted(bib_keys - cites) or "none")  # orphans are as bad
```
Both directions matter: an uncited `\bibitem` is an orphan that should be
removed or re-cited in its natural home; a cite without an entry breaks the
compile. Run this audit at the END of every revision pass (caught in one
session: five orphaned entries after a restructure, plus a fabricated entry
that had to be replaced — see `references/verified-citations-choquet-moment.md`).

When removing a cited reference, first strip all `\cite{Key}` from the `.tex`,
then remove the `@misc{Key,...}` from the `.bib`.

### 6b. Correcting a bib entry's venue/year after the fact

When the user supplies corrected bibliographic data (an arXiv preprint that is
now published, or a year correction — e.g. "JMAA 455(1), 212–220, (2017)"),
the fix is NOT a one-line `\bibitem` swap. It propagates, and a half-done edit
compiles silently because citation keys are just labels:

1. **Rename the citation key to match the corrected year** if the key encodes it
   (`AlaghmandanGhasemi2015` → `AlaghmandanGhasemi2017`), keeping the manuscript's
   `AuthorYYYY` convention (cf. `CGIK2023`). Find the count first:
   `grep -c OldKey paper.tex` must equal (# `\cite` occurrences + 1 bibitem);
   replace ALL occurrences, then assert the old key is gone.
2. **Replace the entry body** with the full journal reference — initials first,
   `\emph{title}`, `{\bf vol}` (year), no., pages — per user-latex-style.
3. **Compile + pymupdf-verify the NEW venue/vol/year/pages render** (e.g. "J. Math.
   Anal. Appl.") and the OLD line (bare "arXiv:….") is gone — same polarity +
   prose-substring discipline as the removal check above.
4. **Propagate to the local wiki** if the paper was ingested there (raw header +
   recomputed `sha256`, entity title/header, index + query display titles); see
   wiki-maintenance. The file *slug* may keep the arXiv year — only display text
   changes.

### 7. Applying a Reviewer Report (verify claims first)

When a referee/advisor report demands structural changes, do NOT execute the
fixes directly from the report. A review is a critique, not ground truth:

1. **Verify every numbered claim against the manuscript text.** For each
   review item, locate the criticized theorem/definition/proof and confirm
   the manuscript really says what the review quotes, with line numbers.
   Build a small table (claim | manuscript location | verdict). A review can
   misquote, target a stale version, or number theorems differently than the
   compiled PDF.

   **Prove a review targets a stale build via the `.aux` file.** When a
   review cites numbers ("Theorem 6.6", "Lemma 7.13") that do not obviously
   exist, read the `.aux`, which records the authoritative label→number
   mapping from the *current* compilation:
   ```bash
   grep -oE 'newlabel\{[^}]+\}\{\{[0-9.]+' paper.aux
   ```
   Compare the review's numbers against it. Decisive signature of a
   stale-build review: it praises one number that *matches* the current
   build (e.g. cites "Definition 7.13" and `\label{def:galois_coh}` really
   is 7.13) while its other cited numbers have no matching label (e.g.
   "Theorem 6.6" — 6.6 is now a Remark, the theorem is 6.9). That lets you
   report "already resolved" for items whose target no longer exists
   instead of re-fixing phantom content. This is stronger than just
   noticing the review "may" be stale — it is positive evidence.

   **Superseded-draft confusion (the wrong FILE, not just the wrong build).**
   A review can mix versions of two *different files*: in one session
   (MomentSheaf Review-07, 2026-08-30) the review's opening praise matched
   the canonical article exactly ("Prop 6.2–6.3, Thm 6.9") while its four
   highest-priority items ($\iota(x)$ index, Thm 6.11, Crl 6.12, cokernel
   of $\Delta$) existed ONLY in `moment_sheaf_unified.tex` — an early
   merged draft still sitting in the same `manuscript/` directory.
   Signature: the review coherently describes the current version AND
   cites numbered objects that produce 0 grep hits in the canonical file.
   Then:
   1. `git log -S '<distinctive flagged phrase>' -- <canonical>.tex` —
      empty output PROVES the content never existed in that file's
      history (positive evidence, stronger than "not found now").
   2. Grep the flagged phrase across every OTHER `.tex` in the directory
      to locate the superseded draft it actually targets.
   3. Root-cause fix, not just disposition: `git mv` the superseded drafts
      to `archive/superseded/` and update the project README so no future
      review (human or agent) reads the wrong file. Record in the
      disposition which file each review item belongs to.
   Full worked instance: `references/stale-review-wrong-file.md`.

   **"Already resolved" is a claim you must PROVE, not assert.** The
   single most common way a revision pass under-delivers is to mark a
   reviewer item "already fixed" after only a string-level grep, then
   move on. When the user pushes back ("make sure the severe issues are
   actually fixed"), re-read the replacement theorem/definition/proof
   line-by-line and state in the disposition *what the replacement says
   and why it is sound*, not just that the old text is gone. If an item
   is "already resolved", the deliverable is proof-level evidence
   (the corrected statement + its hypotheses + why the proof works),
   not a string-absence report.
2. **Independently check the review's mathematical verdict** — in one
   session the review was fully accurate, AND the verification pass found an
   additional defect the review missed (a remark using "common smaller
   neighborhood" while the definition used "common larger" — an internal
   contradiction). Report extra findings back to the user; they strengthen
   the revision.
   **Do not implement a recommended replacement proof unexamined.** A
   review can correctly flag a false hypothesis ("locally compact Hausdorff
   ⇒ partitions of unity on $U$") and then propose a stronger-wrong
   substitute (glue a *finite* Radon measure on a possibly non-finite open
   $U$). The justified middle is often already in the manuscript: a
   compact-support partition of unity on $\operatorname{supp} f$ uses only
   that a compact Hausdorff set is normal, and does not require $U$ to be
   paracompact. Adopt the review's *diagnosis*; write the replacement proof
   only after checking it against the objects' actual hypotheses.
3. **Classify fixes by the report's own hierarchy** (must-fix / reformulate
   / preserve) and keep the preserved material intact — a review usually
   names the strongest parts to keep; don't rewrite those.
4. **Prove replacement claims inline where feasible.** When a review says a
   cited bound "needs verification", give the short kernel/counting proof in
   the manuscript itself (e.g., extreme points of a truncated
   representing-measure set have ≤ N = dim span{b̂} atoms: atomless part ⇒
   non-extreme via the L¹(μ₀)→ℝ^N kernel; > N atoms ⇒ non-extreme via the
   N×k moment-matrix kernel) and cite the literature only for attribution.
5. **Verify any newly introduced or corrected citations against the actual
   sources** — chapter numbers against the book's real table of contents
   (Google Books TOC snippets work), journal entries against the journal
   archive. A wrong chapter number (Phelps "Ch. 10" for the Choquet
   boundary, actually Ch. 6) and a fabricated bib entry were both caught
   this way in one pass. Verified citation bank:
   `references/verified-citations-choquet-moment.md`.
6. **Track each pass in the project's review report** (verdict per item,
   resolution note, compile/verification evidence) so later sessions see
   what was fixed.

### 7c. Novelty / prior-art audit repositioning

When a novelty audit arrives (external literature check, referee's "this
is already known" report, or the user asking "is this new?"), it is a
critique of the manuscript's *positioning*, not ground truth about either
the literature or the manuscript. The disposition workflow:

1. **Verify the audit's own citations first** (Citation Verification Gate):
   Crossref API (`https://api.crossref.org/works/<DOI>`) for journal
   metadata; Numdam for Ann. Inst. Fourier and other French archives
   (best-in-class metadata incl. MR/Zbl numbers); `web_search` as fallback
   when the arXiv API is down (it 503s under load — don't retry it more
   than once). Never accept an audit's bibliographic claim unverified.
2. **Cross-check every audit row against the ACTUAL manuscript state**
   before implementing. In one session (MomentSheaf, 2026-08-31) a
   theorem-by-theorem audit recommended "state hypotheses in the theorem,
   not the proof" — but first countability was already IN the statement;
   the audit was reviewing its memory of an older version. Classify each
   row: already satisfied / partially satisfied / genuine gap. Only the
   genuine gaps get edits.
3. **Distinguish attribution from positioning.** A result can be correctly
   cited yet badly *positioned*: the IKKM 2022 projective-limit paper was
   cited exactly once, buried in a failure-mode remark, while the abstract
   and introduction claimed the inverse-limit framing — that is a
   positioning defect that no citation-hygiene audit catches.
4. **Implement the standard repositioning package** for genuine gaps:
   (a) prominent acknowledgment in abstract + a dedicated "Relation to
   previous work" subsection in the introduction; (b) a three-tier
   contribution classification — *established foundations* (named, "not
   claimed as new"), *new structural results* (numbered, with precise
   hypotheses), *open directions* (cross-referenced to open problems);
   (c) no-novelty disclaimers on propositions that are standard theory
   (e.g. "standard Lasserre–Putinar–Schmüdgen theory; we include it with
   proof for completeness and claim no novelty"); (d) sharpened central
   claim wording that names the distinguishing technical angle (e.g.
   inverse system of representing-measure SETS for a fixed functional vs.
   projective limits of character spaces).
5. **Write the disposition report** with the three-way verdict table
   (already satisfied / fixed / residual) and commit with the manuscript
   in the same commit.

Full worked instance (two audit rounds, all edits, verification):
`references/novelty-audit-repositioning.md`.

### 8. Ingest-and-map: from a new source to manuscript citations

When the user says "ingest this paper into the wiki AND check whether it
sheds light on the manuscript's open problems," the deliverable is
threefold, and the citation edits come LAST:

1. **Wiki ingestion** (llm-wiki workflow): raw + entity page + concept-page
   update + index.md + log.md. Keep the arXiv id; verify the raw `sha256`
   against the body below the frontmatter, not the PDF binary.
2. **Open-problem mapping**: file a `queries/` page with a two-column table
   (paper result → manuscript open problem / theorem) and an explicit
   "what the paper does NOT address" list — the negative mapping is what
   keeps the synthesis honest and prevents over-citing.
3. **Manuscript citation edits**: only after the mapping confirms relevance.
   Add the `\bibitem` (alphabetically by first author) and
   `\cite[Thm N.M]{Key}` at each mapped site; compile + pymupdf-verify.

Two heuristics that paid off (MomentSheaf + Alaghmandan–Ghasemi 2015):

- **Check for uncited self-work first.** If the paper is (co-)authored by
  the user, it is frequently their own prior work that the manuscript
  already should cite but does not — a low-risk, high-value citation.
  Search the .tex for the author surname and the arXiv id BEFORE assuming
  it is new to the manuscript.
- **Cite the specific numbered result, not the survey.** Each `\cite`
  should pin a theorem (Thm 2.5, Prop 3.9), never "see also [X]"; the
  strongest contribution is usually one density/compactness criterion and
  one counterexample/obstruction, each mapped to exactly the open problem
  or section it resolves.

Full worked instance: `references/source-to-manuscript-citation-bridge.md`.

### 8b. Reference value assessment ("does source X improve the article?")

When the user asks whether a specific reference — often one just queried
from the LightRAG KB — would improve the manuscript, the deliverable is a
verdict backed by a content comparison, not an impression. Assessment
comes FIRST; edits only after the user approves:

1. **Confirm the source actually contributes.** Query the KB with
   `/query/data` first and filter retrieved chunks by `file_path` — a
   KB-wide answer blends many documents, and an LLM synthesis will
   attribute other documents' content to the one named in the question.
   Then run `/query` (with `hl_keywords`) for synthesis, and report
   references per-source.
2. **Read the manuscript sections the reference targets.** A reference
   recommended to fill a gap may be obsolete advice: the gap may already
   be closed (definitions added, proofs made self-contained, better-suited
   citations in place). Verify against the CURRENT `.tex`, not against an
   audit report's memory of it.
3. **Build the comparison table**: reference content | manuscript status
   (already present / citeable support / absent) | adds value?
4. **Verdict honestly.** If the reference only duplicates what the
   manuscript now proves inline, say so — recommending a citation that
   adds nothing wastes a revision pass. The usual surviving value is one
   supporting citation at an existing remark or proof (e.g. the textbook
   provenance of an averaging/Reynolds operator), not new material. Note
   explicitly what the reference does NOT provide (e.g. a textbook with no
   ring-level definition of the concept under discussion).
5. **On approval, apply the citation**: verify metadata against primary
   sources (Crossref `api.crossref.org/works/<DOI>` for books and
   articles), read the NEIGHBORING `\bibitem`s and match the file's own
   house format for that entry type (book entries: series, volume,
   publisher on their own lines; journal entries: `\emph{title}`,
   `vol (year), pages`), patch the in-text `\cite` and the `\bibitem` in
   the same pass, compile, and verify per the pymupdf rules above
   (prose-substring probe for the body, separate probe for the bib entry).

### Phase-completion sync must revise stale items, not just add new ones

When the task is "update the manuscript based on recent progress" — merging a
completed phase's deliverables (theory notes + claims-ledger rows) into the
`.tex` — an ADD-ONLY pass under-delivers. New results routinely invalidate
pre-existing manuscript content in three ways, each invisible to the compiler:
1. **A new result refutes or closes an existing open problem.** Grep the
discussion/open-problems section for every subject of the new results and
revisit each hit: an item now answered (positively or by counterexample) must
be rewritten as a resolved remark with a `\ref` to the closing theorem, not
left in the list. A refutation is worse than an answer — leaving a refuted
question open means the next reviewer re-derives your own counterexample.
2. **Abstract/introduction theme lists go stale.** Intro "this paper covers
two/four themes" enumerations and abstract scope claims must be extended when a
new phase lands; check every enumerated list in §1 against the actual section
map before compiling.
3. **Claims-ledger status changes propagate.** When a ledger row flips from
`conjecture` to `proven (core)` / splits into proven-core + conjectural-full,
the manuscript's prose must carry the same split — label the conjectural part
as such in the body, per the claims-ledger discipline. Verify each inserted
statement against its ledger row (status, location, dependencies) before
writing; a theorem inserted with `proven` status that the ledger marks
conjectural is an overclaim.
Order: revise stale items FIRST (they are small and unblock numbering), then
insert new material, then run the citation-hygiene + numbering audits above so
either pass's side effects are caught together.

### Hand-off Patch Verification (cross-session .tex edits)

When a session resumes from a hand-off document listing unverified .tex
patches (a common pattern: prior session edits + verifies mathematically, but
defers compile/commit), do not trust that the edits are present or render
correctly. Three-stage check before committing:

The mirror case is a hand-off that records only read-only preparation (file
reads, ledger checks, registry lookups) and is silent on writes — a task can
span many turns of prep with zero edits applied. Before reporting status
("did the update finish?"), decide it with ONE grep for the change's content
markers: the new theorem's title string, the new `\bibitem` keys, a
distinctive prose phrase that should have been inserted. Zero hits means no
edit ever landed — answer honestly and apply the edit batch now, instead of
replaying the read-only prep.

1. **Grep the .tex** (`search_files` with the exact patched string) for each
   claimed edit — confirms the edit landed in source. Note line numbers to
   cross-check against the hand-off's stated locations.
2. **Compile** with `latexmk -pdf -interaction=nonstopmode -halt-on-error`,
   then `grep -c 'LaTeX Warning'` and `grep -i 'undefined\|multiply defined'`
   on the log — both must be 0/empty. Minor overfull hboxes (<25pt) are
   cosmetic; for large ones (>100pt), check the line numbers against the
   patch regions to confirm they're pre-existing, not introduced.
3. **Render-verify with pymupdf**: open the built PDF, search each page's
   `get_text()` for a distinctive substring of the patched passage, and
   print the surrounding text — confirms the corrected wording (e.g. a
   fixed quantifier or hypothesis) actually renders. Source and PDF can
   drift (stale PDF, partial build); verify by content, not by error count.

Then commit in the subproject repo with a DOX.md `[Fix: ...]` prefix
describing the patch content, not the verification work.

## Pitfalls

### Backslash escaping in `patch` tool (historical note)

The `patch` tool with `mode='replace'` handles LaTeX backslashes correctly —
verified across multiple sessions with 10+ edits per session. The old warning
about backslash doubling was incorrect for `mode='replace'`. If you ever see
doubled backslashes in output, revert with `git checkout` and fall back to
the `terminal` heredoc approach below.

### Recovering from corrupted `.tex` files

If an edit corrupts the file (doubled backslashes, missing content), revert
immediately — do not try to fix in place:
```bash
git checkout paper.tex
```
Then redo the edit via `execute_code`. This is faster and safer than trying
to manually undo a broken patch.

### Adding theorem-like environments

When adding a new environment type (e.g., `\begin{example}`), ensure the
corresponding `\newtheorem{example}{Example}` exists in the preamble.
Missing this causes `! LaTeX Error: Environment example undefined.` — a
trivial error that breaks compilation entirely. Check the preamble with
`grep -n '\\newtheorem' paper.tex` before inserting any new env.

### Two-pass without bibtex (inline bibliography)

When the manuscript uses `\begin{thebibliography}` (inline) rather than
an external `.bib` file, skip `bibtex` — a 2-pass pdflatex cycle suffices:
```bash
pdflatex -interaction=nonstopmode -halt-on-error paper.tex && \
pdflatex -interaction=nonstopmode -halt-on-error paper.tex
```
Run `grep -ciE 'error|Error|Emergency' paper.log` after pass 2; should be 0.
If `grep` finds `Rerun` or `Label(s) may have changed`, run a third pass.
Always do a final pymupdf verification afterward
(see `references/verification-script.md`).

### Merged-manuscript proof traps

When a manuscript was assembled from multiple drafts, proofs labeled
`[Sketch]` may hide incorrect claims. A lemma citing a reference may
claim what the reference does *not* prove (e.g., existence vs. universal
extendability). Verify every sketch proof against the cited source
independently — do not trust the draft author checked this. Full
procedure in `references/proof-audit-checklist.md`.

### Numeric constants: verify against the artifact, not the report

When merging an experiment phase into a manuscript, every number you carry
over (from the phase report, the claims ledger, or a session summary) must be
re-checked against the run's *artifact* — the saved stdout log and the
JSON/CSV the script wrote — before it enters the `.tex`. Prose reports drift
from the artifacts they cite: in one Phase-4 closeout the same residual
appeared as `1.07e−5` (report and claims row), `1.08e−4` (the saved run log)
and `7.36e−5` (the current `results.json`, rewritten by a later run) — three
values, none agreeing, under a report that claimed to be "transcribed from
actual stdout".

Rules:
1. `grep` the report and the ledger for the number, then read the value out
   of the artifact yourself (`experiments/*.json`, `*_stdout_*.txt`).
2. When artifact and report disagree, fix the report AND the ledger row in the
   same commit as the manuscript, and record the correction in the ledger's
   provenance notes — never silently use one of them.
3. For a statistic that is a min/max over *unseeded random trials* the exact
   value varies per run: quote it in the manuscript as an order of magnitude
   ("of order $10^{-4}$") and record the artifact value plus the observed
   run-to-run spread in the ledger. A 3-significant-figure random-trial
   statistic does not belong in a manuscript.
4. Re-verify cheap computable constants before printing them verbatim: e.g.
   `numpy.linalg.eigvalsh` on the matrix whose eigenvalues the manuscript
   quotes, a Gauss–Hermite evaluation of an integral identity it asserts, and
   a `pdftotext`/grep probe of the compiled PDF for the new theorem numbers
   and phrases.
5. On conflicts of substance: the ledger row wins for claim wording/status,
   and the theory file versus the manuscript statement must be diffed
   explicitly (quantifiers, hypotheses) before compiling.

### Claims ledger: track proof strength, not just a flat status

A claims ledger that maps every theorem to a single status word
(`proven (informal)` / `conjecture` / `framework`) *overstates* rigor: it
records citation-based and reassembled results on a par with self-contained
proofs. When building or auditing a `claims.md`, track a second, orthogonal
axis per entry — **how the proof is delivered**: `full` (self-contained) ·
`full (restated)` (attributed but reproved) · `citation` (defers to a named
source) · `reassembly` (immediate combination of prior numbered results) ·
`sketch`. Reclassify citation-based results as `classical · attributed`, never
`proven (informal)` — a proof body that is "Theorem X (Marshall Thm 3.4)" or
"assertion 1 is prop:A, assertion 2 is a definition, assertion 3 is thm:B" is
a citation or a reassembly, not an original proof. Record each entry's
resolved location (from the `.aux` `\newlabel` map) and its dependencies, so a
reader sees which flagships stand on which lemmas.
**After inserting a lemma that shares the theorem counter, re-read the `.aux`
before updating `claims.md` locs** — every later environment in that section
shifts (`thm:galois_descent` 7.9 → 7.10). Do not copy loc numbers from the
pre-insert ledger. Edit markdown tables with Python `str.replace` on a unique
row, not `patch`: a failed table patch can leave `|||` double pipes and
doubled `\\\\varprojlim` that compile nowhere and break the ledger.

### Proof Audit & Repair Workflow (restate-and-reprove)

When asked to "check if this proof is correct" — or when a proof-audit
report flags items for repair — use this class-level workflow. A full
worked instance (a truncation-theory manuscript, 4 repair passes in one session)
lives in the project's own notes:
`references/truncation-theory-proof-audit.md`. A second worked instance
(MomentSheaf, 2026-08-31: mixed-atom case missing from a stalk
extreme-ray classification; three silent holes in a descent
correspondence — compactness, continuity, formula applied outside its
defining hypotheses) lives in
`references/proof-audit-momentsheaf-gaps.md`.

**Audit checklist (six failure modes, in detection order):**
1. **Hypothesis mismatch** — does every assumption used in the proof appear in the statement? (Caught: proof used "compactness" while the statement said "constructible".)
2. **Ill-defined host object** — is the object the claim is about the right type? (Caught: "QM in $B_d$" where $B_d$ was only a span/vector space, not a ring; and homological machinery — group cohomology $H^n$, $\operatorname{Ext}$, $\varprojlim^1$, spectral sequences — applied to a *cone* or convex set such as positive measures/functionals, which are not abelian groups.)
3. **Unlinked data** — do all conditions involve the same objects, with the relation stated? (Caught: an equivalence whose three conditions used three unrelated objects.)
4. **Citation content mismatch** — does the article's OWN description of a cited theorem match its use? (Caught: a theorem the article itself described as "Tchakaloff" cited for "compact ⟹ Archimedean".)
5. **Missing converse** — does the argument show both inclusions, or just one? (Caught: "measures define functionals" proves moment cone ⊆ dual cone only.)
6. **Internal contradiction** — test joint consistency of all statements on a canonical example. (Caught: Lemma + Prop + Remark jointly forced a false conclusion for $y'=y$.)
7. **Construction used outside its defining hypotheses** — does every
   application of a constructed object respect the hypotheses under which
   the construction was defined? (Caught twice in one flagship proof,
   2026-08-31 MomentSheaf Thm 7.6(2): (a) the measure $\tilde\mu$ was
   defined by an integral formula valid for continuous $f$, then applied
   to $\chi_E$ (discontinuous) to check $\pi_*\tilde\mu=\mu$ — the check
   must instead test against $h\in C(K)$; (b) compactness of $K'$ and
   continuity of the averaged integrand $g_f$ were silently assumed but
   never proved, though the Riesz representation theorem and weak-$*$
   topology on $\Mcal(K')$ both require them. The same audit found a
   missing case in the sibling result: the extreme-ray classification of
   the stalk proved only the atomless case $\mu(\{x\})=0$, never the
   mixed case — a nontrivial atom at $x$ with a nonzero residual germ.)

**When a review closes with "perform a final proof-level audit of the
genuinely nontrivial claims" — do it as a genuine audit, not a
formality.** In the 2026-08-31 session the reviewer's two suggested
audit targets BOTH contained real gaps the reviewer did not flag
(above), while several of the reviewer's own 14 items were already
satisfied. The final pre-submission audit of the paper's original
mathematics is where remaining defects concentrate, because those are
the statements no prior literature has vetted. Audit order per claim:
read the statement; list every object the proof constructs; check each
construction is used only within its defining hypotheses; enumerate the
cases the proof actually treats versus the cases the claim asserts.

**Fabricated citations in AI-assisted drafts (verify everything):**
AI-generated manuscripts contain fabricated bibliography entries and
pin-cites at a high rate. In one audit: "D. Póldrop", "Jarnicki–Pólak",
"W. C. Woodin (1964)", "Kolchin Cor II.2.5", "Prestel Thm 3.4" were all
fabricated; a real author's initial was wrong (S. vs Q. Brouette); a
real paper's title/pages/venue were wrong (CGIK); and a theorem number
was misattributed (CGIK Thm 4.2 is Stochel-type, cited as a rate). Verify
each entry by web search; for theorem numbers, `web_extract` the actual
PDF (arXiv) and grep the cached full text for "Theorem N.M". Also check
the article's own prose paraphrases of cited theorems for internal
consistency — a miscited number is often detectable without the source.

**Bibliography fact-check pass (pre-submission).** Run the WHOLE
`\begin{thebibliography}` through primary metadata, not just the entries a
review already questioned — an AI-merged manuscript fails in bulk (one pass
over a 27-entry bibliography found eight bad entries). Four failure modes
recur: (a) a plausible entry with no existing publication (a real author and
a real-looking title, but no such paper — sometimes a conflation of two real
papers under one invented citation); (b) a real paper under the wrong
journal/volume/pages; (c) an appendix author recorded as a co-author — check
the title page: "with an appendix by X" is not "and X"; (d) a published paper
recorded as a preprint under its arXiv *submission* year — recover the
published venue from the arXiv API `journal_ref` field and cite the published
version. The submission-year label propagates: a wiki entity and its index can
both carry "2008 preprint" years after the paper appeared in 2009, so fix the
manuscript and every derived record in the same pass.

**Self-containment audit: define what a section uses, use what you declare.**
A section can invoke an operator or group ("the Galois group $G$", "the trace
$\operatorname{Tr}$", the phrase "Galois descent" in a title) across many
results without ever defining it, and can declare a macro
(`\DeclareMathOperator{\Gal}{Gal}`) that is never used — both invisible to the
compiler, both trip a reader who meets the notation cold. Before finalizing a
section: grep the preamble for `\DeclareMathOperator`/`\newcommand` and confirm
each is used in the body; symmetrically, list every operator/notation the
section relies on and confirm each carries a definition `\label` in or before
that section. Add the missing definition (with `\label`), and put the unused
macro into service or delete it. This is the notation-level twin of citation
hygiene (cite↔bibitem): the compiler validates neither.

**Repair patterns that worked:**
- Restate-and-reprove: replace a broken equivalence with a true one
  (e.g., embedding ⟺ finite colength, proved via the squares-span
  identity $(a+1)^2-(a-1)^2=4a$ and a monomial-coset basis).
- Route fabricated bounds to the real literature (qualitative statement
  + citation to verified quantitative results) instead of inventing
  formulas.
- **Linearize the cone.** When homological machinery ($H^n$,
  $\operatorname{Ext}$, $\varprojlim^1$, Hochschild–Serre) is mistakenly
  applied to a *cone* or convex set (positive measures, positive
  functionals, a representing-measure set), do not patch the formula —
  replace the coefficient object with a genuine abelian group (signed
  measures / difference spaces), then state the cone-level claim
  set-theoretically and reserve the cohomological statement for the
  linearization. Worked instance: MomentSheaf Galois descent — the cone
  $P'(K')$ was replaced throughout by the signed-measure module
  $M(K')=C(K')^*$, with "$\mu'$ descends iff $\sigma\mu'=\mu'$" stated
  separately from the $H^0(G,M(K'))$ statement, and the cone-invariant
  set $\Mcal_+(K')^G$ explicitly denied the status of a group-cohomological
  $H^0$. This is a recurring trap in moment-problem / convexity research.
- Track repairs as dated passes in the audit report (verdict line,
  resolution note, severity-table counts) so later sessions see what
  was fixed and what remains.
- After each pass: 2-pass pdflatex + grep for undefined refs + pymupdf
  probe for the NEW theorem text + a stale-notation sweep (see the
  verification notes in `references/verification-script.md`).

### Notation harmonization when merging from .md notes

When inserting a theorem + proof from a standalone `.md` note into an
existing LaTeX manuscript, the note will almost certainly use different
notation (variable names, math alphabets, degree conventions) than the
target manuscript. Before insertion, audit and adapt:

1. **Variable names**: `.md` notes often use $x_i$; the manuscript may
   use $Y_i$, $X_i$, or $y_a$.
2. **Math alphabets**: A note may use $M_{q,p}$ for a form while the
   manuscript already reserves $M_{q,p}$ for a different related form.
   If the forms are scalar multiples, relate them explicitly (e.g.,
   $\Phi_{q,q-1} = W^q \cdot M_{q,q-1}$) and use a distinct alphabetic
   variant ($\Phi$, $\mathscr{M}$, $\mathfrak{M}$) to avoid ambiguity.
3. **Cross-references**: The note won't have `\label` / `\ref` at all.
   After insertion, add `\label{thm:...}` and wire `\ref` back to
   related existing results (e.g., connect to open questions).
4. **Environment names**: Verify the manuscript preamble declares the
   environment types the proof uses (e.g., `\newtheorem{lemma}{Lemma}`).
   Missing declarations cause hard-to-diagnose `Environment undefined`
   errors.

Do this audit BEFORE the first compile — fixing notation drift after
the fact requires re-reading the entire inserted block. Full procedure
in `references/notation-harmonization.md`.

### Compilation ≠ Content Verification

A clean pdflatex log (0 errors, 0 undefined) does not guarantee new content
rendered correctly. Always run pymupdf text extraction afterwards (see
`references/verification-script.md` for the full assertion-based pattern).

### Formal Proofs via Lean 4 + Mathlib

When a manuscript revision requires formal verification of polynomial
nonnegativity, use the power-mean lemma chain. The complete proof pattern
(including Lake setup, `Even.convexOn_pow` → `map_sum_le` pathway, and the
`s` section-variable gotcha) is in `references/lean4-power-mean-proof.md`.

### Replacing SDP Claims with Formal Proofs

When a manuscript relies on an SDP decomposition as the sole evidence
for SOS membership, systematically upgrade or qualify those claims. The
1. Explicit rational SOS → replace SDP entirely
2. Formal inequality proof + SDP caveat
3. Computational evidence with explicit limitations

### Pymupdf ligature issues

LaTeX ligatures (ff, fi, fl) and subscripts ($x_0$) may not extract cleanly
from PDF — `x_0` may render as `x0` in pymupdf output, and `\textbf{theorem}`
may split across characters. Search for shorter substrings and be tolerant of
missing hyphenation. **Normalization trap (caught 2026-08-28):** if you
normalize the extracted text by stripping ALL whitespace (`re.sub(r"\s+",
"", text)`), then any multi-word needle like `"Stone–Weierstrass determinacy"`
will never match — compare space-containing phrases against a
space-normalized copy (`" ".join(text.split())`), and reserve the squashed
copy for whitespace-insensitive checks. Also: PDF line-wrapping inserts
spaces inside hyphenated compounds (`Stone–Weierstrass` may extract as
`Stone– Weierstrass`), and superscripts extract as plain digits (`lim¹` →
`lim1`); normalize both sides (strip spaces, map –/— to -, ¹→1) when the
match matters. The reliable per-page normalization recipe is
`flat = re.sub(r"-\s*\n\s*", "", t)` (rejoin hyphenated line breaks)
**followed by** whitespace collapse (`re.sub(r"\s+", " ", flat)`) — applying
only the whitespace collapse leaves the spurious break-space inside the
compound.

**German diacritics in bibliography entries extract displaced:** `Über`
comes out as `¨Uber`, `Größe` as `Gr¨oße`, `für` as `f¨ur`, and hyphenated
bib lines split words (`Funk- tionen`). For probes involving umlauts/ß,
normalize both sides (ü→u, ö→o, ä→a, ß→ss, á→a, strip stray `¨`) or probe a
diacritic-free substring; on a miss, print the raw extracted region around
the keyword before declaring failure — a displaced-diacritic hit is a render
success, not a content error.

**Citation markers render as numbers, not names.** When verifying a newly
added `\cite{}` in the compiled PDF, do not probe the body text for the
cited author's surname — `\cite{DerksenKemper2015}` renders as `[5]`, and
the surname appears only in the bibliography. Probe for a distinctive
*prose* substring of the new sentence (or the rendered `[n]` marker), and
verify the bibliography entry as a separate probe on its own page.
A surname-in-body probe returns a false "citation missing" even though
the compile is clean and the marker is there. For stubborn cases, use font-aware extraction:
```python
page = doc[pg]
blocks = page.get_text("dict")["blocks"]
for block in blocks:
    if "lines" in block:
        for line in block["lines"]:
            line_text = "".join(span["text"] for span in line["spans"])
            if "target" in line_text.lower():
                print(f"Found via font search: {line_text}")
```

### Semantic purge: fix the CLAIM, not the quoted string

When a reviewer flags an overstatement ("$H^1$ measures the failure of
descent for torsors"), the claim is usually stated in *several* places —
the definition, a theorem body, a remark, an example, a summary table,
and the abstract/intro prose — each in slightly different wording. Fixing
the single cited location leaves the claim alive elsewhere, and it will
be caught on the next review round (or by the user asking you to "make
sure the severe issues are actually fixed").

**Procedure:** after any edit that *weakens or removes* a mathematical
claim, do a semantic purge, not a literal-string grep:
1. List every synonym/phrasing of the claim — including prose
   paraphrases and near-synonyms, not just the exact math the reviewer
   quoted ("measures the failure of descent", "measures the ambiguity of
   descending", "is an obstruction for", "controls the descent of").
2. `grep` the .tex for each phrasing over the WHOLE document.
3. Fix every hit; a single remaining site is a failure.
4. Verify all absent (grep on source as primary; pymupdf as render
   check), with the absence polarity labeled correctly.

The trap that bit in practice: running a residual grep for the literal
math strings ($H^1(G,P$, $P_x$) while the overstatement survived as
*prose* ("measures the failure of descent for torsors") — the math-mode
needles were clean, the semantic claim was not. Grep for the claim's
*meaning*, not its LaTeX spelling. Worked instance and the companion
table-formatting regression:
`references/semantic-purge-pattern.md`.

**Substring-superset false positives (caught 2026-08-31, MomentSheaf):**
when the CORRECTED phrase contains the flagged phrase as a substring, a
naive `content.count(flagged)` reports the fix as failed even though it
succeeded — swept twice in one session (batch residual check and the
pymupdf absence probe) for the correction
"variance distinction" → "covariance distinction" (which *contains*
"variance distinction"). Fix: probe with a boundary-aware regex
(`re.findall(r'(?<!co)variance distinction', tex)` — negative lookbehind
for the correction's prefix) or match on a longer distinctive context
spanning the correction. This applies to BOTH source greps and PDF
absence probes. Before declaring a residual sweep failed, check whether
the hit is inside the new corrected text.


### Table column spec: lengthening a row in a no-wrap table

A summary table declared `\begin{tabular}{@{}ll@{}}` does not wrap; any
edit that lengthens a row (e.g. expanding a terse "$H^0$ vs. $H^1$"
cell into a full sentence) produces a catastrophic `Overfull \hbox`
(hundreds of pt). When an edit touches a summary table row, either keep
the cell text short or switch the column spec to a wrapping column
(`p{4cm}p{9cm}`). Always grep the log for `Overfull` after edits near a
`tabular`, and treat a >100pt overfull introduced *by your edit* as a
regression to fix, not a cosmetic pre-existing wart.

### Verifying that removed content is actually gone

When a revision deletes a passage, confirm *absence* — but mind the
polarity and the extraction. (1) **Polarity**: an absence-check that
returns "FOUND" is the BAD outcome; label the check so the pass/fail
verdict reads correctly (a "FAIL" on the OLD-text probe often means the
deletion *succeeded*). (2) **Math-mode needles lie**: superscripts,
$\operatorname{Ext}$, Greek letters, and primes extract unreliably, so a
naive math-mode needle can report "still present" when the text is gone.
Use a distinctive *prose* substring (e.g. "Galois cohomology of moment
sheaves") for absence checks, and use `grep` on the .tex as the primary
source-level confirmation — pymupdf is only the secondary render check.

### Inserting items into auto-numbered lists that are referenced by number

When text elsewhere in the manuscript references enumerated items by
HARDCODED number (`Problem~(9) in Section~\ref{sec:open}` — the section is
a `\ref` but the item number is literal), inserting a new item BEFORE that
position silently shifts every downstream reference. After any insertion:

1. `grep -n 'Problem~(' paper.tex` (and `Item~(`, `Question~(` etc.) —
   collect every hardcoded number reference.
2. Determine which references semantically target WHICH item (read context;
   several references to the same number may split between the old item
   and its new neighbor — in one session, of five `(9)` references, three
   were the families-descent question that now had its own item (10),
   two were the old Hochschild–Serre item that remained (9)).
3. Retarget, recompile, and verify the ACTUAL numbering by extracting the
   compiled PDF (regex `\((\d+)\)\s*([A-Z][^:]*:)` over the item titles)
   — do not trust source-order reasoning alone.

Related trap: reference-retarget edits go through the atomic batch — a
single anchor with wrong line-wrap rolls back the WHOLE batch, so the
sibling retargets must be reapplied after fixing the one failed anchor
(diagnose with `sed -n 'N,Mp' file | cat -A`).

### Demoting or promoting a theorem environment

When a review asks to downgrade a theorem to a corollary (or promote a
lemma), the `\begin{theorem}` → `\begin{corollary}` swap itself is safe:
the `\label` is untouched and numbering re-flows automatically through
the shared counter. But **prose references spell the environment name** —
`Theorem~\ref{thm:persistence}`, `Thm.~\ref{thm:persistence}` — and LaTeX
resolves these silently (the `\ref` prints only the number), so **no
compile error or warning exists to catch a stale prose name**. The
compiled PDF would say "by Corollary 7.11" in the statement and
"Theorem 7.11 shows..." in the summary — an internal inconsistency a
referee will catch.

Procedure after any environment demotion/promotion:
1. `grep -n -E '(Theorem|Thm\.?|Lemma|Proposition|Prop\.?|Corollary|Cor\.?)~?\\ref\{<label>}' paper.tex`
   — collect every prose reference to the changed label.
2. Retarget each to the new environment name (keep the label unchanged).
3. Include these retargets in the SAME atomic edit batch as the
   environment swap, so a failed anchor rolls back the whole change.
4. Verify in the compiled PDF: `re.search(r'Corollary 7\.\d+ \(Persistence', spaced_text)`
   — confirm the printed environment name, not just the number.

Worked instance (2026-08-31, MomentSheaf): thm:persistence theorem →
corollary; three prose sites retargeted (remark, summary table, section-9
established-results list); PDF probe confirmed `Corollary 7.11`.

### `\newcommand` Double-Subscript Errors

When a `\newcommand` wraps a subscript (e.g.,
`\newcommand{\Tmean}{T_{\mathrm{mean}}}`), using it with a further
subscript like `\Tmean_r` produces "! Double subscript." because it
expands to `T_{\mathrm{mean}}_r`.

**Fix:** Wrap the macro in braces before adding any subscript or
superscript: `{\Tmean}_{,r}` or `{\Tmean}^{(1)}`. This is especially
common in beamer decks where short macros substitute for verbose math
notation. Audit suspicious usages with:
```bash
grep -n '\\[A-Z][a-z]*_[a-z]' beamer.tex
```

See `references/beamer-pitfalls.md` for a full beamer troubleshooting
guide covering `\coloneqq`, double subscripts, and build cycles.
