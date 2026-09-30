# djvu2pdf internals & reconnaissance notes

Evidence behind the engine choices in `SKILL.md`. Re-verify with the regression suite
(`scripts/test_djvu2pdf.sh`) rather than trusting these notes blindly.

## Why not `dpsprep --socr`

`dpsprep 2.8.3` has an OCR path (`--socr`, equivalently
`--ocr '{"language":["eng"]}'`) that drives OCRmyPDF through its API. On this host it
deadlocks: with a clean `/var/tmp/dpsprep` and `-p 1`, a 3-page bitonal DjVu writes
`page_bg_{1,2,3}.pdf` and then hangs indefinitely. `faulthandler` (SIGABRT) shows the
main thread parked in

```
multiprocessing/connection.py:1136 wait
multiprocessing/connection.py:440  _poll
  -> dpsprep/concurrency/processor.py:84 process
  -> dpsprep/concurrency/api.py:21 concurrently_process_pages
  -> dpsprep/cli.py:134 dpsprep
```

with no worker children alive — the workers died and the parent waits forever. There is
no timeout and no error; the process just sleeps. Reproduced with the stale
`/var/tmp/dpsprep/<hash>` directory from the killed run cleared, so it is not a cache
artifact. Full stack dump, reproduction command, and the control checks that clear
OCRmyPDF of blame: `references/dpsprep-ocr-deadlock.txt`.

OCRmyPDF itself is fine: both the apt build (15.2.0) and the venv build (17.12.1) OCR a
raster PDF correctly in ~1s. So `-m ocr` rasterizes with `ddjvu` and then OCRs with the
`ocrmypdf` CLI — same output quality, no deadlock, and it is resumable/observable.

## Verified toolchain

| Component | Version / path |
|---|---|
| DjVuLibre CLI (`ddjvu`, `djvused`, `djvutxt`, `djvm`, `cjb2`, `djvumake`) | 3.5.28-2ubuntu0.24.04.2 |
| `dpsprep` | 2.8.3, venv `~/.local/share/djvu-pipeline/venv` |
| `djvulibre-python` | 0.9.3 (compiled; needs `python3.12-dev` + `libdjvulibre-dev`) |
| `ocrmypdf` | apt 15.2.0 + venv 17.12.1 |
| `tesseract` | 5.x, `eng` + `osd` traineddata |
| `qpdf` | 11.9.0 (used only for outline verification) |

## What dpsprep actually preserves

Given a DjVu whose hidden text layer and outline are set, `dpsprep` carries both into
the PDF. Verified end-to-end on a purpose-built fixture (3 pages, line-level text layer,
3 bookmarks):

- `pdftotext -layout` returns each page's three lines in the correct order,
- `pdfinfo` reports the source page count,
- `qpdf --json --json-key=outlines` returns `Page One/Two/Three` pointing at pages 1/2/3.

Image PDFs are larger than the DjVu (≈4.7× on the bitonal fixture: 3.9 KB → 19 KB) —
the 5–6× figure quoted in dpsprep's README is the right order of magnitude.

## Real-file results

`lipsum_words.djvu`, `lipsum_lines.djvu` (and the deliberately-corrupt
`lipsum_words_invalid.djvu`) from dpsprep's `fixtures/` — 2 pages, 4961×7016 px at
600 dpi, word-level text layers:

| Metric | Result |
|---|---|
| Conversion | exit 0, engine `text`, pages match |
| PDF text recall vs source layer | 0.990–0.994 |
| PDF page-1 recall vs original LaTeX text | 0.984 |

Recall is computed as `|{w in reference : w in extracted}| / |reference|` over
whitespace-split tokens; word counts differ by a handful (≈672 vs 677) because dpsprep
drops a few tokens and normalizes hyphenation. Sequence order is not byte-identical.

## DjVu hidden-text format (for fixtures and repair)

From `djvused(1)`, "Hidden text syntax": structural components are
`(type xmin ymin xmax ymax ...)` where *type* ∈ page, column, region, para, line, word,
char; **coordinates are in pixels with origin at the bottom-left corner**. Text layers
may be page-only, line-level, or word-level (word-level is what ABBYY/IA produce).

Gotchas hit while building the fixture:

- `(line x y width height "t")` is wrong — it is two corners. `djvused` silently
  rewrites the fields, so read back with `print-txt` to confirm.
- Nested parens around the box (`(line (1 2 3 4) "t")`) produce
  `Syntax error in txt data: number expected` and `document was not modified`.
- The page box must match the true pixel size (`djvused -e 'select 1; size'`), e.g.
  `(page 0 0 2479 3508 ...)` for A4 at 300 dpi.
- Points→pixels factor is `dpi/72` (4.1667 at 300 dpi).

Outline syntax is `(bookmarks ("Title" "#PAGE") ...)`, applied with
`djvused -e 'set-outline f; save'`.

## Verification design

`verify()` in `scripts/djvu2pdf.sh` checks three things against the source DjVu and
fails (exit 5) on any of them:

1. `pdfinfo` page count == `djvused -e 'n'`,
2. if a text layer was requested, `pdftotext` yields ≥ 25 non-space chars,
3. if the source has bookmark entries, the output's outline count (recursive count over
   `qpdf --json --json-key=outlines`) is ≥ 1.

Raster mode skips checks 2–3 by design and says so (`image-only by design`).
