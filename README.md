# Cinema Taste — الذائقة السينمائية

Cinema Taste is a local-first app that turns a real viewing history into an explainable taste profile. It helps viewers organize what they liked, disliked, and plan to watch, then discuss a new movie or series using evidence from their own history rather than popularity alone.

The complete interface now switches between Arabic and English from the header. Every section, dynamic status, watchlist explanation, Likelihood result, and session summary follows the selected language with automatic RTL/LTR direction.

## Live judge demo

Open the public, installation-free demo: [cinema-taste.abdullashammary.chatgpt.site](https://cinema-taste.abdullashammary.chatgpt.site/)

The live demo opens in English, includes the full bilingual interface, and supports the instant no-key Likelihood analysis. It is read-only so the public experience cannot modify the private local CSV records.

## Why it matters

Streaming catalogs are large, generic recommendation feeds optimize for engagement, and a title's global rating rarely explains whether one specific person will enjoy it. Cinema Taste keeps the viewer's records local and shows the evidence behind every reading.

## Core experience

- Maintain liked, disliked, and watchlist records in portable CSV files.
- Search OMDb and review metadata before adding a title.
- Move an existing title safely between lists without duplicates.
- Explore genre, director, rating, and high-rated-reference patterns.
- Read an explainable watchlist ranking.
- Open the dedicated **مدى القابلية** (Likelihood) page to see a percentage, confidence, reasons, and comparable liked/disliked works.
- Send OMDb metadata directly from **إضافة عمل** (Add Work) to the Likelihood page without searching twice.
- Copy an Arabic or English evidence brief for a nuanced GPT-5.6 discussion.
- Run a no-key public or local demo so judges can test the core analysis immediately.
- Switch the complete product between `العربية | English`; `?lang=en` opens the English experience directly.

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

To test without an OMDb key, open **مدى القابلية** (Likelihood) and select **تجربة فورية بلا مفتاح** (Instant no-key demo).

## Optional OMDb setup

OMDb is used only to search public movie metadata. Add a key from the **إضافة عمل** (Add Work) page or set `OMDB_API_KEY` in the environment. The key is stored outside this repository in the user's local application settings.

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

The public repository preserves the imported pre-hackathon baseline at commit [`8aa5211`](https://github.com/ibnkabed/cinema-taste/commit/8aa5211b64fa74b3ea92dde87ca6965111b77b01) on the public `agent/add-bilingual-interface` branch. The default `main` branch contains the later squash-merged submission history, so the baseline commit and [dated change boundary](docs/BUILD_WEEK_CHANGELOG.md) are the clearest old-versus-new evidence. The new Build Week work includes:

- an isolated contest copy with its own Git history and submission-safe files;
- removal of torrent/download shortcuts and the VPN prompt;
- an explainable taste-analysis engine derived from the viewer's actual records;
- similar-liked and similar-disliked evidence;
- uncertainty and confidence reporting instead of a deterministic verdict;
- a dedicated Likelihood page plus a direct Add Work → Likelihood metadata handoff;
- Arabic and English GPT-5.6 discussion briefs;
- a complete Arabic–English interface switch with dynamic content and RTL/LTR direction;
- a no-key judge demo, portable launchers, automated tests, and English documentation.

See [docs/BUILD_WEEK_CHANGELOG.md](docs/BUILD_WEEK_CHANGELOG.md) for the old-versus-new boundary and [docs/JUDGE_GUIDE.md](docs/JUDGE_GUIDE.md) for a short evaluation path.

## Key decisions and Codex collaboration

- The owner chose to keep the original daily-use project protected and build the submission in a separate contest copy.
- The product decision was to show an explainable percentage, confidence, positive evidence, and caution evidence rather than produce an opaque recommendation.
- Score and confidence remain separate so a plausible match is not presented with more certainty than the available viewing history supports.
- The public judge path is read-only and needs no key; OMDb search remains optional, and private CSV records stay local.
- Codex with GPT-5.6 accelerated the repository isolation, engine and API implementation, bilingual interface, automated tests, and real browser verification. The owner retained the key product, privacy, and submission-scope decisions above.

## Project structure

```text
assets/                 Interface styles and behavior
data/                   Generated local profile and session data
tests/                  Standard-library unit and API tests
tools/cinema_server.py  Local HTTP server, OMDb bridge, CSV safety
tools/taste_engine.py   Explainable taste-analysis engine
*.csv                   Portable viewing records
```

## License

This project is licensed under the [MIT License](LICENSE).
