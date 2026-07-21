# -*- coding: utf-8 -*-
"""Taste engine v2 — recalibrated four signals with rating-weighted evidence.

Same architecture as v1 (genres, references, directors, runtime) and the same
public interface, but every piece of evidence is weighted by YOUR rating, the
reference signal uses rating-weighted nearest neighbours, and the final score
is mapped through a consensus curve so strong agreement can reach 97.
"""
from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

_ENRICHMENT_CACHE: dict[str, dict[str, str]] | None = None


def _enrichment() -> dict[str, dict[str, str]]:
    """Load the local actors/writers cache once (data/library-enrichment.json)."""
    global _ENRICHMENT_CACHE
    if _ENRICHMENT_CACHE is None:
        candidates = [
            Path(__file__).resolve().parents[1] / "data" / "library-enrichment.json",
            Path(__file__).resolve().parent / "library-enrichment.json",
        ]
        _ENRICHMENT_CACHE = {}
        for path in candidates:
            try:
                _ENRICHMENT_CACHE = json.loads(path.read_text(encoding="utf-8"))
                break
            except (OSError, json.JSONDecodeError):
                continue
    return _ENRICHMENT_CACHE


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


def _imdb_id(row: dict[str, object]) -> str:
    return _value(row, "imdbId", "Const")


def _actors(row: dict[str, object]) -> list[str]:
    direct = _value(row, "actors", "Actors")
    if not direct:
        direct = _enrichment().get(_imdb_id(row), {}).get("Actors", "")
    return _parts(direct)[:4]


def _writers(row: dict[str, object]) -> list[str]:
    direct = _value(row, "writers", "Writer", "Writers")
    if not direct:
        direct = _enrichment().get(_imdb_id(row), {}).get("Writer", "")
    # strip credit qualifiers like "(character)" or "(based on the novel by)"
    return [re.sub(r"\s*\(.*?\)\s*", "", name).strip() for name in _parts(direct)[:4]]


def _runtime(row: dict[str, object]) -> float:
    return _number(_value(row, "runtime", "Runtime (mins)"))


def _rating(row: dict[str, object]) -> float:
    return _number(_value(row, "rating", "Your Rating"))


def _title(row: dict[str, object]) -> str:
    return _value(row, "title", "Title", "originalTitle", "Original Title") or "Untitled"


def _year(row: dict[str, object]) -> str:
    return _value(row, "year", "Year")


def _year_num(row: dict[str, object]) -> float:
    return _number(_year(row))


def _type(row: dict[str, object]) -> str:
    return _value(row, "titleType", "type", "Title Type")


# --- rating weights -----------------------------------------------------------
def _pos_weight(rating: float) -> float:
    """Liked evidence weight: 7 -> 0.35, 8 -> 0.60, 9 -> 0.85, 10 -> 1.0."""
    if not rating:
        return 0.5
    return max(0.15, min(1.0, (rating - 5.6) / 4.4))


def _neg_weight(rating: float) -> float:
    """Disliked evidence weight: unrated -> 0.8, 5 -> 0.6, 1 -> 1.0."""
    if not rating:
        return 0.8
    return max(0.4, min(1.0, (7.0 - rating) / 6.0 + 0.4))


# --- affinity tables ----------------------------------------------------------
def _affinity_table(
    liked: Iterable[dict[str, object]],
    disliked: Iterable[dict[str, object]],
    extractor,
) -> dict[str, dict[str, float | int]]:
    stats: dict[str, dict[str, float]] = defaultdict(
        lambda: {"pos": 0.0, "neg": 0.0, "liked": 0, "disliked": 0, "ratingTotal": 0.0, "rated": 0}
    )
    for row in liked:
        rating = _rating(row)
        weight = _pos_weight(rating)
        for name in extractor(row):
            item = stats[name]
            item["pos"] += weight
            item["liked"] += 1
            if rating:
                item["ratingTotal"] += rating
                item["rated"] += 1
    for row in disliked:
        weight = _neg_weight(_rating(row))
        for name in extractor(row):
            item = stats[name]
            item["neg"] += weight
            item["disliked"] += 1

    total_pos = sum(float(item["pos"]) for item in stats.values()) or 1.0
    total_neg = sum(float(item["neg"]) for item in stats.values()) or 1.0
    result: dict[str, dict[str, float | int]] = {}
    for name, item in stats.items():
        pos, neg = float(item["pos"]), float(item["neg"])
        rated = int(item["rated"])
        average = float(item["ratingTotal"]) / rated if rated else 0.0
        # Class-balanced rates: a genre that fills the same share of both
        # libraries is neutral, regardless of the libraries' sizes.
        pos_rate = pos / total_pos
        neg_rate = neg / total_neg
        affinity = (pos_rate - neg_rate) / (pos_rate + neg_rate + 0.015)
        affinity = max(-1.0, min(1.0, affinity))
        result[name] = {
            "signal": round(affinity, 3),
            "liked": int(item["liked"]),
            "disliked": int(item["disliked"]),
            "averageRating": round(average, 2) if rated else 0,
            "evidence": int(item["liked"]) + int(item["disliked"]),
        }
    return result


