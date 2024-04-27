import re
import unittest
from pathlib import Path

import yaml


class CheckAdditionalDepsTestCase(unittest.TestCase):
    def test_additional_deps_represented(self):
        data = yaml.load(Path(".pre-commit-config.yaml").read_text(), yaml.Loader)
        additional = [
            dep
            for repo in data["repos"]
            for hook in repo["hooks"]
            for dep in hook.get("additional_dependencies", [])
        ]
        required = sorted(
            set(
                dep
                for path in Path.cwd().glob("*requirements.txt")
                for dep in path.read_text().splitlines()
                if dep and not re.match(r"^[ #]+", dep)
            )
        )
        for a in additional:
            with self.subTest(dep=a):
                self.assertIn(a, required)


if __name__ == "__main__":
    unittest.main()
