# Contributing

Thank you for helping maintain the `development` branch. This file gives the minimum steps to get set up, follow local checks, and submit pull requests.

## Local setup

- Create and activate a Python virtualenv:
  - `python -m venv .venv`
  - `source .venv/bin/activate` (Unix) or `.\.venv\Scripts\Activate.ps1` (PowerShell)
- Install dependencies: `pip install -r requirements_dev.txt`

## Pre-commit hooks (recommended)

- Install and enable hooks: `pip install pre-commit && pre-commit install`
- Run all hooks manually before a PR: `pre-commit run --all-files`
- If a hook blocks a commit you can fix issues locally or (not recommended) skip with `git commit --no-verify`.

Notes: Hooks include linting (ruff), type checks (mypy), doc coverage (interrogate), and gitlint for Conventional Commits.

## Tests

- Run tests: `python -m pytest -q`
- Coverage is enforced in CI; aim to keep component coverage high (project currently expects full coverage).

## Branching & PR workflow

- Base development work on feature branches off `development`: `git checkout -b feat/your-feature development`.
- Open PRs into `development`. After review and passing checks, `development` is used for upstream merges to `main`.
- Commit messages should follow Conventional Commits (e.g., `Feat: add widget`, `Fix: handle ics content-type`). `.gitlint` enforces this.

## Pull request checklist

- Describe the change and link any issue.
- Run `pre-commit` and tests locally.
- Include screenshots/logs if relevant.
- Wait for CI checks: Gitlint, hassfest, pytest/coverage, and security scans.

If you need help, ping `cheezzz` (repo lead) on GitHub.

