---
name: hermes-tool-edge-cases
description: "Hermes tool edge cases: LaTeX edit/read quirks, terminal transport mangling of long commands, verification recipes."
version: 1.1.0
author: YOUR-USER
metadata:
  hermes:
    tags: [hermes, tools, edge-cases, latex, debugging]
---

# Hermes Tool Edge Cases for Research Workflows

Known pitfalls and workarounds for Hermes built-in tools when working with
LaTeX manuscripts, large source files, and research artifacts.

## When to Use

- You're editing a `.tex` file and the `patch` tool produces garbled output
  (double backslashes, corrupted LaTeX commands)
- `read_file` refuses to show a new section of a file you already read
- You need to verify that LaTeX compilation produced the expected content
- Any time a Hermes built-in tool behaves unexpectedly with non-trivial files

## Pitfalls

### The `patch` Tool and LaTeX Backslashes (Updated 2026-07)

The Hermes built-in `patch` tool in mode=`replace` now handles LaTeX backslashes correctly — no doubling occurs. You can safely use it for targeted `.tex` edits:

```python
# patch(mode='replace', path='paper.tex', old_string=r'\textbf{old}', new_string=r'\textbf{new}')
```

**Caveat:** For multi-section edits across non-contiguous regions of a large file, still prefer `execute_code` with Python `str.replace()` to batch all changes in one read/write cycle — this avoids multiple patch round-trips and the risk of stale matches.

If you ever see backslash doubling (a regression), immediately revert with
`git checkout <file>.tex` and fall back to `execute_code`.

**Escape-drift guard (2026-09):** a distinct, pre-application failure mode. When the tool-call JSON layer escapes arguments one extra time, every backslash run in your `old_string` arrives exactly 2× longer than on disk, and `patch` refuses with "Escape-drift detected ... would double every backslash in the file" — nothing is written. This hits `.md` theory documents with heavy LaTeX (`$$...$$`, `$\ell^{2d}$`) as easily as `.tex`. Fix: re-read the target region with `read_file` and resend both strings copying the on-disk backslash count **verbatim** (single backslashes for content read_file shows as single) — do NOT add escapes to "fix" it, and do NOT retry the rejected call unchanged. It is a sibling of the stale-`old_string` pitfall below: verbatim copy from disk is the only reliable match source.

### `read_file` Dedup Blocks Large Files

`read_file` may refuse to display new sections of a large file with the
message "File unchanged since last read." The dedup mechanism prevents
re-reading a file it already served, even when you're asking for different
line ranges or offsets.  This also affects `.py` files (e.g., large
implementation files under `Irene/`) and `.bib` bibliography files.

**Fix:** Use `terminal` with `sed` to read specific line ranges:

```bash
sed -n '1545,1580p' /path/to/large/file.tex
sed -n '826,900p' /path/to/large/file.py      # Python source
cat /path/to/file.bib                           # entire bib file
```

This is especially common with:
- Large `.tex` manuscripts (1000+ lines) where you need to inspect
  multiple non-overlapping sections before editing
- Files opened once for metadata, then re-accessed for content

### Citation Merging (Absorbing a Reference)

When a self-citation (e.g., an unpublished manuscript marked "in preparation")
needs to be absorbed into the main text and removed from the bibliography,
follow the step-by-step workflow in `references/citation-merge-workflow.md`.
The pattern: locate all `\cite{Key}` sites → replace with self-contained
content → optionally enrich with algorithmic detail from the source →
remove bib entry → 3-pass verify.

### `\theoremstyle{remark}` for Upright Remark Body

LaTeX's `amsthm` default `plain` theorem style renders remark body text in
italic. To make ALL remark blocks use upright (roman) body text, wrap the
`\newtheorem{remark}` declaration with `\theoremstyle{remark}` in the preamble:

```tex
\newtheorem{definition}{Definition}
\theoremstyle{remark}
\newtheorem{remark}{Remark}
\newtheorem{conjecture}{Conjecture}
\newtheorem{example}{Example}
\theoremstyle{plain}  % restore plain style for subsequent theorems
```

This also applies to `example` and `conjecture` environments. Without the
style wrapper, remark bodies render in italic (`cmti`), which the user
considers incorrect for mathematical remarks.

### Theorem Environment Names Must Match the Preamble (2026-08)

