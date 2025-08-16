# Repository Guidelines

## Project Structure & Module Organization
- **Source:** `custom_components/rental_control/` contains the Home Assistant integration (calendar, sensor, coordinator, util, manifest).  
- **Config & metadata:** `manifest.json`, `strings.json`, `translations/`.  
- **Dev deps & scripts:** `requirements_dev.txt`, `requirements_test.txt`, `validate_ical.py`.

## Build, Test, and Development Commands
- Create venv: `python -m venv .venv` then `source .venv/bin/activate`.  
- Install dev deps: `pip install -r requirements_dev.txt`.  
- Run linters/formatters: `pre-commit run --all-files` (hooks run `ruff`, `mypy`, `yamllint`, etc.).  
- Run tests: `pytest` (configured to run coverage over `custom_components.rental_control`).

## Coding Style & Naming Conventions
- **Indentation:** 4 spaces.  
- **Line length:** 88 characters (Black-compatible).  
- **Imports:** `isort` profile `black` (see `setup.cfg`).  
- **Type hints:** Use mypy-compatible annotations; run `mypy` via pre-commit.
- **Files:** keep platform modules under `custom_components/rental_control/` and follow existing naming (`sensor.py`, `calendar.py`).

## Testing Guidelines
- **Framework:** `pytest`.  
- **Coverage:** Project enforces 100% coverage for `custom_components.rental_control` (see `setup.cfg`).  
- **Test names:** `test_*.py`. Place tests in `tests/` or alongside modules (mirror package structure).  
- **Doc coverage:** `interrogate` is used in pre-commit; aim for full docstring coverage.

## Commit & Pull Request Guidelines
- **Commit messages:** Follow Conventional Commits with capitalized types (e.g., `Fix:`, `Feat:`, `Chore:`). `gitlint` is configured to enforce this.  
- **PRs:** Include a clear description, link related issue, list migration steps, and add screenshots if UI changes. Ensure pre-commit passes and CI tests (pytest + coverage) succeed before asking for review.

## Security & Configuration Tips
- Never commit credentials or secrets; use Home Assistant `secrets.yaml`.  
- Keep `manifest.json` and translations up to date when adding platforms or services.

If you want, I can also add a short `CONTRIBUTING.md` or a GitHub PR template next.

