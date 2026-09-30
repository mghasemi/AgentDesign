#!/bin/bash
# LaTeX build verification script — 3-pass clean build + audit
# Usage: bash latex-verify.sh /path/to/paper.tex
set -euo pipefail

TEX="${1:?Usage: $0 /path/to/paper.tex}"
DIR=$(dirname "$TEX")
BASE=$(basename "$TEX" .tex)
cd "$DIR"

# Clean
rm -f "${BASE}.aux" "${BASE}.bbl" "${BASE}.blg" "${BASE}.out" "${BASE}.log"

# 3-pass build
pdflatex -interaction=nonstopmode "${BASE}.tex" > /dev/null 2>&1
bibtex "${BASE}" > /dev/null 2>&1
pdflatex -interaction=nonstopmode "${BASE}.tex" > /dev/null 2>&1
pdflatex -interaction=nonstopmode "${BASE}.tex" > /dev/null 2>&1

# Audit
PAGES=$(pdfinfo "${BASE}.pdf" 2>/dev/null | grep Pages | awk '{print $2}')
UR=$(grep -c 'Reference.*undefined' "${BASE}.log" 2>/dev/null || echo 0)
UC=$(grep -c 'Citation.*undefined' "${BASE}.log" 2>/dev/null || echo 0)
BW=$(grep -c 'Warning' "${BASE}.blg" 2>/dev/null || echo 0)
LE=$(grep -c '^!' "${BASE}.log" 2>/dev/null || echo 0)

echo "Pages=$PAGES UndefRefs=$UR UndefCites=$UC BibWarns=$BW LatexErrs=$LE"

if [ "$UR" != "0" ] || [ "$UC" != "0" ] || [ "$BW" != "0" ] || [ "$LE" != "0" ]; then
    echo "VERDICT: FAIL"
    exit 1
fi

if [ -z "$PAGES" ] || [ "$PAGES" = "0" ]; then
    echo "VERDICT: FAIL (no pages)"
    exit 1
fi

echo "VERDICT: PASS"
