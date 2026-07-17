from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Iterable


def _clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _number(value: object, default: float = 0.0) -> float:
    try:
        return float(_clean(value))
    except (TypeError, ValueError):
        return default


def _value(row: dict[str, object], *names: str) -> str:
    for name in names:
        value = _clean(row.get(name))
        if value:
            return value
    return ""


def _parts(value: object) -> list[str]:
    return [part for item in str(value or "").split(",") if (part := _clean(item))]


def _genres(row: dict[str, object]) -> list[str]:
    return _parts(_value(row, "genres", "Genres"))


def _directors(row: dict[str, object]) -> list[str]:
    return _parts(_value(row, "directors", "Directors", "Director"))


def _runtime(row: dict[str, object]) -> float:
    return _number(_value(row, "runtime", "Runtime (mins)"))


def _rating(row: dict[str, object]) -> float:
    return _number(_value(row, "rating", "Your Rating"))


def _title(row: dict[str, object]) -> str:
    return _value(row, "title", "Title", "originalTitle", "Original Title") or "Untitled"


def _year(row: dict[str, object]) -> str:
    return _value(row, "year", "Year")


def _type(row: dict[str, object]) -> str:
    return _value(row, "titleType", "type", "Title Type")


def _signal_table(
    liked: Iterable[dict[str, object]],
    disliked: Iterable[dict[str, object]],
    extractor,
) -> dict[str, dict[str, float | int]]:
    stats: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"liked": 0, "disliked": 0, "ratingTotal": 0.0, "rated": 0}
    )
    for row in liked:
        rating = _rating(row)
        for name in extractor(row):
            stats[name]["liked"] = int(stats[name]["liked"]) + 1
            if rating:
                stats[name]["ratingTotal"] = float(stats[name]["ratingTotal"]) + rating
                stats[name]["rated"] = int(stats[name]["rated"]) + 1
    for row in disliked:
        for name in extractor(row):
            stats[name]["disliked"] = int(stats[name]["disliked"]) + 1

    result: dict[str, dict[str, float | int]] = {}
    for name, item in stats.items():
        liked_count = int(item["liked"])
        disliked_count = int(item["disliked"])
        rated = int(item["rated"])
        average = float(item["ratingTotal"]) / rated if rated else 7.0
        rating_quality = max(-1.0, min(1.0, (average - 6.5) / 2.5))
        evidence = liked_count + disliked_count
        raw = liked_count * (1.0 + rating_quality) - disliked_count * 2.25
        signal = max(-2.0, min(2.0, raw / (evidence + 3.0)))
        result[name] = {
            "signal": round(signal, 3),
            "liked": liked_count,
            "disliked": disliked_count,
            "averageRating": round(average, 2) if rated else 0,
            "evidence": evidence,
        }
    return result


def _similarity(candidate: dict[str, object], row: dict[str, object]) -> float:
    candidate_genres = set(_genres(candidate))
    row_genres = set(_genres(row))
    union = candidate_genres | row_genres
    genre_score = len(candidate_genres & row_genres) / len(union) if union else 0.0

    candidate_directors = set(_directors(candidate))
    director_score = 1.0 if candidate_directors & set(_directors(row)) else 0.0
    type_score = 1.0 if _type(candidate) and _type(candidate).lower() == _type(row).lower() else 0.0

    candidate_runtime = _runtime(candidate)
    row_runtime = _runtime(row)
    runtime_score = 0.0
    if candidate_runtime and row_runtime:
        runtime_score = max(0.0, 1.0 - abs(candidate_runtime - row_runtime) / 90.0)

    return genre_score * 0.67 + director_score * 0.18 + type_score * 0.08 + runtime_score * 0.07


