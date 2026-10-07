import json
import unittest
from datetime import datetime, timezone

from xautomation.runner import parse_time, run


def write(path, value):
    path.write_text(json.dumps(value))


class RunnerTests(unittest.TestCase):
    def test_dry_run_selects_only_due_uncompleted_tasks(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            from pathlib import Path

            root = Path(directory)
            plan = root / "plan.json"
            state = root / "state.json"
            write(plan, {"tasks": [
                {"id": "due", "run_at": "2026-01-01T00:00:00Z", "action": "x_post", "payload": {"text": "Hello"}},
                {"id": "later", "run_at": "2027-01-01T00:00:00Z", "action": "x_post", "payload": {"text": "Later"}},
                {"id": "done", "run_at": "2026-01-01T00:00:00Z", "action": "x_post", "payload": {"text": "Done"}},
            ]})
            write(state, {"completed": {"done": {}}})
            result = run(plan, state, datetime(2026, 6, 1, tzinfo=timezone.utc), True)
            self.assertEqual(result, 0)

    def test_duplicate_ids_are_rejected(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory() as directory:
            plan = Path(directory) / "plan.json"
            write(plan, {"tasks": [
                {"id": "same", "run_at": "2026-01-01T00:00:00Z", "action": "x_post"},
                {"id": "same", "run_at": "2026-01-02T00:00:00Z", "action": "x_post"},
            ]})
            with self.assertRaisesRegex(ValueError, "unique"):
                run(plan, Path(directory) / "state.json", datetime.now(timezone.utc), True)

    def test_time_requires_timezone(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            parse_time("2026-01-01T00:00:00")

