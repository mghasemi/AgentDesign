#!/usr/bin/env python3
"""Lightweight, reliable PDF text extraction with deterministic fallbacks."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import string
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


DEFAULT_TIMEOUT = float(os.environ.get("PDF_EXTRACT_TIMEOUT", "45"))
DEFAULT_MIN_CHARS_PER_PAGE = float(os.environ.get("PDF_EXTRACT_MIN_CHARS_PER_PAGE", "40"))
DEFAULT_MAX_EMPTY_PAGE_RATIO = float(os.environ.get("PDF_EXTRACT_MAX_EMPTY_PAGE_RATIO", "0.6"))
DEFAULT_MAX_CONTROL_CHAR_RATIO = float(os.environ.get("PDF_EXTRACT_MAX_CONTROL_CHAR_RATIO", "0.15"))


@dataclass
class ExtractionResult:
    method: str
    text: str
    page_count: int
    warnings: list[str]


class ExtractionError(Exception):
    pass


def _fail(message: str, fmt: str = "text") -> None:
    if fmt == "json":
        print(json.dumps({"success": False, "error": message}, ensure_ascii=False, indent=2))
    else:
        print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t\f\v]+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _safe_page_count(candidate: int | None) -> int:
    if candidate is None or candidate <= 0:
        return 1
    return candidate


def _extract_pdftotext(pdf_path: Path, timeout: float) -> ExtractionResult:
    if not shutil.which("pdftotext"):
        raise ExtractionError("pdftotext not available")

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    warnings: list[str] = []
    try:
        proc = subprocess.run(
            ["pdftotext", str(pdf_path), str(tmp_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            raise ExtractionError(f"pdftotext failed with code {proc.returncode}: {stderr}")

        text = tmp_path.read_text(encoding="utf-8", errors="replace")
        page_markers = text.count("\x0c")
        text = text.replace("\x0c", "\n")
        return ExtractionResult(
            method="pdftotext",
            text=_normalize_text(text),
            page_count=_safe_page_count(page_markers),
            warnings=warnings,
        )
    except subprocess.TimeoutExpired as exc:
        raise ExtractionError(f"pdftotext timeout after {timeout}s") from exc
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _extract_pypdf(pdf_path: Path, timeout: float) -> ExtractionResult:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise ExtractionError("pypdf is not installed") from exc

    warnings: list[str] = []

    try:
        reader = PdfReader(str(pdf_path), strict=False)
    except Exception as exc:
        raise ExtractionError(f"pypdf could not open PDF: {exc}") from exc

    page_texts: list[str] = []
    for page in reader.pages:
        try:
            extracted = page.extract_text() or ""
        except Exception as exc:
            warnings.append(f"pypdf page extraction warning: {exc}")
            extracted = ""
        page_texts.append(extracted)

    if not page_texts:
        raise ExtractionError("pypdf found zero pages")

    text = _normalize_text("\n\n".join(page_texts))
    if not text:
        warnings.append("pypdf returned empty text")

    return ExtractionResult(
        method="pypdf",
        text=text,
        page_count=_safe_page_count(len(page_texts)),
        warnings=warnings,
    )


def _ocr_available() -> tuple[bool, str]:
    """Return (available, reason) indicating whether OCR prerequisites exist."""
    if not shutil.which("tesseract"):
        return False, "tesseract not found; install tesseract-ocr"
    if not shutil.which("pdftoppm"):
        return False, "pdftoppm not found; install poppler-utils"
    return True, ""


def _extract_ocr(pdf_path: Path, timeout: float) -> ExtractionResult:
    """OCR-based extractor using pdftoppm + tesseract (phase-2, opt-in only)."""
    available, reason = _ocr_available()
    if not available:
        raise ExtractionError(f"OCR unavailable: {reason}")

    warnings: list[str] = []
    page_texts: list[str] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        prefix = str(Path(tmpdir) / "page")
        proc = subprocess.run(
            ["pdftoppm", "-r", "300", str(pdf_path), prefix],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            raise ExtractionError(f"pdftoppm failed: {proc.stderr.strip()}")

        images = sorted(
            list(Path(tmpdir).glob("page-*.ppm")) + list(Path(tmpdir).glob("page-*.pgm"))
        )
        if not images:
            raise ExtractionError("pdftoppm produced no image output")

        for img in images:
            p = subprocess.run(
                ["tesseract", str(img), "stdout", "-l", "eng", "--psm", "1"],
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if p.returncode == 0:
                page_texts.append(p.stdout)
            else:
                warnings.append(f"tesseract failed on {img.name}: {p.stderr.strip()}")

        page_count = len(images)

    text = _normalize_text("\n\n".join(page_texts))
    if not text:
        warnings.append("OCR returned empty text")

    return ExtractionResult(
        method="ocr",
        text=text,
        page_count=_safe_page_count(page_count),
        warnings=warnings,
    )


def _empty_page_ratio(text: str, page_count: int) -> float:
    if page_count <= 0:
        return 1.0
    # Estimate empties by splitting paragraphs into page buckets when page markers are unavailable.
    paragraphs = [p for p in re.split(r"\n\n+", text) if p.strip()]
    if not paragraphs:
        return 1.0
    approx_non_empty_pages = min(page_count, len(paragraphs))
    empty_pages = max(0, page_count - approx_non_empty_pages)
    return empty_pages / page_count


def _control_char_ratio(text: str) -> float:
    if not text:
        return 1.0
    allowed = set(string.printable) | {"\n", "\t", "\r"}
    bad = sum(1 for c in text if c not in allowed)
    return bad / max(1, len(text))


def _quality_report(
    text: str,
    page_count: int,
    min_chars_per_page: float,
    max_empty_page_ratio: float,
    max_control_char_ratio: float,
) -> tuple[dict[str, float], list[str]]:
    chars = len(text)
    page_count = _safe_page_count(page_count)
    chars_per_page = chars / page_count
    empty_ratio = _empty_page_ratio(text, page_count)
    control_ratio = _control_char_ratio(text)

    warnings: list[str] = []
    if chars == 0:
        warnings.append("extracted text is empty")
    if chars_per_page < min_chars_per_page:
        warnings.append(
            f"low chars_per_page ({chars_per_page:.2f} < {min_chars_per_page:.2f}); PDF may be scanned or complex layout"
        )
    if empty_ratio > max_empty_page_ratio:
        warnings.append(
            f"high empty_page_ratio ({empty_ratio:.2f} > {max_empty_page_ratio:.2f})"
        )
    if control_ratio > max_control_char_ratio:
        warnings.append(
            f"high control_char_ratio ({control_ratio:.3f} > {max_control_char_ratio:.3f})"
        )

    metrics = {
        "chars": chars,
        "page_count": page_count,
        "chars_per_page": chars_per_page,
        "empty_page_ratio": empty_ratio,
        "control_char_ratio": control_ratio,
    }
    return metrics, warnings


def _extract_with_cascade(
    pdf_path: Path,
    timeout: float,
    min_chars_per_page: float,
    max_empty_page_ratio: float,
    max_control_char_ratio: float,
    enable_ocr: bool = False,
) -> dict[str, object]:
    attempts: list[dict[str, str]] = []
    candidates: list[dict[str, object]] = []

    extractors = [
        ("pdftotext", _extract_pdftotext),
        ("pypdf", _extract_pypdf),
    ]

    for name, extractor in extractors:
        try:
            result = extractor(pdf_path, timeout)
            metrics, quality_warnings = _quality_report(
                result.text,
                result.page_count,
                min_chars_per_page,
                max_empty_page_ratio,
                max_control_char_ratio,
            )
            all_warnings = list(result.warnings) + quality_warnings
            candidate = {
                "method": name,
                "text": result.text,
                "warnings": all_warnings,
                "is_weak": len(quality_warnings) > 0,
                **metrics,
            }
            candidates.append(candidate)
            attempts.append({"method": name, "status": "ok"})

            if not candidate["is_weak"]:
                break
        except Exception as exc:  # noqa: BLE001 - we want rich fallback behavior
            attempts.append({"method": name, "status": f"failed: {exc}"})

    # Pick best candidate so far by highest usable text volume and lower noise.
    def _score(item: dict[str, object]) -> float:
        return float(item["chars"]) - (1000.0 * float(item["control_char_ratio"]))

    # OCR phase-2: only when explicitly enabled and current best is still weak (or all failed).
    if enable_ocr:
        best_is_weak = (not candidates) or bool(max(candidates, key=_score).get("is_weak"))
        if best_is_weak:
            ocr_ok, ocr_reason = _ocr_available()
            if ocr_ok:
                try:
                    ocr_result = _extract_ocr(pdf_path, timeout)
                    metrics, quality_warnings = _quality_report(
                        ocr_result.text,
                        ocr_result.page_count,
                        min_chars_per_page,
                        max_empty_page_ratio,
                        max_control_char_ratio,
                    )
                    all_warnings = list(ocr_result.warnings) + quality_warnings
                    candidates.append({
                        "method": "ocr",
                        "text": ocr_result.text,
                        "warnings": all_warnings,
                        "is_weak": len(quality_warnings) > 0,
                        **metrics,
                    })
                    attempts.append({"method": "ocr", "status": "ok"})
                except Exception as exc:  # noqa: BLE001
                    attempts.append({"method": "ocr", "status": f"failed: {exc}"})
            else:
                attempts.append({"method": "ocr", "status": f"skipped: {ocr_reason}"})

    if not candidates:
        raise ExtractionError("all extractors failed: " + " | ".join(a["status"] for a in attempts))

    best = max(candidates, key=_score)
    best["fallback_used"] = best["method"] != candidates[0]["method"] if len(candidates) > 1 else False
    best["attempts"] = attempts
    return best


def _render_text_output(text: str, warnings: list[str]) -> None:
    if warnings:
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
    print(text)


def cmd_extract_pdf(args: argparse.Namespace) -> dict[str, object]:
    pdf_path = Path(args.file)
    if not pdf_path.is_file():
        raise ExtractionError(f"PDF not found: {pdf_path}")

    result = _extract_with_cascade(
        pdf_path=pdf_path,
        timeout=args.timeout,
        min_chars_per_page=args.min_chars_per_page,
        max_empty_page_ratio=args.max_empty_page_ratio,
        max_control_char_ratio=args.max_control_char_ratio,
        enable_ocr=getattr(args, "ocr", False),
    )

    payload: dict[str, object] = {
        "success": True,
        "file": str(pdf_path),
        "method": result["method"],
        "fallback_used": result["fallback_used"],
        "chars": result["chars"],
        "page_count": result["page_count"],
        "chars_per_page": result["chars_per_page"],
        "empty_page_ratio": result["empty_page_ratio"],
        "control_char_ratio": result["control_char_ratio"],
        "is_weak": result["is_weak"],
        "warnings": result["warnings"],
        "attempts": result["attempts"],
    }

    if args.include_text:
        payload["text"] = result["text"]

    return payload


def cmd_inspect_pdf(args: argparse.Namespace) -> dict[str, object]:
    args.include_text = False
    return cmd_extract_pdf(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reliable lightweight PDF text extraction")

    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--format", choices=["text", "json"], default="text")
    common.add_argument("file", help="Path to local PDF file")
    common.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    common.add_argument("--min-chars-per-page", type=float, default=DEFAULT_MIN_CHARS_PER_PAGE)
    common.add_argument("--max-empty-page-ratio", type=float, default=DEFAULT_MAX_EMPTY_PAGE_RATIO)
    common.add_argument("--max-control-char-ratio", type=float, default=DEFAULT_MAX_CONTROL_CHAR_RATIO)

    p_extract = sub.add_parser(
        "extract-pdf",
        parents=[common],
        help="Extract text from PDF using deterministic fallbacks",
    )
    p_extract.add_argument("--include-text", action="store_true", default=True)
    p_extract.add_argument("--no-include-text", action="store_false", dest="include_text")
    p_extract.add_argument(
        "--ocr",
        action="store_true",
        default=False,
        help="Enable OCR fallback when extraction is weak (requires tesseract + pdftoppm)",
    )

    sub.add_parser(
        "inspect-pdf",
        parents=[common],
        help="Run extraction and return quality diagnostics without full text",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "extract-pdf": cmd_extract_pdf,
        "inspect-pdf": cmd_inspect_pdf,
    }

    try:
        data = dispatch[args.command](args)
    except ExtractionError as exc:
        _fail(str(exc), args.format)
        return
    except Exception as exc:  # noqa: BLE001
        _fail(f"unexpected error: {exc}", args.format)
        return

    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    warnings = [str(w) for w in data.get("warnings", [])]
    text = str(data.get("text", ""))
    _render_text_output(text, warnings)


if __name__ == "__main__":
    main()
