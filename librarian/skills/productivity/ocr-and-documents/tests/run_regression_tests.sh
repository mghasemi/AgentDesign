#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

"${PYTHON_BIN}" "${SCRIPT_DIR}/../pdf_extract_tool.py" --help >/dev/null
"${PYTHON_BIN}" "${SCRIPT_DIR}/test_pdf_extract_tool.py"
