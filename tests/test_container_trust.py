"""Container trust regression checks; run directly with Python's stdlib."""
import unittest
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ContainerTrustTests(unittest.TestCase):
    def test_installer_uses_current_trust(self):
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertIn("ghcr.io/astral-sh/uv:0.13.4", dockerfile)
        self.assertIn("certifi==2026.10.19", dockerfile)
        self.assertIn("refresh_ca_trust.py", dockerfile)

    def test_rebuild_removes_old_anchors_and_creates_hashes(self):
        spec = importlib.util.spec_from_file_location("ca_trust", ROOT / "scripts/refresh_ca_trust.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        bundle = (ROOT / "tests/fixtures/root.pem").read_text()
        with tempfile.TemporaryDirectory() as temporary:
            store = Path(temporary) / "certs"
            store.mkdir()
            (store / "distrusted.pem").write_text("old anchor")
            module.rebuild_ca_store(bundle, store)
            self.assertFalse((store / "distrusted.pem").exists())
            self.assertEqual((store / "ca-certificates.crt").read_text(), bundle)
            self.assertTrue(list(store.glob("*.0")))
            with self.assertRaises(ValueError):
                module.rebuild_ca_store("", store)
            self.assertTrue((store / "ca-certificates.crt").exists())


if __name__ == "__main__":
    unittest.main()
