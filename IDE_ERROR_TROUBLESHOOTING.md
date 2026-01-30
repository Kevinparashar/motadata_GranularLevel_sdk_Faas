# IDE Error Troubleshooting Guide

## Problem: Errors Increase When Clicking on Python Files

This is a common issue with Python language servers (Pylance/Pyright) that occurs when:
1. The language server re-analyzes files on open
2. Cache is stale or corrupted
3. Configuration is too strict
4. Import resolution issues

## Solutions Applied

### 1. Updated `pyrightconfig.json`
- Set `typeCheckingMode` to `"basic"` (less strict)
- Disabled many optional warnings that cause noise
- Added exclusions for cache directories
- Configured proper execution environments

### 2. Created `.vscode/settings.json`
- Configured Pylance/Pyright with appropriate settings
- Set diagnostic severity overrides
- Excluded cache directories from analysis

## Quick Fixes

### Option 1: Reload IDE Window
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type: `Developer: Reload Window`
3. Press Enter

### Option 2: Restart Language Server
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type: `Python: Restart Language Server`
3. Press Enter

### Option 3: Clear IDE Cache
1. Close the IDE
2. Delete cache directories:
   ```bash
   rm -rf .vscode/.ropeproject
   rm -rf .pylance_cache
   rm -rf **/__pycache__
   ```
3. Reopen the IDE

### Option 4: Rebuild Python Environment
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall packages
pip install --upgrade pip
pip install -e ".[dev]"
```

## Understanding the Errors

### Real Errors vs False Positives

**Real Errors:**
- Syntax errors
- Undefined names
- Type mismatches in critical paths
- Import errors for installed packages

**False Positives (Can Ignore):**
- `reportOptionalSubscript` - Optional type warnings
- `reportOptionalMemberAccess` - Optional attribute access
- `reportMissingTypeStubs` - Missing type stubs for third-party libraries
- `reportUnusedImport` - Unused imports (warnings only)

### Current Configuration

The `pyrightconfig.json` is configured to:
- ✅ Show real errors (syntax, undefined names)
- ✅ Show warnings for unused imports/variables
- ❌ Hide optional type warnings (too noisy)
- ❌ Hide missing type stub warnings (expected for some packages)

## If Errors Persist

1. **Check Python Interpreter:**
   - Ensure IDE is using the correct virtual environment
   - Check: `Ctrl+Shift+P` -> `Python: Select Interpreter`

2. **Verify Dependencies:**
   ```bash
   source venv/bin/activate
   pip list | grep -E "mypy|pylance|pyright"
   ```

3. **Check for Circular Imports:**
   - Look for import cycles in your code
   - These can cause cascading errors

4. **Review Type Annotations:**
   - Some errors may be legitimate type issues
   - Check the comprehensive analysis report: `SONARQUBE_COMPREHENSIVE_ANALYSIS.md`

## Configuration Files

- `pyrightconfig.json` - Pyright/Pylance configuration
- `.vscode/settings.json` - VS Code/Cursor IDE settings
- `pyproject.toml` - mypy configuration (for command-line type checking)

## Still Having Issues?

1. Check the Problems panel for specific error messages
2. Look at the error location and context
3. Verify the file is in the correct location
4. Check if the error is from a dependency or your code
5. Review the comprehensive analysis report for known issues

---

**Last Updated:** 2026-01-30

