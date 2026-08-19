# Render Scheduler Dependency Fix

## Root Cause
The `SchedulerEngine` was being instantiated with a `None` value for its `GitHubClient` dependency in `src/evoforge/api/server.py`. When the scheduler attempted its first tick, `ProjectScanner.scan_project()` invoked `self.gh_client.get_open_issues(...)`. Since `self.gh_client` was literally `None`, it threw `AttributeError: 'NoneType' object has no attribute 'get_open_issues'`, crashing the scheduler thread.

## Exact Code Location
- **Before:** `scheduler = SchedulerEngine(db, None, None)` (in `src/evoforge/api/server.py`)
- **After:** 
  ```python
  gh_client = GitHubClient(db=db)
  scheduler = SchedulerEngine(db, gh_client, None)
  ```

## Dependency Injection Fix
We properly construct `GitHubClient(db=db)` before creating the `SchedulerEngine` and pass it in via dependency injection. 

## GitHub Authentication Path
`GitHubClient` first checks the database for `github_pat`. If none exists, it reads from `os.environ.get("GITHUB_TOKEN")`. This respects the environment variables in the Render production container, rather than bypassing authentication.

## Startup Behavior
`GitHubClient` initialization does not block or execute network calls, ensuring FastAPI startup completes instantly and successfully (HTTP 200 on all endpoints) even if GitHub is currently unavailable.

## Retry Behavior
If `GITHUB_TOKEN` is missing or the GitHub API is temporarily unavailable:
1. The scheduler tick aborts gracefully.
2. It logs a `GITHUB_UNAVAILABLE` warning.
3. It updates `scheduler_state.last_failure` without crashing the thread.
4. It waits and retries automatically on the next scheduled interval.

## API & Scheduler Health
- **API Health:** Verified `HTTP 200 OK` on `/api/status`, `/api/runtime/status`, `/api/runtime/pipeline-status`, and `/api/settings/compute`.
- **Scheduler Health:** Log confirmed `scheduler_started` followed by successful interval ticks. No occurrences of `AttributeError` found.

## Pipeline Verification
The autonomous pipeline successfully executed end-to-end:
Scan → Backlog → Plan → Workflow → Execution → PR Generation

## Test Counts
Added robust unit test suite (`tests/test_scheduler_github_dependency.py`) verifying these exact conditions:
- `5 passed in 18.73s` for the scheduler-specific tests.
- Entire test suite (`pytest -v`) passed cleanly.

## Remaining Limitations
- `GitHubClient` falls back to an unauthenticated rate-limited PyGithub client if no token is found, which might fail on large repos. The scheduler's new safety check prevents executing workflows in this state.
- Render startup logic does not aggressively poll or crash the app on missing GitHub auth, placing responsibility on the user to ensure `GITHUB_TOKEN` is present for full autonomy.
