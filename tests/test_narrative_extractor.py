import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.processing.narrative_extractor import (
    _load_cache,
    _save_cache,
    build_narrative_radar,
    dedupe_candidates,
    enrich_candidates,
    extract_candidates,
    rank_candidates,
)


class NarrativeExtractorTests(unittest.TestCase):
    def test_load_cache_returns_empty_dict_for_corrupted_json(self):
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            cache_path.write_text("{invalid json", encoding="utf-8")

            loaded = _load_cache(cache_path)

            self.assertEqual(loaded, {})

    def test_save_cache_writes_json_atomically(self):
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "openai_cache.json"
            payload = {"k1": [{"narrative": "Inflation pressure building"}]}

            _save_cache(cache_path, payload)

            loaded = _load_cache(cache_path)
            self.assertEqual(loaded, payload)
            tmp_files = list(Path(tmpdir).glob("*.tmp"))
            self.assertEqual(tmp_files, [])

    def test_dedupe_candidates_removes_duplicates(self):
        candidates = [
            {
                "narrative": "Inflation pressure building",
                "macro_factors": ["inflation"],
                "confidence": 0.7,
                "method": "keyword_fallback",
            },
            {
                "narrative": " inflation pressure building ",
                "macro_factors": ["inflation"],
                "confidence": 0.6,
                "method": "keyword_fallback",
            },
        ]

        deduped = dedupe_candidates(candidates)

        self.assertEqual(len(deduped), 1)

    def test_enrich_candidates_adds_support_metrics(self):
        candidates = [
            {
                "narrative": "Inflation pressure building",
                "macro_factors": ["inflation"],
                "confidence": 0.5,
                "method": "keyword_fallback",
            }
        ]
        records = [
            {"title": "Inflation rises", "summary": "CPI hot"},
            {"title": "Inflation stays elevated", "summary": "Bond yields climb"},
            {"title": "Other story", "summary": "No relevant keyword"},
        ]

        enriched = enrich_candidates(candidates, records)

        self.assertEqual(enriched[0]["support_count"], 2)
        self.assertEqual(enriched[0]["support_ratio"], 0.667)
        self.assertEqual(enriched[0]["signal_strength"], 0.334)

    def test_extract_candidates_returns_enriched_candidates(self):
        records = [
            {
                "title": "Credit spreads widen",
                "summary": "Credit stress and liquidity concerns",
                "published": "today",
            }
        ]

        candidates = extract_candidates(
            records=records,
            openai_enabled=False,
            api_key="",
            model="gpt-4.1-mini",
            cache_path="/tmp/unused-cache.json",
        )

        self.assertTrue(candidates)
        self.assertIn("support_count", candidates[0])
        self.assertIn("support_ratio", candidates[0])
        self.assertIn("signal_strength", candidates[0])
        self.assertIn("recurrence_score", candidates[0])
        self.assertIn("factor_alignment_score", candidates[0])
        self.assertIn("capital_expression_score", candidates[0])
        self.assertIn("temporal_coherence_score", candidates[0])
        self.assertIn("narrative_score", candidates[0])
        self.assertIn("lifecycle_tag", candidates[0])
        self.assertIn("macro_alignment", candidates[0])

    def test_rank_candidates_sorts_by_narrative_score_then_confidence(self):
        candidates = [
            {"narrative": "A", "confidence": 0.8, "narrative_score": 0.5},
            {"narrative": "B", "confidence": 0.9, "narrative_score": 0.7},
            {"narrative": "C", "confidence": 0.7, "narrative_score": 0.7},
        ]

        ranked = rank_candidates(candidates)
        self.assertEqual([item["narrative"] for item in ranked], ["B", "C", "A"])

    def test_build_narrative_radar_splits_aligned_and_contradicting(self):
        candidates = [
            {
                "narrative": "Inflation pressure building",
                "macro_factors": ["inflation"],
                "signal_strength": 0.8,
                "narrative_score": 0.7,
                "lifecycle_tag": "green",
                "macro_alignment": "aligned",
                "confidence": 0.8,
                "method": "keyword_fallback",
            },
            {
                "narrative": "Growth scare despite easing",
                "macro_factors": ["growth", "interest_rates"],
                "signal_strength": 0.6,
                "narrative_score": 0.55,
                "lifecycle_tag": "yellow",
                "macro_alignment": "contradicting",
                "confidence": 0.7,
                "method": "keyword_fallback",
            },
        ]

        radar = build_narrative_radar(candidates, top_k=5)

        self.assertEqual(len(radar["short_term_tactical"]["aligned"]), 1)
        self.assertEqual(len(radar["short_term_tactical"]["contradicting"]), 1)
        self.assertEqual(radar["short_term_tactical"]["aligned"][0]["lifecycle_tag"], "green")
        self.assertEqual(radar["short_term_tactical"]["contradicting"][0]["lifecycle_tag"], "yellow")


if __name__ == "__main__":
    unittest.main()
