# Maintenance Workflow Guide

## Repository Setup

Your repository is configured as follows:
- **origin**: Your fork at `git@github.com:cheezzz/homeassistant-rental-control.git`
- **upstream**: Original project at `https://github.com/tykeal/homeassistant-rental-control.git`

## Branch Strategy

- `main` - Tracks upstream/main for reference (updated: 2025-10-31)
- `development` - Your production branch deployed to Home Assistant

## Your Custom Changes (in development)

Your development branch includes:
1. Fix for blocked calendar events triggering active state
2. Test infrastructure (pytest.ini, tests/)
3. iCalendar validation scripts
4. LekkeSlaap integration documentation
5. Custom gitignore rules

Total: 18 files modified, +424/-24 lines from upstream

## Maintenance Commands

### Check for upstream updates
```bash
git fetch upstream
git log --oneline main..upstream/main  # See what's new
```

### Update your main branch
```bash
git checkout main
git merge upstream/main --ff-only
git push origin main
```

### Selectively merge upstream fixes into development
```bash
# 1. Review what changed upstream
git checkout main
git log --oneline development..main --reverse

# 2. Check for conflicts with your changes
git checkout development
git diff main...development custom_components/rental_control/

# 3. Option A: Merge specific commits (recommended)
git cherry-pick <commit-hash>

# 4. Option B: Merge all upstream changes (use with caution)
git merge main
```

### View differences between branches
```bash
# Files changed
git diff --stat upstream/main...development

# Specific file comparison
git diff upstream/main...development -- <file-path>
```

## Important Upstream Changes Since Your Last Sync

Since your merge at f420833, upstream added:
- **Dependency updates**: codeql-action, pre-commit hooks (mostly safe)
- **Important fix (4f4bf2f)**: "Handle calendar misses" in coordinator.py
  - This might conflict with or complement your changes

### Recommended Action

Review the "Handle calendar misses" fix:
```bash
git show 4f4bf2f
```

Check if it conflicts with your blocked calendar events fix at custom_components/rental_control/coordinator.py:

If compatible, consider cherry-picking it:
```bash
git cherry-pick 4f4bf2f
```

## Testing Before Deployment

After merging any upstream changes:
1. Run your validation script: `python validate_ical.py`
2. Test with your Home Assistant test instance
3. Verify LekkeSlaap calendar compatibility
4. Deploy to production Home Assistant

## Quick Reference

```bash
# Current status
git status
git branch -vv

# What's in development but not upstream
git log --oneline development ^upstream/main

# What's in upstream but not development
git log --oneline upstream/main ^development

# Detailed file changes
git diff --stat upstream/main...development
```

## Notes

- Keep `development` stable - it's running in production
- Only merge upstream changes when necessary (bug fixes, security updates)
- Avoid automatic merges of all upstream changes
- Test thoroughly before deploying to Home Assistant
