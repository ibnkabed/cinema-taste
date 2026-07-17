from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from taste_engine import analyze_candidate  # noqa: E402


LIKED = [
    {"Title": "Tense One", "Year": "2024", "Genres": "Thriller, Mystery", "Directors": "A Director", "Runtime (mins)": "105", "Your Rating": "9", "Title Type": "Movie"},
    {"Title": "Dark Route", "Year": "2022", "Genres": "Crime, Thriller", "Directors": "B Director", "Runtime (mins)": "112", "Your Rating": "8", "Title Type": "Movie"},
    {"Title": "Mystery Room", "Year": "2020", "Genres": "Mystery, Horror", "Directors": "A Director", "Runtime (mins)": "98", "Your Rating": "9", "Title Type": "Movie"},
]

DISLIKED = [
    {"Title": "Singing Days", "Year": "2021", "Genres": "Musical, Romance", "Directors": "C Director", "Runtime (mins)": "140", "Title Type": "Movie"},
    {"Title": "Old Biography", "Year": "2019", "Genres": "Biography, History", "Directors": "D Director", "Runtime (mins)": "155", "Title Type": "Movie"},
]


class TasteEngineTests(unittest.TestCase):
    def test_positive_history_scores_above_caution_history(self) -> None:
        thriller = analyze_candidate(
            {"title": "New Mystery", "year": "2026", "genres": "Thriller, Mystery", "directors": "A Director", "runtime": "108", "titleType": "Movie"},
            LIKED,
            DISLIKED,
        )
        musical = analyze_candidate(
            {"title": "New Musical", "year": "2026", "genres": "Musical, Romance", "directors": "C Director", "runtime": "145", "titleType": "Movie"},
            LIKED,
            DISLIKED,
        )
        self.assertGreater(thriller["score"], musical["score"])
        self.assertGreater(thriller["confidence"], 25)

    def test_analysis_is_explainable_and_prompt_ready(self) -> None:
        result = analyze_candidate(
            {"title": "Explain Me", "year": "2026", "genres": "Thriller, Mystery", "directors": "A Director", "runtime": "106", "titleType": "Movie"},
            LIKED,
            DISLIKED,
        )
        self.assertTrue(result["similarLiked"])
        self.assertTrue(result["genreSignals"])
        self.assertIn("GPT-5.6", result["codexPromptEn"])
        self.assertIn("Explain Me", result["codexPromptEn"])
        self.assertIn("not a deterministic", result["disclaimerEn"])

    def test_empty_history_stays_uncertain(self) -> None:
        result = analyze_candidate(
            {"title": "Unknown", "genres": "Drama", "runtime": "110"}, [], []
        )
        self.assertEqual(result["score"], 50)
        self.assertEqual(result["confidence"], 25)
        self.assertEqual(result["verdictKey"], "uncertain")


if __name__ == "__main__":
    unittest.main()

