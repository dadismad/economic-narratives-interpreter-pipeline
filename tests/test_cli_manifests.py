import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.cli import run_extract, run_ingest
from src.config import Settings


class CliManifestTests(unittest.TestCase):
    @patch("src.cli.fetch_fred_series")
    @patch("src.cli.load_settings")
    def test_run_ingest_writes_manifest_with_partial_success(self, mock_load_settings, mock_fetch_fred_series):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_load_settings.return_value = Settings(
                data_dir=tmpdir,
                fred_api_key="",
                fred_series_ids=["OK_SERIES", "FAIL_SERIES"],
                rss_urls=[],
                openai_api_key="",
                openai_model="gpt-4.1-mini",
                openai_enabled=False,
                openai_max_items=25,
            )

            def side_effect(series_id, api_key=""):
                if series_id == "FAIL_SERIES":
                    raise RuntimeError("upstream unavailable")
                return [
                    {
                        "source": "fred",
                        "series_id": series_id,
                        "date": "2024-01-01",
                        "value": 1.0,
                        "ingested_at": "2024-01-01T00:00:00+00:00",
                    }
                ]

            mock_fetch_fred_series.side_effect = side_effect

            run_ingest(source="fred")

            run_dir = Path(tmpdir) / "runs" / "ingest"
            manifests = sorted(run_dir.glob("*.json"))
            self.assertEqual(len(manifests), 1)
            payload = json.loads(manifests[0].read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "partial_success")
            self.assertEqual(payload["sources"]["fred"]["rows"], 1)
            self.assertEqual(len(payload["sources"]["fred"]["errors"]), 1)

    @patch("src.cli.extract_candidates")
    @patch("src.cli.load_settings")
    def test_run_extract_writes_manifest(self, mock_load_settings, mock_extract_candidates):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_load_settings.return_value = Settings(
                data_dir=tmpdir,
                fred_api_key="",
                fred_series_ids=["CPIAUCSL"],
                rss_urls=["https://example.com/feed.xml"],
                openai_api_key="",
                openai_model="gpt-4.1-mini",
                openai_enabled=False,
                openai_max_items=25,
            )
            raw_dir = Path(tmpdir) / "raw" / "rss"
            raw_dir.mkdir(parents=True, exist_ok=True)
            raw_file = raw_dir / "input.jsonl"
            raw_file.write_text(
                '{"source":"rss","feed_url":"https://example.com/feed.xml","title":"Inflation","link":"https://example.com/1","published":"today","summary":"rising","ingested_at":"2024-01-01T00:00:00+00:00"}\n',
                encoding="utf-8",
            )

            mock_extract_candidates.return_value = [
                {
                    "narrative": "Inflation pressure building",
                    "macro_factors": ["inflation"],
                    "confidence": 0.7,
                    "method": "keyword_fallback",
                    "support_count": 1,
                    "support_ratio": 1.0,
                    "signal_strength": 0.7,
                    "narrative_score": 0.6,
                    "lifecycle_tag": "green",
                    "macro_alignment": "aligned",
                }
            ]

            run_extract(str(raw_file))

            run_dir = Path(tmpdir) / "runs" / "extract"
            manifests = sorted(run_dir.glob("*.json"))
            self.assertEqual(len(manifests), 1)
            payload = json.loads(manifests[0].read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "success")
            self.assertEqual(payload["input_rows"], 1)
            self.assertEqual(payload["valid_input_rows"], 1)
            self.assertEqual(payload["invalid_input_rows"], 0)
            self.assertEqual(payload["output_rows"], 1)
            self.assertEqual(payload["method"], "keyword_fallback")
            self.assertIn("radar_output_path", payload)
            self.assertEqual(payload["radar_counts"]["aligned"], 1)
            self.assertEqual(payload["radar_counts"]["contradicting"], 0)

            radar_path = Path(payload["radar_output_path"])
            self.assertTrue(radar_path.exists())
            radar_payload = json.loads(radar_path.read_text(encoding="utf-8"))
            self.assertIn("short_term_tactical", radar_payload)
            self.assertEqual(len(radar_payload["short_term_tactical"]["aligned"]), 1)

    @patch("src.cli.extract_candidates")
    @patch("src.cli.load_settings")
    def test_run_extract_marks_partial_success_when_invalid_rows_present(
        self, mock_load_settings, mock_extract_candidates
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_load_settings.return_value = Settings(
                data_dir=tmpdir,
                fred_api_key="",
                fred_series_ids=["CPIAUCSL"],
                rss_urls=["https://example.com/feed.xml"],
                openai_api_key="",
                openai_model="gpt-4.1-mini",
                openai_enabled=False,
                openai_max_items=25,
            )
            raw_dir = Path(tmpdir) / "raw" / "rss"
            raw_dir.mkdir(parents=True, exist_ok=True)
            raw_file = raw_dir / "input.jsonl"
            raw_file.write_text(
                "\n".join(
                    [
                        '{"source":"rss","feed_url":"https://example.com/feed.xml","title":"Inflation","link":"https://example.com/1","published":"today","summary":"rising","ingested_at":"2024-01-01T00:00:00+00:00"}',
                        '{"source":"rss","feed_url":"https://example.com/feed.xml","title":"Missing link","published":"today","summary":"bad","ingested_at":"2024-01-01T00:00:00+00:00"}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            mock_extract_candidates.return_value = []

            run_extract(str(raw_file))

            run_dir = Path(tmpdir) / "runs" / "extract"
            manifests = sorted(run_dir.glob("*.json"))
            payload = json.loads(manifests[0].read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "partial_success")
            self.assertEqual(payload["input_rows"], 2)
            self.assertEqual(payload["valid_input_rows"], 1)
            self.assertEqual(payload["invalid_input_rows"], 1)
            self.assertEqual(len(payload["input_errors"]), 1)

    @patch("src.cli.extract_candidates")
    @patch("src.cli.load_settings")
    def test_run_extract_handles_malformed_json_lines_as_partial_success(
        self, mock_load_settings, mock_extract_candidates
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_load_settings.return_value = Settings(
                data_dir=tmpdir,
                fred_api_key="",
                fred_series_ids=["CPIAUCSL"],
                rss_urls=["https://example.com/feed.xml"],
                openai_api_key="",
                openai_model="gpt-4.1-mini",
                openai_enabled=False,
                openai_max_items=25,
            )
            raw_dir = Path(tmpdir) / "raw" / "rss"
            raw_dir.mkdir(parents=True, exist_ok=True)
            raw_file = raw_dir / "input.jsonl"
            raw_file.write_text(
                "\n".join(
                    [
                        '{"source":"rss","feed_url":"https://example.com/feed.xml","title":"Inflation","link":"https://example.com/1","published":"today","summary":"rising","ingested_at":"2024-01-01T00:00:00+00:00"}',
                        '{"source":"rss","feed_url":"https://example.com/feed.xml",',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            mock_extract_candidates.return_value = []

            run_extract(str(raw_file))

            run_dir = Path(tmpdir) / "runs" / "extract"
            manifests = sorted(run_dir.glob("*.json"))
            payload = json.loads(manifests[0].read_text(encoding="utf-8"))

            self.assertEqual(payload["status"], "partial_success")
            self.assertEqual(payload["input_rows"], 2)
            self.assertEqual(payload["valid_input_rows"], 1)
            self.assertEqual(payload["invalid_input_rows"], 1)
            self.assertEqual(payload["input_errors"][0]["line"], 2)
            self.assertIn("Malformed JSON", payload["input_errors"][0]["error"])


if __name__ == "__main__":
    unittest.main()
