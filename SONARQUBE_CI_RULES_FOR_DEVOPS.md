# SonarQube CI/CD Rules for PR Validation - Python AI SDK

**Document for DevOps Team: SonarQube Quality Gate Configuration and CI Pipeline Rules**

---

## Quick Reference: PR Validation Rules

### ✅ PR Can Be Merged If:
- All quality gate conditions pass
- All CI checks pass
- No blocking issues found

### ❌ PR Must Be Rejected If:
- Any quality gate condition fails
- Any blocking CI check fails
- New bugs, vulnerabilities, or critical issues introduced

---

## 1. SonarQube Quality Gate Configuration

### Quality Gate Name: `Python SDK Production Gate`

### Mandatory Conditions (All Must Pass)

| Condition | Threshold | Action on Failure |
|-----------|-----------|-------------------|
| **New Bugs** | **0** | **BLOCK MERGE** |
| **New Vulnerabilities** | **0** | **BLOCK MERGE** |
| **New Security Hotspots (Unreviewed)** | **0** | **BLOCK MERGE** |
| **New Critical Code Smells** | **0** | **BLOCK MERGE** |
| **New Major Code Smells** | **0** | **BLOCK MERGE** |
| **Reliability Rating** | **A** | **BLOCK MERGE** |
| **Security Rating** | **A** | **BLOCK MERGE** |
| **Maintainability Rating** | **A or B** | **BLOCK MERGE** |
| **Coverage on New Code** | **≥ 85%** | **BLOCK MERGE** |
| **Overall Code Coverage** | **≥ 85%** | **BLOCK MERGE** |
| **Duplications on New Code** | **≤ 3%** | **BLOCK MERGE** |

---

## 2. SonarQube Project Configuration

### File: `sonar-project.properties`

```properties
# Project identification
sonar.projectKey=motadata-python-ai-sdk
sonar.projectName=Motadata Python AI SDK
sonar.projectVersion=0.1.0

# Source code
sonar.sources=src
sonar.sourceEncoding=UTF-8

# Test code
sonar.tests=tests
sonar.test.inclusions=**/test_*.py,**/*_test.py

# Exclusions (files/folders to ignore in analysis)
sonar.exclusions=**/__pycache__/**,**/*.pyc,**/*.pyo,**/venv/**,**/env/**,**/.venv/**,**/build/**,**/dist/**,**/*.egg-info/**,**/node_modules/**,**/examples/**

# Coverage exclusions
sonar.coverage.exclusions=**/test_*.py,**/*_test.py,**/tests/**,**/__pycache__/**,**/*.pyc,**/*.pyo,**/venv/**,**/env/**,**/.venv/**,**/build/**,**/dist/**,**/*.egg-info/**,**/testdata/**,**/*_pb2.py,**/mock_*.py,**/mocks/**,**/conftest.py,**/setup.py,**/examples/**

# Coverage report paths
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.xunit.reportPath=test-results.xml

# Python version support
sonar.python.version=3.8,3.9,3.10,3.11,3.12
```

---

## 3. CI Pipeline Requirements

### Required CI Steps (All Must Pass)

| Step | Tool | Command | Blocks Merge? |
|------|------|---------|---------------|
| **Format Check** | Black | `black --check src tests` | ✅ YES |
| **Import Sort** | isort | `isort --check-only src tests` | ✅ YES |
| **Lint Check** | Ruff | `ruff check src tests` | ✅ YES |
| **Type Check** | MyPy | `mypy src` | ✅ YES |
| **Security Scan** | Bandit | `bandit -r src -f json -o bandit-report.json` | ✅ YES |
| **Dependency Audit** | pip-audit | `pip-audit --format json --output pip-audit.json` | ✅ YES |
| **Secrets Detection** | detect-secrets | `detect-secrets scan --baseline .secrets.baseline` | ✅ YES |
| **Unit Tests** | pytest | `pytest tests/unit_tests -v --cov=src --cov-report=xml` | ✅ YES |
| **Integration Tests** | pytest | `pytest tests/integration_tests -v` | ✅ YES |
| **Build Verification** | build | `python -m build` | ✅ YES |
| **SonarQube Scan** | SonarScanner | `sonar-scanner` | ✅ YES |

