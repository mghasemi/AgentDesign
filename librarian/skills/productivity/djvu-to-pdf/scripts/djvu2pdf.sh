#!/usr/bin/env bash
# djvu2pdf — DjVu → PDF conversion preserving text layer + bookmarks (TOC).
#
# Engines
#   text   : dpsprep — transfers the DjVu hidden text layer and the outline into
#            the PDF. No OCR cost, keeps the scan's own (usually better) OCR.
#            Default when a hidden text layer is detected.
#   ocr    : ddjvu raster -> ocrmypdf (tesseract). Default when there is NO text
#            layer. Deliberately NOT dpsprep --socr, which deadlocks here.
#   raster : ddjvu -format=pdf — fast flattened image PDF, no text layer.
#
# Usage: djvu2pdf [options] FILE.djvu [FILE2.djvu ...]
#
#   -m, --mode auto|text|ocr|raster  engine (default auto: text if a text layer
#                                    exists, else ocr)
#   -l, --lang LANGS                 OCR languages, e.g. eng or eng+grc (eng)
#   -q, --quality N                  JPEG quality 1..100 for RGB/gray (85)
#   -j, --jobs N                     worker processes (default: nproc)
#   -O, --opt 0|1|2|3                OCRmyPDF PDF optimizer level (0)
#   -M, --dps-mode SPEC              forward --mode to dpsprep, e.g.
#                                    'bitonal[2-end]' to keep a color cover small
#       --deskew                     deskew pages during OCR
#   -t, --timeout SEC                per-file engine timeout (1800)
#   -o, --out DIR                    output directory (default: beside source)
#   -f, --force                      overwrite existing PDFs
#   -n, --dry-run                    probe only, write nothing
#   -v, --verbose                    show engine commands
#
# Exit codes: 0 ok · 2 usage · 3 source missing · 4 conversion failed · 5 verification/degraded

set -uo pipefail

DPSPREP="${DPSPREP:-$(command -v dpsprep || echo /home/YOUR-USER/.local/bin/dpsprep)}"
MODE=auto; LANG=eng; QUALITY=85; JOBS=""; OPT=0; OUTDIR=""; FORCE=0; DRY=0; VERBOSE=0
TIMEOUT="${DJVU2PDF_TIMEOUT:-1800}"   # per-file engine timeout, seconds
DESKEW=0; DPS_MODE=""
MIN_TEXT_CHARS=25                      # below this a text layer counts as absent

die() { printf 'djvu2pdf: %s\n' "$*" >&2; exit "${2:-4}"; }
usage() { awk 'NR>1 && /^#/ { sub(/^# ?/, ""); print; next } NR>1 { exit }' "$0"; exit 0; }
log() { [ "$VERBOSE" = 1 ] && printf '   %s\n' "$*" >&2; return 0; }

while [ $# -gt 0 ]; do
  case "$1" in
    -m|--mode)     MODE="${2:-}"; shift 2 ;;
    -l|--lang)     LANG="${2:-}"; shift 2 ;;
    -q|--quality)  QUALITY="${2:-}"; shift 2 ;;
    -j|--jobs)     JOBS="${2:-}"; shift 2 ;;
    -O|--opt)      OPT="${2:-}"; shift 2 ;;
    -o|--out)      OUTDIR="${2:-}"; shift 2 ;;
    -t|--timeout)  TIMEOUT="${2:-}"; shift 2 ;;
    -f|--force)    FORCE=1; shift ;;
    -n|--dry-run)  DRY=1; shift ;;
    -v|--verbose)  VERBOSE=1; shift ;;
    --deskew)      DESKEW=1; shift ;;
    -M|--dps-mode) DPS_MODE="${2:-}"; shift 2 ;;
    -h|--help)     usage ;;
    -*)            die "unknown option: $1" 2 ;;
    *)             SRC+=("$1"); shift ;;
  esac
done

[ "${#SRC[@]}" -gt 0 ] || { printf 'djvu2pdf: no input files\n' >&2; usage; }
case "$MODE" in auto|text|ocr|raster) ;; *) die "bad --mode '$MODE'" 2 ;; esac
case "$OPT"  in 0|1|2|3) ;; *) die "bad --opt '$OPT' (0|1|2|3)" 2 ;; esac

