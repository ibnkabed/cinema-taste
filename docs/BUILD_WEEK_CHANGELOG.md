# OpenAI Build Week change boundary

## Pre-existing work

Before the submission period, Cinema Taste already provided an Arabic local interface, CSV-backed liked/disliked/watchlist records, OMDb lookup, safe add/transfer operations, a static taste profile, watchlist scoring, and session notes.

Git commit `8aa5211` preserves that imported baseline without rewriting its history.

## Work added during the submission period

All commits after the baseline are Build Week work. The contest extension adds:

1. A separate contest copy with its own Git history, documentation, tests, and submission-safe surface.
2. A contest-safe discovery surface with torrent shortcuts and the VPN prompt removed.
3. A learned, explainable taste engine that derives genre/director signals and reference similarity from the actual records.
4. Confidence and uncertainty reporting; the product intentionally avoids a closed yes/no prediction.
5. Similar-liked and similar-disliked evidence for every analysis.
6. Arabic and English structured briefs designed for a GPT-5.6 discussion.
7. A local no-key judge demo, portable launchers, automated tests, and English documentation.
8. A dedicated **مدى القابلية** (Likelihood) page with a visible percentage, confidence, and reasons.
9. A direct handoff that sends already-fetched OMDb metadata from Add Work to Likelihood without a second lookup.

After the owner approved the concept, the same dedicated Likelihood workflow was also added deliberately to the private daily-use copy. The two folders remain independent, and no viewing-record CSV data was changed by this interface work.

## Evidence

- Dated Git commits after the baseline.
- Automated tests in `tests/`.
- The primary Codex `/feedback` Session ID will be recorded in the Devpost submission.
- The demo video will show the local analysis and the GPT-5.6 evidence brief.
