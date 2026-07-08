import unittest

from hardware_ai_benchmark.core.system_detect import (
    detect_platform, detect_backends, detect_all, summarize_for_display,
)


class TestSystemDetect(unittest.TestCase):
    def test_platform_fields(self):
        info = detect_platform()
        for key in ("os", "arch", "python", "os_release"):
            self.assertIn(key, info)
        self.assertTrue(info["os"])
        self.assertTrue(info["arch"])

    def test_backends_shape(self):
        backends = detect_backends()
        self.assertTrue(backends)
        for backend in backends:
            self.assertIn("name", backend)
            self.assertIn("available", backend)

    def test_detect_all_never_raises_and_summarizes(self):
        info = detect_all(extended=True)
        rows = summarize_for_display(info)
        labels = [label for label, _ in rows]
        self.assertIn("CPU", labels)
        self.assertIn("GPU", labels)
        self.assertIn("Available backends", labels)


if __name__ == "__main__":
    unittest.main()
