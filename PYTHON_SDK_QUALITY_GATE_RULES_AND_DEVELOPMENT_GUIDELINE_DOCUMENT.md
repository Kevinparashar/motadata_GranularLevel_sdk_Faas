# PYTHON SDK QUALITY GATE RULES AND DEVELOPMENT GUIDELINE DOCUMENT

> **Audience:** Python SDK contributors, reviewers, maintainers  
> **Enforcement model:** **CI blocks merge** + **Sonar Quality Gate blocks merge**  
> **Repo alignment note:** This document is **cross-checked** against the current SDK repo structure (Makefile + pyproject + tests). Where the repo is missing enforcement/config, this doc provides **exact drop-in templates** to close the gaps.

---

## 0) What your SDK already has (verified) vs what must be added

### 0.1 Verified in your SDK repo (already present)
**Tooling**
- `pyproject.toml` config exists for: **black**, **isort**, **mypy**, **pytest**.
- Dev deps include: `pytest`, `pytest-asyncio`, `pytest-mock`, `pytest-cov`, `black`, `isort`, `mypy`.

**Makefile targets (usable today)**
- `format`, `format-check` → black + isort
- `type-check` → mypy
- `test`, `test-unit`, `test-integration`, `test-cov` → pytest + coverage report (HTML/term)
- `build` → `python -m build`
- `ci` → runs clean + install-dev + test + format-check + type-check

**Test structure**
- `src/tests/unit_tests`, `src/tests/integration_tests`, `src/tests/benchmarks`

### 0.2 Not present in the repo (must be added to be Sonar+CI compliant)
These are **Quality Gate must-haves** that are missing today:
- ❌ **No CI pipeline configuration** (no `.github/workflows/*`, no GitLab CI, etc.)
- ❌ **No Sonar configuration** (`sonar-project.properties` / scanner settings)
- ❌ **No enforced coverage threshold** (`--cov-fail-under=80` is not used in Makefile)
- ❌ **Lint is a placeholder** in Makefile (no ruff/flake8/pylint installed or executed)
- ❌ **No complexity enforcement**
- ❌ **No security gates** (`bandit`, `pip-audit`, `detect-secrets`) not present
- ❌ **No branch protection / PR governance documented with templates**

This document upgrades your current baseline into a **merge-blocking Quality Gate system**.

---

## 1) Mandatory Operating Model (non-negotiable)

### 1.1 Branch protection rules (mandatory)
- **No direct commits to `main`** (protected default branch).
- **All changes must be via PR**.
- **Mandatory CI pass** on PR.
- **Mandatory Sonar Quality Gate pass** on PR.
- **Mandatory approvals** (minimum 1; increase for critical components).

**Branch protection checklist (admin settings)**
- [ ] Disallow force-pushes to `main`
- [ ] Disallow direct pushes to `main`
- [ ] Require PR before merge
- [ ] Require status checks to pass (CI + Sonar gate)
- [ ] Require at least 1 approval
- [ ] Require linear history (recommended)

### 1.2 Gate waiver policy (strict)
Waivers are allowed **only** with:
- written justification in PR
- risk statement
- remediation ticket
- owner + deadline

No silent bypasses. No “we will fix later” without a tracked ticket.

---

## 2) Quality Gate Definition (Sonar + CI aligned)

### 2.1 PR Quality Gate (merge-blocking)
A PR is mergeable only if **all** pass:

**CI checks**
1. Format check (black/isort or ruff-format)
2. Lint check (ruff standardized)
3. Type check (mypy)
4. Unit tests
5. Integration tests (when component touches external dependency)
6. Coverage threshold: **≥ 80% (new code)**
7. Security scans: secrets + SAST + dependency audit
8. Build/package verification

**Sonar checks**
1. **Quality Gate = PASSED**
2. **Coverage on New Code ≥ 80%**
3. Reliability rating on New Code = **A**
4. Security rating on New Code = **A**
5. Maintainability rating on New Code = **A**
6. **0 new Blocker/Critical** issues

> **Rule:** If Sonar or CI is red → **no merge**.

