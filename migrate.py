"""Migrates the legacy Java code to Python with Claude Haiku, then repairs mismatches.

Usage:
    python migrate.py              generate billing.py, then repair mismatches (up to 3 iterations)
    python migrate.py --fix-only   skip generation, repair the existing billing.py

The key is read only from the ANTHROPIC_API_KEY environment variable.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent
JAVA_DIR = ROOT / "legacy-java" / "src" / "billing"
OUT_FILE = ROOT / "billing.py"
DIFF_FILE = ROOT / "cases" / "diff.txt"
COMPARE = ROOT / "compare.py"
MODEL = "claude-haiku-5-5"
MAX_FIX_ITERATIONS = 3

SYSTEM = """You are a senior engineer migrating legacy Java 8 code to Python 3.12.
Your output must behave IDENTICALLY to the Java original, byte for byte on stdout.
Rules:
- Use decimal.Decimal for all money (never float). Mirror BigDecimal semantics:
  scale-2 rounding with ROUND_HALF_UP at every step where the Java code rounds,
  and plain (non-scientific) string output like toPlainString().
- Keep the same input/output text formats and the same error messages.
- Expose exactly one public entry point: def run(input_text: str) -> str
  which takes the whole stdin text and returns the whole stdout text
  (one line per invoice, joined with "\\n", with a trailing "\\n" if non-empty).
- Use only the standard library. No third-party imports.
- Reply with ONLY the complete contents of billing.py in a single ```python code block.
  No explanations."""


def read_java_sources() -> str:
    parts = []
    for path in sorted(JAVA_DIR.glob("*.java")):
        parts.append(f"// ===== {path.name} =====\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def extract_code(text: str) -> str:
    match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    return (match.group(1) if match else text).strip() + "\n"


def ask_model(client: anthropic.Anthropic, user_prompt: str) -> str | None:
    """One model request. Returns the billing.py code, or None if the reply is unusable."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "disabled"},  # extended thinking used up the whole token budget in the first run
        system=SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )
    # The reply may contain non-text blocks: keep only the text ones.
    answer = "".join(b.text for b in response.content if b.type == "text")
    u = response.usage
    print(f"  tokens: input {u.input_tokens}, output {u.output_tokens}")
    if response.stop_reason == "max_tokens" or not answer.strip():
        print(f"  reply truncated or empty (stop_reason={response.stop_reason}), file left unchanged.")
        return None
    return extract_code(answer)


def run_compare() -> tuple[bool, str]:
    """Runs compare.py as a separate process (so a broken billing.py cannot crash the loop)."""
    proc = subprocess.run(
        [sys.executable, str(COMPARE)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},  # the child would otherwise write in the console codepage
    )
    first_line = proc.stdout.strip().splitlines()[0] if proc.stdout.strip() else "(empty output)"
    print(f"  compare: {first_line}")
    if proc.returncode == 0:
        return True, ""
    details = DIFF_FILE.read_text(encoding="utf-8") if DIFF_FILE.exists() else ""
    if proc.returncode == 2 or not details.strip():  # billing.py crashed outright
        details = proc.stdout + proc.stderr
    return False, details


def generate(client: anthropic.Anthropic, java_code: str) -> bool:
    print(f"Generating: {len(java_code)} characters of Java -> {MODEL}")
    code = ask_model(client, "Migrate this Java code:\n\n" + java_code)
    if code is None:
        return False
    OUT_FILE.write_text(code, encoding="utf-8")
    print(f"  saved {OUT_FILE.name} ({len(code.splitlines())} lines)")
    return True


def fix_loop(client: anthropic.Anthropic, java_code: str) -> bool:
    for attempt in range(1, MAX_FIX_ITERATIONS + 1):
        print(f"Check before iteration {attempt}:")
        ok, details = run_compare()
        if ok:
            return True
        print(f"Repair, iteration {attempt} of {MAX_FIX_ITERATIONS}:")
        prompt = (
            "Original Java code:\n\n" + java_code
            + "\n\nCurrent billing.py:\n```python\n" + OUT_FILE.read_text(encoding="utf-8") + "```\n\n"
            + "Running it against the reference outputs of the Java program gave these mismatches "
            + "(INPUT block, EXPECTED line from Java, ACTUAL line from Python), or a crash:\n\n"
            + details[:12000]
            + "\n\nFix billing.py so that it matches the Java behaviour exactly. "
            + "Return the complete corrected file."
        )
        code = ask_model(client, prompt)
        if code is None:
            return False
        OUT_FILE.write_text(code, encoding="utf-8")
    print("Final check:")
    ok, _ = run_compare()
    return ok


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set (open a new terminal after setting it).")
        return 1

    client = anthropic.Anthropic()
    java_code = read_java_sources()

    if "--fix-only" not in sys.argv:
        if not generate(client, java_code):
            return 1

    ok = fix_loop(client, java_code)
    print("RESULT: all invoices match." if ok else "RESULT: mismatches remain, see cases/diff.txt.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
