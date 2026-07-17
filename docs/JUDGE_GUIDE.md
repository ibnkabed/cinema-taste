# Judge guide

## Fastest evaluation path (no external key)

1. Install Python 3.10 or newer.
2. On Windows, run `تشغيل الذائقة السينمائية.cmd`. On macOS/Linux, run `sh run.sh`.
3. Open `http://127.0.0.1:8765/` if it does not open automatically.
4. Select **البحث عن أعمال جديدة** — this means **Find New Works**.
5. Select **تجربة فورية بلا مفتاح** — this means **Instant no-key demo**.
6. Review the initial reading, confidence, reasons, closest liked works, and caution references.
7. Expand **English judge summary**.
8. Select **Copy English brief** to inspect the structured GPT-5.6 discussion context.

This path is local and does not call OMDb or OpenAI.

## Full search path (optional)

1. Add an OMDb key on the **إضافة عمل** (Add Work) page, or set `OMDB_API_KEY`.
2. Return to **Find New Works**.
3. Search for a movie or series and select the correct result.
4. The app fetches public metadata, then performs the taste analysis locally.

## What to evaluate

- The product uses real personal-history evidence instead of a generic popularity score.
- Every reading exposes comparable liked and disliked references.
- Confidence changes with evidence quantity.
- The output is a conversation starting point, not an opaque deterministic recommendation.
- The user's lists remain local; external metadata lookup is optional.

