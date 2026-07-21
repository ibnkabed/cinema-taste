# Cinema Taste — الذائقة السينمائية

Cinema Taste is a local-first app that turns a real viewing history into an explainable taste profile. It helps viewers organize what they liked, disliked, and plan to watch, then decide whether a new movie or series is worth trying using evidence from their own history rather than popularity alone — and it shows exactly which signals produced every estimate.

The complete interface now switches between Arabic and English from the header. Every section, dynamic status, watchlist explanation, Likelihood result, and session summary follows the selected language with automatic RTL/LTR direction.

## Live judge demo

Open the public, installation-free demo: [cinema-taste.abdullashammary.chatgpt.site](https://cinema-taste.abdullashammary.chatgpt.site/?lang=en)

The live demo opens in English, includes the full bilingual interface, and provides two instant no-key judge paths: **Add Title** populates complete sample metadata for *A Time to Kill*, while **Likelihood** analyses *The Lincoln Lawyer* with a transparent signal breakdown. Both demos run without exposing or modifying the owner's private local CSV records.

## Why it matters

Streaming catalogs are large, generic recommendation feeds optimize for engagement, and a title's global rating rarely explains whether one specific person will enjoy it. Cinema Taste keeps the viewer's records local and shows the evidence behind every reading — including an honest "split taste" verdict when the viewer's own history is divided, rather than a falsely confident number.

## Core experience

- Maintain liked, disliked, and watchlist records in portable CSV files.
- Search OMDb and review metadata — genres, director, cast, writers, language, and plot — before adding a title.
- Move an existing title safely between lists without duplicates.
- Explore genre, director, cast, writer, rating, and high-rated-reference patterns.
- Read a watchlist ranked by the **same** engine as the Likelihood page, so the two views never disagree and scores refresh automatically.
- Open the dedicated **مدى القابلية** (Likelihood) page to see a percentage, confidence, reasons, and comparable liked/disliked titles.
- Expand **“على ماذا استندت النسبة؟” / “What is this score based on?”** to see each signal with its value, weight, and contribution — with any unavailable evidence clearly marked as excluded.
- Send OMDb metadata directly from **إضافة عمل** (Add Title) to the Likelihood page without searching twice, and add a title to the watchlist in one click from a Likelihood result.
- Copy an Arabic or English evidence brief for a nuanced GPT-5.6 discussion.
- Run a no-key public or local demo so judges can test the core analysis immediately.
- Switch the complete product between `العربية | English`; `?lang=en` opens the English experience directly.

## How the Likelihood engine works

The engine compares a title's genres, directors, cast, writers, runtime, and release year against the viewer's liked and disliked history, using rating-weighted affinities and a nearest-neighbour reference match (closest liked and disliked titles, plus a single best-match "anchor"). Evidence is weighted by how strongly the viewer rated it, the two libraries are balanced so a shared genre reads as neutral rather than negative, and a conflict index lowers confidence and reports "split taste" when the history is divided. Cast, writers, language, and plot are retrieved from OMDb to enrich the profile; the score is a bounded, explainable estimate — never a flat 0 or 100, and never a deterministic yes/no.

## Quick start

Requirements: Python 3.10 or newer. The application uses only the Python standard library and needs no package installation.

Windows:

```text
Double-click: تشغيل الذائقة السينمائية.cmd
```

macOS or Linux:

```bash
sh run.sh
```

Then open [http://127.0.0.1:18765/?lang=en](http://127.0.0.1:18765/?lang=en) for English, or use the language control in the header. The contest copy uses its own port so it can run alongside the original private app on port `8765` without a conflict.

To test without an OMDb key, open **إضافة عمل** (Add Title) and select **تجربة إضافة بلا مفتاح** (Instant no-key Add Title demo), or open **مدى القابلية** (Likelihood) and select **تجربة فورية بلا مفتاح** (Instant no-key demo).

## Optional OMDb setup

OMDb is used only to search public movie metadata (genres, director, cast, writers, language, and plot). Add a key from the **إضافة عمل** (Add Title) page or set `OMDB_API_KEY` in the environment. A free key takes about a minute to obtain at [omdbapi.com](https://www.omdbapi.com/apikey.aspx). The key is stored outside this repository in the user's local application settings.

## Tests

```bash
python -m unittest discover -s tests -v
python -m py_compile tools/cinema_server.py tools/taste_engine.py
node --check assets/cinema.js
```

The Python test suite covers scoring behavior, uncertainty, GPT-5.6 brief generation, live local API responses, HTML identifiers, and the removal of unsafe download links.

## Privacy model

- Taste CSV files stay on the local machine.
- The no-key demo makes no external request.
- OMDb receives only normal metadata lookup parameters when the user searches.
- No OpenAI API key is required by the application.
- A user explicitly chooses what evidence brief to copy into Codex or ChatGPT.

## Build Week scope

The public repository preserves the imported pre-hackathon baseline at commit [`8aa5211`](https://github.com/ibnkabed/cinema-taste/commit/8aa5211b64fa74b3ea92dde87ca6965111b77b01) on the public `agent/add-bilingual-interface` branch. The default `main` branch contains the later submission history, so the baseline commit and [dated change boundary](docs/BUILD_WEEK_CHANGELOG.md) are the clearest old-versus-new evidence. The new Build Week work includes:

- an isolated contest copy with its own Git history and submission-safe files;
- removal of torrent/download shortcuts and the VPN prompt;
- an explainable taste-analysis engine, recalibrated against the viewer's own library with leave-one-out testing;
- a transparent **“What is this score based on?”** signal breakdown under every result, in Arabic and English;
- a conflict index that reports honest uncertainty ("split taste") instead of false confidence;
- OMDb enrichment — cast, writers, language, and plot — feeding a seven-dimension similarity model;
- similar-liked and similar-disliked evidence, with confidence and uncertainty reporting instead of a deterministic verdict;
- a dedicated Likelihood page, a direct Add Title → Likelihood metadata handoff, a watchlist ranked by the same engine, and one-click add-to-watchlist from a result;
- Arabic and English GPT-5.6 discussion briefs;
- a complete Arabic–English interface switch with dynamic content and RTL/LTR direction;
- a no-key judge demo, portable launchers, automated tests, and English documentation.

See [docs/BUILD_WEEK_CHANGELOG.md](docs/BUILD_WEEK_CHANGELOG.md) for the old-versus-new boundary and [docs/JUDGE_GUIDE.md](docs/JUDGE_GUIDE.md) for a short evaluation path.

## Key decisions and Codex collaboration

- The owner chose to keep the original daily-use project protected and build the submission in a separate contest copy.
- The product decision was to show an explainable percentage, confidence, positive evidence, caution evidence, and a per-signal breakdown rather than produce an opaque recommendation.
- Score and confidence remain separate, and conflicting evidence lowers confidence, so a plausible match is not presented with more certainty than the viewing history supports.
- The public judge path needs no key and runs on ephemeral sample data; OMDb search remains optional, and the owner's private CSV records stay local.
- Codex with GPT-5.6 accelerated the repository isolation, engine implementation and leave-one-out recalibration, the transparency breakdown and conflict index, OMDb enrichment, the bilingual interface, automated tests, and real browser verification. The owner retained the key product, privacy, and submission-scope decisions above.

## Project structure

```text
assets/                 Interface styles and behavior
data/                   Generated local profile, session data, and OMDb enrichment cache
tests/                  Standard-library unit and API tests
tools/cinema_server.py  Local HTTP server, OMDb bridge, CSV safety
tools/taste_engine.py   Explainable taste-analysis engine
*.csv                   Portable viewing records
```

## License

This project is licensed under the [MIT License](LICENSE).
