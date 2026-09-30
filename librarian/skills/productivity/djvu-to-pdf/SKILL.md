---
name: djvu-to-pdf
description: Convert DjVu to PDF keeping text layer and TOC bookmarks.
version: 1.0.0
author: YOUR-USER Ghasemi, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [DjVu, PDF, OCR, Conversion, LibDjVuLibre, dpsprep, Documents]
    related_skills: [ocr-and-documents, calibre-library-ingestion]
---

# DjVu → PDF conversion

Converts `.djvu` scans to PDF while **carrying over the hidden OCR text layer and the
bookmark outline (TOC)** — the difference between a searchable library book and a
stack of flat images. Ships `scripts/djvu2pdf.sh`, a probe→convert→verify pipeline.
Do not hand-roll `ddjvu -format=pdf` as the default: it flattens to images and drops
the text layer and TOC (use it only via `--mode raster`).

## When to Use

- Adding a DjVu book/scan to the library or wiki — convert first, then ingest.
- "Make this .djvu searchable / give me a PDF of this .djvu."
- Batch-converting a folder of `.djvu` files.
- Don't use for: PDFs (see `ocr-and-documents`), DjVu *creation/editing* (`djvused`,
  `cjb2`, `djvm` directly), or reading DjVu text without conversion (`djvutxt file.djvu`).

## Prerequisites

Installed on this host (re-run only after a rebuild):

```bash
# system tools + OCR stack
sudo apt-get install -y djvulibre-bin libdjvulibre-dev libtiff-tools poppler-utils \
  qpdf ocrmypdf ghostscript tesseract-ocr unpaper pngquant python3.12-venv python3.12-dev

# dpsprep (not in apt; own venv because PEP 668 blocks system pip)
/usr/bin/python3 -m venv ~/.local/share/djvu-pipeline/venv
~/.local/share/djvu-pipeline/venv/bin/pip install "dpsprep[ocr,compress]"
ln -sf ~/.local/share/djvu-pipeline/venv/bin/dpsprep ~/.local/bin/dpsprep
ln -sf ~/.hermes/profiles/librarian/skills/productivity/djvu-to-pdf/scripts/djvu2pdf.sh ~/.local/bin/djvu2pdf
```

`python3.12-dev` is required — without `Python.h`, `djvulibre-python` fails to build.
`~/.local/bin` must be on PATH; the script also finds dpsprep via `$DPSPREP` if not.

## How to Run

```bash
# one file, default output beside the source
djvu2pdf book.djvu

# convert into a staging dir, then ingest with calibre-library-ingestion
djvu2pdf -o ~/Documents/ToLib book.djvu

# batch, 8 workers, aggressive PDF optimization
djvu2pdf -j 8 -O 3 -o out/ *.djvu

# scan with no text layer -> OCR it
djvu2pdf -m ocr -l eng+grc scanned.djvu
```

Prefer `terminal(command="djvu2pdf ...")` over bare shell prose.

## Engine selection

| Situation | Engine | Result |
|---|---|---|
| Hidden text layer present (`auto`) | `text` (dpsprep) | image + original OCR text + TOC |
| No text layer (`auto`) | `ocr` (ddjvu → ocrmypdf) | image + fresh tesseract text |
| `-m raster` | `ddjvu` | image only, 5–6× larger, no text/TOC |

`auto` probes the file with `djvutxt` (≥25 non-space chars counts as a text layer)
and `djvused -e 'print-outline'`, then picks `text` or `ocr`. Converting a book that
already has OCR is much cheaper and more accurate than re-OCRing it — leave `auto` alone.

## Procedure

1. **Probe before converting** — `djvu2pdf -n file.djvu` prints pages, dpi, page size,
text chars, outline entries and the engine it would use. Completion: you know whether
the scan already has OCR and a TOC.
2. **Check for an existing PDF** before writing: `djvu2pdf` skips an existing output
unless `-f` is given, so a re-run is safe.
3. **Convert** with `djvu2pdf [-m MODE] -o DIR file.djvu`. Completion: exit 0 and the
log line `verified: pages OK, text layer present`.
4. **Read the exit code**, not just the log: `0` ok, `3` missing input, `4` engine
failed outright, `5` produced but DEGRADED (image-only) or TOC/text missing.
5. **Confirm searchability on the real artifact** — the pipeline does this for you, but
when text quality matters (math books): `pdftotext out/book.pdf - | head -40`.
6. **Ingest** the PDF via `calibre-library-ingestion` (hash the PDF into the duplicate
check, then `add_books` with `{"PDF": path}`); keep the `.djvu` as the archival copy.

