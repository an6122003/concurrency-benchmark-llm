import json
import tempfile
import unittest
from pathlib import Path

from hardware_ai_benchmark.core.report_generator import load_engine_results, write_result_files


class TestReportGenerator(unittest.TestCase):
    def test_write_result_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "results.json").write_text(json.dumps({"summaries": []}))
            (out / "report.md").write_text("# hi")
            document = {"result_id": "abc123", "hello": "world"}
            artifacts = write_result_files(out, document)

            self.assertIn("result.json", artifacts)
            self.assertIn("app_metadata.json", artifacts)
            self.assertIn("report.md", artifacts)
            saved = json.loads((out / "result.json").read_text())
            self.assertEqual(saved["result_id"], "abc123")
            metadata = json.loads((out / "app_metadata.json").read_text())
            self.assertEqual(metadata["result_id"], "abc123")
            self.assertIn("results.json", metadata["files"])

    def test_load_engine_results_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(load_engine_results(Path(tmp)))

    def test_load_engine_results_corrupt(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "results.json").write_text("{not json")
            self.assertIsNone(load_engine_results(Path(tmp)))


if __name__ == "__main__":
    unittest.main()
