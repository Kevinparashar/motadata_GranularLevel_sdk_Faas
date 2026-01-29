# Motadata CONTRIBUTING.md
## Motadata Python AI SDK

This document defines the **official contribution process** for the Motadata Python AI SDK.
It is written for **organizational use**: onboarding, training, and consistent engineering execution.

---

## 1) Non-negotiable rules (merge blocking)

### Branch protection
- ❌ **No direct commits to `main`**
- ✅ **All changes via Pull Request**
- ✅ **CI must pass**
- ✅ **Sonar Quality Gate must pass**
- ✅ At least **one reviewer approval** (maintainers can raise this)

### Waiver policy (strict)
Waivers are allowed only with:
- written justification in the PR
- risk statement
- remediation ticket
- owner + deadline

No silent bypasses.

---

## 2) Repository structure (what contributors must know)

You will primarily work in:

- `src/core/` → Core SDK components (agent, gateway, rag, etc.)
- `src/faas/` → Stateless services (agent service, rag service, gateway service, etc.)
- `src/tests/` → Unit, integration, benchmarks
  - `src/tests/unit_tests/`
  - `src/tests/integration_tests/`
  - `src/tests/benchmarks/`
- `pyproject.toml` → tooling config (black/isort/mypy/pytest)
- `Makefile` → standardized local commands

---

## 3) Branching and commit standards

### Branch naming
- `feature/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`
- `chore/<short-description>`

### Commit message convention
Use clear, searchable messages:
- `feat: add <thing>`
- `fix: correct <thing>`
- `docs: update <thing>`
- `chore: improve <thing>`

Example:
- `feat: add tenant-scoped cache key builder`
- `fix: enforce gateway timeout defaults`
- `docs: add dev environment setup steps`

---

## 4) Local development workflow (mandatory)

### Step 1: Set up your environment
Follow: **PYTHON_SDK_DEV_ENVIRONMENT_SETUP_GUIDE.md**

### Step 2: Make changes
- Keep changes scoped and component-focused
- Update tests and docs with the change

### Step 3: Run the mandatory local checks
Run these before you open a PR:

```bash
make format-check
make type-check
make test
make test-cov
```

> If your change touches external dependencies, also run:
```bash
make test-integration
```

---

## 5) Quality Gate alignment (mandatory)

Your PR must comply with the Quality Gate rules:
- coverage threshold (≥ 80% on new code in CI)
- linting rules (standardized linter in CI)
- complexity limits
- security checks (secrets, unsafe eval/exec, dependency audit)
- CI + Sonar enforcement

Reference: **PYTHON_SDK_QUALITY_GATE_RULES_AND_DEVELOPMENT_GUIDELINE_DOCUMENT.md**

---

## 6) Component development rules (mandatory)

### When adding a new component
A component lives under `src/core/<component_name>/` and must include:

**Required files**
- `__init__.py` (public exports)
- `README.md` (component documentation)
- `<component>.py` (implementation)

**Recommended files (as needed)**
- `interfaces.py` (interfaces/abstractions)
- `config.py` (configuration + defaults)
- `exceptions.py` (component-specific exceptions)
- `utils.py` (helpers)

### Component README must include
- Purpose and scope
- Public APIs (functions/classes)
- Configuration options
- Failure modes + recovery
- Testing notes (unit/integration paths)

**Component README mini-template**
```markdown
# Component: <name>

## Purpose
What this component does.

## Public APIs
- <function/class>(...) – what it does

## Configuration
- ENV_VAR_1: description (default: ...)

## Failure Modes
- What can fail
- What error is raised
- Suggested fix

## Tests
- Unit: src/tests/unit_tests/...
- Integration: src/tests/integration_tests/...
```

---

## 7) Testing policy (mandatory)

### Required expectations
| Change type | Required tests |
|---|---|
| Bug fix | Regression test (unit) |
| Feature | Unit tests + integration tests if external deps |
| Refactor | Unit tests (and integration if behavior touches I/O) |
| Performance changes | Benchmark or performance notes |

### Test writing standards
- Tests must be deterministic
- No real secrets/keys in tests
- Prefer fakes/mocks for external calls unless explicitly integration-tested

---

## 8) Documentation policy (mandatory)

Update docs when:
- public API changes
- behavior changes (timeouts/retries/config defaults)
- new component added
- breaking changes introduced

Changelog rule:
- Add user-facing entry to **CHANGELOG.md** under **[Unreleased]** for user-visible changes.

---

## 9) Pull Request template (copy/paste)

```markdown
## Summary
What changed in 1–3 lines.

## Why
Reason / business context.

## Risk level
Low / Medium / High
- Blast radius:
- Rollback plan:

## Validation evidence
- [ ] make format-check
- [ ] make type-check
- [ ] make test
- [ ] make test-cov
- [ ] make test-integration (if applicable)

## Quality Gate
- [ ] CI passed
- [ ] Sonar Quality Gate passed
- [ ] Coverage threshold met
- [ ] Security checks clean
```

---

## 10) Code of conduct (professional standard)
Be respectful, factual, and execution-focused. Escalate issues early to maintainers.

---

**End of file**
