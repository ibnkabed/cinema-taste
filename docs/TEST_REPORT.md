# Verification report — 18 July 2026

## Automated checks

- `python -m unittest discover -s tests -v`: 10 tests passed.
- `python -m py_compile tools/cinema_server.py tools/taste_engine.py`: passed.
- `node --check assets/cinema.js`: passed.
- `git diff --check`: passed before the feature commit.

The test suite covers the taste engine, uncertainty behavior, GPT-5.6 brief content, live local API responses, direct supplied-OMDb metadata analysis, unique HTML identifiers, the dedicated Likelihood view, the requested Arabic section name, and the absence of the removed download/VPN elements.

## Visual and interaction checks

Browser viewport: 1280 × 720 at 100% zoom.

- Home page: full content fits the viewport; document height equals viewport height (720 px).
- Dedicated Likelihood page before analysis: full layout visible with no vertical document scroll.
- Instant no-key demo: returned a real local analysis with score, confidence, reasons, four liked references, and four caution references.
- Analysis result: document height remained 720 px; the analysis panel did not require internal scrolling; both GPT-5.6 brief buttons were fully visible.
- English judge summary content was present.
- Copy English brief action displayed its success confirmation.
- Browser console: no errors or warnings.
- Standalone discovery page: title and heading are `البحث عن أعمال جديدة`; only IMDb, Rotten Tomatoes, and JustWatch remain; no vertical scroll.
- The seven-item navigation was compacted without reducing the approved 14 px link size; the full update timestamp remains visible at 1280 px.

## Safety boundary

The contest and private daily-use folders remain independent. At the owner's explicit request, the dedicated Likelihood experience was added to both; the contest-only safety cleanup and submission materials remain confined to the Build Week folder. Visual testing used temporary local ports and did not change the viewing-record CSV files.
