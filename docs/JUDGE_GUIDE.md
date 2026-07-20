# Judge guide

## Fastest evaluation path (no external key)

1. Open the public demo: `https://cinema-taste.onrender.com/?lang=en`. It is hosted on a free tier, so the first load after idle may take up to a minute.
2. Select **Likelihood**.
3. Select **Instant no-key demo**.
4. Review the initial reading, confidence, reasons, closest liked titles, and caution references.
5. Review the English explanation and expand **English judge summary** if desired.
6. Select **Copy English brief** to inspect the structured GPT-5.6 discussion context.

This public path requires no installation and does not call OMDb or OpenAI. It runs on ephemeral sample data, so the owner's private CSV records are never exposed or modified.

## Full local edition

For OMDb search and local CSV updates, install Python 3.10 or newer, run `تشغيل الذائقة السينمائية.cmd` on Windows or `sh run.sh` on macOS/Linux, then open `http://127.0.0.1:18765/?lang=en`.

## Full search path (optional)

1. Add an OMDb key on the **Add Title** page, or set `OMDB_API_KEY`.
2. Search on the dedicated **Likelihood** page, or fetch a title on **Add Title**.
3. If using Add Title, select **Measure Likelihood** after OMDb fills the title details.
4. The app sends the fetched metadata to Likelihood, then compares it locally with the liked and disliked records.

## What to evaluate

- The product uses real personal-history evidence instead of a generic popularity score.
- Every reading exposes comparable liked and disliked references.
- Confidence changes with evidence quantity.
- The output is a conversation starting point, not an opaque deterministic recommendation.
- The user's lists remain local; external metadata lookup is optional.
- The complete interface can be evaluated in English while the original Arabic experience remains available.