---

## 4. Specific Rule Categories

### 4.1 Reliability Rules (Bugs)

**Enforced by:** SonarQube + Ruff + MyPy

| Rule | Tool | Severity |
|------|------|----------|
| No unused imports | Ruff | Error |
| No unused variables | Ruff | Error |
| No undefined names | Ruff, MyPy | Error |
| No unreachable code | SonarQube | Blocker |
| No duplicate conditions | SonarQube | Blocker |
| No self-assigned variables | SonarQube | Blocker |
| No useless if(True)/if(False) | SonarQube | Blocker |

### 4.2 Security Rules

**Enforced by:** SonarQube + Bandit + detect-secrets

| Rule | Tool | Severity |
|------|------|----------|
| No hard-coded credentials | detect-secrets, Bandit | Blocker |
| No hard-coded IP addresses | SonarQube | Blocker |
| No SQL injection vulnerabilities | SonarQube, Bandit | Blocker |
| No command injection | SonarQube, Bandit | Blocker |
| No unsafe eval/exec | SonarQube, Bandit | Blocker |
| No secrets in code | detect-secrets | Blocker |
| No known dependency vulnerabilities | pip-audit | Blocker |

### 4.3 Code Quality Rules

**Enforced by:** SonarQube

| Rule | Threshold | Severity |
|------|-----------|----------|
| Function cognitive complexity | ≤ 15 | Warning (11-15), Blocker (>15) |
| Function maximum lines | ≤ 80 | Blocker |
| Function maximum parameters | ≤ 5 | Warning |
| File maximum lines | ≤ 1000 | Blocker (except generated code) |
| Code duplication | ≤ 3% | Blocker |
| Deep nesting (if/for/while) | Not allowed | Blocker |

### 4.4 Coding Standards

**Enforced by:** Black + isort + Ruff + MyPy

| Rule | Tool | Severity |
|------|------|----------|
| Code formatting | Black | Error |
| Import sorting | isort | Error |
| Type hints on public functions | MyPy | Error |
| No bare except clauses | Ruff, SonarQube | Error |
| No mutable default arguments | Ruff, MyPy | Error |
| Docstrings on public classes/functions | Ruff, SonarQube | Warning |

---

## 5. Coverage Requirements

### Coverage Thresholds

| Metric | Threshold | Applies To |
|--------|-----------|------------|
| **Overall Coverage** | ≥ 85% | Entire codebase |
| **Coverage on New Code** | ≥ 85% | Code changed in PR |
| **Branch Coverage** | ≥ 80% | All branches |
| **Line Coverage** | ≥ 85% | All lines |

### Coverage Exclusions

The following are excluded from coverage calculations:
- Test files (`**/test_*.py`, `**/*_test.py`)
- Test directories (`**/tests/**`)
- Mock implementations (`**/mock_*.py`, `**/mocks/**`)
- Generated code (`**/*_pb2.py`)
- Test data (`**/testdata/**`)
- Examples (`**/examples/**`)

---

## 6. CI Pipeline Template (GitHub Actions Example)

```yaml
name: CI Pipeline

on:
  pull_request:
    branches: [main, develop]

jobs:
  quality-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install black isort ruff mypy bandit pip-audit detect-secrets pytest pytest-cov pytest-asyncio
      
      - name: Format check (Black)
        run: black --check src tests
      
      - name: Import sort check (isort)
        run: isort --check-only src tests
      
      - name: Lint check (Ruff)
        run: ruff check src tests
      
      - name: Type check (MyPy)
        run: mypy src
      
      - name: Security scan (Bandit)
        run: bandit -r src -f json -o bandit-report.json
      
      - name: Dependency audit (pip-audit)
        run: pip-audit --format json --output pip-audit.json
      
      - name: Secrets detection (detect-secrets)
        run: detect-secrets scan --baseline .secrets.baseline
      
      - name: Run unit tests with coverage
        run: |
          pytest tests/unit_tests -v --cov=src --cov-report=xml --cov-report=term
      
      - name: Run integration tests
        run: pytest tests/integration_tests -v
      
      - name: Build verification
        run: python -m build
      
      - name: SonarQube Scan
        uses: sonarsource/sonarqube-scan-action@master
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
```

---

