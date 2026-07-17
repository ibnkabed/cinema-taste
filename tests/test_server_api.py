from __future__ import annotations

import json
import sys
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from cinema_server import CinemaHandler  # noqa: E402


class ServerApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        handler = partial(CinemaHandler, directory=str(ROOT))
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def get_json(self, path: str) -> dict[str, object]:
        with urlopen(self.base_url + path, timeout=5) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def test_status_endpoint(self) -> None:
        payload = self.get_json("/api/status")
        self.assertTrue(payload["ok"])
        self.assertIn("omdbConfigured", payload)

    def test_demo_analysis_requires_no_external_api(self) -> None:
        payload = self.get_json("/api/taste/demo")
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["demo"])
        analysis = payload["analysis"]
        self.assertIn("score", analysis)
        self.assertIn("confidence", analysis)
        self.assertIn("GPT-5.6", analysis["codexPromptEn"])

    def test_supplied_omdb_work_can_be_sent_directly_to_likelihood(self) -> None:
        work = {
            "imdbId": "tt-test",
            "title": "Test Thriller",
            "year": "2026",
            "genres": "Thriller, Mystery",
            "directors": "Test Director",
            "runtime": "112",
            "imdbRating": "7.8",
        }
        request = Request(
            self.base_url + "/api/taste/analyze",
            data=json.dumps({"work": work}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["work"]["imdbId"], "tt-test")
        self.assertIn("score", payload["analysis"])


if __name__ == "__main__":
    unittest.main()
