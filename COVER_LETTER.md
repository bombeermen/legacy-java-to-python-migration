# Cover letter: Python Developer: Migrate Legacy Java/PHP Projects to Python and Integrate AI/LLMs

Hi,

Your post asks for legacy code rewritten in FastAPI with the business logic documented and the new version proven to match the old one. I built a small working example of exactly that, so you can check it instead of taking my word for it:

https://github.com/bombeermen/legacy-java-to-python-migration

What it does:
- Takes a legacy Java 8 billing app (discounts, shipping, tax, late fees, BigDecimal rounding quirks) and migrates it to Python with Claude.
- Compares the Python output with the real Java program's output on 192 invoices, including error cases. Result: 192 of 192 identical.
- Has a repair loop: when outputs differ, the diffs go back to the model. I broke one business rule on purpose (187 of 192 matched) and the loop fixed it in one iteration.
- Exposes the result as a FastAPI service (`POST /invoice`).

To be upfront: the Java app and all invoices are synthetic test data I made for this demo, and a run on your real code would need a sample of it from you. The example is also Java only. I have not yet done the same for PHP, but the approach (golden outputs from the original program, then automated comparison) does not depend on the language.

If useful, I can run the same process on one small module of your code as a paid or short test, so you see the result on your own logic before committing to anything.

Which part of the legacy system would you start with, and is it Java or PHP?

Best regards,
bombeermen
