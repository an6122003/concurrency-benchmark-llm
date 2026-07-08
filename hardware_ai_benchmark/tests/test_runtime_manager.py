import unittest
from pathlib import Path

from hardware_ai_benchmark.core import model_catalog, runtime_manager


class AssetSelectionTests(unittest.TestCase):
    def test_macos_arm(self):
        self.assertEqual(runtime_manager.asset_name("b9916", "darwin", "arm64"),
                         "llama-b9916-bin-macos-arm64.tar.gz")

    def test_macos_intel(self):
        self.assertEqual(runtime_manager.asset_name("b9916", "darwin", "x86_64"),
                         "llama-b9916-bin-macos-x64.tar.gz")

    def test_windows_prefers_vulkan(self):
        self.assertEqual(runtime_manager.asset_name("b9916", "win32", "amd64", vulkan=True),
                         "llama-b9916-bin-win-vulkan-x64.zip")

    def test_windows_cpu_fallback(self):
        self.assertEqual(runtime_manager.asset_name("b9916", "win32", "amd64", vulkan=False),
                         "llama-b9916-bin-win-cpu-x64.zip")

    def test_windows_arm(self):
        self.assertEqual(runtime_manager.asset_name("b9916", "win32", "arm64", vulkan=True),
                         "llama-b9916-bin-win-cpu-arm64.zip")

    def test_linux_vulkan_and_cpu(self):
        self.assertEqual(runtime_manager.asset_name("b9916", "linux", "x86_64", vulkan=True),
                         "llama-b9916-bin-ubuntu-vulkan-x64.tar.gz")
        self.assertEqual(runtime_manager.asset_name("b9916", "linux", "x86_64", vulkan=False),
                         "llama-b9916-bin-ubuntu-x64.tar.gz")

    def test_linux_arm(self):
        self.assertEqual(runtime_manager.asset_name("b9916", "linux", "aarch64", vulkan=False),
                         "llama-b9916-bin-ubuntu-arm64.tar.gz")


class ManagedServerTests(unittest.TestCase):
    def test_command_shape(self):
        server = runtime_manager.ManagedServer(Path("/models/test.gguf"),
                                               context_per_slot=4096, parallel=4)
        command = server.command(Path("/runtime/llama-server"))
        self.assertIn("--parallel", command)
        self.assertEqual(command[command.index("--parallel") + 1], "4")
        self.assertEqual(command[command.index("--ctx-size") + 1], str(4096 * 4))
        self.assertIn("--no-webui", command)
        self.assertIn(str(server.port), command)

    def test_parallel_is_clamped(self):
        server = runtime_manager.ManagedServer(Path("x.gguf"), parallel=32)
        self.assertEqual(server.parallel, 8)
        server = runtime_manager.ManagedServer(Path("x.gguf"), parallel=0)
        self.assertEqual(server.parallel, 1)

    def test_start_without_install_raises(self):
        server = runtime_manager.ManagedServer(Path("definitely-missing.gguf"))
        if not runtime_manager.is_installed():
            with self.assertRaises(OSError):
                server.start()


class CatalogTests(unittest.TestCase):
    def test_catalog_integrity(self):
        keys = set()
        for model in model_catalog.CATALOG:
            self.assertNotIn(model.key, keys)
            keys.add(model.key)
            self.assertTrue(model.url.startswith("https://huggingface.co/"))
            self.assertTrue(model.filename.endswith(".gguf"))
            self.assertTrue(model.url.endswith(model.filename))
            self.assertGreater(model.size_mb, 0)
            self.assertGreater(model.min_ram_gb, 0)

    def test_catalog_is_sorted_small_to_large(self):
        sizes = [m.size_mb for m in model_catalog.CATALOG]
        self.assertEqual(sizes, sorted(sizes))

    def test_fit_hint(self):
        big = model_catalog.by_key("qwen3-14b")
        self.assertIn("too big", model_catalog.fit_hint(big, 8))
        self.assertIn("tight", model_catalog.fit_hint(big, 20))
        self.assertEqual(model_catalog.fit_hint(big, 64), "")
        self.assertEqual(model_catalog.fit_hint(big, None), "")


if __name__ == "__main__":
    unittest.main()