When INSERTING a new section into an existing manuscript, the theorem
environments you write must match the names the manuscript actually
declares in its preamble — not the short aliases that happen to be
conventional. A manuscript may declare `theorem`/`remark`/`example` while
the ghasemi-latex-style convention names them `thm`/`rem`/`exm`. Using the
alias that is NOT declared produces a hard `Environment ... undefined`
compile error, one per environment.

**Fix — grep the preamble FIRST, before writing any new theorem block:**

```bash
grep -oE 'newtheorem\{[a-z]+\}' paper.tex
# e.g. -> newtheorem{theorem} newtheorem{lemma} newtheorem{remark}
#        newtheorem{example} newtheorem{definition} newtheorem{proposition}
```

Then use exactly those names in the inserted content. This session hit
three separate compile failures from `thm`→`theorem`, `rem`→`remark`,
`exm`→`example` after inserting a new section. One preamble grep up front
saves the whole round of recompile-and-fix.

Also scan the inserted region for any other undefined control sequences or
macros (e.g. `\rx`, `\sp`, `\C(`) — a fresh section is the most likely place
to introduce a macro the rest of the manuscript never defined.

### PDF Content Verification with pymupdf

After compiling LaTeX, `pdflatex` may succeed with zero errors while
producing output that's silently wrong — ligature breakage, font
substitution, or overfull boxes that truncate critical content. Use
`pymupdf` in an `execute_code` block to verify specific text made it
into the PDF:

```python
import pymupdf
doc = pymupdf.open("paper.pdf")
full_text = "".join(doc[i].get_text() for i in range(doc.page_count))
# Search for key terms — use substrings, not full sentences
for term in ["Ostrowski", "Schur complement", "auxiliary lift"]:
    assert term in full_text, f"Missing from PDF: {term}"
doc.close()
```

**Ligature caveat:** pymupdf text extraction can break on LaTeX ligatures
(ff, fi, fl, ffi). If a search for a full sentence fails but the PDF
appears correct, search for shorter substrings. The content is present;
the extraction just splits the ligature across characters.

**Unicode math-minus caveat (2026-08):** math-mode minus signs extract as U+2212, not an ASCII hyphen — asserting a table cell like "-1.413" against extracted text silently fails though the PDF is correct. Replace U+2212 with "-" in the extracted text before matching negative numbers.

### pymupdf on Scanned / Mixed Text-Layer Input PDFs (2026-09)

`get_text()` reads whatever embedded text layer exists — for old scanned math papers that is often a garbage OCR layer, while digitally-created front matter pages extract perfectly. Such mixed documents pass any spot-check yet are unusable for the body. Before trusting pymupdf output from a local legacy/scanned PDF, check per-page quality:

```python
for i, page in enumerate(doc):
    t = page.get_text()
    if len(t.strip()) < 50 or sum(c.isalnum() for c in t) / max(len(t), 1) < 0.3:
        print(i + 1, "WEAK")
```

Weak pages → render + vision (`pdftoppm -jpeg -r 150 -f N -l N file.pdf /tmp/page`, then `vision_analyze`) for a few pages, or marker-pdf for bulk OCR. If the document also exists remotely (arXiv `/pdf/` URL, publisher site), prefer `web_extract` on that PDF URL — the remote pipeline returned clean text from a 25-page scan in seconds where local extraction produced only garbage, with no multi-GB install.

### `write_file` vs `patch` for Multi-Section LaTeX Edits

When a single session needs edits across multiple non-contiguous sections
of a `.tex` file, batch all changes into one `execute_code` block using
multiple `str.replace()` calls — this avoids the patch tool entirely and
reads the file only once:

```python
with open("paper.tex", "r") as f:
    content = f.read()

edits = [
    (r"old text 1", r"new text 1"),
    (r"old text 2", r"new text 2"),
    (r"old text 3", r"new text 3"),
]
for old, new in edits:
    assert old in content, f"Not found: {old[:50]}..."
    content = content.replace(old, new)

with open("paper.tex", "w") as f:
    f.write(content)
```

### Verify What a Write Actually Put on Disk (2026-08)

