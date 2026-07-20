# OpenAI Build Week change boundary

## Pre-existing work

Before the submission period, Cinema Taste already provided an Arabic local interface, CSV-backed liked/disliked/watchlist records, OMDb lookup, safe add/transfer operations, a static taste profile, watchlist scoring, and session notes.

Git commit [`8aa5211`](https://github.com/ibnkabed/cinema-taste/commit/8aa5211b64fa74b3ea92dde87ca6965111b77b01) preserves that imported baseline without rewriting its history. It remains publicly reachable on the `agent/add-bilingual-interface` branch; the default `main` branch contains the later squash-merged submission history.

## Work added during the submission period

The dated commits following the baseline on that public branch, together with the squash-merged submission commits on `main`, document the Build Week work. The contest extension adds:

1. A separate contest copy with its own Git history, documentation, tests, and submission-safe surface.
2. A contest-safe discovery surface with torrent shortcuts and the VPN prompt removed.
3. A learned, explainable taste engine that derives genre/director signals and reference similarity from the actual records.
4. Confidence and uncertainty reporting; the product intentionally avoids a closed yes/no prediction.
5. Similar-liked and similar-disliked evidence for every analysis.
6. Arabic and English structured briefs designed for a GPT-5.6 discussion.
7. A local no-key judge demo, portable launchers, automated tests, and English documentation.
8. A dedicated **مدى القابلية** (Likelihood) page with a visible percentage, confidence, and reasons.
9. A direct handoff that sends already-fetched OMDb metadata from Add Title to Likelihood without a second lookup.
10. A complete `العربية | English` interface switch across every page, dynamic status, watchlist explanation, Likelihood analysis, and judge-safe session summary, with automatic RTL/LTR direction.

After the owner approved the concept, the same dedicated Likelihood workflow was also added deliberately to the private daily-use copy. The two folders remain independent, and no viewing-record CSV data was changed by this interface work.

## Evidence

- Dated Git commits after the baseline.
- Automated tests in `tests/`.
- The primary Codex `/feedback` Session ID is recorded in the Devpost submission.
- The public demo video shows the local analysis and explains the Codex and GPT-5.6 contribution.
