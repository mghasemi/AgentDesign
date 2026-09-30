#!/usr/bin/env python3
"""Regression tests for pdf_extract_tool.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfWriter


TOOL_PATH = Path(__file__).resolve().parents[1] / "pdf_extract_tool.py"


def _write_text_pdf(path: Path, text: str) -> None:
    # Minimal single-page PDF with an embedded text stream.
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET"
    stream_bytes = stream.encode("latin-1", errors="replace")

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        (
            b"5 0 obj << /Length "
            + str(len(stream_bytes)).encode("ascii")
            + b" >> stream\n"
            + stream_bytes
            + b"\nendstream endobj\n"
        ),
    ]

    pdf_header = b"%PDF-1.4\n"
    xref_positions: list[int] = []
    data = bytearray(pdf_header)

    for obj in objects:
        xref_positions.append(len(data))
        data.extend(obj)

    xref_start = len(data)
    data.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    data.extend(b"0000000000 65535 f \n")
    for pos in xref_positions:
        data.extend(f"{pos:010d} 00000 n \n".encode("ascii"))
    data.extend(
        b"trailer << /Size "
        + str(len(objects) + 1).encode("ascii")
        + b" /Root 1 0 R >>\nstartxref\n"
        + str(xref_start).encode("ascii")
        + b"\n%%EOF\n"
    )

    path.write_bytes(bytes(data))


def _write_blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with path.open("wb") as fp:
        writer.write(fp)


def _run_tool(args: list[str], env: dict[str, str] | None = None) -> dict[str, object]:
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)

    proc = subprocess.run(
        [sys.executable, str(TOOL_PATH), *args],
        check=False,
        capture_output=True,
        text=True,
        env=proc_env,
    )
    if proc.returncode != 0:
        raise AssertionError(f"Tool failed ({proc.returncode}): {proc.stderr or proc.stdout}")
    return json.loads(proc.stdout)


class TestPdfExtractTool(unittest.TestCase):
    def test_strong_text_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "strong.pdf"
            _write_text_pdf(pdf, "Reliable extraction text " * 40)

            data = _run_tool(["extract-pdf", str(pdf), "--format", "json"])

            self.assertTrue(bool(data["success"]))
            self.assertGreater(int(data["chars"]), 50)
            self.assertFalse(bool(data["is_weak"]))
            self.assertIn("text", data)

    def test_weak_blank_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "blank.pdf"
            _write_blank_pdf(pdf)

            data = _run_tool(["extract-pdf", str(pdf), "--format", "json"])

            self.assertTrue(bool(data["success"]))
            self.assertTrue(bool(data["is_weak"]))
            self.assertGreaterEqual(len(list(data.get("warnings", []))), 1)

    def test_inspect_excludes_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "inspect.pdf"
            _write_text_pdf(pdf, "Inspect mode text " * 40)

            data = _run_tool(["inspect-pdf", str(pdf), "--format", "json"])

            self.assertTrue(bool(data["success"]))
            self.assertNotIn("text", data)
            self.assertIn("chars", data)

    def test_threshold_override_marks_weak(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "threshold.pdf"
            _write_text_pdf(pdf, "Threshold control text " * 20)

            data = _run_tool(
                ["extract-pdf", str(pdf), "--format", "json"],
                env={"PDF_EXTRACT_MIN_CHARS_PER_PAGE": "5000"},
            )

            self.assertTrue(bool(data["success"]))
            self.assertTrue(bool(data["is_weak"]))
            warnings = list(data.get("warnings", []))
            self.assertTrue(any("chars_per_page" in str(w) for w in warnings))

    def test_golden_text_recovery(self) -> None:
        """Embedded sentinel text must appear verbatim in the extracted output."""
        sentinel = "GOLDEN_SENTINEL_99142"
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "golden.pdf"
            _write_text_pdf(pdf, f"{sentinel} golden output verification text " * 10)

            data = _run_tool(["extract-pdf", str(pdf), "--format", "json"])

            self.assertTrue(bool(data["success"]))
            self.assertIn(sentinel, str(data.get("text", "")))

    def test_fallback_without_pdftotext(self) -> None:
        """When PATH hides pdftotext, pypdf must be used and extraction must still succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "fallback.pdf"
            _write_text_pdf(pdf, "Fallback pypdf text " * 40)

            # Empty PATH means pdftotext lookup will fail; sys.executable is absolute so it runs.
            data = _run_tool(
                ["extract-pdf", str(pdf), "--format", "json"],
                env={"PATH": ""},
            )

            self.assertTrue(bool(data["success"]))
            self.assertEqual(data["method"], "pypdf")
            attempts = list(data.get("attempts", []))
            pdftotext_attempt = next((a for a in attempts if a["method"] == "pdftotext"), None)
            self.assertIsNotNone(pdftotext_attempt)
            self.assertIn("not available", str(pdftotext_attempt["status"]))

    def test_ocr_flag_skips_gracefully_when_unavailable(self) -> None:
        """--ocr with empty PATH skips OCR gracefully and still returns best-effort text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf = Path(tmpdir) / "ocr_skip.pdf"
            _write_blank_pdf(pdf)

            data = _run_tool(
                ["extract-pdf", str(pdf), "--ocr", "--format", "json"],
                env={"PATH": ""},
            )

            self.assertTrue(bool(data["success"]))
            attempts = list(data.get("attempts", []))
            ocr_attempt = next((a for a in attempts if a["method"] == "ocr"), None)
            self.assertIsNotNone(ocr_attempt)
            self.assertIn("skipped", str(ocr_attempt["status"]))


if __name__ == "__main__":
    unittest.main()
