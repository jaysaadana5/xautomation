from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .actions import ACTIONS, ActionError


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("run_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def run(plan_path: Path, state_path: Path, now: datetime, dry_run: bool) -> int:
    plan = load_json(plan_path, {"tasks": []})
    state = load_json(state_path, {"completed": {}})
    completed = state.setdefault("completed", {})
    tasks = plan.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("plan.tasks must be a list")

    due = []
    seen = set()
    for task in tasks:
        task_id = task.get("id")
        if not task_id or task_id in seen:
            raise ValueError("Every task needs a unique, non-empty id")
        seen.add(task_id)
        if task_id not in completed and parse_time(task["run_at"]) <= now:
            due.append(task)

    print(f"Found {len(due)} due task(s)")
    failed = False
    for task in due:
        task_id = task["id"]
        action_name = task.get("action")
        action = ACTIONS.get(action_name)
        if action is None:
            print(f"ERROR {task_id}: unknown action {action_name!r}", file=sys.stderr)
            failed = True
            continue
        if dry_run:
            print(f"DRY RUN {task_id}: {action_name}")
            continue
        try:
            result = action.run(task.get("payload", {}))
            completed[task_id] = {
                "completed_at": now.isoformat(),
                "result": result,
            }
            state_path.parent.mkdir(parents=True, exist_ok=True)
            temp = state_path.with_suffix(".tmp")
            temp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
            temp.replace(state_path)
            print(f"DONE {task_id}: {action_name}")
        except (ActionError, OSError, ValueError) as exc:
            print(f"ERROR {task_id}: {exc}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, default=Path("automation-plan.json"))
    parser.add_argument("--state", type=Path, default=Path("automation-state.json"))
    parser.add_argument(
        "--dry-run", action="store_true", default=os.environ.get("DRY_RUN") == "1"
    )
    args = parser.parse_args()
    return run(args.plan, args.state, datetime.now(timezone.utc), args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())