## Quick Reference

```bash
djvu2pdf -h                              # full option list
djvu2pdf -n file.djvu                    # probe: pages/dpi/text layer/TOC/engine
bash scripts/test_djvu2pdf.sh            # regression suite (22 checks)
```

| Flag | Meaning |
|---|---|
| `-m auto\|text\|ocr\|raster` | engine (default `auto`) |
| `-l eng+grc` | OCR languages |
| `-q N` | JPEG quality for RGB/gray pages (85) |
| `-j N` | worker processes (default nproc) |
| `-O 0..3` | OCRmyPDF PDF optimizer level |
| `-M 'bitonal[2-end]'` | forward `--mode` to dpsprep (keep a color cover small) |
| `--deskew` | deskew during OCR |
| `-t SEC` | per-file engine timeout (1800) |
| `-o DIR` / `-f` / `-n` / `-v` | outdir / overwrite / dry-run / verbose |

## Pitfalls

- **Never use `dpsprep --socr` for OCR.** On this host its worker processes die
  (bitonal/TIFF pages) and the parent blocks forever in
  `concurrency/processor.py` waiting on results — no timeout, no error. `djvu2pdf -m ocr`
  uses `ddjvu` → `ocrmypdf` instead, which is verified working and ~1s for 3 pages.
- **dpsprep's own `--help` is wrong**: it documents `--ocrs` in the prose but the flag
  is `--socr` (`--ocr '{"language":["eng"]}'` is the long form). Neither is used here.
- **Always run engines under `timeout`** (the script does, `-t`, default 1800s). A
  dpsprep worker that dies hangs the parent silently; a hung conversion is worse than
  a failed one.
- **Stale working directory**: dpsprep caches per-source-path state under
  `/var/tmp/dpsprep/<hash>`. After a killed run it *reuses* that directory
  ("Reusing working directory") and can hang or exit early. If a run misbehaves:
  `rm -rf /var/tmp/dpsprep/*` and retry; add `-d` to dpsprep for a clean slate.
- **`Failed to encode page N. Trying again without setting quality` is benign** on
  bitonal pages — Pillow falls back to TIFF/G4, which has no quality knob. Warnings in
  this pattern mean failure, not this.
- **`djvused` hidden-text syntax is `(line xmin ymin xmax ymax "text")`** — corner
  coordinates in **pixels** (not points), origin at the **bottom-left**
  (djvused(1) "Hidden text syntax"). Writing `(x y width height)` silently produces
  overlapping, jumbled text in the converted PDF. When building fixtures, scale by
  `dpi/72`; read back with `djvused -e 'select 1; print-txt'`.
- **The carried text is the scan's own OCR.** It is usually better than re-OCRing, but
  superscripts and math still degrade (`x^2` → `x'2`). Spot-check with `pdftotext`
  before treating the text layer as authoritative for citation extraction.
- **OCR language data must be installed.** `tesseract --list-langs` decides what `-l`
  can use; this host ships only `eng` + `osd`. `sudo apt-get install tesseract-ocr-<lang>`
  (e.g. `-grc`, `-deu`) before using `-l eng+grc`, otherwise OCR yields little or no text
  and the run exits 5. Tesseract's `osd` data is what `--deskew` needs.
- **`--mode raster` output is 5–6× larger and loses text/TOC.** It reports
  `image-only by design` and exits 0 — that is not a failure, but do not ship it as a
  library copy when the source had a text layer.
- **A degraded result exits 5, not 0.** If you batch-convert and only read the log tail,
  a fallback-to-raster (image-only) conversion can pass unnoticed.

## Verification

- Built-in, per file: page count vs source, text-layer presence when one was
  requested, and TOC entry count in the output (via `qpdf --json --json-key=outlines`)
  against the source's `print-outline`. Exit 5 = any of those failed or the engine fell
  back to raster.
- Full regression suite (hermetic, ~40s, no network; builds its own fixtures and
  exercises all engines plus the failure paths):

  ```bash
  bash ~/.hermes/profiles/librarian/skills/productivity/djvu-to-pdf/scripts/test_djvu2pdf.sh
  ```

  Expect `22 passed, 0 failed`.
- Measured on real DjVu files (dpsprep's `lipsum_*.djvu` fixtures, word-level text
  layers at 600 dpi): conversion succeeds, page counts match, text recall ≈0.99
  against the source text layer (98.4% against the original LaTeX PDF's text).
- See `references/pipeline-internals.md` for the engine internals, the dpsprep
  deadlock traceback, and the fixture format details.