### 2.2 Release Quality Gate (stricter)
All PR gates plus:
- cross-version run (e.g., 3.8–3.12)
- packaging install smoke test in clean environment
- vulnerability scan must have **0 High/Critical** (or approved waiver)

---

## 3) Mandatory Code Rules (with examples)

### 3.1 Formatting rules (mandatory)
**Rule**
- Black + isort output is the canonical style. No “pretty formatting” by hand.

**Good example**
```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
```

**Bad example (will fail format-check)**
```python
from dataclasses import dataclass
@dataclass
class User: id:int; name:str
```

**Commands**
```bash
make format
make format-check
```

---

### 3.2 Linting rules (mandatory) — Standardized on Ruff

**Standard**
- Use **Ruff** as the single linter (fast + rule-rich).
- Optional: keep flake8/pylint only if legacy demands (not recommended for greenfield).

**Must-block categories**
- unused imports/variables
- undefined names
- broad exception patterns (bare `except:`)
- swallowing exceptions without context/logging
- dangerous calls (`eval`, `exec`)
- import cycles (where detectable)
- poor practices (mutable defaults, etc.)

**Bad → Good examples**

**(A) Bare except**
```python
# BAD (blocks)
try:
    do_work()
except:
    pass
```

```python
# GOOD
import logging

logger = logging.getLogger(__name__)

try:
    do_work()
except KnownError as exc:
    logger.exception("do_work failed: %s", exc)
    raise
```

**(B) Mutable default**
```python
# BAD (blocks)
def add_item(x, items=[]):
    items.append(x)
    return items
```

```python
# GOOD
from typing import Optional

def add_item(x, items: Optional[list] = None):
    items = [] if items is None else items
    items.append(x)
    return items
```

**Ruff commands**
```bash
ruff check .
ruff format --check .
```

**Drop-in Ruff config template (add to `pyproject.toml`)**
```toml
[tool.ruff]
line-length = 100
target-version = "py38"
fix = false

[tool.ruff.lint]
select = ["E", "F", "B", "I", "UP", "SIM", "PL", "RUF"]
ignore = []
```

**Add dev dependency**
```text
ruff>=0.6.0
```

---

### 3.3 Typing rules (mandatory)
**Rules**
- All **new/modified public** functions/classes must be type-hinted.
- No `Any` in public signatures unless justified.
- `# type: ignore` requires a reason.

**Bad**
```python
def fetch_user(user_id):
    ...
```

**Good**
```python
def fetch_user(user_id: int) -> dict[str, str]:
    ...
```

**Repo current-state note**
- `mypy` exists but `disallow_untyped_defs = false` currently allows untyped defs.  
  **Gate requirement:** enforce stricter typing on **new code**.

**Recommended mypy tightening (pyproject)**
```toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
check_untyped_defs = true
no_implicit_optional = true
```

---

## 4) Coverage Gate (≥ 80%) — Mandatory with examples

### 4.1 Coverage threshold (mandatory)
- **Coverage on New Code ≥ 80%** (Sonar gate)
- CI must enforce `--cov-fail-under=80` for immediate feedback.

**Repo current-state note**
- `pytest-cov` exists, but `test-cov` does not enforce threshold today.

### 4.2 Update Makefile (drop-in replacement)
Replace `test-cov` with:

```make
test-cov: ## Run tests with coverage report + enforce threshold
	$(PYTHON) -m pytest $(TESTS_DIR) \
		--cov=$(SRC_DIR) --cov-report=term-missing --cov-report=xml \
		--cov-fail-under=80
```

### 4.3 Example: what “good coverage” means
If you add a new helper `normalize_headers()` you must add a test that covers:
- normal input
- empty input
- mixed-case headers
- invalid types (raises)

**Implementation**
```python
def normalize_headers(headers: dict[str, str]) -> dict[str, str]:
    return {k.lower(): v.strip() for k, v in headers.items()}
```

**Tests**
```python
def test_normalize_headers_lowercases_and_strips():
    assert normalize_headers({"X-Token": " abc "}) == {"x-token": "abc"}
```

---

## 5) Complexity Limits (mandatory)

