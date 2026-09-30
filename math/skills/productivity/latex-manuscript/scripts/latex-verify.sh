#!/bin/bash
# latex-verify.sh — 3-pass clean build + audit for LaTeX manuscripts
# Usage: bash latex-verify.sh path/to/paper
#   or:  bash latex-verify.sh paper  (assumes paper.tex in cwd)
set -euo pipefail

BASE="${1%.tex}"
DIR=$(dirname "$BASE.tex")
NAME=$(basename "$BASE")
cd "$DIR"

# Clean
rm -f "$NAME.aux" "$NAME.bbl" "$NAME.blg" "$NAME.out" "$NAME.log"

# 3-pass build
pdflatex -interaction=nonstopmode "$NAME" >/dev/null 2>&1 || true
bibtex "$NAME" >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode "$NAME" >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode "$NAME" >/dev/null 2>&1 || true

# Audit — grep -c exits 1 on 0 matches, so capture separately from exit code
set +e
P=$(pdfinfo "$NAME.pdf" 2>/dev/null | awk '/Pages/{print $2}')
E=$(grep -c '^!' "$NAME.log" 2>/dev/null); E=${E:-0}
R=$(grep -c 'Reference.*undefined' "$NAME.log" 2>/dev/null); R=${R:-0}
C=$(grep -c 'Citation.*undefined' "$NAME.log" 2>/dev/null); C=${C:-0}
W=$(grep -c 'Warning' "$NAME.blg" 2>/dev/null); W=${W:-0}

printf "pages=%-3s errors=%-2s undef_ref=%-2s undef_cite=%-2s bib_warn=%-2s  " "$P" "$E" "$R" "$C" "$W"

if [ "$P" -gt 0 ] && [ "$E" = 0 ] && [ "$R" = 0 ] && [ "$C" = 0 ] && [ "$W" = 0 ]; then
    echo "PASS"
    exit 0
else
    echo "FAIL"
    exit 1
fi