1. **Stale byte-identical "revisions":** a prior session may have left an exact copy of the original under a new name (`md5sum` identical). After context compaction, re-hash before treating any claimed revision as real content.
2. **Re-read after large writes:** long `write_file` payloads can arrive truncated in context or land differently than remembered — especially across a compaction boundary where earlier tool outputs are stubs. Re-read from disk in small bounded slices; disk bytes are ground truth, not your recollection of the payload.
3. **Splice hygiene for new sections:** grep all label macros first and check every ref target in the inserted block resolves (dangling refs compile with only a warning); verify hard-coded section numbers against actual numbering order (unnumbered early sections shift it); locate splice points by short distinctive fragments or regex, not full environment headers typed verbatim — count-assert the match.

### Lean4 MCP Tool Failures

When `lean4_repl`, `lean4_prove`, or `lean4_search` fail with missing cache
or empty results, fall back to a standalone Lake project. See
`references/lean4-lake-project-workflow.md` for the full setup recipe,
including the critical `HOME=/home/YOUR-USER` fix, current Mathlib version
(v4.31.0), and key lemmas discovered for power-mean inequality proofs.

### `tocbasic` Package Produces `\addcontentsline` Warnings

When using the `tocbasic` package (for custom ToC entries or part-level
table of contents), pdflatex emits warnings like:

```
LaTeX Warning: \addcontentsline as \numberline ... will be moved.
```

These are cosmetic but clutter the log and can mask real issues. Suppress
them by adding to the preamble BEFORE `\begin{document}`:

```tex
\makeatletter
\let\l@part\l@chapter  % or whatever section level you use
\makeatother
```

Alternatively, if you don't need `tocbasic` features, omit the package —
standard `\addcontentsline` works without it.

### `search_files` Finds Nothing Inside `~/.hermes` — Use `terminal grep` for Hermes Source

Answering "what does Hermes actually do when I X?" means reading the installed
source at `$HOME/.hermes/hermes-agent` (and, for the desktop app, its packaged
Electron output). `search_files` returns `total_count: 0` for any pattern under
`/home/YOUR-USER/.hermes/**`, silently — the path prefix looks like a dot-directory
it declines to walk, so an empty result there is NOT evidence the symbol is
absent. Run the search in the shell instead:

```bash
grep -rn "desktop_project\|projects\.db\|def create_project" --include=*.py \
  ~/.hermes/hermes-agent | grep -v test | head -40
```

Also note the desktop app ships **built** JS: `apps/desktop/dist/electron-main.mjs`
is the authoritative behavior for the running app when `apps/desktop/electron/*.ts`
and the built bundle disagree (compare `apps/desktop/release/*/resources/install-stamp.json`
commit against source HEAD for skew).

### Verifying Hermes' Own Behavior: Read the Source, Then Probe a Scratch `HERMES_HOME`