### 5.1 Limits (enforced)
- **Cyclomatic complexity per function: ≤ 10**
- **Cognitive complexity per function: ≤ 15** (Sonar)
- **Function length soft limit: ≤ 80 LOC** (review gate; make hard later if needed)

### 5.2 Enforcement options (choose 1 path, but enforce consistently)
**Primary (recommended): Sonar**
- Enforce cognitive complexity via Sonar rules.
- Fail Quality Gate on new violations.

**Secondary (CI local enforcement): Radon**
Add dev dependency:
```text
radon>=6.0.0
```

CI command:
```bash
radon cc -s -n B src
# "B" or better only; adjust if needed
```

### 5.3 Example: reducing complexity
**Bad (complex, nested, fragile)**
```python
def build_payload(data):
    if data:
        if "user" in data:
            if "id" in data["user"]:
                ...
```

**Good (early returns + helpers)**
```python
def build_payload(data: dict) -> dict:
    user = data.get("user") or {}
    user_id = user.get("id")
    if not user_id:
        raise ValueError("user.id is required")
    return {"userId": user_id}
```

---

## 6) Security Rules (mandatory) — secrets, unsafe eval, dependency risk

### 6.1 Mandatory block rules
CI must fail if:
- **Secrets** exist in repo (keys, tokens, passwords, private keys)
- **Unsafe eval/exec** used
- **Pickle loads on untrusted input** exists
- `subprocess` uses `shell=True` without strict justification
- HTTP clients lack timeouts
- retries are unbounded

### 6.2 Examples (bad → good)

**(A) `eval`**
```python
# BAD (blocks)
result = eval(user_input)
```

```python
# GOOD (safe alternative)
import json
result = json.loads(user_input)
```

**(B) No HTTP timeout**
```python
# BAD (blocks)
requests.get(url)
```

```python
# GOOD
requests.get(url, timeout=10)
```

**(C) Secrets in code**
```python
# BAD (blocks)
API_KEY = "sk_live_..."
```

```python
# GOOD (env + secrets manager)
import os
API_KEY = os.environ["API_KEY"]
```

### 6.3 Mandatory security tools (CI)
Add dev deps:
```text
bandit>=1.7.0
pip-audit>=2.7.0
detect-secrets>=1.5.0
```

Commands:
```bash
detect-secrets scan --baseline .secrets.baseline
bandit -r src -q
pip-audit
```

**detect-secrets baseline template**
```bash
detect-secrets scan > .secrets.baseline
```

---

## 7) PR Rules (mandatory) — templates and checkpoints

### 7.1 PR requirements (merge-blocking)
- [ ] No direct commits to `main`
- [ ] PR has description + risk assessment
- [ ] CI green
- [ ] Sonar gate green
- [ ] Coverage ≥ 80% new code
- [ ] Lint passes (ruff)
- [ ] Type-check passes (mypy)
- [ ] Security scans pass
- [ ] Component docs updated (if public behavior changes)

### 7.2 PR description template (copy/paste)
```markdown
## What changed
- 

## Why
- 

## Risk & blast radius
- Low / Medium / High
- Affected components:
- Rollback plan:

## Validation evidence
- [ ] ruff check .
- [ ] mypy src
- [ ] pytest unit
- [ ] pytest integration (if applicable)
- [ ] coverage >= 80%
- [ ] security scans (bandit/pip-audit/detect-secrets)

## Sonar
- Quality Gate: PASSED
- New Code Coverage: __%
- New issues: 0 critical/blocker
```

### 7.3 Review checklist (for reviewers)
- [ ] Tests cover critical paths
- [ ] Exceptions are actionable (context + remediation)
- [ ] No hidden breaking change
- [ ] Complexity within limits
- [ ] No secrets / security smells
- [ ] Public API changes documented

---

## 8) Component-based gates (mandatory)

### 8.1 Component definition
A “component” is any top-level functional module under `src/` (e.g., gateway, cache, db, rag, services).

### 8.2 Component gate checklist (required per component touched)
For every component modified, PR must include:
- [ ] **Unit tests** for new/changed logic
- [ ] **Integration tests** if component touches external dependency
- [ ] Updated **component docs** (README or doc page) when behavior changes
- [ ] **API contract** stability (or migration notes if breaking)
- [ ] Observability expectations (logs/metrics) respected

