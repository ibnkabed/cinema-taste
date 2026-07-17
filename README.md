# Cinema Taste — الذائقة السينمائية

Cinema Taste is a local-first app that turns a real viewing history into an explainable taste profile. It helps viewers organize what they liked, disliked, and plan to watch, then discuss a new movie or series using evidence from their own history rather than popularity alone.

The Arabic interface is the product's primary experience. This README and the judge guide provide the complete English testing path required for OpenAI Build Week.

## Why it matters

Streaming catalogs are large, generic recommendation feeds optimize for engagement, and a title's global rating rarely explains whether one specific person will enjoy it. Cinema Taste keeps the viewer's records local and shows the evidence behind every reading.

## Core experience

- Maintain liked, disliked, and watchlist records in portable CSV files.
- Search OMDb and review metadata before adding a title.
- Move an existing title safely between lists without duplicates.
- Explore genre, director, rating, and high-rated-reference patterns.
- Read an explainable watchlist ranking.
- Analyze a new title against similar liked and disliked works.
- Copy an Arabic or English evidence brief for a nuanced GPT-5.6 discussion.
- Run a no-key local demo so judges can test the core analysis immediately.

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

Then open [http://127.0.0.1:8765/](http://127.0.0.1:8765/).

To test without an OMDb key, open **البحث عن أعمال جديدة** (Find New Works) and select **تجربة فورية بلا مفتاح** (Instant no-key demo).

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

The repository begins with a commit containing the pre-hackathon project baseline. Every contest change follows it in normal Git history. The new Build Week work includes:

- an isolated contest copy that never modifies the daily-use project;
- removal of torrent/download shortcuts and the VPN prompt;
- an explainable taste-analysis engine derived from the viewer's actual records;
- similar-liked and similar-disliked evidence;
- uncertainty and confidence reporting instead of a deterministic verdict;
- Arabic and English GPT-5.6 discussion briefs;
- a no-key judge demo, portable launchers, automated tests, and English documentation.

See [docs/BUILD_WEEK_CHANGELOG.md](docs/BUILD_WEEK_CHANGELOG.md) for the old-versus-new boundary and [docs/JUDGE_GUIDE.md](docs/JUDGE_GUIDE.md) for a short evaluation path.

## Project structure

```text
assets/                 Interface styles and behavior
data/                   Generated local profile and session data
tests/                  Standard-library unit and API tests
tools/cinema_server.py  Local HTTP server, OMDb bridge, CSV safety
tools/taste_engine.py   Explainable taste-analysis engine
*.csv                   Portable viewing records
```

