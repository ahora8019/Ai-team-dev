import tempfile
import unittest
from pathlib import Path
from ai_team.run_state import RunRecord, RunStore, redact

class RunStateTests(unittest.TestCase):
    def test_lifecycle_and_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RunStore(Path(directory) / "runs" / "run.json")
            run = RunRecord.create("TASK-1", "mock", max_attempts=2)
            run.transition("running")
            run.transition("failed", exit_code=1, error_summary="temporary error")
            store.save(run)
            loaded = store.load()
            self.assertEqual((loaded.run_id, loaded.status, loaded.attempt, loaded.exit_code),
                             (run.run_id, "failed", 1, 1))

    def test_terminal_status_cannot_restart(self):
        run = RunRecord.create("TASK-2", "mock")
        run.transition("skipped")
        with self.assertRaisesRegex(ValueError, "invalid run transition"):
            run.transition("running")

    def test_attempts_are_bounded(self):
        run = RunRecord.create("TASK-3", "mock", max_attempts=1)
        run.transition("running")
        run.transition("failed")
        with self.assertRaisesRegex(ValueError, "invalid run transition"):
            run.transition("running")

    def test_secret_redaction(self):
        value = redact("failed with api_key=abc123secret and Bearer abcdefghijklmnopqrstuvwxyz")
        self.assertNotIn("abc123secret", value)
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz", value)
        self.assertIn("[REDACTED]", value)

    def test_invalid_attempt_limit(self):
        with self.assertRaises(ValueError):
            RunRecord.create("TASK-4", "mock", max_attempts=0)

if __name__ == "__main__":
    unittest.main()