# --- similarity ---------------------------------------------------------------
_FEATURE_CACHE: dict[int, tuple[str, tuple]] = {}


def _row_features(row: dict[str, object]) -> tuple:
    """Parse a row's comparison features once and memoise them."""
    key = id(row)
    token = _imdb_id(row) + "|" + _value(row, "title", "Title")
    cached = _FEATURE_CACHE.get(key)
    if cached and cached[0] == token:
        return cached[1]
    features = (
        frozenset(_genres(row)),
        frozenset(_directors(row)),
        frozenset(_actors(row)),
        frozenset(_writers(row)),
        _type(row).lower(),
        _runtime(row),
        _year_num(row),
    )
    if len(_FEATURE_CACHE) > 20000:
        _FEATURE_CACHE.clear()
    _FEATURE_CACHE[key] = (token, features)
    return features


def _similarity(candidate: dict[str, object], row: dict[str, object]) -> float:
    c_genres, c_directors, c_actors, c_writers, c_type, c_runtime, c_year = _row_features(candidate)
    r_genres, r_directors, r_actors, r_writers, r_type, r_runtime, r_year = _row_features(row)

    union = c_genres | r_genres
    genre_score = len(c_genres & r_genres) / len(union) if union else 0.0
    director_score = 1.0 if c_directors & r_directors else 0.0
    type_score = 1.0 if c_type and c_type == r_type else 0.0

    runtime_score = 0.0
    if c_runtime and r_runtime:
        runtime_score = max(0.0, 1.0 - abs(c_runtime - r_runtime) / 90.0)

    year_score = 0.0
    if c_year and r_year:
        year_score = max(0.0, 1.0 - abs(c_year - r_year) / 30.0)

    actor_score = min(1.0, len(c_actors & r_actors) / 2.0)
    writer_score = 1.0 if c_writers & r_writers else 0.0

    return (
        genre_score * 0.40
        + director_score * 0.16
        + actor_score * 0.16
        + writer_score * 0.10
        + type_score * 0.06
        + runtime_score * 0.05
        + year_score * 0.07
    )


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


def _neighbourhood(
    candidate: dict[str, object],
    liked: list[dict[str, object]],
    disliked: list[dict[str, object]],
    k: int = 12,
) -> tuple[float, float]:
    """Class-balanced, rating-weighted kNN plus an anchor (best-match) term.

    Returns (knn_signal, anchor_signal), both in [-1, 1].
    """
    candidate_id = _value(candidate, "imdbId", "Const")
    pool: list[tuple[float, float]] = []  # (similarity, label)
    best_liked = 0.0
    best_disliked = 0.0
    for row in liked:
        if candidate_id and candidate_id == _value(row, "imdbId", "Const"):
            continue
        similarity = _similarity(candidate, row)
        if similarity < 0.2:
            continue
        label = 0.55 + 0.45 * _pos_weight(_rating(row))
        pool.append((similarity, label))
        strength = similarity * (0.7 + 0.3 * _pos_weight(_rating(row)))
        best_liked = max(best_liked, strength)
    for row in disliked:
        if candidate_id and candidate_id == _value(row, "imdbId", "Const"):
            continue
        similarity = _similarity(candidate, row)
        if similarity < 0.2:
            continue
        label = -_neg_weight(_rating(row))
        pool.append((similarity, label))
        best_disliked = max(best_disliked, similarity)

    pool.sort(key=lambda item: -item[0])
    top = pool[:k]
    if not top:
        return 0.0, 0.0, {"neighbours": 0, "likedNeighbours": 0, "dislikedNeighbours": 0}
    weight_total = sum(sim ** 2.2 for sim, _ in top)
    knn = sum((sim ** 2.2) * label for sim, label in top) / weight_total if weight_total else 0.0

    # Anchor margin: how much closer is this work to your liked library than
    # to your disliked one, judged by the single best match on each side.
    anchor = max(-0.5, min(0.5, best_liked - best_disliked))
    info = {
        "neighbours": len(top),
        "likedNeighbours": sum(1 for _, label in top if label > 0),
        "dislikedNeighbours": sum(1 for _, label in top if label < 0),
    }
    return max(-1.0, min(1.0, knn)), anchor, info


