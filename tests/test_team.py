import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
TEAM_SCRIPT = SOURCE_ROOT / "team.py"


class TeamCliSmokeTests(unittest.TestCase):
    def run_cli(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(root / "team.py"), *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        shutil.copy2(TEAM_SCRIPT, self.root / "team.py")
        (self.root / "tasks").mkdir()
        shutil.copy2(SOURCE_ROOT / "tasks" / "current-task.md", self.root / "tasks" / "current-task.md")
        (self.root / "reports").mkdir()
        (self.root / "decisions").mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_status_returns_success(self) -> None:
        result = self.run_cli(self.root, "status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Coordinator mode: file-based", result.stdout)

    def test_prompt_includes_role_and_task(self) -> None:
        result = self.run_cli(self.root, "prompt", "--role", "reviewer")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Reviewer brief", result.stdout)
        self.assertIn("Bootstrap the multi-agent coding workspace", result.stdout)

    def test_new_task_refuses_to_overwrite_by_default(self) -> None:
        result = self.run_cli(self.root, "new-task", "Second task")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)


if __name__ == "__main__":
    unittest.main()
