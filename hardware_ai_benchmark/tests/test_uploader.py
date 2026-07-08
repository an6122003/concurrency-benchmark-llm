import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from hardware_ai_benchmark.core import uploader as uploader_module
from hardware_ai_benchmark.core.uploader import (
    MockUploader, sanitize_for_upload, upload_preview, retry_pending,
)

DOCUMENT = {
    "result_id": "r1",
    "status": "completed",
    "user_alias": None,
    "platform": {"os": "Darwin", "arch": "arm64", "python": "3.12"},
    "system": {
        "cpu": {"processor": "Test CPU"},
        "gpu": {"detected": [{"name": "Test GPU", "pnp_device_id": "PCI\\VEN_1002"}]},
    },
    "config": {
        "base_url": "http://192.168.1.50:1234",
        "model": "test-model",
        "out_dir": "/Users/alice/Documents/run-1",
    },
    "model": {"name": "test-model"},
    "results": {"summaries": [{"concurrency": 1}]},
    "notes": "logs at /Users/alice/secret and C:\\Users\\alice\\stuff",
}


class TestSanitize(unittest.TestCase):
    def test_private_keys_removed(self):
        payload = sanitize_for_upload(DOCUMENT)
        self.assertNotIn("base_url", payload["config"])
        self.assertNotIn("out_dir", payload["config"])
        self.assertNotIn("pnp_device_id", payload["system"]["gpu"]["detected"][0])

    def test_home_paths_scrubbed(self):
        payload = sanitize_for_upload(DOCUMENT)
        self.assertNotIn("alice", json.dumps(payload))

    def test_original_untouched(self):
        sanitize_for_upload(DOCUMENT)
        self.assertIn("base_url", DOCUMENT["config"])

    def test_metadata_withheld_mode(self):
        payload = sanitize_for_upload(DOCUMENT, include_system_metadata=False)
        self.assertEqual(payload["system"], {"withheld": True})
        self.assertEqual(payload["platform"], {"os": "Darwin", "arch": "arm64"})

    def test_preview_mentions_gpu_and_anonymity(self):
        text = "\n".join(upload_preview(sanitize_for_upload(DOCUMENT)))
        self.assertIn("Test GPU", text)
        self.assertIn("anonymous", text)


class TestMockUploaderAndRetry(unittest.TestCase):
    def test_mock_upload_writes_outbox_and_retry_lists_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(uploader_module, "outbox_dir", return_value=Path(tmp)):
                result = MockUploader().upload(sanitize_for_upload(DOCUMENT))
                self.assertTrue(result.ok)
                self.assertTrue(result.saved_to.exists())

                results = retry_pending(MockUploader())
                self.assertEqual(len(results), 1)
                self.assertTrue(results[0].ok)
                # mock retries never delete the outbox entry
                self.assertTrue(result.saved_to.exists())


if __name__ == "__main__":
    unittest.main()
