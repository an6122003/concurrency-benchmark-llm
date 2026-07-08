import unittest
from pathlib import Path

from hardware_ai_benchmark.core.config import BenchmarkConfig, _parse_concurrency


class TestConcurrencyParse(unittest.TestCase):
    def test_range(self):
        self.assertEqual(_parse_concurrency("1-4"), [1, 2, 3, 4])

    def test_list(self):
        self.assertEqual(_parse_concurrency("1,2,5,10"), [1, 2, 5, 10])

    def test_mixed_dedup_sorted(self):
        self.assertEqual(_parse_concurrency("4, 1-3, 2"), [1, 2, 3, 4])


class TestValidation(unittest.TestCase):
    def test_missing_model_is_error(self):
        config = BenchmarkConfig()
        self.assertTrue(any("Model is required" in e for e in config.validate()))

    def test_valid_config_has_no_errors(self):
        config = BenchmarkConfig(model="gemma3:27b")
        self.assertEqual(config.validate(), [])

    def test_bad_url(self):
        config = BenchmarkConfig(model="m", base_url="localhost:1234")
        self.assertTrue(any("http" in e for e in config.validate()))

    def test_bad_concurrency(self):
        config = BenchmarkConfig(model="m", concurrency="abc")
        self.assertTrue(config.validate())

    def test_warnings_for_heavy_settings(self):
        config = BenchmarkConfig(model="m", concurrency="1-16", max_tokens=2048,
                                 context_size=65536, warmup=0)
        warns = "\n".join(config.warnings())
        self.assertIn("16 concurrent users", warns)
        self.assertIn("tokens per request", warns)
        self.assertIn("VRAM", warns)
        self.assertIn("warmup", warns.lower())


class TestPresetsAndArgs(unittest.TestCase):
    def test_all_presets_valid_once_model_set(self):
        for name, preset in BenchmarkConfig.presets().items():
            preset.model = "test-model"
            self.assertEqual(preset.validate(), [], f"preset {name} invalid")
            self.assertTrue(preset.preset_hint)

    def test_cli_args_round_trip(self):
        config = BenchmarkConfig(model="gemma3:27b", quantization="Q4_K_M",
                                 context_size=8192, notes="hello")
        args = config.to_cli_args(Path("/tmp/out"))
        self.assertIn("--model", args)
        self.assertEqual(args[args.index("--model") + 1], "gemma3:27b")
        self.assertEqual(args[args.index("--quantization") + 1], "Q4_K_M")
        self.assertEqual(args[args.index("--context-size") + 1], "8192")
        self.assertEqual(args[args.index("--out-dir") + 1], "/tmp/out")

    def test_app_fields_excluded_from_engine_dict(self):
        data = BenchmarkConfig(model="m").to_dict(include_app_fields=False)
        self.assertNotIn("auto_upload", data)
        self.assertNotIn("user_alias", data)
        self.assertIn("max_tokens", data)

    def test_from_dict_ignores_unknown_keys(self):
        config = BenchmarkConfig.from_dict({"model": "m", "bogus": 1})
        self.assertEqual(config.model, "m")


if __name__ == "__main__":
    unittest.main()
