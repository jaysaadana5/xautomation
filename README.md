# X Automation

This repository runs scheduled tasks in GitHub Actions, independently of any laptop. Every 15 minutes it checks `automation-plan.json`, executes due tasks, and records successful task IDs in `automation-state.json` to avoid normal rerun duplicates.

## Supported actions

- `x_post`: publishes a text post through X API v2 using OAuth 1.0a.
- `webhook`: sends a JSON body to an HTTPS endpoint for another cloud task.

## Add a task

Times must include a timezone. UTC (`Z`) is recommended.

```json
{
  "tasks": [
    {
      "id": "launch-message-2026-10-10",
      "run_at": "2026-10-10T04:30:00Z",
      "action": "x_post",
      "payload": {"text": "Your post text"}
    }
  ]
}
```

Commit and push the plan. Do not put credentials or private webhook tokens in it.

## Required GitHub secrets

For X posts, create a project/app in the official X developer portal with read/write permission, then add these repository Actions secrets:

- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

For webhook tasks, add `AUTOMATION_WEBHOOK_URL` and, if required, `AUTOMATION_WEBHOOK_TOKEN`.

Enable Actions for the repository. The workflow has `contents: write` so it can commit successful task state. You can also run **Cloud automation** manually with dry-run enabled.

## Local validation

```bash
PYTHONPATH=src python -m unittest discover -s tests
PYTHONPATH=src python -m xautomation.runner --dry-run
```

## Reliability boundary

The state commit prevents ordinary duplicate runs, and workflow concurrency prevents simultaneous workers. There is still a narrow failure window if an external action succeeds but GitHub becomes unavailable before state is committed. Workflows requiring strict exactly-once delivery should use a durable transactional job service/database instead of repository state.
