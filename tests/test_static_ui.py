from __future__ import annotations

import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "الذائقة السينمائية.html"
STANDALONE = ROOT / "البحث والتنزيل.html"
CSS = ROOT / "assets" / "cinema.css"
JS = ROOT / "assets" / "cinema.js"
I18N = ROOT / "assets" / "i18n.js"


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name == "id" and value:
                self.ids.append(value)


class StaticUiTests(unittest.TestCase):
    def test_main_page_has_unique_ids_and_analysis_controls(self) -> None:
        parser = IdCollector()
        parser.feed(MAIN.read_text(encoding="utf-8"))
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        for required in (
            "discovery-search-form",
            "discovery-demo-button",
            "discovery-results",
            "discovery-analysis",
            "copy-prompt-ar",
            "copy-prompt-en",
        ):
            self.assertIn(required, parser.ids)

    def test_contest_ui_has_no_removed_download_sites_or_vpn_prompt(self) -> None:
        visible_sources = "\n".join(
            path.read_text(encoding="utf-8") for path in (MAIN, STANDALONE, CSS)
        ).lower()
        for forbidden in ("1337x", "thepiratebay", "the pirate bay", "vpn", "vpnpulse"):
            self.assertNotIn(forbidden, visible_sources)

    def test_requested_section_name_is_visible(self) -> None:
        html = MAIN.read_text(encoding="utf-8")
        self.assertGreaterEqual(html.count("البحث عن أعمال جديدة"), 4)

    def test_likelihood_is_a_separate_view(self) -> None:
        html = MAIN.read_text(encoding="utf-8")
        self.assertIn('data-view="predict"', html)
        self.assertIn('id="view-predict" data-page="predict"', html)
        self.assertIn('id="view-search" data-page="search"', html)
        self.assertIn('id="predict-from-add-btn"', html)

    def test_complete_bilingual_interface_contract(self) -> None:
        html = MAIN.read_text(encoding="utf-8")
        standalone = STANDALONE.read_text(encoding="utf-8")
        behavior = JS.read_text(encoding="utf-8")
        translations = I18N.read_text(encoding="utf-8")
        for page in (html, standalone):
            self.assertIn('data-language-option="ar"', page)
            self.assertIn('data-language-option="en"', page)
            self.assertIn("assets/i18n.js", page)
        self.assertIn("cinema-languagechange", behavior)
        self.assertIn("analysis.verdictEn", behavior)
        self.assertIn("analysis.reasonsEn", behavior)
        self.assertIn("sessionEnglish", behavior)
        self.assertIn("localStorage.getItem('cinema-language')", translations)
        self.assertIn("document.documentElement.dir", translations)
        self.assertIn("Discover New Titles", translations)


if __name__ == "__main__":
    unittest.main()
