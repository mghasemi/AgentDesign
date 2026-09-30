#!/usr/bin/env bash
# Regression test for djvu2pdf. Builds fixtures from scratch, then exercises
# every engine and the failure/degradation paths. Exits non-zero on any mismatch.
#
#   bash test_djvu2pdf.sh [WORKDIR]      (default /tmp/djvu2pdf-test)
#
# Uses only the installed system tools; no network.

set -uo pipefail
WORK="${1:-/tmp/djvu2pdf-test}"
HERE="$(cd "$(dirname "$0")" && pwd)"
CONV="${DJVU2PDF:-$HERE/djvu2pdf.sh}"
PASS=0; FAIL=0

say()  { printf '\n=== %s\n' "$*"; }
ok()   { PASS=$((PASS+1)); printf '  PASS: %s\n' "$*"; }
bad()  { FAIL=$((FAIL+1)); printf '  FAIL: %s\n' "$*"; }
check(){ [ "$2" = "$3" ] && ok "$1 ($2)" || bad "$1: got '$2' want '$3'"; }

rm -rf "$WORK"; mkdir -p "$WORK"; cd "$WORK"

for t in djvused djvutxt djvm cjb2 ddjvu gs pdfinfo pdftotext; do
  command -v "$t" >/dev/null || { echo "missing tool: $t"; exit 3; }
done
[ -x "$CONV" ] || { echo "djvu2pdf not executable: $CONV"; exit 3; }

say "build fixture (3 pages, line-level text layer, 3 bookmarks)"
bash "$HERE/make_djvu_fixture.sh" "$WORK" >/dev/null || exit 4
cp fixture_raw.djvu fixture_notext.djvu

say "A: text engine — hidden text layer + TOC carried across"
"$CONV" -m text -f -o A fixture.djvu >A.log 2>&1; check "exit" "$?" "0"
grep -q 'text layer present' A.log && ok "log reports text layer" || bad "text layer not reported"
grep -q 'TOC: 3 bookmark' A.log && ok "TOC entries carried" || bad "TOC not carried"
[ "$(pdfinfo A/fixture.pdf | sed -n 's/^Pages: *//p')" = 3 ] && ok "3 pages" || bad "page count"
pdftotext A/fixture.pdf - | grep -q 'ALPHA PAGE ONE' && ok "page 1 text" || bad "page 1 text missing"
pdftotext A/fixture.pdf - | grep -q 'CHARLIE PAGE THREE' && ok "page 3 text" || bad "page 3 text missing"

say "B: ocr engine — no text layer in source, OCR produces one"
"$CONV" -m ocr -f -o B -l eng fixture_notext.djvu >B.log 2>&1; check "exit" "$?" "0"
grep -q 'text layer present' B.log && ok "OCR text layer present" || bad "no OCR text layer"
pdftotext B/fixture_notext.pdf - | grep -qi 'ALPHA' && ok "OCR read page 1" || bad "OCR text empty"

say "C: raster engine — image-only by design, not a failure"
"$CONV" -m raster -f -o C fixture.djvu >C.log 2>&1; check "exit" "$?" "0"
grep -q 'image-only by design' C.log && ok "lossy outcome stated" || bad "lossy outcome not stated"

say "D: auto engine — picks text, then ocr"
"$CONV" -f -o D fixture.djvu fixture_notext.djvu >D.log 2>&1; check "exit" "$?" "0"
check "text picked for page-layer file" "$(grep -c 'engine=text' D.log)" "1"
check "ocr picked for bare file"       "$(grep -c 'engine=ocr' D.log)"  "1"

say "E: idempotency — existing PDF skipped, exit 0"
"$CONV" -m text -o A fixture.djvu >E.log 2>&1; check "exit" "$?" "0"
grep -q 'exists, skipping' E.log && ok "skip reported" || bad "did not skip"

say "F: degraded path — broken engine falls back to raster and reports failure"
DPSPREP=/bin/false "$CONV" -m text -f -o F fixture.djvu >F.log 2>&1; check "exit" "$?" "5"
grep -q 'DEGRADED' F.log && ok "degradation flagged" || bad "degradation not flagged"
[ -s F/fixture.pdf ] && ok "fallback produced a PDF" || bad "no fallback PDF"

say "G: dry run writes nothing"
"$CONV" -n -o G fixture.djvu >G.log 2>&1; check "exit" "$?" "0"
[ ! -e G/fixture.pdf ] && ok "nothing written" || bad "dry run wrote a file"

say "H: missing input is exit 3"
"$CONV" -f -o H nope.djvu >H.log 2>&1; check "exit" "$?" "3"

printf '\n================ %s passed, %s failed ================\n' "$PASS" "$FAIL"
[ "$FAIL" = 0 ]
