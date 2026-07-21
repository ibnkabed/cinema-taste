# -*- coding: utf-8 -*-
"""One-time library enrichment: fetch Actors/Writer/Language/Country for every
work in the three CSV libraries from OMDb and cache them locally.

The cache is incremental: already-fetched titles are skipped, so re-running
after adding new works only fetches the new ones. Run it from the project
folder (double-click "إثراء المكتبة.cmd").
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
CSV_FILES = [
    ROOT / "افلام ومسلسلات اعجبتني.csv",
    ROOT / "افلام ومسلسلات لم تعجبني.csv",
    ROOT / "My Watchlist.csv",
]
CACHE_PATH = ROOT / "data" / "library-enrichment.json"
OMDB_KEY_PATH = Path(os.environ.get("LOCALAPPDATA") or ROOT / "tools") / "CinemaTaste" / "omdb_api_key.txt"


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_key() -> str:
    key = clean(os.environ.get("OMDB_API_KEY"))
    if key:
        return key
    if OMDB_KEY_PATH.exists():
        return clean(OMDB_KEY_PATH.read_text(encoding="utf-8"))
    return ""


def collect_ids() -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for path in CSV_FILES:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                imdb_id = clean(row.get("Const") or row.get("imdbId"))
                if imdb_id and imdb_id not in seen:
                    seen.add(imdb_id)
                    ids.append(imdb_id)
    return ids


def fetch(imdb_id: str, key: str) -> dict[str, str] | None:
    url = "https://www.omdbapi.com/?" + urlencode({"apikey": key, "i": imdb_id, "plot": "full"})
    request = Request(url, headers={"User-Agent": "CinemaTaste/1.0"})
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # network hiccup: caller retries once
        print(f"  خطأ شبكة عند {imdb_id}: {exc}")
        return None
    if clean(payload.get("Response")).lower() != "true":
        print(f"  OMDb رفض {imdb_id}: {clean(payload.get('Error')) or 'غير معروف'}")
        return {"error": clean(payload.get("Error")) or "unknown"}
    keep = ("Title", "Actors", "Writer", "Director", "Language", "Country", "imdbRating", "imdbVotes", "Rated", "Plot")
    return {field: clean(payload.get(field)) for field in keep if clean(payload.get(field)) not in ("", "N/A")}


def main() -> int:
    key = read_key()
    if not key:
        print("لم يتم العثور على مفتاح OMDb. أضفه من داخل التطبيق أولًا.")
        return 1
    cache: dict[str, dict[str, str]] = {}
    if CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}
    ids = collect_ids()
    # A cached entry without Plot text is incomplete (older script version):
    # refetch it so the semantic signal has full coverage.
    missing = [
        imdb_id for imdb_id in ids
        if imdb_id not in cache or not clean(cache.get(imdb_id, {}).get("Plot"))
    ]
    print(f"إجمالي الأعمال: {len(ids)} | مخزن مسبقًا: {len(ids) - len(missing)} | مطلوب جلبها: {len(missing)}")
    fetched = 0
    for index, imdb_id in enumerate(missing, 1):
        record = fetch(imdb_id, key)
        if record is None:
            time.sleep(3.0)
            record = fetch(imdb_id, key)
        if record is None:
            print("  تخطي مؤقت — أعد تشغيل السكربت لاحقًا لاستكمال الناقص.")
            continue
        cache[imdb_id] = record
        fetched += 1
        if index % 25 == 0 or index == len(missing):
            CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            CACHE_PATH.write_text(
                json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8"
            )
            print(f"  {index}/{len(missing)} — تم الحفظ.")
        time.sleep(0.25)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"اكتمل. أُضيف {fetched} عملًا. الملف: {CACHE_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
