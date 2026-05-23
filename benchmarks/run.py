"""Benchmark PDF input backends on speed and extraction accuracy (B2).

For each test PDF that has a golden JSON, runs ``extract_data()`` with each
registered backend and scores how many golden fields it reproduces (this
reflects real template compatibility, since the templates are tuned for
``pdftotext -layout``); it also times raw text extraction.

Run with the package installed (the relevant ``--extra`` backends synced):

    python benchmarks/run.py
"""

import datetime
import json
import logging
import statistics
import time
from pathlib import Path

from invoice2data.__main__ import extract_data
from invoice2data.extract.loader import read_templates
from invoice2data.input import INPUT_MODULES
from invoice2data.input import is_available


ROOT = Path(__file__).resolve().parent.parent
COMPARE = ROOT / "tests" / "compare"
CUSTOM_TEMPLATES = ROOT / "tests" / "custom" / "templates"
BACKENDS = ["pdftotext", "pdfium", "pdfoxide", "pdfminer", "pdfplumber", "hotpdf"]
RUNS = 3


def _norm(value: object, date_format: str = "%Y-%m-%d") -> object:
    if isinstance(value, datetime.date):
        return value.strftime(date_format)
    return value


def _score(result: dict, golden: dict) -> tuple[int, int]:
    matched = total = 0
    for key, gold in golden.items():
        total += 1
        got = result.get(key)
        if isinstance(gold, list):
            if isinstance(got, list) and len(got) == len(gold):
                matched += 1
        elif _norm(got) == _norm(gold):
            matched += 1
    return matched, total


def main() -> None:
    logging.disable(logging.CRITICAL)  # silence per-extraction warnings/errors
    templates = read_templates(str(CUSTOM_TEMPLATES)) + read_templates()
    cases = [
        (pdf, COMPARE / f"{pdf.stem}.json")
        for pdf in sorted(COMPARE.glob("*.pdf"))
        if (COMPARE / f"{pdf.stem}.json").exists()
    ]
    print(f"Backends on {len(cases)} PDF/golden pairs ({RUNS} timing runs)\n")
    print(f"{'backend':11s} {'accuracy':>9s} {'matched':>10s} {'speed':>13s}")
    for backend in BACKENDS:
        module = INPUT_MODULES.get(backend)
        if module is None or not is_available(module):
            print(f"{backend:11s} {'UNAVAILABLE':>9s}")
            continue
        matched = total = 0
        for pdf, golden_path in cases:
            with open(golden_path, encoding="utf-8") as handle:
                golden = json.load(handle)[0]
            try:
                result = extract_data(str(pdf), templates, backend)
            except Exception:
                result = {}
            if not isinstance(result, dict):
                result = {}
            got, want = _score(result, golden)
            matched += got
            total += want
        times = []
        for _ in range(RUNS):
            start = time.perf_counter()
            for pdf, _golden_path in cases:
                try:
                    module.to_text(str(pdf))
                except Exception:  # noqa: S110
                    pass
            times.append(time.perf_counter() - start)
        accuracy = 100 * matched / total if total else 0.0
        speed = statistics.median(times) / len(cases) * 1000
        print(
            f"{backend:11s} {accuracy:8.1f}% {matched:5d}/{total:<5d} {speed:8.1f} ms/file"
        )


if __name__ == "__main__":
    main()
