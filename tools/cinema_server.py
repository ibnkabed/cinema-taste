from __future__ import annotations

import argparse
import ctypes
import csv
import json
import os
import re
import shutil
import sys
import threading
import webbrowser
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from taste_engine import analyze_candidate

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BACKUP_DIR = ROOT / "نسخ احتياطية"
JSON_PATH = DATA_DIR / "project-data.json"
JS_PATH = DATA_DIR / "project-data.js"

LIKED_FILE = ROOT / "افلام ومسلسلات اعجبتني.csv"
DISLIKED_FILE = ROOT / "افلام ومسلسلات لم تعجبني.csv"
WATCHLIST_FILE = ROOT / "My Watchlist.csv"
OMDB_CONFIG_DIR = Path(os.environ.get("LOCALAPPDATA") or ROOT / "tools") / "CinemaTaste"
OMDB_KEY_PATH = OMDB_CONFIG_DIR / "omdb_api_key.txt"

POSITIVE_GENRES = {
    "Thriller": 13, "Action": 10, "Mystery": 10, "Sci-Fi": 10,
    "Crime": 8, "Horror": 7, "Adventure": 4, "Drama": 2,
    "Fantasy": 1, "Western": 3,
}
RISK_GENRES = {
    "Biography": -10, "History": -8, "Musical": -9, "Music": -5,
    "Romance": -3, "Comedy": -2, "War": -3,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def csv_headers(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def number(value: object, default: float = 0.0) -> float:
    try:
        return float(clean(value))
    except (TypeError, ValueError):
        return default


class ApiError(Exception):
    def __init__(
        self,
        status: int,
        message: str,
        code: str = "api_error",
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code
        self.details = details or {}


def read_omdb_key() -> str:
    environment_key = clean(os.environ.get("OMDB_API_KEY"))
    if environment_key:
        return environment_key
    if not OMDB_KEY_PATH.exists():
        return ""
    try:
        return clean(OMDB_KEY_PATH.read_text(encoding="utf-8"))
    except OSError:
        return ""


def save_omdb_key(value: object) -> None:
    key = clean(value)
    if not re.fullmatch(r"[A-Za-z0-9]{5,64}", key):
        raise ApiError(400, "مفتاح OMDb غير صالح.", "invalid_key")
    OMDB_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    OMDB_KEY_PATH.write_text(key + "\n", encoding="utf-8")


def omdb_request(params: dict[str, object], api_key: str | None = None) -> dict[str, object]:
    key = clean(api_key) or read_omdb_key()
    if not key:
        raise ApiError(400, "أضف مفتاح OMDb أولًا لتفعيل البحث.", "missing_key")
    query = {"apikey": key, "r": "json", **{name: clean(value) for name, value in params.items() if clean(value)}}
    request = Request(
        "https://www.omdbapi.com/?" + urlencode(query),
        headers={"Accept": "application/json", "User-Agent": "CinemaTaste/1.0"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise ApiError(502, f"تعذر الاتصال بـOMDb (HTTP {exc.code}).", "omdb_http") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ApiError(502, "تعذر الاتصال بـOMDb. تحقق من الإنترنت ثم أعد المحاولة.", "omdb_unreachable") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApiError(502, "وصل رد غير صالح من OMDb.", "omdb_response") from exc
    if not isinstance(payload, dict):
        raise ApiError(502, "وصل رد غير متوقع من OMDb.", "omdb_response")
    return payload


def omdb_error_status(payload: dict[str, object]) -> tuple[int, str, str]:
    message = clean(payload.get("Error")) or "تعذر إكمال الطلب من OMDb."
    lowered = message.lower()
    if "invalid api key" in lowered:
        return 401, "مفتاح OMDb غير صحيح أو غير مفعّل بعد.", "invalid_key"
    if "not found" in lowered:
        return 404, "لم يعثر OMDb على عمل مطابق.", "not_found"
    if "limit" in lowered:
        return 429, "تم بلوغ حد طلبات OMDb لهذا اليوم.", "rate_limit"
    return 502, message, "omdb_error"


def search_omdb(title: object, year: object = "") -> list[dict[str, str]]:
    query = clean(title)
    if len(query) < 2:
        raise ApiError(400, "اكتب حرفين على الأقل من اسم العمل.", "invalid_search")
    params: dict[str, object] = {"s": query}
    year_text = clean(year)
    if year_text:
        if not re.fullmatch(r"(?:18|19|20|21)\d{2}", year_text):
            raise ApiError(400, "سنة الإصدار غير صحيحة.", "invalid_year")
        params["y"] = year_text
    payload = omdb_request(params)
    if clean(payload.get("Response")).lower() == "false":
        status, message, code = omdb_error_status(payload)
        if code == "not_found":
            return []
        raise ApiError(status, message, code)
    rows = payload.get("Search") if isinstance(payload.get("Search"), list) else []
    results: list[dict[str, str]] = []
    for item in rows[:10]:
        if not isinstance(item, dict):
            continue
        imdb_id = clean(item.get("imdbID"))
        if not re.fullmatch(r"tt\d{7,10}", imdb_id):
            continue
        results.append({
            "imdbId": imdb_id,
            "title": clean(item.get("Title")),
            "year": clean(item.get("Year")),
            "type": clean(item.get("Type")),
            "poster": "" if clean(item.get("Poster")) == "N/A" else clean(item.get("Poster")),
        })
    return results


def parse_omdb_date(value: object) -> str:
    text = clean(value)
    if not text or text == "N/A":
        return ""
    months = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }
    match = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})", text)
    if not match or match.group(2).title() not in months:
        return text
    day, month_name, year = match.groups()
    return f"{int(year):04d}-{months[month_name.title()]:02d}-{int(day):02d}"


def omdb_details(imdb_id: object) -> dict[str, str]:
    identifier = clean(imdb_id)
    if not re.fullmatch(r"tt\d{7,10}", identifier):
        raise ApiError(400, "رقم IMDb غير صالح.", "invalid_imdb_id")
    payload = omdb_request({"i": identifier, "plot": "short"})
    if clean(payload.get("Response")).lower() == "false":
        status, message, code = omdb_error_status(payload)
        raise ApiError(status, message, code)

    def omdb_value(name: str) -> str:
        value = clean(payload.get(name))
        return "" if value == "N/A" else value

    runtime_match = re.search(r"\d+", omdb_value("Runtime"))
    year_match = re.search(r"(?:18|19|20|21)\d{2}", omdb_value("Year"))
    type_label = {"movie": "Movie", "series": "TV Series", "episode": "TV Episode"}.get(
        omdb_value("Type").lower(), omdb_value("Type")
    )
    title = omdb_value("Title")
    return {
        "imdbId": identifier,
        "title": title,
        "originalTitle": title,
        "url": f"https://www.imdb.com/title/{identifier}/",
        "titleType": type_label,
        "imdbRating": omdb_value("imdbRating"),
        "runtime": runtime_match.group(0) if runtime_match else "",
        "year": year_match.group(0) if year_match else "",
        "genres": omdb_value("Genre"),
        "numVotes": re.sub(r"\D", "", omdb_value("imdbVotes")),
        "releaseDate": parse_omdb_date(payload.get("Released")),
        "directors": omdb_value("Director"),
        "poster": omdb_value("Poster"),
    }


def backup_csv(path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S-%f")
    backup_path = BACKUP_DIR / f"{path.stem}-{stamp}{path.suffix}"
    shutil.copy2(path, backup_path)
    return backup_path


def work_targets() -> dict[str, tuple[Path, str]]:
    return {
        "liked": (LIKED_FILE, "أعمال أعجبتني"),
        "disliked": (DISLIKED_FILE, "أعمال لم تعجبني"),
        "watchlist": (WATCHLIST_FILE, "قائمة المشاهدة"),
    }


def row_imdb_id(row: dict[str, str]) -> str:
    row_id = clean(row.get("Const"))
    if not row_id:
        match = re.search(r"tt\d{7,10}", clean(row.get("URL")), re.IGNORECASE)
        row_id = match.group(0) if match else ""
    return row_id.lower()


def duplicate_location(imdb_id: str) -> tuple[str, Path, str, int, dict[str, str]] | None:
    for key, (path, label) in work_targets().items():
        for index, row in enumerate(read_csv(path)):
            if row_imdb_id(row) == imdb_id.lower():
                return key, path, label, index, row
    return None


def duplicate_destination(imdb_id: str) -> str:
    location = duplicate_location(imdb_id)
    return location[2] if location else ""


def normalize_editable_work(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ApiError(400, "بيانات العمل غير مكتملة.", "invalid_work")
    limits = {
        "title": 300, "originalTitle": 300, "url": 500, "titleType": 80,
        "imdbRating": 12, "runtime": 12, "year": 12, "genres": 500,
        "numVotes": 30, "releaseDate": 40, "directors": 500,
    }
    work = {name: clean(value.get(name))[:limit] for name, limit in limits.items()}
    work["imdbId"] = clean(value.get("imdbId"))
    if not re.fullmatch(r"tt\d{7,10}", work["imdbId"]):
        raise ApiError(400, "رقم IMDb غير صالح.", "invalid_imdb_id")
    if not work["title"]:
        raise ApiError(400, "اسم العمل مطلوب.", "missing_title")
    if work["year"] and not re.fullmatch(r"(?:18|19|20|21)\d{2}", work["year"]):
        raise ApiError(400, "سنة الإصدار غير صحيحة.", "invalid_year")
    if work["imdbRating"] and not re.fullmatch(r"\d{1,2}(?:\.\d)?", work["imdbRating"]):
        raise ApiError(400, "تقييم IMDb غير صحيح.", "invalid_imdb_rating")
    work["runtime"] = re.sub(r"\D", "", work["runtime"])
    work["numVotes"] = re.sub(r"\D", "", work["numVotes"])
    if not work["url"]:
        work["url"] = f"https://www.imdb.com/title/{work['imdbId']}/"
    return work


def normalize_destination_and_rating(payload: dict[str, object]) -> tuple[str, str, Path, str]:
    destination = clean(payload.get("destination"))
    targets = work_targets()
    if destination not in targets:
        raise ApiError(400, "اختر القائمة التي سيضاف إليها العمل.", "invalid_destination")
    rating = clean(payload.get("rating"))
    if destination == "liked":
        if not rating.isdigit() or not 1 <= int(rating) <= 10:
            raise ApiError(400, "اختر تقييمك من 1 إلى 10.", "missing_rating")
    else:
        rating = ""
    target_path, destination_label = targets[destination]
    return destination, rating, target_path, destination_label


def build_destination_row(
    target_path: Path,
    destination: str,
    rating: str,
    work: dict[str, str],
    base_row: dict[str, str] | None = None,
) -> tuple[list[str], dict[str, str]]:
    headers = csv_headers(target_path)
    if not headers:
        raise ApiError(500, "تعذر قراءة أعمدة ملف القائمة.", "csv_headers")
    today = datetime.now().astimezone().date().isoformat()
    row = {header: clean((base_row or {}).get(header)) for header in headers}
    common = {
        "Const": work["imdbId"],
        "Title": work["title"],
        "Original Title": work["originalTitle"] or work["title"],
        "URL": work["url"],
        "Title Type": work["titleType"],
        "IMDb Rating": work["imdbRating"],
        "Runtime (mins)": work["runtime"],
        "Year": work["year"],
        "Genres": work["genres"],
        "Num Votes": work["numVotes"],
        "Release Date": work["releaseDate"],
        "Directors": work["directors"],
        "Your Rating": rating,
        "Date Rated": today if destination == "liked" else "",
    }
    for name, value in common.items():
        if name in row:
            row[name] = value
    if "Position" in row:
        positions = [int(number(item.get("Position"))) for item in read_csv(target_path) if number(item.get("Position"))]
        row["Position"] = str(max(positions, default=0) + 1)
    if "Created" in row:
        row["Created"] = today
    if "Modified" in row:
        row["Modified"] = today
    return headers, row


def add_work(payload: object) -> tuple[dict[str, object], dict[str, object], str]:
    if not isinstance(payload, dict):
        raise ApiError(400, "طلب الإضافة غير مكتمل.", "invalid_request")
    destination, rating, target_path, destination_label = normalize_destination_and_rating(payload)
    work = normalize_editable_work(payload.get("work"))
    existing = duplicate_location(work["imdbId"])
    if existing:
        existing_key, _path, existing_label, _index, _row = existing
        raise ApiError(
            409,
            f"العمل موجود مسبقًا داخل «{existing_label}».",
            "duplicate",
            {
                "existingDestination": existing_key,
                "existingDestinationLabel": existing_label,
                "requestedDestination": destination,
                "requestedDestinationLabel": destination_label,
            },
        )
    headers, row = build_destination_row(target_path, destination, rating, work)

    try:
        backup_csv(target_path)
    except OSError as exc:
        raise ApiError(500, "تعذر إنشاء النسخة الاحتياطية. أغلق الملف في Excel ثم أعد المحاولة.", "backup_failed") from exc
    try:
        with target_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
            writer.writerow(row)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise ApiError(500, "تعذر الكتابة في ملف القائمة. أغلق الملف في Excel ثم أعد المحاولة.", "csv_locked") from exc
    data, changes = build_data()
    return data, changes, destination_label


def write_csv_rows(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S-%f")
    temporary = path.with_name(f".{path.name}.{stamp}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def transfer_work(payload: object) -> tuple[dict[str, object], dict[str, object], str, str]:
    if not isinstance(payload, dict):
        raise ApiError(400, "طلب النقل غير مكتمل.", "invalid_request")
    destination, rating, target_path, destination_label = normalize_destination_and_rating(payload)
    work = normalize_editable_work(payload.get("work"))
    existing = duplicate_location(work["imdbId"])
    if not existing:
        raise ApiError(404, "لم يعد العمل موجودًا في أي قائمة. أعد البحث ثم حاول مجددًا.", "work_not_found")
    source_key, source_path, source_label, source_index, source_row = existing
    if source_key == destination:
        raise ApiError(409, f"العمل موجود بالفعل داخل «{source_label}».", "duplicate_same_destination")

    source_headers = csv_headers(source_path)
    source_rows = read_csv(source_path)
    target_rows = read_csv(target_path)
    if source_index >= len(source_rows) or row_imdb_id(source_rows[source_index]) != work["imdbId"].lower():
        raise ApiError(409, "تغيرت بيانات القوائم أثناء العملية. أعد المحاولة.", "stale_transfer")
    source_rows.pop(source_index)
    if "Position" in source_headers:
        for position, row in enumerate(source_rows, start=1):
            row["Position"] = str(position)

    target_headers, target_row = build_destination_row(
        target_path,
        destination,
        rating,
        work,
        base_row=source_row,
    )
    target_rows.append(target_row)

    try:
        source_backup = backup_csv(source_path)
        target_backup = backup_csv(target_path)
    except OSError as exc:
        raise ApiError(500, "تعذر إنشاء نسخة أمان قبل النقل. أغلق ملفات CSV ثم أعد المحاولة.", "backup_failed") from exc
    try:
        write_csv_rows(source_path, source_headers, source_rows)
        write_csv_rows(target_path, target_headers, target_rows)
    except OSError as exc:
        shutil.copy2(source_backup, source_path)
        shutil.copy2(target_backup, target_path)
        raise ApiError(500, "تعذر إكمال النقل، وتمت استعادة القائمتين كما كانتا.", "transfer_failed") from exc

    data, changes = build_data()
    return data, changes, source_label, destination_label


def genres_of(row: dict[str, str]) -> list[str]:
    return [clean(item) for item in clean(row.get("Genres")).split(",") if clean(item)]


def directors_of(row: dict[str, str]) -> list[str]:
    return [clean(item) for item in clean(row.get("Directors")).split(",") if clean(item)]


def file_info(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "name": path.name,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
        "mtimeNs": stat.st_mtime_ns,
    }


def extract_docx(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
        root = ET.fromstring(xml)
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        paragraphs: list[str] = []
        for paragraph in root.iter(f"{ns}p"):
            text = "".join(node.text or "" for node in paragraph.iter(f"{ns}t"))
            text = clean(text)
            if text:
                paragraphs.append(text)
        return "\n".join(paragraphs)
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError):
        return ""


def session_date(path: Path, text: str) -> str:
    sample = (path.name + " " + text[:500]).translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))
    match = re.search(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", sample)
    if match:
        year, month, day = match.groups()
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    months = {
        "يناير": 1, "فبراير": 2, "مارس": 3, "أبريل": 4, "ابريل": 4,
        "مايو": 5, "يونيو": 6, "يوليو": 7, "أغسطس": 8, "اغسطس": 8,
        "سبتمبر": 9, "أكتوبر": 10, "اكتوبر": 10, "نوفمبر": 11, "ديسمبر": 12,
    }
    arabic_match = re.search(r"(\d{1,2})\s+([\u0621-\u064a]+)\s+(20\d{2})", sample)
    if arabic_match and arabic_match.group(2) in months:
        day, month_name, year = arabic_match.groups()
        return f"{int(year):04d}-{months[month_name]:02d}-{int(day):02d}"
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().date().isoformat()


def build_sessions() -> list[dict[str, object]]:
    sessions: list[dict[str, object]] = []
    for path in ROOT.glob("*.docx"):
        text = extract_docx(path)
        ratings = re.findall(r"(?:[0-9٠-٩]{1,2})\s*(?:/|من)\s*(?:10|١٠)", text)
        excerpt = clean(text[:700])
        sessions.append({
            "title": path.stem,
            "date": session_date(path, text),
            "excerpt": excerpt[:360] + ("…" if len(excerpt) > 360 else ""),
            "text": text,
            "ratings": list(dict.fromkeys(ratings))[:6],
            "file": path.name,
        })
    return sorted(sessions, key=lambda item: (item["date"], item["title"]), reverse=True)


def genre_summary(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    counts = Counter(genre for row in rows for genre in genres_of(row))
    total = max(1, len(rows))
    return [
        {"name": name, "count": count, "ratio": round(count * 100 / total, 1)}
        for name, count in counts.most_common(12)
    ]


def director_signals(liked: list[dict[str, str]], disliked: list[dict[str, str]]) -> dict[str, int]:
    positive = Counter(director for row in liked for director in directors_of(row))
    negative = Counter(director for row in disliked for director in directors_of(row))
    all_names = set(positive) | set(negative)
    return {
        name: max(-10, min(12, positive[name] * 2 - negative[name] * 4))
        for name in all_names
    }


def score_watchlist(
    rows: list[dict[str, str]], signals: dict[str, int]
) -> list[dict[str, object]]:
    scored: list[dict[str, object]] = []
    for row in rows:
        genres = genres_of(row)
        directors = directors_of(row)
        weights = [POSITIVE_GENRES.get(genre, 0) + RISK_GENRES.get(genre, 0) for genre in genres]
        score = 53 + (sum(weights) / max(1, len(weights)))
        director_bonus = max([signals.get(name, 0) for name in directors] or [0])
        score += director_bonus
        runtime = number(row.get("Runtime (mins)"))
        if 85 <= runtime <= 135:
            score += 4
        elif runtime >= 165:
            score -= 6
        imdb = number(row.get("IMDb Rating"))
        if 5.8 <= imdb <= 7.8:
            score += 2
        score = int(round(max(25, min(93, score))))

        positives = [genre for genre in genres if POSITIVE_GENRES.get(genre, 0) >= 7]
        risks = [genre for genre in genres if RISK_GENRES.get(genre, 0) <= -5]
        reasons: list[str] = []
        if positives:
            reasons.append("تركيبة مناسبة: " + "، ".join(positives[:3]))
        if director_bonus >= 4 and directors:
            reasons.append("إشارة مخرج إيجابية: " + directors[0])
        if 85 <= runtime <= 135:
            reasons.append("مدة مناسبة لإيقاعك")
        if risks:
            reasons.append("عامل مخاطرة: " + "، ".join(risks[:2]))
        if not reasons:
            reasons.append("توافق متوسط يحتاج معايرة بعد المشاهدة")

        if score >= 75:
            verdict = "شاهد أولًا"
            band = "high"
        elif score >= 63:
            verdict = "مرشح جيد"
            band = "good"
        elif score >= 50:
            verdict = "مخاطرة متوسطة"
            band = "medium"
        else:
            verdict = "أجّله"
            band = "low"

        scored.append({
            "const": clean(row.get("Const")),
            "title": clean(row.get("Title")),
            "originalTitle": clean(row.get("Original Title")),
            "year": int(number(row.get("Year"))) if number(row.get("Year")) else None,
            "type": clean(row.get("Title Type")),
            "genres": genres,
            "directors": directors,
            "runtime": int(runtime) if runtime else None,
            "imdb": imdb or None,
            "url": clean(row.get("URL")),
            "score": score,
            "verdict": verdict,
            "band": band,
            "reasons": reasons,
        })
    return sorted(scored, key=lambda item: (-item["score"], item["title"]))


def compact_work(row: dict[str, str]) -> dict[str, object]:
    return {
        "title": clean(row.get("Title")),
        "year": int(number(row.get("Year"))) if number(row.get("Year")) else None,
        "rating": int(number(row.get("Your Rating"))) if number(row.get("Your Rating")) else None,
        "genres": genres_of(row),
        "directors": directors_of(row),
        "imdb": number(row.get("IMDb Rating")) or None,
        "url": clean(row.get("URL")),
    }


def load_old() -> dict[str, object]:
    if not JSON_PATH.exists():
        return {}
    try:
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def make_generated_file_replaceable(path: Path) -> None:
    """Clear Windows hidden/read-only flags from generated files before rewriting."""
    if os.name != "nt" or not path.exists():
        return
    attributes = ctypes.windll.kernel32.GetFileAttributesW(str(path))
    if attributes == -1:
        return
    hidden = 0x2
    read_only = 0x1
    ctypes.windll.kernel32.SetFileAttributesW(str(path), attributes & ~hidden & ~read_only)


def backup_previous(old: dict[str, object]) -> None:
    if not old or not JSON_PATH.exists():
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(JSON_PATH, BACKUP_DIR / f"project-data-{stamp}.json")
    if JS_PATH.exists():
        shutil.copy2(JS_PATH, BACKUP_DIR / f"project-data-{stamp}.js")


def changed_files(old: dict[str, object], current: list[dict[str, object]]) -> list[str]:
    previous = {
        item.get("name"): (item.get("size"), item.get("mtimeNs"))
        for item in old.get("meta", {}).get("sourceFiles", [])
        if isinstance(item, dict)
    }
    return [
        item["name"] for item in current
        if previous.get(item["name"]) != (item["size"], item["mtimeNs"])
    ]


def build_data() -> tuple[dict[str, object], dict[str, object]]:
    liked = read_csv(LIKED_FILE)
    disliked = read_csv(DISLIKED_FILE)
    watchlist = read_csv(WATCHLIST_FILE)
    sessions = build_sessions()
    source_paths = [path for path in [LIKED_FILE, DISLIKED_FILE, WATCHLIST_FILE] if path.exists()]
    source_paths.extend(sorted(ROOT.glob("*.docx")))
    source_files = [file_info(path) for path in source_paths]

    ratings = [number(row.get("Your Rating")) for row in liked if number(row.get("Your Rating"))]
    distribution = Counter(str(int(value)) for value in ratings)
    liked_genres = genre_summary(liked)
    disliked_genres = genre_summary(disliked)
    liked_genre_counts = {item["name"]: item["count"] for item in liked_genres}
    top_genre = max(
        POSITIVE_GENRES,
        key=lambda name: liked_genre_counts.get(name, 0) * POSITIVE_GENRES[name],
        default="—",
    )
    high_rated = [compact_work(row) for row in liked if number(row.get("Your Rating")) >= 9]
    high_rated.sort(key=lambda item: (-(item["rating"] or 0), item["title"]))

    signals = director_signals(liked, disliked)
    directors = sorted(
        ({"name": name, "signal": signal} for name, signal in signals.items() if signal >= 4),
        key=lambda item: (-item["signal"], item["name"]),
    )[:15]
    scored_watchlist = score_watchlist(watchlist, signals)

    old = load_old()
    changed = changed_files(old, source_files)
    previous_summary = old.get("summary", {}) if isinstance(old.get("summary"), dict) else {}
    summary = {
        "liked": len(liked),
        "disliked": len(disliked),
        "watchlist": len(watchlist),
        "averageRating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
        "highRated": len(high_rated),
        "sessions": len(sessions),
        "topGenre": top_genre,
    }
    deltas = {
        key: summary[key] - int(previous_summary.get(key, summary[key]) or 0)
        for key in ("liked", "disliked", "watchlist", "sessions")
    }

    data: dict[str, object] = {
        "meta": {
            "projectName": "الذائقة السينمائية",
            "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
            "version": 1,
            "sourceFiles": source_files,
        },
        "summary": summary,
        "taste": {
            "likedGenres": liked_genres,
            "dislikedGenres": disliked_genres,
            "ratingDistribution": dict(sorted(distribution.items())),
            "positiveDirectors": directors,
            "formula": "حبكة مشدودة + خطر واضح + شخصية مأزومة + تصعيد مبرر",
            "riskFormula": "إيقاع بطيء + معالجة باردة أو جوائزية + توتر مباشر ضعيف",
        },
        "watchlist": scored_watchlist,
        "references": {
            "highRated": high_rated,
            "dislikedExamples": [compact_work(row) for row in disliked[:24]],
        },
        "sessions": sessions,
    }
    changes = {"files": changed, "deltas": deltas, "hasChanges": bool(changed or any(deltas.values()))}
    data["meta"]["changes"] = changes

    if changes["hasChanges"] and old:
        backup_previous(old)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    make_generated_file_replaceable(JSON_PATH)
    make_generated_file_replaceable(JS_PATH)
    JSON_PATH.write_text(payload, encoding="utf-8")
    JS_PATH.write_text("window.CINEMA_DATA = " + payload + ";\n", encoding="utf-8")
    return data, changes


class CinemaHandler(SimpleHTTPRequestHandler):
    server_version = "CinemaTaste/1.0"

    def log_message(self, format: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ApiError(400, "حجم الطلب غير صالح.", "invalid_request") from exc
        if length <= 0 or length > 65536:
            raise ApiError(400, "حجم الطلب غير صالح.", "invalid_request")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ApiError(400, "تعذر قراءة الطلب.", "invalid_json") from exc
        if not isinstance(payload, dict):
            raise ApiError(400, "صيغة الطلب غير صحيحة.", "invalid_json")
        return payload

    def do_GET(self) -> None:
        path = unquote(urlparse(self.path).path)
        if path == "/api/status":
            self.send_json({"ok": True, "omdbConfigured": bool(read_omdb_key())})
            return
        if path == "/api/taste/demo":
            watchlist = read_csv(WATCHLIST_FILE)
            if not watchlist:
                self.send_json({"ok": False, "error": "لا توجد عينة في قائمة المشاهدة.", "code": "demo_unavailable"}, 404)
                return
            work = watchlist[0]
            analysis = analyze_candidate(work, read_csv(LIKED_FILE), read_csv(DISLIKED_FILE))
            self.send_json({"ok": True, "work": work, "analysis": analysis, "demo": True})
            return
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/%D8%A7%D9%84%D8%B0%D8%A7%D8%A6%D9%82%D8%A9%20%D8%A7%D9%84%D8%B3%D9%8A%D9%86%D9%85%D8%A7%D8%A6%D9%8A%D8%A9.html")
            self.end_headers()
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/refresh":
                data, changes = build_data()
                self.send_json({"ok": True, "changes": changes, "summary": data["summary"]})
                return
            payload = self.read_json()
            if path == "/api/omdb/key":
                key = clean(payload.get("key"))
                if not re.fullmatch(r"[A-Za-z0-9]{5,64}", key):
                    raise ApiError(400, "مفتاح OMDb غير صالح.", "invalid_key")
                test = omdb_request({"i": "tt0111161"}, api_key=key)
                if clean(test.get("Response")).lower() == "false":
                    status, message, code = omdb_error_status(test)
                    raise ApiError(status, message, code)
                save_omdb_key(key)
                self.send_json({"ok": True, "omdbConfigured": True})
                return
            if path == "/api/omdb/search":
                results = search_omdb(payload.get("title"), payload.get("year"))
                self.send_json({"ok": True, "results": results})
                return
            if path == "/api/omdb/details":
                self.send_json({"ok": True, "work": omdb_details(payload.get("imdbId"))})
                return
            if path == "/api/taste/analyze":
                work = omdb_details(payload.get("imdbId"))
                analysis = analyze_candidate(work, read_csv(LIKED_FILE), read_csv(DISLIKED_FILE))
                self.send_json({"ok": True, "work": work, "analysis": analysis})
                return
            if path == "/api/works/add":
                data, changes, destination_label = add_work(payload)
                self.send_json({
                    "ok": True,
                    "message": f"تمت إضافة العمل إلى «{destination_label}».",
                    "destination": destination_label,
                    "changes": changes,
                    "data": data,
                })
                return
            if path == "/api/works/transfer":
                data, changes, source_label, destination_label = transfer_work(payload)
                self.send_json({
                    "ok": True,
                    "message": f"تم نقل العمل من «{source_label}» إلى «{destination_label}».",
                    "source": source_label,
                    "destination": destination_label,
                    "changes": changes,
                    "data": data,
                })
                return
            self.send_json({"ok": False, "error": "المسار غير موجود.", "code": "not_found"}, 404)
        except ApiError as exc:
            self.send_json({"ok": False, "error": exc.message, "code": exc.code, **exc.details}, exc.status)
        except Exception as exc:  # pragma: no cover - visible as a local diagnostic
            self.send_json({"ok": False, "error": str(exc), "code": "server_error"}, 500)


def run_server(port: int, open_browser: bool = True, host: str = "127.0.0.1") -> None:
    build_data()
    handler = partial(CinemaHandler, directory=str(ROOT))
    server = ThreadingHTTPServer((host, port), handler)
    display_host = "127.0.0.1" if host == "0.0.0.0" else host
    url = f"http://{display_host}:{port}/"
    print("\nالذائقة السينمائية تعمل محليًا:")
    print(url)
    print("أغلق هذه النافذة لإيقاف المشروع.\n")
    if open_browser:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="تشغيل وتحديث مشروع الذائقة السينمائية")
    parser.add_argument("--refresh-only", action="store_true")
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    if args.refresh_only:
        data, changes = build_data()
        print(json.dumps({"summary": data["summary"], "changes": changes}, ensure_ascii=False, indent=2))
    else:
        run_server(args.port, open_browser=not args.no_open, host=args.host)