for t in djvused djvutxt ddjvu pdfinfo pdftotext; do
  command -v "$t" >/dev/null || die "missing system tool: $t (apt install djvulibre-bin poppler-utils)"
done
[ -n "$JOBS" ] || JOBS="$(nproc 2>/dev/null || echo 2)"

# ---------- probe -------------------------------------------------------------
# Sets PAGES TEXTCHARS OUTLINES DPI PAGEBOX
probe() {
  local f="$1"
  PAGES="$(djvused "$f" -e 'n' 2>/dev/null | tr -dc '0-9')"; [ -n "$PAGES" ] || PAGES=0
  TEXTCHARS="$(djvutxt "$f" 2>/dev/null | tr -d '[:space:]' | wc -c)"
  OUTLINES="$(djvused "$f" -e 'print-outline' 2>/dev/null | grep -c '"#' || true)"
  DPI="$(djvudump "$f" 2>/dev/null | sed -n 's/.*[^0-9]\([0-9][0-9]*\) *dpi.*/\1/p' | head -1)"
  [ -n "${DPI:-}" ] || DPI="?"
  PAGEBOX="$(djvused "$f" -e 'select 1; size' 2>/dev/null | tr '\n' ' ' | sed 's/ *$//')"
}
has_text() { [ "$TEXTCHARS" -ge "$MIN_TEXT_CHARS" ]; }

# ---------- verify ------------------------------------------------------------
# 1 = ok, 5 = problem. Compares the PDF against the source DjVu.
verify() {
  local src="$1" pdf="$2" want_text="$3" expect_lossy="${4:-0}" rc=0 got chars toc_out=0
  got="$(pdfinfo "$pdf" 2>/dev/null | sed -n 's/^Pages: *//p')"
  if [ "$got" != "$PAGES" ]; then
    printf '   !! page count %s != source %s\n' "${got:-?}" "$PAGES" >&2; rc=5
  fi
  if [ "$expect_lossy" = 1 ]; then
    printf '   image-only by design: text layer%s intentionally not carried\n' \
      "$([ "${OUTLINES:-0}" -gt 0 ] && echo ' and TOC' || echo '')"
    return $rc
  fi
  if [ "$want_text" = 1 ]; then
    chars="$(pdftotext "$pdf" - 2>/dev/null | tr -d '[:space:]' | wc -c)"
    if [ "$chars" -lt "$MIN_TEXT_CHARS" ]; then
      printf '   !! text layer requested but PDF yields only %s chars\n' "$chars" >&2; rc=5
    else
      log "text layer: $chars chars (source $TEXTCHARS)"
    fi
  fi
  if [ "${OUTLINES:-0}" -gt 0 ]; then
    if command -v qpdf >/dev/null; then
      toc_out="$(qpdf --json --json-key=outlines "$pdf" 2>/dev/null \
        | python3 -c 'import json,sys
try: o=json.load(sys.stdin).get("outlines") or []
except Exception: o=[]
def n(x): return 1+sum(n(c.get("kids") or []) for c in (x.get("kids") or []))
print(sum(n(c) for c in o))' 2>/dev/null || echo 0)"
    fi
    if [ "${toc_out:-0}" -ge 1 ]; then
      printf '   TOC: %s bookmark entry(ies) carried into the PDF\n' "$toc_out"
    else
      printf '   !! source has %s bookmark entry(ies); none found in the PDF\n' "$OUTLINES" >&2
      rc=5
    fi
  fi
  return $rc
}

