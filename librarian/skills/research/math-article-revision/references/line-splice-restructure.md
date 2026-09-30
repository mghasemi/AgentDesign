# Wholesale Section Replacement via Deterministic Line-Splice

When reviewer feedback demands restructuring ~50% of a manuscript
(removing false theorems, replacing whole sections with corrected
constructions, a new central theorem), anchor-based `patch` on
300-line blocks is brittle. Use a deterministic line-splice.

## Procedure

1. `read_file` the whole manuscript in paginated chunks; record exact
   1-based inclusive line ranges for every block to replace.
2. `git add -A && git commit` a pre-restructure checkpoint first.
3. Write ONE Python script: fragments as raw strings, spliced bottom-up:

   ```python
   FRAGMENTS = [(start, end, r'''...replacement LaTeX...'''), ...]

   lines = open(PATH, encoding="utf-8").read().split("\n")
   for s, e, t in sorted(FRAGMENTS, key=lambda x: -x[0]):   # descending start
       lines = lines[:s-1] + t.split("\n") + lines[e:]
   open(PATH, "w", encoding="utf-8").write("\n".join(lines))
   ```

   Descending start-line order keeps all earlier ranges valid. Apply
   EVERY change this way in one pass (title, abstract, intro bullets,
   sections, open problems) rather than mixing splice + patch calls.

## Many small splices (10–20 local replacements, not a 50% rewrite)

Do **not** batch these as `content.replace(old, new)` of guessed multi-line
anchors. Wrapping inside math/`\cite` fails the unique-count assert, and a
single Python file that mixes `\\` (for matching) with `\\\\` (for writing)
will emit the wrong LaTeX.

1. Collect every `(start, end)` range from `search_files` / `.aux` numbers.
2. Dump the live lines from disk — do not type the old text from memory:
   ```python
   lines = Path(PATH).read_text().splitlines(keepends=True)
   for a, b in ranges:
       print(f"===== {a}-{b} =====")
       for i in range(a, b+1):
           print(f"{i}|{lines[i-1]}", end="")
   ```
3. Write a splice function that **verifies the head** before writing:
   ```python
   def splice(start, end, new, head):
       block = "".join(lines[start-1:end])
       if not block.startswith(head):
           raise SystemExit(f"HEAD FAIL {start}-{end}")
       lines[start-1:end] = new.splitlines(keepends=True)
   ```
   Call `splice` **bottom-up** (highest `start` first). `new` is an `r'''...'''`
   with **single** TeX backslashes, identical to the source file.
4. `head` is the first source line of the range including its trailing
   newline (copy it from the dump, do not re-type). A failed head check
   means the range drifted — dump again, do not guess wrapping.
4. Post-splice sweep in the same script: grep the output for
   `\ref{` + every label you REMOVED (a curated stale-label list), and
   for leftover phrasing probes ("indeterminacy group",
   "unification theorems").
5. Compile 3 passes (inline `thebibliography` needs no bibtex), grep the
   log for BOTH `undefined` AND `multiply`, then run the content audit
   below.

## Pitfalls (all hit in the 2026-08-28 MomentSheaf Review-4 rewrite)

- **Lines adjacent to a splice range.** Content just BEFORE or AFTER a
  replaced range often belongs to the replacement: a stale intro sentence
  ("...the following unification theorems:") survived because it sat one
  line above the range; a `\subsection{...}` + `\label{sec:...}` was
  silently deleted because it sat INSIDE the range. Re-read each boundary
  region (±2 lines) before splicing and decide ownership explicitly.
- **Reused labels ⇒ multiply-defined.** If a new fragment reuses an
  existing `\label` (e.g. a corrected theorem keeps its old name), the
  OLD definition must be inside a replaced range — or explicitly deleted
  (it may live in a block you chose to keep). Symptom:
  `LaTeX Warning: Label ... multiply defined.` Grep for `multiply` after
  every pass, not just `undefined`.
- **Raw-string hygiene.** Use `r'''...'''` (preserves backslashes); lint
  the script before running — a `{len(lines}` brace typo is a SyntaxError
  that only surfaces at run time.
- **PDF text-extraction false negatives.** pymupdf splits a title across
  lines ("...Inverse Limits and the\nMeasure Sheaf") and renders en-dashes
  as "–" or hyphenation as "x-\ny". Before substring matching:
  `re.sub(r"\s+", " ", text)`, normalize –/— to `-`, strip superscript
  digits ("lim¹" → "lim1").
- **PDF substring false positives.** A check like "reduced moment problem"
  matches the NEW title "Gelfand-reduced moment problem". Treat every
  FOUND in the absent-list as a suspect: inspect its source context —
  negated usages ("not a sheafification", "admits no sheafification")
  are intentional and correct.
- **Build artifacts.** Add `*.aux *.log *.out *.toc *.fls *.fdb_latexmk
  *.synctex.gz *.bbl *.blg` to .gitignore BEFORE the checkpoint commit.

## Content-audit pattern (after clean compile)

```python
import fitz, re
doc = fitz.open("paper.pdf")
t = re.sub(r"\s+", " ", "".join(p.get_text() for p in doc))
t = t.replace("\u2013", "-").replace("\u2014", "-")
must, absent = [...], [...]      # new theorem titles / removed claims
for c in must:   assert c in t, f"MISSING: {c}"
for c in absent:
    if c in t: print("check context:", c)   # inspect source; may be legit
```
