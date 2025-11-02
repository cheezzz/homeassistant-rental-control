# Testing Quick Reference

## Setup (First Time Only)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements_test.txt
```

## Daily Workflow

### 1. Start Working
```bash
# Activate venv (ALWAYS do this first!)
source .venv/bin/activate

# Verify you're in the venv (should see (.venv) in prompt)
which python3
# Should output: /path/to/project/.venv/bin/python3
```

### 2. Run Tests Before Deployment
```bash
# Quick test run (all working tests)
python3 -m pytest tests/ --ignore=tests/test_real_calendars.py -q

# Verbose output (see each test name)
python3 -m pytest tests/ --ignore=tests/test_real_calendars.py -v

# Specific test file only
python3 -m pytest tests/test_checkin_links.py -v
```

### 3. Check Code Coverage
```bash
# Show coverage report with missing lines
python3 -m pytest tests/ --ignore=tests/test_real_calendars.py \
  --cov=custom_components.rental_control \
  --cov-report=term-missing

# Generate HTML coverage report
python3 -m pytest tests/ --ignore=tests/test_real_calendars.py \
  --cov=custom_components.rental_control \
  --cov-report=html

# Open coverage report in browser
xdg-open htmlcov/index.html  # Linux
# or: open htmlcov/index.html  # Mac
```

### 4. Run Quality Checks
```bash
# Run all pre-commit checks
pre-commit run --all-files

# Run specific check
pre-commit run ruff --all-files
pre-commit run mypy --all-files
```

### 5. Done Working
```bash
# Deactivate venv
deactivate
```

## Common Issues

### Issue: `python: command not found` or `python` points to Python 2
**Fix:** Always use `python3` explicitly on Linux systems.

### Issue: `ModuleNotFoundError: No module named 'pytest'`
**Fix:** You forgot to activate the venv!
```bash
source .venv/bin/activate
pip install -r requirements_test.txt
```

### Issue: Tests fail with `ImportError` or `AttributeError`
**Fix:** Some tests are broken. Use `--ignore` to skip them:
```bash
python3 -m pytest tests/ --ignore=tests/test_real_calendars.py
```

### Issue: `No such file or directory: '.venv'`
**Fix:** Create the venv first:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_test.txt
```

## Pre-Deployment Checklist

Before deploying to production Home Assistant:

- [ ] Activate venv: `source .venv/bin/activate`
- [ ] Run tests: `python3 -m pytest tests/ --ignore=tests/test_real_calendars.py -v`
- [ ] All tests pass ✅
- [ ] Run pre-commit: `pre-commit run --all-files`
- [ ] All checks pass ✅
- [ ] Commit changes: `git add . && git commit -m "Fix: description"`
- [ ] Push to repo: `git push`
- [ ] Deploy to Home Assistant
- [ ] Verify in HA logs (no errors)

## VS Code Integration

The project includes `.vscode/settings.json` which:
- Automatically uses the `.venv` Python interpreter
- Enables pytest test discovery
- Hides cache directories in file explorer
- Auto-activates venv when opening integrated terminal

## Current Test Status

✅ **Working Tests (11 total):**
- `tests/test_checkin_links.py` - All 11 tests passing

❌ **Broken Tests (skip these):**
- `tests/test_real_calendars.py` - Imports non-existent function
- `tests/test_config_flow.py` - Home Assistant fixture issues
- `tests/test_init.py` - Home Assistant fixture issues

## Resources

- Full documentation: See `CLAUDE.md`
- Pytest docs: https://docs.pytest.org/
- Home Assistant testing: https://developers.home-assistant.io/docs/development_testing/