# ---------- convert -----------------------------------------------------------
convert_one() {
  local src="$1"
  [ -f "$src" ] || die "no such file: $src" 3
  local base out mode want_text=0 tmp
  base="$(basename "$src")"; base="${base%.*}"
  if [ -n "$OUTDIR" ]; then mkdir -p "$OUTDIR"; out="$OUTDIR/$base.pdf"; else out="$(dirname "$src")/$base.pdf"; fi

  probe "$src"
  [ "$PAGES" -gt 0 ] || die "not a readable DjVu: $src"
  mode="$MODE"
  [ "$mode" = auto ] && { if has_text; then mode=text; else mode=ocr; fi; }

  printf '== %s\n   pages=%s dpi=%s page_px=%s text_chars=%s outline_entries=%s\n' \
    "$src" "$PAGES" "$DPI" "${PAGEBOX:-?}" "$TEXTCHARS" "${OUTLINES:-0}"
  printf '   engine=%s -> %s\n' "$mode" "$out"

  if [ "$DRY" = 1 ]; then log '[dry-run] nothing written'; return 0; fi
  if [ -e "$out" ] && [ "$FORCE" != 1 ]; then
    printf '   exists, skipping (use -f to overwrite)\n'; return 0
  fi

  tmp="$(mktemp -d /tmp/djvu2pdf.XXXXXX)" || die "cannot create temp dir"
  local rc_engine=0 degraded=0 t0 t1
  t0=$(date +%s)

  case "$mode" in
    text)
      want_text=1
      local -a cmd=("$DPSPREP" -p "$JOBS" -q "$QUALITY" -f)
      [ "$OPT" != 0 ] && cmd+=("-O$OPT")
      [ -n "$DPS_MODE" ] && cmd+=("--mode" "$DPS_MODE")
      cmd+=("$src" "$out")
      log "cmd: ${cmd[*]}"
      timeout "$TIMEOUT" "${cmd[@]}" >"$tmp/log" 2>&1 || rc_engine=$?
      ;;
    ocr)
      want_text=1
      # Rasterize first, then OCR the raster PDF. Robust, resumable, and immune
      # to the dpsprep --socr worker deadlock.
      ddjvu -format=pdf -quality="$QUALITY" "$src" "$tmp/raster.pdf" >"$tmp/log" 2>&1 || rc_engine=$?
      if [ "$rc_engine" = 0 ] && command -v ocrmypdf >/dev/null; then
        local -a ocmd=(ocrmypdf -l "$LANG" --optimize "$OPT" --output-type pdf)
        [ "$DESKEW" = 1 ] && ocmd+=(--deskew)
        ocmd+=("$tmp/raster.pdf" "$out")
        log "cmd: ${ocmd[*]}"
        timeout "$TIMEOUT" "${ocmd[@]}" >>"$tmp/log" 2>&1 || rc_engine=$?
      elif [ "$rc_engine" = 0 ]; then
        printf '   !! ocrmypdf not installed; cannot OCR\n' >&2; rc_engine=4
      fi
      ;;
    raster)
      ddjvu -format=pdf -quality="$QUALITY" "$src" "$out" >"$tmp/log" 2>&1 || rc_engine=$?
      ;;
  esac

  if [ "$rc_engine" != 0 ]; then
    printf '   !! %s engine failed (rc=%s)\n' "$mode" "$rc_engine" >&2
    tail -3 "$tmp/log" >&2
    if [ "$mode" != raster ]; then
      printf '   falling back to ddjvu raster (image-only)\n' >&2
      degraded=1; want_text=0
      ddjvu -format=pdf -quality="$QUALITY" "$src" "$out" >>"$tmp/log" 2>&1 \
        || { cat "$tmp/log" >&2; rm -rf "$tmp"; die "conversion failed: $src"; }
    else
      cat "$tmp/log" >&2; rm -rf "$tmp"; die "conversion failed: $src"
    fi
  fi
  rm -rf "$tmp"
  t1=$(date +%s)

  [ -s "$out" ] || die "no output produced: $out"
  printf '   wrote %s (%s bytes, %ss)\n' "$out" "$(stat -c%s "$out")" "$((t1-t0))"
  if [ "$degraded" = 1 ]; then
    printf '   DEGRADED: output is image-only (no text layer)\n' >&2
    verify "$src" "$out" 0 1; return 5
  fi
  if verify "$src" "$out" "$want_text" "$([ "$mode" = raster ] && echo 1 || echo 0)"; then
    printf '   verified: pages OK, %s\n' "$([ "$want_text" = 1 ] && echo 'text layer present' || echo 'image-only')"
    return 0
  fi
  return 5
}

rc_all=0
for f in "${SRC[@]}"; do convert_one "$f" || rc_all=$?; done
exit $rc_all