def _references(
    candidate: dict[str, object], rows: Iterable[dict[str, object]], limit: int = 4
) -> list[dict[str, object]]:
    candidate_id = _value(candidate, "imdbId", "Const")
    scored: list[tuple[float, dict[str, object]]] = []
    for row in rows:
        if candidate_id and candidate_id == _value(row, "imdbId", "Const"):
            continue
        similarity = _similarity(candidate, row)
        if similarity <= 0:
            continue
        scored.append((similarity, row))
    scored.sort(key=lambda item: (-item[0], -_rating(item[1]), _title(item[1])))
    return [
        {
            "title": _title(row),
            "year": _year(row),
            "rating": int(_rating(row)) if _rating(row) else None,
            "similarity": round(score * 100),
            "sharedGenres": sorted(set(_genres(candidate)) & set(_genres(row))),
        }
        for score, row in scored[:limit]
    ]


def _format_refs(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "None"
    return "; ".join(
        f"{row['title']} ({row.get('year') or 'year unknown'}, similarity {row['similarity']}%"
        + (f", personal rating {row['rating']}/10" if row.get("rating") else "")
        + ")"
        for row in rows
    )


def analyze_candidate(
    candidate: dict[str, object],
    liked: list[dict[str, object]],
    disliked: list[dict[str, object]],
) -> dict[str, object]:
    genre_stats = _signal_table(liked, disliked, _genres)
    director_stats = _signal_table(liked, disliked, _directors)
    candidate_genres = _genres(candidate)
    candidate_directors = _directors(candidate)

    genre_evidence = [genre_stats[name] for name in candidate_genres if name in genre_stats]
    director_evidence = [director_stats[name] for name in candidate_directors if name in director_stats]
    genre_signal = (
        sum(float(item["signal"]) for item in genre_evidence) / len(genre_evidence)
        if genre_evidence else 0.0
    )
    director_signal = max(
        [float(item["signal"]) for item in director_evidence] or [0.0],
        key=abs,
    )

    liked_refs = _references(candidate, liked)
    disliked_refs = _references(candidate, disliked)
    liked_similarity = sum(float(item["similarity"]) for item in liked_refs[:3]) / max(1, min(3, len(liked_refs)))
    disliked_similarity = sum(float(item["similarity"]) for item in disliked_refs[:3]) / max(1, min(3, len(disliked_refs)))
    reference_delta = (liked_similarity - disliked_similarity) / 100.0

    rated_runtimes = [_runtime(row) for row in liked if _rating(row) >= 8 and _runtime(row)]
    runtime_signal = 0.0
    candidate_runtime = _runtime(candidate)
    preferred_runtime = sum(rated_runtimes) / len(rated_runtimes) if rated_runtimes else 0.0
    if candidate_runtime and preferred_runtime:
        runtime_signal = max(-1.0, 1.0 - abs(candidate_runtime - preferred_runtime) / 75.0)

    score = 50.0 + genre_signal * 13.0 + director_signal * 6.0 + reference_delta * 15.0 + runtime_signal * 3.0
    score = int(round(max(18.0, min(92.0, score))))

    evidence_points = sum(int(item["evidence"]) for item in genre_evidence)
    evidence_points += sum(int(item["evidence"]) for item in director_evidence) * 2
    evidence_points += len(liked_refs) * 2 + len(disliked_refs) * 2
    confidence = int(round(max(25.0, min(91.0, 25.0 + math.sqrt(evidence_points) * 8.0))))

    if score >= 74:
        verdict_key, verdict_ar, verdict_en = "strong", "واعد جدًا للنقاش", "Strong conversation starter"
    elif score >= 61:
        verdict_key, verdict_ar, verdict_en = "promising", "مرشح واعد", "Promising candidate"
    elif score >= 46:
        verdict_key, verdict_ar, verdict_en = "uncertain", "يحتاج نقاشًا أعمق", "Needs a closer discussion"
    else:
        verdict_key, verdict_ar, verdict_en = "caution", "إشارات الحذر أعلى", "More caution signals than matches"

    genre_signals = [
        {"name": name, **genre_stats[name]}
        for name in candidate_genres if name in genre_stats
    ]
    director_signals = [
        {"name": name, **director_stats[name]}
        for name in candidate_directors if name in director_stats
    ]
    genre_signals.sort(key=lambda item: (-abs(float(item["signal"])), item["name"]))
    director_signals.sort(key=lambda item: (-abs(float(item["signal"])), item["name"]))

    positive_genres = [item["name"] for item in genre_signals if float(item["signal"]) > 0.2]
    risky_genres = [item["name"] for item in genre_signals if float(item["signal"]) < -0.2]
    reasons_ar: list[str] = []
    reasons_en: list[str] = []
    if positive_genres:
        reasons_ar.append("أنواع متوافقة مع السجل: " + "، ".join(positive_genres[:3]))
        reasons_en.append("Genres with positive history: " + ", ".join(positive_genres[:3]))
    if risky_genres:
        reasons_ar.append("أنواع تحمل إشارات حذر: " + "، ".join(risky_genres[:3]))
        reasons_en.append("Genres with caution history: " + ", ".join(risky_genres[:3]))
    if liked_refs:
        reasons_ar.append("أقرب عمل أعجبك: " + liked_refs[0]["title"])
        reasons_en.append("Closest liked reference: " + str(liked_refs[0]["title"]))
    if disliked_refs:
        reasons_ar.append("أقرب إشارة معاكسة: " + disliked_refs[0]["title"])
        reasons_en.append("Closest disliked reference: " + str(disliked_refs[0]["title"]))
    if not reasons_ar:
        reasons_ar.append("الأدلة الحالية محدودة؛ الأفضل التعامل معها كنقطة بداية للحوار.")
        reasons_en.append("Current evidence is limited; use this only as a conversation starting point.")

    title = _title(candidate)
    candidate_line = (
        f"{title} ({_year(candidate) or 'year unknown'}), type {_type(candidate) or 'unknown'}, "
        f"genres {', '.join(candidate_genres) or 'unknown'}, directors {', '.join(candidate_directors) or 'unknown'}, "
        f"runtime {int(candidate_runtime) if candidate_runtime else 'unknown'} minutes."
    )
    prompt_en = f"""You are a careful cinema-taste discussion partner using GPT-5.6.
Do not give a deterministic yes/no verdict. Explain uncertainty, challenge weak evidence, and distinguish personal-taste evidence from popularity.

Candidate: {candidate_line}
Local engine reading: {score}/100, confidence {confidence}/100, label: {verdict_en}.
Positive/caution notes: {'; '.join(reasons_en)}
Closest liked references: {_format_refs(liked_refs)}
Closest disliked references: {_format_refs(disliked_refs)}

Please discuss whether this work is worth trying for this viewer. Start with the strongest evidence, mention the main risk, and end with one practical recommendation. Reply in Arabic unless I ask for English."""
    prompt_ar = f"""أنت شريك نقاش دقيق في الذائقة السينمائية وتستخدم GPT-5.6.
لا تعطِ حكمًا قطعيًا بنعم أو لا. وضّح درجة عدم اليقين، وانتقد الأدلة الضعيفة، وافصل بين الذائقة الشخصية وشهرة العمل.

العمل المرشح: {candidate_line}
قراءة المحرك المحلي: {score}/100، والثقة {confidence}/100، والتصنيف: {verdict_ar}.
الأدلة: {'؛ '.join(reasons_ar)}
أقرب أعمال أعجبت المشاهد: {_format_refs(liked_refs)}
أقرب أعمال لم تعجبه: {_format_refs(disliked_refs)}

ناقش هل يستحق هذا العمل التجربة لهذا المشاهد. ابدأ بأقوى دليل، ثم اذكر الخطر الأهم، واختم بتوصية عملية واحدة."""

    return {
        "score": score,
        "confidence": confidence,
        "verdictKey": verdict_key,
        "verdictAr": verdict_ar,
        "verdictEn": verdict_en,
        "reasonsAr": reasons_ar,
        "reasonsEn": reasons_en,
        "genreSignals": genre_signals[:6],
        "directorSignals": director_signals[:4],
        "similarLiked": liked_refs,
        "similarDisliked": disliked_refs,
        "codexPromptAr": prompt_ar,
        "codexPromptEn": prompt_en,
        "disclaimerAr": "هذه قراءة تفسيرية مبنية على سجلك، وليست حكمًا آليًا نهائيًا.",
        "disclaimerEn": "This is an explainable reading of your history, not a deterministic verdict.",
    }
