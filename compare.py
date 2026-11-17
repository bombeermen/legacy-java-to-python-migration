"""Runs cases/cases.txt through billing.run() and compares the result with cases/golden.txt.

Usage:
    python compare.py

Prints the match count and every mismatch together with the invoice input.
Mismatches are also written to cases/diff.txt (used by the repair loop in migrate.py).
"""
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

CASES = ROOT / "cases" / "cases.txt"
GOLDEN = ROOT / "cases" / "golden.txt"
DIFF_OUT = ROOT / "cases" / "diff.txt"


def split_invoices(text: str) -> list[str]:
    """Splits the input into INVOICE ... END blocks (the way the Java Main reads them)."""
    blocks, current = [], []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        current.append(line)
        if line == "END":
            blocks.append("\n".join(current))
            current = []
    return blocks


def main() -> int:
    cases_text = CASES.read_text(encoding="utf-8")
    expected = GOLDEN.read_text(encoding="utf-8").splitlines()
    blocks = split_invoices(cases_text)

    try:
        billing = importlib.import_module("billing")
        actual = billing.run(cases_text).splitlines()
    except Exception as exc:  # generated code may crash outright
        print(f"billing.run() crashed: {type(exc).__name__}: {exc}")
        return 2

    total = len(expected)
    report = []
    ok = 0
    for i in range(total):
        exp = expected[i]
        act = actual[i] if i < len(actual) else "<missing line>"
        if exp == act:
            ok += 1
        else:
            inp = blocks[i] if i < len(blocks) else "<missing block>"
            report.append(f"#{i + 1}\nINPUT:\n{inp}\nEXPECTED (Java): {exp}\nACTUAL (Python): {act}\n")

    if len(actual) != total:
        report.append(f"Line count: expected {total}, got {len(actual)}\n")

    print(f"Matches: {ok} of {total}")
    if report:
        text = "\n".join(report)
        DIFF_OUT.write_text(text, encoding="utf-8")
        print(f"Mismatches: {total - ok}. Full list in {DIFF_OUT}\n")
        print(text[:4000])
    else:
        DIFF_OUT.write_text("", encoding="utf-8")
        print("Everything matches.")
    return 0 if ok == total and len(actual) == total else 1


if __name__ == "__main__":
    sys.exit(main())