### 8.3 Component documentation mini-template
```markdown
# Component: <name>

## Purpose
What it does.

## Public API
- function/class list
- input/output types

## Configuration
- env vars / config keys

## Failure modes
- what can fail
- what error is raised
- how to recover

## Testing
- unit tests location
- integration tests location
```

---

## 9) CI + Sonar enforcement templates (drop-in)

> Your repo currently has **no CI config** and **no Sonar config**. Use the following templates.

### 9.1 `sonar-project.properties` template (root)
```properties
sonar.projectKey=motadata_python_sdk
sonar.projectName=Motadata Python SDK
sonar.sources=src
sonar.tests=src/tests
sonar.python.version=3.8

# Coverage
sonar.python.coverage.reportPaths=coverage.xml

# Optional
sonar.exclusions=**/__pycache__/**,**/*.pyc
sonar.test.inclusions=src/tests/**

# If you generate junit report:
# sonar.python.xunit.reportPath=test-results.xml
```

### 9.2 GitHub Actions CI template (merge-blocking)
Create: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          pip install ruff bandit pip-audit detect-secrets radon

      - name: Format check
        run: |
          ruff format --check .

      - name: Lint
        run: |
          ruff check .

      - name: Type check
        run: |
          python -m mypy src

      - name: Tests + Coverage Gate
        run: |
          pytest -q src/tests --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=80

      - name: Security - secrets
        run: |
          detect-secrets scan --baseline .secrets.baseline

      - name: Security - SAST
        run: |
          bandit -r src -q

      - name: Security - dependency audit
        run: |
          pip-audit

      - name: Complexity gate
        run: |
          radon cc -s -n B src

      - name: Build package
        run: |
          python -m build

      # Sonar scan step depends on your Sonar setup
      # - name: Sonar Scan
      #   uses: SonarSource/sonarqube-scan-action@v2
      #   env:
      #     SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
      #     SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
```

### 9.3 GitLab CI template (if you use GitLab)
Create: `.gitlab-ci.yml`
```yaml
stages: [quality]

quality_gate:
  stage: quality
  image: python:3.11
  script:
    - pip install -e ".[dev]"
    - pip install ruff bandit pip-audit detect-secrets radon build
    - ruff format --check .
    - ruff check .
    - python -m mypy src
    - pytest -q src/tests --cov=src --cov-report=xml --cov-fail-under=80
    - detect-secrets scan --baseline .secrets.baseline
    - bandit -r src -q
    - pip-audit
    - radon cc -s -n B src
    - python -m build
  only:
    - merge_requests
```

---

## 10) Mandatory checkpoints (single-page summary)

### 10.1 Developer must run before PR
```bash
make format
ruff check .
python -m mypy src
pytest -q src/tests --cov=src --cov-report=xml --cov-fail-under=80
bandit -r src -q
pip-audit
detect-secrets scan --baseline .secrets.baseline
radon cc -s -n B src
python -m build
```

### 10.2 CI must enforce (merge-blocking)
- Format check
- Ruff lint
- Mypy
- Tests + coverage fail-under 80
- Secret scan
- Bandit
- Pip-audit
- Complexity gate
- Build + smoke import (optional but recommended)
- Sonar Quality Gate pass

---

## 11) Action plan to fully align the repo (what to change now)

**P0 (must-do to be “Quality Gate compliant”)**
1. Add **CI pipeline** (GitHub/GitLab).
2. Add **Sonar properties + scanner** integration.
3. Enforce **coverage threshold** (`--cov-fail-under=80`) in CI and Makefile.
4. Replace placeholder `lint` target with **ruff**.
5. Add **security scanners** (`detect-secrets`, `bandit`, `pip-audit`).
6. Add **complexity gate** (Sonar + radon).

**P1 (next hardening)**
- Multi-Python version matrix (3.8–3.12)
- Pre-commit hooks
- Packaging smoke test in clean venv/container
- Changelog and semantic versioning policy

---

*End of document.*
