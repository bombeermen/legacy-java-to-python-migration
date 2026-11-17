# Legacy Java → Python migration with an LLM, proven by tests

## In plain words

The hard part of migrating an old system is not rewriting it in another language. It is making sure
the business logic did not change on the way. Old systems carry years of rules (discounts, rounding,
exceptions) that nobody fully remembers, and one wrong rounding rule means wrong invoices sent to customers.

So this project does not ask you to trust that the rewrite "looks right". It records how the old Java
program behaves, has an AI model write the Python version, and then **automatically proves the two
give the same answers**, down to the cent and the wording of every error message. If they differ,
the differences are sent back to the model to fix. You can re-run that proof yourself in two minutes.

**What "192 of 192" means:** on 192 test invoices, including deliberately invalid ones, the new Python
code and the original Java program produced identical results. It does not mean the work is done for
your system. It shows the method works and how I would apply it to your code.

A small legacy Java 8 billing application (invoice totals with discounts, shipping, tax and late fees)
migrated to Python by Claude Haiku, then wrapped in a FastAPI service.
The migration is not "looks right" — it is **verified against the original program's output**.

## Result

| Check | Result |
|---|---|
| Java reference vs. generated Python, 192 invoices (incl. error cases) | **192 / 192 identical** |
| Self-repair loop | Deliberately broke one business rule (late-fee period rounding): 187 / 192 → model fixed it in 1 iteration → 192 / 192 |

## Verify in 2 minutes (no API key, no packages)

Needs only Python 3.9+. This re-checks the already generated `billing.py` against the stored Java output:

```bash
git clone https://github.com/bombeermen/legacy-java-to-python-migration.git
cd legacy-java-to-python-migration
python compare.py
```

Expected output: `Matches: 192 of 192` and `Everything matches.`

## Transparency: test data, not production

- The Java application and all 192 invoices are **synthetic test data I created** for this demonstration,
  not a real client system. The business rules are plausible legacy quirks, not anyone's real logic.
- The generated `billing.py` is evidence that the method works, not a tool you can point at arbitrary code.
  The scripts are tailored to this example's invoice format.
- A run on **real code** needs a sample from you: the module to migrate, a way to run the original
  (or its recorded outputs) and representative input data. From those I build the reference outputs,
  migrate, compare and repair, exactly as above. Results on real data may differ from this example,
  and the comparison report would show exactly where.

## How it works

1. `legacy-java/` — the original Java 8 app (`BigDecimal` money, HALF_UP rounding, historical quirks).
2. `tools/gen_cases.py` — generates 192 invoices: hand-picked edge cases plus seeded random ones.
   `cases/golden.txt` is the output of the **real Java program** on `cases/cases.txt`.
3. `migrate.py` — sends the Java sources to `claude-haiku-5-5`, saves the result as `billing.py`.
4. `compare.py` — runs every invoice through `billing.run()`, compares line by line with the golden file,
   prints the score and each mismatch together with its input (also saved to `cases/diff.txt`).
5. Repair loop (in `migrate.py`) — on mismatches, sends the Java code, the current Python and the diffs
   back to the model; up to 3 iterations.
6. `app.py` — FastAPI wrapper, `POST /invoice`.

Key migration rules given to the model: `decimal.Decimal` only (never `float`), half-up rounding at
every step the Java code rounds, identical error messages, standard library only.

## Run it

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Migrate + auto-repair (needs a key in the ANTHROPIC_API_KEY environment variable)
.venv\Scripts\python.exe migrate.py
# Re-check only, no API call
.venv\Scripts\python.exe compare.py
# Repair an existing billing.py without regenerating
.venv\Scripts\python.exe migrate.py --fix-only

# API
.venv\Scripts\python.exe -m uvicorn app:app
```

Interactive docs: http://127.0.0.1:8000/docs

### Example

```http
POST /invoice
{"id": "E001", "customer_type": "RETAIL", "region": "EU", "days_late": 0,
 "items": [{"sku": "A", "qty": 1, "unit_price": "12.34"}]}
```

```json
{"id": "E001", "subtotal": "12.34", "discount": "0.00", "shipping": "15.00",
 "tax": "5.74", "late_fee": "0.00", "total": "33.08"}
```

Business errors (unknown region or customer type, non-positive quantity) return HTTP 422 with the same
message the Java program printed, e.g. `Unknown region: XX`.

## Notes

- Money is returned as strings to avoid any float precision loss.
- The API key is read only from the environment and is never written to files.
- Model output is non-deterministic: a fresh `migrate.py` run may produce different code, which is why
  the comparison harness and repair loop exist.