For a yes/no question about a Hermes-side effect ("does creating a project also
`git init`?", "is a row written on this RPC?") a source read alone earns a
"probably" — the durable answer is a probe of the real code path against a
throwaway home. Never probe against the live profile: you would pollute
`projects.db`/`state.db` and, for `desktop_project`, re-anchor the very session
you are answering from.

```python
# write_file /tmp/probe.py, then: HERMES_HOME=/tmp/hproj/home \
#   ~/.hermes/hermes-agent/venv/bin/python /tmp/probe.py
import os
os.environ["HERMES_HOME"] = "/tmp/hproj/home"          # reset BEFORE importing hermes modules
from hermes_cli import projects_db as pdb
with pdb.connect_closing() as conn:
    pid = pdb.create_project(conn, name="Probe", folders=["/tmp/hproj/d"], primary_path="/tmp/hproj/d")
print(os.path.exists("/tmp/hproj/d/.git"))               # the claim under test
```

Rules that make this cheap: set `HERMES_HOME` before the first `hermes_*` import
(paths are resolved at import time); call the same function the tool/RPC handler
calls (`pdb.create_project`, `web_git.worktree_add`) rather than a re-implementation;
`rm -rf` the scratch tree when done; and report the raw probe output plus the
`file:line` call chain in the answer so the claim is checkable.

Source tree, call chains, and the project↔git-init map:
`references/hermes-internals-verification.md`.

### Memory Tool: Atomic Batch Rejections When Over Budget (2026-08)

The `memory` tool checks the character limit only on the FINAL result of an
`operations` array — but each rejected batch reports the arithmetic
(`would be at N/M chars — over the limit`, with current entries listed).
When memory is near its cap, an `add` alone will not fit, and shrinking only
one entry often still misses. The efficient pattern (avoids a 3-failure loop):

1. Read the rejection's `current_entries` and `usage` from the FIRST failure.
2. Compute the shortfall once: `sum(len(new entry)) − (limit − usage)`.
3. Build ONE batch that shortens/removes enough entries to clear the whole
   shortfall **plus** the add — `replace` several stale entries with condensed
   versions and `add` the new one in the same atomic call.
4. Do not retry the same add unchanged; each identical retry re-lists all
   entries and the tool-loop detector fires after 3 failures.

If the budget genuinely cannot fit the entry, drop it rather than evicting
high-signal facts — content already encoded in AGENTS.md or a skill body is
durably persisted and a memory duplicate is redundant.

### `patch` Sibling-Subagent Warning on Unread Files (2026-08)

`patch` may succeed on a file this session never read, returning only a
warning that a sibling subagent modified it (`_warning` field). The write
lands, but it was applied blind over unknown content. Treat that warning
as a signal to `read_file` the region and verify the merge before building
on it.

### Stale `old_string` From Recalled or Partially-Viewed Files (2026-09)

A patch whose match text was reconstructed from memory — or from a file only
previously viewed with offset/limit pagination — fails with "Could not find a
match" even when the intended region exists in near form. Fuzzy matching cannot
bridge a remembered version that differs from disk (the file changed in an
intervening session, or OCR'd source text was recalled cleaner than it is).

**Rule:** before any non-trivial `patch`, `read_file` the exact target region
and copy match text verbatim from what comes back — never from recall. When a
match fails and the error returns "Did you mean one of these sections?", diff
those suggestions against your intent instead of re-guessing; they show what is
actually on disk near the target.

### Compaction Resumption with Elided Tool Outputs (2026-09)

After a context-compaction boundary, prior `read_file`/`execute_code`
outputs appear in the resumed context as one-line stubs (`(1 lines output)`).
Re-running the same full-file reads to "recover" them is an unproductive loop:
each new read can be elided again, so repeated recovery passes consume turns
without accumulating usable content (one manuscript-sync session burned 40+
turns re-reading a ~50KB `.tex` and two theory files across three boundaries,
applied no edit).

**Rules:**
1. **Probe once, cheaply.** On resumption establish current state with `wc -c`
on every input file plus one structural grep (heading map / line count) — not
another full read. If sizes match the pre-compaction record, files are
unchanged; if a size differs, re-read only what shifted.
2. **Read minimal slices, once.** For the pending edit, read exactly the
regions you will patch (`read_file` offset/limit or `sed -n 'N,Mp'`). A
full-file re-read of a 50KB manuscript to pin a ~100-line insertion point
discards nothing but context budget.
3. **Extract-to-disk for durability.** The only state that survives compaction
is what you wrote to disk: as soon as an edit's exact inputs are recovered
(theorem statements, ledger rows, insertion boundaries), append them in the
same call to a small workspace scratch file (e.g.
`workspace/<task>-extract.md`). After the next boundary you read one small
file instead of re-pulling five large ones.
4. **Never retry an elided call unchanged.** A stub output is not an error —
   the identical call returns another stub and trips the tool-loop detector.
   Switch method (`read_file` slice ↔ `terminal sed -n 'N,Mp'`) and verify file
   integrity with `wc -c`/`md5sum` before suspecting corruption. Anomalous short
   reads (319 chars from an 11,640-char file) are preview artifacts, not file
   damage — re-probe differently rather than concluding the file changed.
   Channel switch: if a RUN of short `terminal` calls right at the boundary all
   come back as one-line stubs (even trivial ones like `wc -c`, `ls`, short
   greps), stop sending through that channel — route evidence-producing work
   through `execute_code` (its stdout delivered in full where terminal's did not)
   or redirect to a file and `read_file` it back. The terminal stdout channel is
   flaky only *right at* the boundary and typically recovers after a few turns.

### Terminal Transport Mangles Long / Complex Commands (2026-09)

Distinct from post-compaction elision: while a session is live, `terminal` calls whose command strings are long or quote-heavy can arrive corrupted — bash reports `` eval: line N: unexpected EOF while looking for matching backtick `` and exits 2, or the call returns exit 127 with no usable output. Multi-line Python heredocs (`python3 - <<'PYEOF'`) are the most frequent victims; long compound one-liners (several echos + sed + wc chained) can also come back as a one-line elided stub even when they succeeded, hiding their stdout.

**Rules (what worked):**
1. One purpose per `terminal` call; keep each command short enough to read in full on the result line. A five-part compound command is a mangling candidate — split it into separate calls or drop the logic into a file.
2. Never put Python logic in a shell heredoc when you can avoid it: `write_file` the script (e.g. `/tmp/<name>.py`) and run `python3 /tmp/<name>.py`. Same for multi-step grep/awk pipelines — write them as a file, or use `execute_code` with `hermes_tools.terminal`.
3. When output returns as a one-line stub or the shell reports a quoting EOF, do NOT re-send the same command (loop detector fires and the transport corrupts it again). Re-issue split into shorter pieces or via a script file; verify results by reading files back (`wc -c`, `grep -c`) instead of trusting elided stdout.
4. **When the output IS the evidence** (experiment validation, test suite, benchmark, compile gate), redirect stdout+stderr to a file and echo the exit code, then read the file back — never take the verdict from the inline result line:
   ```bash
   python3 script.py > reports/<name>_stdout_<date>.txt 2>&1; echo "exit=$?"
   ```
   The log doubles as the durable artifact the report or claims-ledger row cites, and it survives context compaction (see the compaction section above).

### Deferred Tools: `tool_call` Batches ONE Local Tool Per Call

`tool_call` accepts several entries in `calls` ONLY when every entry is a
`connectors__` name. Two local (MCP) tools in one `calls` array is rejected
outright, and the error names the retry shape:

```
tool_call takes exactly one entry for local tools; you sent 2. Retry with only:
{"calls":[{"name":"mcp__vikunja__tasks_get","arguments":{"task_id":765}}]} then
issue the remaining 1 call(s) as separate tool_call invocations.
```

**Rules:**
1. **One local tool per `tool_call`.** For N independent local calls, issue N
   `tool_call` invocations *in the same assistant turn* — independent calls run
   concurrently there, so this costs no extra wall-clock over a batch and avoids
   the rejection round-trip entirely.
2. **Every entry needs both `name` and `arguments`.** Omitting `name` fails
   independently with `tool_call calls[0] requires a 'name'` — the batching and
   the shape errors are separate, so a rejected call may violate either or both.
3. **The batched call in this family is `tool_describe`, not `tool_call`.**
   `tool_search` (keyword queries, not questions) → `tool_describe` (a LIST of
   names, one call) → `tool_call` (one local tool, or a batch of connectors).
4. On rejection, follow the suggested retry shape verbatim rather than re-emitting
   the same batch; the loop detector fires on identical re-sends.

### Protected Agent-Instruction Files Are Consent-Gated

Writes to protected agent-instruction files (a project `AGENTS.md`) raise an
approval prompt. With no user present it times out and the write is refused:

```
BLOCKED: write to protected agent-instruction file(s) (AGENTS.md) approval
prompt timed out without a user response. Silence is not consent.
```

The same block applies to routing around the gate (`terminal` heredoc,
`execute_code` rewrite) — those are refused as well, and retrying is pointless.

**Procedure:** make the edit once. On refusal, finish every other part of the
same-commit status sync that is *not* gated (README status row, claims ledger,
project reports, tracker task records), state plainly in the handoff that the
AGENTS.md row is pending approval, and offer to retry on request. When the user
then asks for it, re-issue the identical edit — in-conversation consent is what
never report a gated file as synced when it is not.

### `source <venv>/bin/activate` Is Shadowed by the Shell's Pinned venv (2026-09)

A `terminal` command that starts `source <project>/.venv/bin/activate && python …`
can silently run a *different* interpreter. The Hermes shell already exports a
pinned `VIRTUAL_ENV`, and in a non-interactive shell `which python` (and
`sys.executable`) resolves to that one, not the venv you just sourced. The
symptom is `ModuleNotFoundError` for a package the project venv definitely has
(e.g. `sympy`) even though `<project>/.venv/bin/python -c "import sympy"`
succeeds — the tell is that activation "worked" but the dependency is "missing".

**Fix:** select the interpreter by path — `../Irene/.venv/bin/python script.py`
(also for `-c`, `-m pip list`, `-m pytest`). Confirm with `which python` or
`python -c 'import sys; print(sys.executable)'` when a run behaves oddly.
Exporting and reusing plain env *vars* across calls still works; it is the
*interpreter selection* the pinned `VIRTUAL_ENV` overrides.

### `.emv` Credential Files Walk Up the Directory Tree (2026-09)

Hermes tool scripts auto-discover `.emv` credential files by walking up the
directory tree from the script's location. A skill's tool script (e.g.
`vikunja_tool.py`) implements `_load_emv()` which checks for a `.emv` file
in the script's own directory and each parent directory up to the profile root;
the first `.emv` found is loaded as environment variables before the tool runs.
This means credentials can be co-located at the skill level (more granular than
the profile-level `.env`).

**Rule:** When a skill's tool appears to lack credentials that should be set,
look for `.emv` files in the skill directory and parent directories — not just the
profile `.env`. The `.env` holds all service URLs and tokens; individual `.emv`
files in skill directories hold skill-specific credentials that override or
supplement the profile `.env`.

```bash
find ~/.hermes/profiles/math/skills -name ".emv" -exec ls -la {} ;
# Look in: skill_dir/.emv, skill_dir/productivity/zotero/.emv, etc.
```

### Cross-Profile MCP Script Paths Create Hidden Dependencies (2026-09)

MCP server entries in `config.yaml` specify `command` paths that are
**absolute**, not profile-relative. When one profile's MCP config references
a script inside another profile's directory, it creates a structural dependency
that breaks profile isolation.

**Observed example:** The librarian profile's `config.yaml` registers three
CLI-adapter MCP servers (vikunja, wolfram-alpha, lightrag-query) whose `command`
points to `/home/YOUR-USER/.hermes/profiles/math/scripts/mcp_cli_adapter.py` — the
math profile's directory. The librarian profile has no `scripts/` directory
of its own. Deleting or renaming the math profile silently breaks the
librarian profile's MCP servers (they fail at startup with "script not found").

**Rule:** When inspecting or modifying a profile's MCP config,
verify every script path lands inside the profile being examined:

```bash
grep -n "mcp_cli_adapter\\|math/scripts" config.yaml
# If any path contains a DIFFERENT profile name (e.g. profiles/math in the
# librarian config), that server breaks if the referenced profile is removed.
```

The fix for profile independence: copy `mcp_cli_adapter.py` into each
profile's own `scripts/` directory, or place it in a shared `~/.hermes/tools/`
path and use profile-relative path variables in `config.yaml`.

### MCP Schema Cache Diverges from config.yaml (2026-09)

MCP server schemas are cached at
`~/.hermes/profiles/<profile>/cache/mcp_schema_cache.json` at session start.
The cache reflects what was loaded in the **last session**, not the current
config — it is not invalidated when `config.yaml` changes. A server may be
in config.yaml but missing from the cache (if the last session failed to
load it), or present in the cache but removed from config.yaml (stale entry).

**Rule:** When debugging "why isn't my MCP tool available?", check the cache
file for the ground truth of what tools the last session actually loaded.
Compare cache keys against `config.yaml` `mcp_servers` keys:

```bash
python3 -c "\nimport json, os\np = os.environ.get('HERMES_PROFILE', 'math')\ncache = os.path.expanduser(f'~/.hermes/profiles/{p}/cache/mcp_schema_cache.json')\nwith open(cache) as f:\n    print(sorted(json.load(f).keys()))\n"
```

## Verification Checklist

After any LaTeX edit, run this sequence:

1. `pdflatex -interaction=nonstopmode paper.tex`
2. `bibtex paper` (if citations changed)
3. `pdflatex -interaction=nonstopmode paper.tex`
4. `pdflatex -interaction=nonstopmode paper.tex` (resolve cross-refs)
5. Check log: `grep -c 'Citation.*undefined\|Reference.*undefined\|^! ' paper.log`
6. Verify content: pymupdf check for key terms (see pitfall above)

**First-pass citation warnings are a false alarm.** When compiling with
`latexmk -pdf` (or a single `pdflatex` pass before `.aux` is populated),
the log will report every `\cite` as "Citation ... undefined" and every
`\ref` as "Reference ... undefined" — even when all keys exist in the
bibliography. These clear on the subsequent pass once the `.aux`/`.bbl`
files are written. Do NOT treat a first-pass "56 undefined citations" as a
real failure. The authoritative check is the FINAL pass: after `latexmk`
converges, `grep -aic 'undefined' paper.log` should return `0`, and the
`.aux` should contain a `\bibcite{...}` entry per cited key. If the final
log still shows undefineds, only then investigate the bib keys.
