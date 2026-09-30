# Multi-Session Manuscript Continuation (2026-08)

Recipes for continuing LaTeX work after a context-compaction boundary, when
earlier tool outputs arrive truncated or as stubs and prior "completed" steps
must be re-verified from disk.

## 1. Establish ground truth before editing

```bash
cd <project>
git status --short | head -20          # what is actually modified/new?
git log --oneline -5                   # where did the last real commit land?
md5sum original.tex revision_v2.tex    # identical => no real change was made
wc -l original.tex revision_v2.tex     # size sanity check
```

If a prior session claimed "wrote v2" but md5s match, rebuild from the true
base — do not build on the narrative.

Probe and audit artifacts left by earlier sessions (cross-ref lists, label
inventories, ground-truth dumps in /tmp) are UNTRUSTED input: they may contain
fabricated entries or stale counts that never existed in the source. Before
building on one, re-derive it with a fresh script run against the current
md5-pinned file and verify reproducibility — write the audit script to disk,
run it twice into two outputs, `diff -q` them; only byte-identical output
counts as ground truth. Cross-check derived counts independently (e.g. grep
each listed label for its `\label` definition: 0 hits = fabricated entry).

## 2. Recover large file contents in small slices

After compaction, `read_file` results for big files may be stubs (one-line
summaries instead of content). Re-read in bounded windows:

```bash
sed -n '1,40p' paper.tex      # preamble + abstract
grep -oE 'newtheorem\{[a-z]+\}' paper.tex   # theorem env names BEFORE writing any new block
grep -oE '\\label\{[^}]+\}' paper.tex | sort -u > /tmp/labels.txt
```

For JSON artifacts (validation results, convergence data), print them in full
via `execute_code` + `json.load` rather than trusting memory of their values.
Every number that will appear in new manuscript text must be traceable to a
disk artifact read in THIS session.

## 3. Splice discipline for inserted sections

- Cross-reference audit before compiling:

```python
import re
v1 = open("paper.tex").read()
new_sec = open("section_new.tex").read()
known = set(re.findall(r"\\label\{([^}]+)\}", v1)) | \
        set(re.findall(r"\\label\{([^}]+)\}", new_sec))
dangling = set(re.findall(r"\\ref\{([^}]+)\}", new_sec)) - known
print(dangling)   # must be empty; also check \cite keys against bib entries
```

The dangling check above is per-section only. When an earlier part of the
manuscript must become self-contained in a split-off paper (recap, mirror,
or restatement), close the label set transitively: for each mirrored target,
collect the labels referenced INSIDE its statement block and add them — the
closed set can be materially larger than the naive distinct-label count.
- Hard-coded section numbers ("Section 3") in prose drift when early sections
  are unnumbered. Verify against the actual `\section` order, or use labels.
- Splice markers: build long environment headers from fragments or find them by
  regex on a short distinctive fragment; always `assert count == expected`
  before splicing. Silent corruption of long backslash strings in tool args is
  the classic failure this catches.
- Prefer writing an edit script to `/tmp/apply_v2.py` and running it over
  embedding many large string literals inline — smaller per-call payloads, and
  the script itself can assert every anchor before touching the file.

## 4. Compile gate + content verification

```bash
pdflatex -interaction=nonstopmode paper.tex > /tmp/p1.log 2>&1; echo $?
pdflatex -interaction=nonstopmode paper.tex > /tmp/p2.log 2>&1; echo $?
```

Audit the FINAL log only (first-pass undefined refs/citations are a false
alarm). Then verify rendering with pymupdf:

```python
import fitz
doc = fitz.open("paper.pdf")
text = "".join(p.get_text() for p in doc)
text = text.replace("\u2212", "-")   # math minus -> ASCII hyphen BEFORE matching numbers
for term in ["0.4670882772", "-1.413137"]:    # exact table cells from the JSON artifact
    assert term in text, f"missing: {term}"
```

Also grep the log for overfull hboxes (`grep -c 'Overfull' paper.log`) — wide
tables are the usual offender; see `references/table-overflow-fix.md`.

## 5. Close out

- Clean up scratch files (`_section*.tex`, /tmp scripts) before finishing.
- Check whether new `.tex`/`.pdf` artifacts should be committed (repo may only
  track the canonical v1 pair) — ask or follow project convention; never commit
  secrets or large binary junk.
