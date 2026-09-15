import json
from pathlib import Path
import unittest

from stage_root_test import select_executable


class RootArtifactTests(unittest.TestCase):
    def artifact(self, path="test-binary", test=True, name="ltbox_patch"):
        return json.dumps({"reason": "compiler-artifact", "target": {"name": name},
                           "profile": {"test": test}, "executable": path})

    def test_selects_only_current_test_artifact(self):
        lines = [self.artifact(test=False), self.artifact(name="other"),
                 json.dumps({"reason": "build-finished", "success": True}), self.artifact()]
        self.assertEqual(select_executable(lines), Path("test-binary"))

    def test_missing_or_ambiguous_artifacts_fail(self):
        for lines in [[], [self.artifact(path=None)],
                      [self.artifact(), self.artifact(path="another")]]:
            with self.assertRaises(ValueError):
                select_executable(lines)


if __name__ == "__main__":
    unittest.main()
