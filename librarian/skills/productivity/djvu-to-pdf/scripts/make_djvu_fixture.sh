#!/usr/bin/env bash
# Build a small DjVu test fixture: 3 pages, hidden text layer, 3 bookmarks.
#   bash make_djvu_fixture.sh [OUTDIR]
# Produces $OUTDIR/fixture.djvu  (with text layer + outline)
#          $OUTDIR/fixture_raw.djvu (no text layer)
#
# Hidden-text box syntax is (line xmin ymin xmax ymax "text") with integer
# PIXEL coordinates and origin at the BOTTOM-LEFT (djvused(1)).

set -euo pipefail
OUT="${1:-/tmp/djvu2pdf-fixture}"
mkdir -p "$OUT"; cd "$OUT"

cat > make_fixture.ps <<'PS'
%!PS-Adobe-3.0
%%Pages: 3
/Helvetica-Bold findfont 28 scalefont setfont
72 720 moveto (ALPHA PAGE ONE) show
/Helvetica findfont 16 scalefont setfont
72 680 moveto (quadratic form x^2 + y^2 - 1) show
72 655 moveto (second line of page one text) show
showpage
/Helvetica-Bold findfont 28 scalefont setfont
72 720 moveto (BRAVO PAGE TWO) show
/Helvetica findfont 16 scalefont setfont
72 680 moveto (sum of squares decomposition) show
72 655 moveto (second line of page two text) show
showpage
/Helvetica-Bold findfont 28 scalefont setfont
72 720 moveto (CHARLIE PAGE THREE) show
/Helvetica findfont 16 scalefont setfont
72 680 moveto (semidefinite programming bound) show
72 655 moveto (second line of page three text) show
showpage
PS

rm -f page-*.pgm out-*.djvu fixture.djvu fixture_raw.djvu
gs -q -dNOPAUSE -dBATCH -sDEVICE=pgm -r300 -sOutputFile=page-%d.pgm make_fixture.ps
for i in 1 2 3; do cjb2 -dpi 300 "page-$i.pgm" "out-$i.djvu"; done
djvm -c fixture_raw.djvu out-1.djvu out-2.djvu out-3.djvu

gen_txt() {   # $1=file $2..$4=line texts
  python3 - "$@" <<'PY'
import sys
f, t1, t2, t3 = sys.argv[1:5]
K = 300/72.0                                  # A4 page = 2479x3508 px @300dpi
def box(x0pt, y0pt, x1pt, y1pt):
    return "%d %d %d %d" % (round(x0pt*K), round(y0pt*K), round(x1pt*K), round(y1pt*K))
lines = [(box(72,705,400,745), t1), (box(72,670,400,688), t2), (box(72,645,400,663), t3)]
open(f, "w").write("(page 0 0 2479 3508\n%s\n)\n"
                   % "\n".join('  (line %s "%s")' % (b, t) for b, t in lines))
PY
}

gen_txt t1.txt "ALPHA PAGE ONE"     "quadratic form x^2 + y^2 - 1"   "second line of page one text"
gen_txt t2.txt "BRAVO PAGE TWO"     "sum of squares decomposition"   "second line of page two text"
gen_txt t3.txt "CHARLIE PAGE THREE" "semidefinite programming bound" "second line of page three text"

cp fixture_raw.djvu fixture.djvu
for i in 1 2 3; do
  djvused -e "select $i
set-txt t$i.txt
save" fixture.djvu
done

cat > outline.txt <<'EOF'
(bookmarks
 ("Page One" "#1")
 ("Page Two" "#2")
 ("Page Three" "#3"))
EOF
djvused -e 'set-outline outline.txt
save' fixture.djvu

printf 'fixture: %s (with text layer + outline), %s (image only)\n' \
  "$OUT/fixture.djvu" "$OUT/fixture_raw.djvu"
