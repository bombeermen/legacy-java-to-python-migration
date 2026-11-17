"""Крок 4: прогоняє cases/cases.txt через billing.run() і звіряє з cases/golden.txt.

Запуск (з будь-якої теки):
    & "E:\\My\\Claude Projects\\UpWork\\ex02\\.venv\\Scripts\\python.exe" "E:\\My\\Claude Projects\\UpWork\\ex02\\compare.py"

Друкує частку збігів і розбіжності з вхідними даними рахунку.
Розбіжності також пишуться в cases/diff.txt (для кроку 5).
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
    """Ділить вхід на блоки INVOICE ... END (як їх читає Java Main)."""
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
    except Exception as exc:  # згенерований код може впасти цілком
        print(f"billing.run() впав: {type(exc).__name__}: {exc}")
        return 2

    total = len(expected)
    report = []
    ok = 0
    for i in range(total):
        exp = expected[i]
        act = actual[i] if i < len(actual) else "<немає рядка>"
        if exp == act:
            ok += 1
        else:
            inp = blocks[i] if i < len(blocks) else "<немає блоку>"
            report.append(f"#{i + 1}\nВХІД:\n{inp}\nОЧІКУВАЛОСЬ: {exp}\nОТРИМАНО:    {act}\n")

    if len(actual) != total:
        report.append(f"Кількість рядків: очікувалось {total}, отримано {len(actual)}\n")

    print(f"Збігів: {ok} з {total}")
    if report:
        text = "\n".join(report)
        DIFF_OUT.write_text(text, encoding="utf-8")
        print(f"Розбіжностей: {total - ok}. Повний список у {DIFF_OUT}\n")
        print(text[:4000])
    else:
        DIFF_OUT.write_text("", encoding="utf-8")
        print("Усе збігається.")
    return 0 if ok == total and len(actual) == total else 1


if __name__ == "__main__":
    sys.exit(main())
