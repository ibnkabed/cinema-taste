# Judge guide

## Fastest evaluation path (no external key)

1. Install Python 3.10 or newer.
2. On Windows, run `تشغيل الذائقة السينمائية.cmd`. On macOS/Linux, run `sh run.sh`.
3. Open `http://127.0.0.1:8765/` if it does not open automatically.
4. Select **مدى القابلية** — this means **Likelihood**.
5. Select **تجربة فورية بلا مفتاح** — this means **Instant no-key demo**.
6. Review the initial reading, confidence, reasons, closest liked works, and caution references.
7. Expand **English judge summary**.
8. Select **Copy English brief** to inspect the structured GPT-5.6 discussion context.

This path is local and does not call OMDb or OpenAI.

## Full search path (optional)

1. Add an OMDb key on the **إضافة عمل** (Add Work) page, or set `OMDB_API_KEY`.
2. Search on the dedicated **Likelihood** page, or fetch a title on **Add Work**.
3. If using Add Work, select **قياس مدى القابلية** (Measure Likelihood) after OMDb fills the title details.
4. The app sends the fetched metadata to Likelihood, then compares it locally with the liked and disliked records.

## What to evaluate

- The product uses real personal-history evidence instead of a generic popularity score.
- Every reading exposes comparable liked and disliked references.
- Confidence changes with evidence quantity.
- The output is a conversation starting point, not an opaque deterministic recommendation.
- The user's lists remain local; external metadata lookup is optional.
