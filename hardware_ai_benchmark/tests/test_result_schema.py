import json
import unittest
from pathlib import Path

from hardware_ai_benchmark.core.config import BenchmarkConfig
from hardware_ai_benchmark.core.result_schema import build_result, validate_result, _derive_scores

REPO = Path(__file__).resolve().parents[2]
REAL_RESULTS = REPO / "benchmark-results-20260630-014501" / "results.json"

SYSTEM_INFO = {
    "platform": {"os": "Darwin", "arch": "arm64", "python": "3.12"},
    "cpu": {"processor": "Test CPU"},
    "memory": {"total_human": "32 GB"},
    "gpu": {"detected": [{"name": "Test GPU", "vram_total_human": "24 GB"}]},
    "backends": [{"name": "Metal", "available": True}],
}


def make_document(status="completed", engine_results=None):
    if engine_results is None and REAL_RESULTS.exists():
        engine_results = json.loads(REAL_RESULTS.read_text(encoding="utf-8"))
    config = BenchmarkConfig(model="google/gemma-4-26b-a4b", user_alias="tester")
    return build_result(config, SYSTEM_INFO, engine_results, status=status)


class TestSchema(unittest.TestCase):
    def test_completed_document_is_valid(self):
        document = make_document()
        self.assertEqual(validate_result(document), [])

    def test_checksum_detects_tampering(self):
        document = make_document()
        document["results"]["derived"]["peak_aggregate_tps"] = 99999
        problems = validate_result(document)
        self.assertTrue(any("checksum" in p for p in problems))

    def test_status_must_be_known(self):
        document = make_document()
        document["status"] = "exploded"
        # recompute checksum so only the status rule fires
        from hardware_ai_benchmark.core.result_schema import _checksum
        document["checksum"] = _checksum(document)
        problems = validate_result(document)
        self.assertTrue(any("status" in p for p in problems), problems)

    def test_completed_requires_summaries(self):
        document = make_document(engine_results={"summaries": []})
        from hardware_ai_benchmark.core.result_schema import _checksum
        document["checksum"] = _checksum(document)
        self.assertTrue(any("summaries" in p for p in validate_result(document)))

    def test_failed_run_without_summaries_is_valid(self):
        document = make_document(status="failed", engine_results=None)
        self.assertEqual(validate_result(document), [])

    def test_derived_scores_from_real_run(self):
        if not REAL_RESULTS.exists():
            self.skipTest("real results fixture not present")
        summaries = json.loads(REAL_RESULTS.read_text())["summaries"]
        derived = _derive_scores(summaries)
        self.assertAlmostEqual(derived["peak_aggregate_tps"], 156.1, places=1)
        self.assertEqual(derived["best_concurrency"], 2)
        # users=2 still has TTFT 2.3s <= 3s and 78 tok/s per user; users=3 TTFT 13.8s
        self.assertEqual(derived["comfortable_users"], 2)


if __name__ == "__main__":
    unittest.main()