## 7. SonarQube Quality Profile Rules

### Required Active Rules (Python)

#### Reliability (Bugs)
- `python:S1481` - Unused local variables should be removed
- `python:S1854` - Dead code should be removed
- `python:S3923` - All branches in a conditional structure should not have exactly the same implementation
- `python:S1764` - Identical expressions should not be used on both sides of a binary operator

#### Security
- `python:S1313` - Hardcoded IP addresses are security-sensitive
- `python:S2068` - Hard-coded credentials are security-sensitive
- `python:S2076` - SQL injection vulnerabilities
- `python:S2077` - Command injection vulnerabilities
- `python:S2078` - Path traversal vulnerabilities

#### Maintainability
- `python:S3776` - Cognitive Complexity of functions should not be too high (threshold: 15)
- `python:S138` - Functions should not have too many lines of code (threshold: 80)
- `python:S107` - Functions should not have too many parameters (threshold: 5)
- `python:S104` - Files should not have too many lines of code (threshold: 1000)

#### Code Smells
- `python:S1186` - Functions should not be empty
- `python:S4144` - Functions should not have identical implementations
- `python:S1192` - String literals should not be duplicated (threshold: 3)

---

## 8. PR Validation Checklist

### Before PR Can Be Merged:

- [ ] SonarQube Quality Gate: **PASSED**
- [ ] New Bugs: **0**
- [ ] New Vulnerabilities: **0**
- [ ] New Security Hotspots: **0**
- [ ] New Critical/Major Code Smells: **0**
- [ ] Coverage on New Code: **≥ 85%**
- [ ] All CI checks: **PASSED**
- [ ] Format check (Black): **PASSED**
- [ ] Lint check (Ruff): **PASSED**
- [ ] Type check (MyPy): **PASSED**
- [ ] Security scans: **PASSED**
- [ ] Unit tests: **PASSED**
- [ ] Integration tests: **PASSED**
- [ ] Build verification: **PASSED**

---

## 9. Failure Handling

### If Quality Gate Fails:

1. **Developer Action Required:**
   - Fix all blocking issues
   - Address new bugs, vulnerabilities, or code smells
   - Improve coverage if below 85%
   - Resolve all CI check failures

2. **DevOps Action:**
   - PR status: **BLOCKED**
   - Do not merge until all conditions pass
   - Notify developer of failures

### If CI Checks Fail:

1. **Format/Lint Failures:**
   - Run: `black src tests && isort src tests && ruff check --fix src tests`
   - Commit fixes

2. **Type Check Failures:**
   - Fix type errors reported by MyPy
   - Add missing type hints

3. **Test Failures:**
   - Fix failing tests
   - Ensure coverage ≥ 85%

4. **Security Failures:**
   - Remove hard-coded secrets
   - Fix dependency vulnerabilities
   - Address security hotspots

---

## 10. Configuration Files Required

### Files Needed in Repository:

1. **`sonar-project.properties`** - SonarQube configuration
2. **`.secrets.baseline`** - detect-secrets baseline
3. **`pyproject.toml`** - Black, isort, Ruff, MyPy configuration
4. **`requirements.txt`** - Python dependencies
5. **`.github/workflows/ci.yml`** - CI pipeline (if using GitHub Actions)
6. **`.gitlab-ci.yml`** - CI pipeline (if using GitLab CI)

---

## 11. Contact & Support

**For Questions:**
- Quality Gate Rules: See `docs/guide/quality-testing/sonarqube-quality-gate.md`
- Development Guidelines: See `docs/guide/developer-guides/PYTHON_SDK_DEVELOPER_GUIDELINES.md`
- Full Documentation: See `docs/guide/quality-testing/PYTHON_SDK_QUALITY_GATE_RULES_AND_DEVELOPMENT_GUIDELINE_DOCUMENT.md`

---

## Summary

**PR Validation Rules:**
- ✅ **0 new bugs, vulnerabilities, or critical issues**
- ✅ **85%+ code coverage on new code**
- ✅ **All CI checks must pass**
- ✅ **SonarQube Quality Gate must pass**

**Result:** PR can only be merged if ALL conditions are met.

---

**Last Updated:** 2025-01-XX  
**SDK Version:** 0.1.0

