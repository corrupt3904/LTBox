import json
from pathlib import Path
import tempfile
import unittest

from release_policy import check_tag, compare, version
from render_manifests import render, sidecar_sha256


class PackagingTests(unittest.TestCase):
    def test_stable_versions(self):
        self.assertGreater(version("v3.10.0"), version("3.9.0"))
        for invalid in ["v1.2.3-rc1", "1.2", "01.2.3", "v1.2.3+build"]:
            with self.assertRaises(ValueError):
                version(invalid)

    def test_tag_matches_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Cargo.toml"
            path.write_text('[workspace.package]\nversion = "3.2.8"\n')
            check_tag("v3.2.8", path)
            for invalid in ["v3.2.9", "3.2.8"]:
                with self.assertRaises(ValueError):
                    check_tag(invalid, path)

    def test_all_destinations_reject_downgrades(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, content in [
                ("ltbox.json", '{"version":"3.10.0"}'),
                ("ltbox.rb", '  version "3.10.0"\n'),
                ("Release", "Version: 3.10.0\n"),
            ]:
                path = Path(directory) / name
                path.write_text(content)
                compare("v3.10.0", path)
                compare("v3.11.0", path)
                with self.assertRaises(ValueError):
                    compare("v3.9.0", path)
            path = Path(directory) / "Release"
            path.write_text("invalid")
            with self.assertRaises(ValueError):
                compare("v3.11.0", path)

    def test_sidecars_and_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sidecar = root / "hash"
            valid = "a" * 64 + "  expected.zip\n"
            sidecar.write_text(valid)
            self.assertEqual(sidecar_sha256(sidecar, "expected.zip"), "a" * 64)
            for invalid in [valid * 2, valid.replace("expected", "wrong"), "bad"]:
                sidecar.write_text(invalid)
                with self.assertRaises(ValueError):
                    sidecar_sha256(sidecar, "expected.zip")
            replacements = {"VERSION": "3.2.8", "WIN_X86_64_SHA256": "a" * 64,
                            "WIN_ARM64_SHA256": "b" * 64, "MACOS_UNIVERSAL_SHA256": "c" * 64}
            for source in ["scoop/ltbox.json.tmpl", "homebrew/Casks/ltbox.rb.tmpl"]:
                output = root / Path(source).stem
                render(Path(__file__).parent / source, output, replacements)
                if output.suffix == ".json":
                    self.assertEqual(json.loads(output.read_text())["version"], "3.2.8")
            template = root / "unknown"
            template.write_text("@@UNKNOWN@@")
            with self.assertRaises(ValueError):
                render(template, root / "output", replacements)


if __name__ == "__main__":
    unittest.main()