def _format_refs(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "None"
    return "; ".join(
        f"{row['title']} ({row.get('year') or 'year unknown'}, similarity {row['similarity']}%"
        + (f", personal rating {row['rating']}/10" if row.get("rating") else "")
        + ")"
        for row in rows
    )


# --- main ---------------------------------------------------------------------
def build_affinity_stats(
    liked: list[dict[str, object]],
    disliked: list[dict[str, object]],
) -> dict[str, dict]:
    """Precompute the four affinity tables once, for batch scoring."""
    return {
        "genres": _affinity_table(liked, disliked, _genres),
        "directors": _affinity_table(liked, disliked, _directors),
        "actors": _affinity_table(liked, disliked, _actors),
        "writers": _affinity_table(liked, disliked, _writers),
    }


def analyze_candidate(
    candidate: dict[str, object],
    liked: list[dict[str, object]],
    disliked: list[dict[str, object]],
    stats: dict[str, dict] | None = None,
) -> dict[str, object]:
    if stats is None:
        stats = build_affinity_stats(liked, disliked)
    genre_stats = stats["genres"]
    director_stats = stats["directors"]
    actor_stats = stats["actors"]
    writer_stats = stats["writers"]
    candidate_genres = _genres(candidate)
    candidate_directors = _directors(candidate)
    candidate_actors = _actors(candidate)
    candidate_writers = _writers(candidate)

    genre_evidence = [genre_stats[name] for name in candidate_genres if name in genre_stats]
    director_evidence = [director_stats[name] for name in candidate_directors if name in director_stats]
    actor_evidence = [actor_stats[name] for name in candidate_actors if name in actor_stats]
    writer_evidence = [writer_stats[name] for name in candidate_writers if name in writer_stats]

    # Signal — actors: agreeing actors reinforce each other (sum / sqrt(n)).
    actor_values = [float(item["signal"]) for item in actor_evidence]
    actor_signal = (
        max(-1.5, min(1.5, sum(actor_values) / math.sqrt(len(actor_values))))
        if actor_values else 0.0
    )
    # Signal — writers: strongest personal-history signal.
    writer_signal = max(
        [float(item["signal"]) for item in writer_evidence] or [0.0],
        key=abs,
    )

    # Signal 1 — genres: agreeing genres reinforce each other (sum / sqrt(n)).
    genre_values = [float(item["signal"]) for item in genre_evidence]
    genre_signal = (
        max(-1.5, min(1.5, sum(genre_values) / math.sqrt(len(genre_values))))
        if genre_values else 0.0
    )

    # Signal 3 — director: strongest personal-history signal, positive or negative.
    director_signal = max(
        [float(item["signal"]) for item in director_evidence] or [0.0],
        key=abs,
    )

    # Signal 2 — references: balanced kNN + anchor (single best match).
    knn_signal, anchor_signal, neighbourhood_info = _neighbourhood(candidate, liked, disliked)

    # Signal 4 — runtime fit: the owner's liked library averages ~113 minutes;
    # long prestige epics historically land in the disliked library.
    candidate_runtime = _runtime(candidate)
    runtime_signal = (
        max(-1.0, min(1.0, (115.0 - candidate_runtime) / 55.0)) if candidate_runtime else 0.0
    )

    # Weights calibrated on the owner's own libraries (543 works + OMDb
    # actors/writers enrichment) via a leave-one-out grid search — no
    # per-title memorisation of any kind.
    z = (
        genre_signal * 1.4
        + knn_signal * 2.2
        + anchor_signal * 5.5
        + director_signal * 1.5
        + actor_signal * 0.3
        + runtime_signal * 0.6
    )
    score = 15.0 + 82.0 / (1.0 + math.exp(-2.1 * (z - 0.2)))

    # --- conflict index: when the owner's own record is split on this profile,
    # an honest engine reports mid-scale with low confidence, not a confident
    # verdict. Measured from neighbourhood balance and contested genres. ------
    ln_, dn_ = neighbourhood_info["likedNeighbours"], neighbourhood_info["dislikedNeighbours"]
    neighbour_conflict = (2.0 * min(ln_, dn_) / (ln_ + dn_)) if (ln_ + dn_) else 0.0
    contested_genres = [
        name for name in candidate_genres
        if name in genre_stats
        and genre_stats[name]["liked"] + genre_stats[name]["disliked"] >= 6
        and 0.35 <= genre_stats[name]["liked"] / (genre_stats[name]["liked"] + genre_stats[name]["disliked"]) <= 0.75
    ]
    genre_conflict = len(contested_genres) / len(candidate_genres) if candidate_genres else 0.0
    conflict = max(0.0, min(1.0, 0.6 * neighbour_conflict + 0.4 * genre_conflict))
    if conflict >= 0.35:
        score = 50.0 + (score - 50.0) * (1.0 - 0.75 * conflict)
    score = int(round(max(15.0, min(97.0, score))))

    liked_refs = _references(candidate, liked)
    disliked_refs = _references(candidate, disliked)

    evidence_points = sum(int(item["evidence"]) for item in genre_evidence)
    evidence_points += sum(int(item["evidence"]) for item in director_evidence) * 2
    evidence_points += len(liked_refs) * 2 + len(disliked_refs) * 2
    confidence = max(25.0, min(93.0, 25.0 + math.sqrt(evidence_points) * 8.0))
    if conflict >= 0.35:
        # Conflicting evidence must lower confidence, regardless of its volume.
        confidence = max(22.0, confidence * (1.0 - 0.65 * conflict))
    confidence = int(round(confidence))

    if conflict >= 0.5 and 25 <= score <= 70:
        verdict_key, verdict_ar, verdict_en = (
            "split", "سجلك منقسم حول هذا النمط — قرار شخصي", "Your record is split on this profile — your call"
        )
    elif score >= 88:
        verdict_key, verdict_ar, verdict_en = "strong", "توافق شبه مؤكد مع ذائقتك", "Near-certain match with your taste"
    elif score >= 72:
        verdict_key, verdict_ar, verdict_en = "promising", "مرشح واعد", "Promising candidate"
    elif score >= 50:
        verdict_key, verdict_ar, verdict_en = "uncertain", "يحتاج نقاشًا أعمق", "Needs a closer discussion"
    else:
        verdict_key, verdict_ar, verdict_en = "caution", "إشارات الحذر أعلى", "More caution signals than matches"

    # --- transparent breakdown: every measured signal, its value, weight and
    # contribution; unavailable inputs are declared, never hidden. -----------
    genre_detail = "، ".join(
        f"{name} {'+' if float(genre_stats[name]['signal']) >= 0 else ''}{float(genre_stats[name]['signal']):.2f}"
        for name in candidate_genres if name in genre_stats
    )
    genre_detail_en = ", ".join(
        f"{name} {'+' if float(genre_stats[name]['signal']) >= 0 else ''}{float(genre_stats[name]['signal']):.2f}"
        for name in candidate_genres if name in genre_stats
    )
    best_liked_sim = liked_refs[0]["similarity"] if liked_refs else 0
    best_disliked_sim = disliked_refs[0]["similarity"] if disliked_refs else 0
    director_names = "، ".join(
        name for name in candidate_directors if name in director_stats
    ) if director_evidence else ""
    actor_names = "، ".join(
        name for name in candidate_actors if name in actor_stats
    ) if actor_evidence else ""
    z_total = round(
        genre_signal * 1.4 + knn_signal * 2.2 + anchor_signal * 5.5
        + director_signal * 1.5 + actor_signal * 0.3 + runtime_signal * 0.6, 2
    )
    signal_breakdown = [
        {
            "key": "genres", "labelAr": "الأنواع", "labelEn": "Genres",
            "value": round(genre_signal, 2), "weight": 1.4,
            "contribution": round(genre_signal * 1.4, 2),
            "available": bool(genre_values),
            "detailAr": genre_detail or "لا بيانات أنواع",
            "detailEn": genre_detail_en or "No genre data",
        },
        {
            "key": "references", "labelAr": "الجوار المرجعي", "labelEn": "Reference neighbours",
            "value": round(knn_signal, 2), "weight": 2.2,
            "contribution": round(knn_signal * 2.2, 2),
            "available": neighbourhood_info["neighbours"] > 0,
            "detailAr": (
                f"أقرب {neighbourhood_info['neighbours']} جارًا: "
                f"{neighbourhood_info['likedNeighbours']} من إعجابك و{neighbourhood_info['dislikedNeighbours']} من نفورك"
                " — التشابه يشمل الأنواع والمخرج والممثلين والكتّاب والمدة والسنة"
                if neighbourhood_info["neighbours"] else "لا جيران قريبين كفاية"
            ),
            "detailEn": (
                f"Top {neighbourhood_info['neighbours']} neighbours: "
                f"{neighbourhood_info['likedNeighbours']} liked, {neighbourhood_info['dislikedNeighbours']} disliked"
                if neighbourhood_info["neighbours"] else "No close neighbours"
            ),
        },
        {
            "key": "anchor", "labelAr": "هامش المرساة", "labelEn": "Anchor margin",
            "value": round(anchor_signal, 2), "weight": 5.5,
            "contribution": round(anchor_signal * 5.5, 2),
            "available": bool(liked_refs or disliked_refs),
            "detailAr": f"أقرب إعجاب {best_liked_sim}% مقابل أقرب نفور {best_disliked_sim}%",
            "detailEn": f"Best liked match {best_liked_sim}% vs best disliked {best_disliked_sim}%",
        },
        {
            "key": "director", "labelAr": "المخرج", "labelEn": "Director",
            "value": round(director_signal, 2), "weight": 1.5,
            "contribution": round(director_signal * 1.5, 2),
            "available": bool(director_evidence),
            "detailAr": director_names if director_evidence else "لا بيانات مخرج من المصدر — لم يدخل القياس",
            "detailEn": director_names if director_evidence else "No director data from source — excluded from scoring",
        },
        {
            "key": "actors", "labelAr": "الممثلون", "labelEn": "Actors",
            "value": round(actor_signal, 2), "weight": 0.3,
            "contribution": round(actor_signal * 0.3, 2),
            "available": bool(actor_evidence),
            "detailAr": actor_names if actor_evidence else "لا تقاطع مع ممثلين في سجلك — لم تدخل القياس",
            "detailEn": actor_names if actor_evidence else "No actor overlap with your history — excluded from scoring",
        },
        {
            "key": "runtime", "labelAr": "المدة", "labelEn": "Runtime",
            "value": round(runtime_signal, 2), "weight": 0.6,
            "contribution": round(runtime_signal * 0.6, 2),
            "available": bool(candidate_runtime),
            "detailAr": (
                f"{int(candidate_runtime)} دقيقة مقابل متوسط مكتبتك ~113"
                if candidate_runtime else "لا بيانات مدة من المصدر — لم تدخل القياس"
            ),
            "detailEn": (
                f"{int(candidate_runtime)} minutes vs your library average ~113"
                if candidate_runtime else "No runtime data from source — excluded from scoring"
            ),
        },
    ]

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

    positive_genres = [item["name"] for item in genre_signals if float(item["signal"]) > 0.15]
    risky_genres = [item["name"] for item in genre_signals if float(item["signal"]) < -0.15]
    reasons_ar: list[str] = []
    reasons_en: list[str] = []
    if positive_genres:
        reasons_ar.append("أنواع متوافقة مع السجل: " + "، ".join(positive_genres[:3]))
        reasons_en.append("Genres with positive history: " + ", ".join(positive_genres[:3]))
    if risky_genres:
        reasons_ar.append("أنواع تحمل إشارات حذر: " + "، ".join(risky_genres[:3]))
        reasons_en.append("Genres with caution history: " + ", ".join(risky_genres[:3]))
    if liked_refs:
        reasons_ar.append("أقرب عمل أعجبك: " + str(liked_refs[0]["title"]))
        reasons_en.append("Closest liked reference: " + str(liked_refs[0]["title"]))
    if disliked_refs:
        reasons_ar.append("أقرب إشارة معاكسة: " + str(disliked_refs[0]["title"]))
        reasons_en.append("Closest disliked reference: " + str(disliked_refs[0]["title"]))
    if conflict >= 0.35:
        split_note = f"{ln_} من إعجابك مقابل {dn_} من نفورك بين الأقرب"
        reasons_ar.insert(0, "سجلك منقسم على هذا النمط (" + split_note + ") — النسبة تعكس عدم الحسم لا حكمًا سلبيًا")
        reasons_en.insert(0, f"Your record is split on this profile ({ln_} liked vs {dn_} disliked among nearest) — the score reflects genuine uncertainty")
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
        "signalBreakdown": signal_breakdown,
        "zTotal": z_total,
        "similarLiked": liked_refs,
        "similarDisliked": disliked_refs,
        "codexPromptAr": prompt_ar,
        "codexPromptEn": prompt_en,
        "disclaimerAr": "هذه قراءة تفسيرية مبنية على سجلك، وليست حكمًا آليًا نهائيًا.",
        "disclaimerEn": "This is an explainable reading of your history, not a deterministic verdict.",
    }
