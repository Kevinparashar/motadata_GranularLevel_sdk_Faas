# MOTADATA - PYTHON SDK QUALITY GATE RULES AND DEVELOPMENT GUIDELINE DOCUMENT

**Official quality gate rules, development guidelines, and contribution standards for the Motadata Python AI SDK with CI enforcement and Sonar Quality Gate integration.**

---

## Table of Contents

- [Executive Summary (Quick Reference)](#executive-summary-quick-reference)
- [Business Value and Industry Alignment](#business-value-and-industry-alignment)
- [Organizational Quality Standards](#organizational-quality-standards)
- [Final Quality Gate Summary](#final-quality-gate-summary)
- [Document Structure](#document-structure)
- [1) Mandatory Operating Model](#1-mandatory-operating-model-non-negotiable)
- [2) Quality Gate Definition](#2-quality-gate-definition-sonar--ci-aligned)
- [3) Mandatory Code Rules](#3-mandatory-code-rules-with-examples)
- [4) Coverage Gate](#4-coverage-gate-85---mandatory-with-examples)
- [5) Complexity Limits](#5-complexity-limits-mandatory)
- [6) Security Rules](#6-security-rules-mandatory---secrets-unsafe-eval-dependency-risk)
- [7) PR Rules](#7-pr-rules-mandatory---templates-and-checkpoints)
- [8) Component-Specific Quality Gates](#8-component-specific-quality-gates-mandatory)
- [9) CI and Sonar Enforcement Templates](#9-ci--sonar-enforcement-templates-drop-in)
- [10) Mandatory Checkpoints](#10-mandatory-checkpoints-single-page-summary)

## Executive Summary (Quick Reference)

### Quality Gate: Python AI SDK

### Purpose
Define a clear and enforceable SonarQube Quality Gate for the Motadata Python AI SDK, aligned with organizational standards, focused on mandatory rules and thresholds required for production readiness.

### Scope
- **Language:** Python 3.8+
- **Domain:** AI/ML SDK (RAG, Agents, LLM Gateway, Multi-tenant Architecture)
- **Based on:** Official SonarQube Python ruleset + Python best practices
- **Alignment:** Organizational quality standards for Python AI/ML SDKs

---

### Merge-Blocking Thresholds

> [!IMPORTANT]
> A build **must fail** if any merge-blocking condition below is violated.

### SonarQube Quality Gate Conditions

| Category | Threshold | Status |
|----------|-----------|--------|
| **New Bugs** | 0 | **Blocks merge** |
| **New Security Hotspots (Unreviewed)** | 0 | **Blocks merge** |
| **New Critical / Major Code Smells** | 0 | **Blocks merge** |
| **Reliability Rating** | A | **Blocks merge** |
| **Security Rating** | A | **Blocks merge** |
| **Maintainability Rating** | A | **Blocks merge** |
| **Coverage on New Code** | ≥ 85% | **Blocks merge** |
| **Duplications on New Code** | ≤ 3% | **Blocks merge** |

### CI Pipeline Checks (Mandatory)

| Check | Tool | Status |
|-------|------|--------|
| **Format Check** | Black + isort | **Blocks merge** |
| **Lint Check** | Ruff | **Blocks merge** |
| **Type Check** | MyPy | **Blocks merge** |
| **Unit Tests** | Pytest | **Blocks merge** |
| **Integration Tests** | Pytest | **Blocks merge** |
| **Security Scans** | Bandit + pip-audit + detect-secrets | **Blocks merge** |
| **Build Verification** | python -m build | **Blocks merge** |

---

### Non-Blocking Warnings

> [!NOTE]
> These checks generate warnings but **do not block** merge.

| Check | Threshold | Status |
|-------|-----------|--------|
| **Cognitive Complexity** | 11-15 | **Warning** - Review recommended |
| **Function Length** | <= 60 LOC | **Warning** - Review recommended |
| **Missing Private Docstrings** | Any | **Warning** - Improve recommended |
| **Minor Code Smells** | Non-critical | **Warning** - Technical debt |
| **Low/Medium Vulnerabilities** | Dependency issues | **Warning** - Update recommended |

---

### Enforced Rule Categories

> [!NOTE]
> **Tool responsibility:** Rules are enforced by either SonarQube (code quality analysis) or CI tools (formatting, linting, type checking). See [Section 2.1.1](#211-sonarqube-vs-ci-tools-responsibility-split) for the responsibility split.

### 1. Reliability (Bugs) - Gate Rule: **New Bugs = 0**
**Enforced by:** SonarQube + CI Tools (Ruff, MyPy)

- No unused imports or variables *(CI: Ruff)*
- No undefined names *(CI: Ruff, MyPy)*
- No unreachable or dead code *(SonarQube)*
- No duplicate conditions in if/elif *(SonarQube)*
- No self-assigned variables *(SonarQube)*
- No useless if(True) / if(False) blocks *(SonarQube)*

### 2. Security Hotspots - Gate Rule: **Unreviewed Hotspots = 0**
**Enforced by:** SonarQube + CI Tools (Bandit, detect-secrets)

- Hard-coded credentials not allowed *(CI: detect-secrets, Bandit)*
- Hard-coded IP addresses not allowed *(SonarQube)*
- SQL injection vulnerabilities not allowed *(SonarQube, Bandit)*
- Dangerous calls (eval, exec) not allowed *(SonarQube, Bandit)*
- Secrets in code not allowed *(CI: detect-secrets)*

### 3. Maintainability & Complexity - Gate Rule: **No new Critical/Major issues**
**Enforced by:** SonarQube

- Function cognitive complexity ≤ 10 (warning at 11-15) *(SonarQube)*
- Function cognitive complexity > 15 (blocks merge) *(SonarQube)*
- Deeply nested if/for/while statements not allowed *(SonarQube)*
- Overly complex expressions not allowed *(SonarQube)*
- Code duplication > 3% not allowed *(SonarQube CPD)*

### 4. Function & File Constraints
**Enforced by:** SonarQube

- Functions must not be empty *(SonarQube)*
- Functions must not have identical implementations *(SonarQube)*
- Parameters should be limited (≤ 5 recommended) *(SonarQube warning)*
- Functions should be reasonably sized (≤ 60 lines recommended) *(SonarQube warning)*
- Files should not be excessively large *(SonarQube warning)*

### 5. Coding Standards & Hygiene
**Enforced by:** CI Tools (Black, Ruff, MyPy) + SonarQube

- Type hints required on all public functions *(CI: MyPy)*
- No bare except: clauses *(CI: Ruff, SonarQube)*
- No mutable default arguments *(CI: Ruff, MyPy)*
- No swallowing exceptions without logging *(SonarQube)*
- TODO/FIXME must have ticket reference (warning) *(SonarQube)*
- Docstrings required on public classes/functions *(CI: Ruff, SonarQube)*

---

## Business Value and Industry Alignment

### How Quality Gates Reduce Production Bugs

Quality gates significantly reduce production bugs through **early detection and prevention**:

#### 1. Automated Bug Detection
- **Static Analysis:** SonarQube and CI tools catch bugs before code reaches production
  - Unused variables, undefined names, unreachable code detected at commit time
  - Type errors caught by MyPy before runtime
  - Logic errors identified through complexity analysis
- **Impact:** Studies show 60-80% reduction in production bugs when static analysis is enforced

#### 2. Test Coverage Enforcement
- **85% Coverage Threshold:** Ensures critical code paths are tested
  - Prevents untested code from reaching production
  - Catches regression bugs early in development cycle
  - Reduces "works on my machine" scenarios
- **Impact:** Teams with ≥80% coverage report 40-60% fewer production incidents

#### 3. Security Vulnerability Prevention
- **Automated Security Scans:** Bandit, pip-audit, and detect-secrets catch vulnerabilities
  - Hard-coded secrets detected before commit
  - Known dependency vulnerabilities flagged immediately
  - SQL injection and unsafe patterns blocked
- **Impact:** Early security fixes cost 10-100x less than post-production remediation

#### 4. Code Quality Metrics
- **Reliability Rating A:** Ensures code follows best practices
  - Dead code elimination reduces maintenance burden
  - Proper error handling prevents unexpected failures
  - Type safety reduces runtime errors
- **Impact:** High-quality code has 3-5x fewer production bugs than low-quality code

#### Industry Tool Standards

Our tool selection aligns with industry standards:

| Tool Category | Industry Standard | Our Choice | Alignment |
|--------------|-------------------|------------|-----------|
| **Code Quality** | SonarQube (most common) | SonarQube | **Standard** |
| **Linting** | Ruff (emerging standard) | Ruff | **Modern standard** |
| **Type Checking** | MyPy (Python standard) | MyPy | **Standard** |
| **Security Scanning** | Bandit + pip-audit | Bandit + pip-audit | **Standard** |
| **Test Framework** | pytest (Python standard) | pytest | **Standard** |

---

### How These Gates Meet Industry Standards

These quality gates align with widely accepted software quality and security standards. The goal is not to "get a certificate", but to follow proven practices that reduce production risk.

#### Quality model alignment (what "good" looks like)
- **ISO/IEC 25010 (Software Quality Model)**: We explicitly enforce reliability, maintainability, and security via gates (bugs=0, ratings=A, complexity limits, duplication limits).
- **Engineering best practices**: Mandatory tests + coverage on new code, consistent formatting, and static checks align with standard industry SDLC practices.

#### Security alignment (what "safe" looks like)
- **OWASP guidance (secure coding)**: Secrets detection, dependency audits, and SAST-style checks reduce common injection and insecure configuration risks.
- **CWE Top Weakness patterns**: Prevents typical issues like hard-coded credentials, unsafe eval/exec usage, and missing input validation patterns.
- **SEI CERT secure coding principles**: Encourages safe error handling, predictable behaviour, and defensive coding patterns.

#### Compliance readiness (why management cares)
- **Audit-friendly**: CI logs + Sonar reports provide evidence of checks, exceptions (waivers), and approvals.
- **Repeatable enforcement**: Automated checks reduce "manual only" dependency and improve consistency across teams.

### Technical Debt Reduction

Quality gates systematically reduce technical debt through **prevention, detection, and remediation**:

#### 1. Prevention of New Technical Debt

**Code Complexity Management:**
- **Cognitive Complexity ≤15:** Prevents overly complex code that becomes unmaintainable
- **Function Length Warnings:** Encourages smaller, focused functions
- **Impact:** Reduces future refactoring costs by 40-60%

**Code Duplication Control:**
- **≤3% Duplication Threshold:** Prevents copy-paste code patterns
- **Early Detection:** Catches duplication before it becomes widespread
- **Impact:** Reduces maintenance burden by eliminating duplicate bug fixes

**Documentation Standards:**
- **Mandatory Docstrings:** Ensures code is self-documenting
- **Type Hints Required:** Reduces need for external documentation
- **Impact:** Reduces onboarding time for new developers by 30-50%

#### 2. Detection of Existing Technical Debt

**Automated Debt Tracking:**
- **SonarQube Code Smells:** Identifies maintainability issues
- **Technical Debt Ratio:** Quantifies debt in hours/days
- **Trend Analysis:** Tracks debt accumulation over time

**Warning System:**
- **Non-Blocking Warnings:** Flags issues without blocking progress
- **Progressive Enforcement:** Allows gradual improvement
- **Impact:** Prevents debt accumulation while allowing incremental fixes

#### 3. Remediation Strategies

**Incremental Improvement:**
- **New Code Standards:** Prevents new debt while allowing legacy code
- **Component-Specific Rules:** Focuses effort on critical areas
- **Impact:** Reduces overall debt by 20-30% annually

**Refactoring Support:**
- **Complexity Warnings:** Identifies code needing refactoring
- **Test Coverage:** Enables safe refactoring with confidence
- **Impact:** Reduces refactoring risk by 50-70%

#### 4. Technical Debt Metrics

**Before Quality Gates (Estimated):**
- Code Duplication: 8-12%
- Average Complexity: 18-25
- Test Coverage: 45-60%
- Technical Debt Ratio: 15-25%

**After Quality Gates (Target):**
- Code Duplication: ≤3%
- Average Complexity: ≤15
- Test Coverage: ≥85%
- Technical Debt Ratio: ≤5%

**Reduction Impact:**
- **Maintenance Time:** 30-40% reduction
- **Bug Fix Time:** 50-60% reduction
- **Onboarding Time:** 30-50% reduction
- **Refactoring Risk:** 50-70% reduction

#### 5. Cost-Benefit Analysis

**Technical Debt Costs (Without Gates):**
- **Maintenance Overhead:** 20-30% of development time
- **Bug Fix Complexity:** 2-3x longer due to poor code quality
- **Onboarding Delays:** 2-4 weeks longer for new developers
- **Refactoring Risks:** High risk of introducing new bugs

**Quality Gate Investment:**
- **Setup Time:** 1-2 days initial setup
- **Ongoing Overhead:** 5-10 minutes per PR (automated)
- **Developer Training:** 2-4 hours for team

#### 6. Long-Term Benefits

**Code Maintainability:**
- **5-Year Outlook:** Code remains maintainable without major rewrites
- **Team Velocity:** Consistent velocity over time (no degradation)
- **Knowledge Transfer:** Self-documenting code reduces bus factor

**Business Continuity:**
- **Reduced Risk:** Lower risk of critical bugs affecting customers
- **Faster Feature Delivery:** Less time spent on bug fixes and refactoring
- **Competitive Advantage:** Higher quality code enables faster innovation

---

## Organizational Quality Standards

The Python AI SDK maintains high quality standards aligned with organizational best practices:

### Quality Thresholds
- **New Bugs:** 0
- **Security Hotspots:** 0
- **Coverage:** ≥ 85%
- **Duplications:** ≤ 3%
- **Reliability Rating:** A
- **Security Rating:** A

### Python AI/ML SDK Standards

| Aspect | Python AI/ML SDK | Rationale |
|--------|------------------|-----------|
| **Maintainability** | A required | AI complexity justifies strict standard |
| **Complexity (warning)** | > 10 | > 15 | Python team maintains higher quality bar |
| **Complexity (blocking)** | > 15 | > 15 | Aligned blocking threshold |
| **Type Checking** | MyPy required | Built-in | Language feature difference |
| **Async Patterns** | Heavily emphasized | Less common | AI operations are async-first |
| **Multi-tenant** | Mandatory | Context-dependent | AI SDK is multi-tenant by design |

---

## Final Quality Gate Summary

### Quality Gate: Python AI SDK Production Gate

**FAIL IF:**
```
New Bugs > 0
New Critical/Major Code Smells > 0
Reliability Rating < A
Security Rating < A
Maintainability Rating < A
Coverage on New Code < 85%
Duplications on New Code > 3%
CI Checks (format/lint/type/test/security) failing
```

**WARN IF:**
```
Cognitive Complexity 11-15
Function Length 80-120 LOC
Missing private method docstrings
Minor code smells (non-critical)
Low/Medium dependency vulnerabilities
```

---

## Document Structure

This document is organized as follows:

1. **Executive Summary:** Quick reference for quality gates and thresholds
2. **Business Value and Industry Alignment:** Why these gates reduce bugs, meet industry standards, and reduce technical debt
3. **Organizational Quality Standards:** Cross-team alignment and baseline thresholds
4. **Final Quality Gate Summary:** One-page "fail/warn" checklist
5. **Section 1:** Mandatory Operating Model (Branch Protection, Waiver Policy)
6. **Section 2:** Quality Gate Definition (PR Gate, Release Gate, Responsibility Split)
7. **Section 3:** Mandatory Code Rules (Formatting, Linting, Type Hints, Docstrings)
8. **Section 4:** Coverage Gate (≥ 85%)
9. **Section 5:** Complexity Limits (cognitive complexity thresholds + enforcement options)
10. **Section 6:** Security Rules (secrets, unsafe eval, dependency risk, required tools)
11. **Section 7:** PR Rules (templates, reviewer checklist, SDK-specific patterns)
12. **Section 8:** Component-Specific Quality Gates (Agent, RAG, Gateway, Cache, FaaS, ML)
13. **Section 9:** CI + Sonar enforcement templates (drop-in)
14. **Section 10:** Mandatory checkpoints (single-page summary)

**For detailed guidance on any topic, refer to the full sections below.**

---

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

No silent bypasses. No "we will fix later" without a tracked ticket.

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
6. Coverage threshold: **≥ 85% (new code)**
7. Security scans: secrets + SAST + dependency audit
8. Build/package verification

**Sonar checks**
1. **Quality Gate = PASSED**
2. **Coverage on New Code ≥ 85%**
3. **Duplications on New Code ≤ 3%**
4. Reliability rating on New Code = **A**
5. Security rating on New Code = **A**
6. Maintainability rating on New Code = **A**
   - **Exception:** Rating B allowed for complex AI algorithm implementations with:
     - Written justification in PR
     - Code review by 2+ engineers
     - Tracked technical debt ticket
7. **0 new Blocker/Critical** issues

> **Rule:** If Sonar or CI is red → **no merge**.

### 2.1.1 SonarQube vs CI Tools: Responsibility Split

**Clear separation of responsibilities prevents confusion and ensures accurate enforcement:**

| Responsibility | Tool(s) | What It Enforces |
|----------------|---------|------------------|
| **Bugs Detection** | SonarQube | Unreachable code, dead code, logic errors, undefined variables |
| **Security Hotspots** | SonarQube | Hard-coded credentials, SQL injection, dangerous patterns |
| **Code Smells** | SonarQube | Maintainability issues, complexity violations, code smells |
| **Code Duplication** | SonarQube CPD | Token-based duplicate code blocks (≥6 lines) |
| **Coverage on New Code** | SonarQube | Test coverage percentage on new/modified code |
| **Quality Ratings** | SonarQube | Reliability, Security, Maintainability ratings (A/B/C/D) |
| **Code Formatting** | CI Tools (Black, isort) | Line length, import sorting, code style |
| **Linting** | CI Tools (Ruff) | Unused imports, undefined names, style violations |
| **Type Checking** | CI Tools (MyPy) | Type annotation correctness, type errors |
| **Secrets Detection** | CI Tools (detect-secrets, bandit) | Hard-coded secrets, API keys, passwords |
| **Dependency Auditing** | CI Tools (pip-audit) | Known vulnerabilities in dependencies |
| **Test Execution** | CI Tools (Pytest) | Unit and integration test execution |
| **Build Verification** | CI Tools (python -m build) | Package builds successfully |

**Key Points:**
- **SonarQube** focuses on code quality metrics, bugs, security hotspots, and maintainability ratings
- **CI Tools** handle formatting, linting, type checking, secrets detection, and test execution
- **Both** enforce coverage thresholds (SonarQube via Quality Gate, CI via `--cov-fail-under=85`)
- **PR Decoration:** SonarQube results are displayed in pull requests via PR decoration (not preview mode)
- **Local Scans:** SonarQube scanner can be run locally for validation, but gates are enforced in CI/CD

### 2.2 Release Quality Gate (stricter)
All PR gates plus:
- cross-version run (e.g., 3.8–3.12)
- packaging install smoke test in clean environment
- vulnerability scan must have **0 High/Critical** (or approved waiver)

---

### 2.3 Quality Standards

The following thresholds are enforced for the Python AI/ML SDK:

#### 2.3.1 Quality Thresholds

| Metric | Python AI/ML SDK | Status |
|--------|------------------|--------|
| **New Bugs** | 0 | **Required** |
| **Security Hotspots (Unreviewed)** | 0 | **Required** |
| **Coverage on New Code** | ≥ 85% | **Required** |
| **Duplications on New Code** | ≤ 3% | **Required** |
| **Reliability Rating** | A | **Required** |
| **Security Rating** | A | **Required** |
| **Cognitive Complexity (Blocking)** | > 15 | **Required** |

#### 2.3.2 Python AI/ML SDK Standards

These standards reflect the unique requirements of the Python AI/ML SDK:

| Aspect | Python AI/ML SDK | Rationale |
|--------|------------------|-----------|
| **Maintainability Rating** | A required (B with waiver) | AI/ML complexity justifies strict standard |
| **Complexity Warning Threshold** | > 10 | Python team maintains higher quality bar |
| **Type Checking Requirement** | MyPy mandatory | Ensures type safety for AI operations |
| **Async Patterns Emphasis** | Heavy (async-first) | AI operations are inherently async |
| **Multi-tenant Architecture** | Mandatory everywhere | AI SDK is multi-tenant by design |
| **Test Coverage Focus** | Unit + Integration + E2E | AI workflows require E2E validation |
| **Component-Specific Rules** | RAG, Agent, Gateway, Memory | Domain-specific patterns |

#### 2.3.3 Rationale for Python-Specific Strictness

The Python AI/ML SDK has stricter standards in certain areas because:

1. **AI/ML Complexity:** LLM interactions, RAG systems, and agent orchestration are inherently more complex than typical microservices
2. **Non-Deterministic Behavior:** AI operations require more rigorous testing and error handling
3. **Cost Implications:** Token usage, API calls, and embeddings have direct cost impact requiring careful design
4. **Multi-Tenant Security:** AI systems handle sensitive data across tenants requiring strict isolation
5. **Production Reliability:** AI systems are mission-critical and require higher maintainability for long-term operation

#### 2.3.4 Synchronization Process

- **Quarterly Review:** Both teams review and align thresholds every quarter
- **Threshold Changes:** Any threshold change requires approval from both team leads
- **New Rules:** New rules are evaluated for cross-team applicability
- **Tooling Alignment:** Where possible, use the same tools (SonarQube, security scanners)

---

### 2.4 Code Duplication Rules

**Threshold:** ≤ 3% duplications on new code

This section defines what constitutes code duplication, when it's acceptable, and how to fix it.

#### 2.4.1 What Counts as Duplication

**SonarQube CPD (Copy/Paste Detector) detects duplication as:**
- **Identical code blocks** ≥ 6 lines in length (token-based matching)
- **Copy-pasted functions** with minor variable name changes
- **Duplicated logic patterns** across different modules
- **Similar code structures** with only variable/function name differences

> **Note:** SonarQube CPD uses token-based analysis, not string literal matching. Repeated string literals are tracked separately as code smells (not duplication) and should be centralized as a coding best practice, but they do not count toward the duplication percentage.

**Measurement:**
```
Duplication % = (Duplicated Lines / Total Lines) × 100
```

#### 2.4.2 Acceptable Exceptions

The following are **NOT** considered violations:

1. **Test Setup/Teardown Boilerplate**
   - Pytest fixtures with similar structure
   - Mock configurations for different test classes
   - Test data initialization patterns

2. **Type Definitions**
   - Pydantic models with similar field patterns
   - TypedDict definitions
   - Dataclass definitions with standard fields

3. **Protocol Implementations**
   - Interface/Protocol method implementations that must match signatures
   - Abstract base class method stubs

4. **Configuration Patterns**
   - Service initialization with similar parameters
   - Standard error handling patterns

#### 2.4.3 How to Fix Duplication

**Example 1: Duplicated Validation Logic**

```python
# BAD: Duplicated validation logic
def validate_agent_input(data: Dict[str, Any]) -> bool:
    if not data.get("name"):
        raise ValueError("name is required")
    if len(data.get("name", "")) < 3:
        raise ValueError("name must be at least 3 characters")
    if not data.get("tenant_id"):
        raise ValueError("tenant_id is required")
    return True

def validate_tool_input(data: Dict[str, Any]) -> bool:
    if not data.get("name"):
        raise ValueError("name is required")
    if len(data.get("name", "")) < 3:
        raise ValueError("name must be at least 3 characters")
    if not data.get("tenant_id"):
        raise ValueError("tenant_id is required")
    return True

# GOOD: Extracted common validation
from typing import Dict, Any, Optional

def validate_name_field(
    data: Dict[str, Any], 
    min_length: int = 3,
    field_name: str = "name"
) -> None:
    """Validate name field with configurable constraints."""
    value = data.get(field_name)
    if not value:
        raise ValueError(f"{field_name} is required")
    if len(value) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters")

def validate_tenant_id(data: Dict[str, Any]) -> None:
    """Validate tenant_id field."""
    if not data.get("tenant_id"):
        raise ValueError("tenant_id is required")

def validate_agent_input(data: Dict[str, Any]) -> bool:
    """Validate agent input data."""
    validate_name_field(data)
    validate_tenant_id(data)
    return True

def validate_tool_input(data: Dict[str, Any]) -> bool:
    """Validate tool input data."""
    validate_name_field(data)
    validate_tenant_id(data)
    return True
```

**Example 2: String Literal Centralization (Coding Best Practice)**

> **Note:** While repeated string literals don't count as Sonar duplication, centralizing them is a coding best practice for maintainability.

```python
# BAD: Repeated string literals (maintenance risk)
def create_agent_cache_key(agent_id: str, tenant_id: str) -> str:
    return f"agent:{tenant_id}:{agent_id}"

def get_agent_from_cache(agent_id: str, tenant_id: str) -> Optional[Agent]:
    key = f"agent:{tenant_id}:{agent_id}"
    return cache.get(key)

def invalidate_agent_cache(agent_id: str, tenant_id: str) -> None:
    key = f"agent:{tenant_id}:{agent_id}"
    cache.delete(key)

# GOOD: Centralized key generation
AGENT_CACHE_PREFIX = "agent"

def create_agent_cache_key(agent_id: str, tenant_id: str) -> str:
    """Generate standardized agent cache key."""
    return f"{AGENT_CACHE_PREFIX}:{tenant_id}:{agent_id}"

def get_agent_from_cache(agent_id: str, tenant_id: str) -> Optional[Agent]:
    """Retrieve agent from cache."""
    key = create_agent_cache_key(agent_id, tenant_id)
    return cache.get(key)

def invalidate_agent_cache(agent_id: str, tenant_id: str) -> None:
    """Invalidate agent cache entry."""
    key = create_agent_cache_key(agent_id, tenant_id)
    cache.delete(key)
```

**Example 3: Duplicated Database Query Patterns**

```python
# BAD: Duplicated query patterns
async def get_agent_by_id(db: DatabaseConnection, agent_id: str, tenant_id: str) -> Optional[Dict]:
    query = "SELECT * FROM agents WHERE agent_id = %s AND tenant_id = %s"
    result = await db.execute_query(query, (agent_id, tenant_id))
    return result[0] if result else None

async def get_tool_by_id(db: DatabaseConnection, tool_id: str, tenant_id: str) -> Optional[Dict]:
    query = "SELECT * FROM tools WHERE tool_id = %s AND tenant_id = %s"
    result = await db.execute_query(query, (tool_id, tool_id))
    return result[0] if result else None

# GOOD: Generic repository pattern
from typing import TypeVar, Generic, Optional, Dict, Any

T = TypeVar('T')

class TenantScopedRepository(Generic[T]):
    """Generic repository with tenant isolation."""
    
    def __init__(self, db: DatabaseConnection, table_name: str, id_field: str):
        self.db = db
        self.table_name = table_name
        self.id_field = id_field
    
    async def get_by_id(self, id_value: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID with tenant isolation."""
        query = f"SELECT * FROM {self.table_name} WHERE {self.id_field} = %s AND tenant_id = %s"
        result = await self.db.execute_query(query, (id_value, tenant_id))
        return result[0] if result else None

# Usage
agent_repo = TenantScopedRepository(db, "agents", "agent_id")
tool_repo = TenantScopedRepository(db, "tools", "tool_id")

agent = await agent_repo.get_by_id("agent_123", "tenant_456")
tool = await tool_repo.get_by_id("tool_789", "tenant_456")
```

#### 2.4.4 Monitoring and Enforcement

**CI Pipeline:**
```yaml
# .github/workflows/quality-gate.yml
- name: Check Code Duplication
  run: |
    sonar-scanner \
      -Dsonar.projectKey=motadata-python-sdk \
      -Dsonar.sources=src \
      -Dsonar.cpd.exclusions=**/tests/**,**/__init__.py
```

**Local Validation (Before Commit):**
```bash
# Run SonarQube scanner locally for validation
# Note: This validates code quality but does not enforce gates
# Quality gates are enforced in CI/CD pipelines
sonar-scanner

# View results in SonarQube dashboard
# PR decoration will show results in your pull request
```

**SonarQube Dashboard:**
- Monitor duplication percentage over time
- Track duplication hotspots
- Review duplication trends per component

#### 2.4.5 Waiver Process

If duplication > 3% is unavoidable:

1. **Document Justification:** Explain why duplication cannot be eliminated
2. **Risk Assessment:** Assess maintenance risk
3. **Remediation Plan:** Create ticket for future refactoring
4. **Approval Required:** 2+ engineer review + tech lead approval
5. **Time Bound:** Set deadline for remediation (max 2 sprints)

**Example Waiver Comment:**
```python
# DUPLICATION WAIVER: TECH-1234
# Justification: Legacy LLM provider adapters have similar structure
#                but different authentication patterns that cannot be
#                easily abstracted without breaking compatibility.
# Risk: Medium - Changes require updates to multiple adapters
# Remediation: Refactor to strategy pattern in Q2 2026 (TECH-1235)
# Approved by: @tech-lead, @senior-engineer-1, @senior-engineer-2
```

---

## 3) Mandatory Code Rules (with examples)

### 3.1 Formatting rules (mandatory)
**Rule**
- Black + isort output is the canonical style. No "pretty formatting" by hand.

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

### 3.4 Project Structure & Naming Conventions (Mandatory)

#### 3.4.1 Project Structure

**Standard SDK Structure:**
```
motadata-python-ai-sdk/
├── src/
│   ├── core/                    # Core AI components
│   │   ├── agno_agent_framework/
│   │   ├── rag/
│   │   ├── litellm_gateway/
│   │   ├── cache_mechanism/
│   │   ├── machine_learning/
│   │   └── ...
│   ├── faas/                    # FaaS Services
│   │   ├── services/
│   │   │   ├── agent_service/
│   │   │   ├── rag_service/
│   │   │   └── ...
│   │   └── shared/
│   ├── integrations/           # Integration components
│   └── tests/                   # Test suite
│       ├── unit_tests/
│       ├── integration_tests/
│       └── benchmarks/
├── examples/                    # Usage examples
├── docs/                        # Documentation
└── pyproject.toml              # Project configuration
```

#### 3.4.2 Naming Conventions

**File Naming:**
- Use `snake_case` for all Python files: `rag_system.py`, `agent_framework.py`
- Test files must start with `test_`: `test_agent.py`, `test_rag_system.py`
- Module files: `__init__.py` (always lowercase)

**Class Naming:**
- Use `PascalCase`: `RAGSystem`, `LiteLLMGateway`, `AgentMemory`
- Exception classes must end with `Error`: `AgentError`, `GatewayError`, `RAGError`

**Function/Method Naming:**
- Use `snake_case`: `create_agent()`, `query_async()`, `ingest_document()`
- Async functions should end with `_async`: `query_async()`, `generate_async()`
- Factory functions should start with `create_`: `create_agent()`, `create_rag_system()`

**Variable Naming:**
- Use `snake_case`: `tenant_id`, `query_text`, `cache_key`
- Constants use `UPPER_SNAKE_CASE`: `DEFAULT_TTL`, `MAX_RETRIES`

**Module/Package Naming:**
- Use `snake_case`: `agno_agent_framework`, `litellm_gateway`, `cache_mechanism`

**Examples:**
```python
# GOOD (follows conventions)
class RAGSystem:
    async def query_async(self, query_text: str, tenant_id: str) -> dict:
        cache_key = f"rag:{tenant_id}:{hash(query_text)}"
        return await self._execute_query(query_text, tenant_id)

def create_rag_system(db, gateway, **kwargs) -> RAGSystem:
    return RAGSystem(db=db, gateway=gateway, **kwargs)

# BAD (violates conventions)
class ragSystem:  # Should be PascalCase
    async def Query(self, queryText: str, tenantId: str):  # Should be snake_case
        CacheKey = f"rag:{tenantId}"  # Should be snake_case
```

---

### 3.5 Docstring Standards (Mandatory)

#### 3.5.1 Docstring Format

**Rule:** All public classes, functions, and methods must have docstrings using Google-style format.

**Required Elements:**
- One-line summary
- Detailed description (if needed)
- Args section (for functions/methods)
- Returns section (for functions/methods)
- Raises section (if exceptions are raised)
- Examples section (for complex functions)

#### 3.5.2 Docstring Examples

**Class Docstring:**
```python
class RAGSystem:
    """
    Complete RAG system integrating document processing, retrieval, and generation.
    
    Handles document ingestion, vector search, and LLM-based answer generation
    with tenant isolation and caching support.
    
    Attributes:
        db: Database connection for vector storage
        gateway: LiteLLM Gateway for LLM operations
        embedding_model: Model name for embeddings
        generation_model: Model name for text generation
        cache: Optional cache mechanism for performance
    """
```

**Function Docstring:**
```python
async def query_async(
    self,
    query_text: str,
    top_k: int = 5,
    tenant_id: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Query RAG system asynchronously with tenant isolation.
    
    Processes a natural language query by:
    1. Generating embeddings for the query
    2. Performing vector similarity search
    3. Generating answer using retrieved context
    
    Args:
        query_text: Natural language query string
        top_k: Number of top documents to retrieve (default: 5)
        tenant_id: Tenant identifier for multi-tenant isolation (required)
        **kwargs: Additional parameters passed to gateway
    
    Returns:
        Dictionary containing:
            - answer: Generated answer text
            - sources: List of retrieved document chunks
            - metadata: Query metadata (model, tokens, etc.)
    
    Raises:
        ValueError: If tenant_id is not provided
        GatewayError: If LLM gateway call fails
        DatabaseError: If vector search fails
    
    Example:
        ```python
        result = await rag.query_async(
            query_text="What is machine learning?",
            top_k=5,
            tenant_id="tenant_123"
        )
        print(result["answer"])
        ```
    """
```

**Factory Function Docstring:**
```python
def create_rag_system(
    db: DatabaseConnection,
    gateway: LiteLLMGateway,
    embedding_model: str = "text-embedding-3-small",
    **kwargs: Any
) -> RAGSystem:
    """
    Factory function to create a RAG system instance.
    
    Creates and configures a RAG system with sensible defaults.
    All components are initialized and ready for use.
    
    Args:
        db: Database connection (required)
        gateway: LiteLLM Gateway instance (required)
        embedding_model: Model for embedding generation (default: "text-embedding-3-small")
        **kwargs: Additional configuration options:
            - generation_model: Model for text generation (default: "gpt-4")
            - cache: Optional cache mechanism
            - chunk_size: Document chunk size (default: 1000)
            - chunk_overlap: Chunk overlap size (default: 200)
    
    Returns:
        Configured RAGSystem instance
    
    Raises:
        ValueError: If required parameters are missing
        ConfigurationError: If configuration is invalid
    
    Example:
        ```python
        rag = create_rag_system(
            db=db_connection,
            gateway=gateway_instance,
            embedding_model="text-embedding-3-small",
            chunk_size=1000
        )
        ```
    """
```

**Bad Docstring Examples:**
```python
# BAD (no docstring)
class RAGSystem:
    def query(self, q):
        pass

# BAD (incomplete docstring)
def query(self, q):
    """Query RAG system."""
    pass

# BAD (wrong format)
def query(self, q):
    """
    @param q: query
    @return: result
    """
    pass
```

#### 3.5.3 Docstring Enforcement

**CI Enforcement:**
- Missing docstrings on public APIs → **FAILS CI**
- Incomplete docstrings (missing Args/Returns) → **WARNING** (for now, will become FAIL in future)
- Private methods (`_method`) → **WARNING** (recommended but not required)

**Tools:**
- Use `pydocstyle` for docstring checking:
```bash
pydocstyle src --convention=google
```

---

### 3.6 CI Failure vs Warnings (Mandatory)

#### 3.6.1 What FAILS CI (Merge-Blocking)

**These checks MUST pass or PR cannot be merged:**

1. **Format Check (FAILS CI)**
   - Black formatting violations
   - isort import ordering violations
   - **Action:** PR is blocked, must fix

2. **Lint Check (FAILS CI)**
   - Unused imports/variables
   - Undefined names
   - Syntax errors
   - Dangerous patterns (`eval`, `exec`, bare `except`)
   - **Action:** PR is blocked, must fix

3. **Type Check (FAILS CI)**
   - Missing type hints on public APIs
   - Type errors (incompatible types)
   - `Any` usage without justification
   - **Action:** PR is blocked, must fix

4. **Unit Tests (FAILS CI)**
   - Any test failure
   - Test timeouts
   - **Action:** PR is blocked, must fix

5. **Coverage Threshold (FAILS CI)**
   - New code coverage < 85%
   - Overall coverage drops below threshold
   - **Action:** PR is blocked, must add tests

6. **Security Scans (FAILS CI)**
   - Secrets detected in code
   - High/Critical vulnerabilities
   - Unsafe patterns (`eval`, `exec`, `shell=True`)
   - **Action:** PR is blocked, must fix

7. **Build Verification (FAILS CI)**
   - Package build fails
   - Import errors
   - **Action:** PR is blocked, must fix

8. **Sonar Quality Gate (FAILS CI)**
   - Quality Gate = FAILED
   - New Blocker/Critical issues
   - Coverage on new code < 85%
   - Security rating < A
   - **Action:** PR is blocked, must fix

#### 3.6.2 What are WARNINGS (Non-Blocking)

**These checks generate warnings but do NOT block merge:**

1. **Code Complexity (WARNING)**
   - Cyclomatic complexity > 10 (but ≤ 15)
   - Function length > 80 LOC (but ≤ 120 LOC)
   - **Action:** Warning in PR, review recommended

2. **Docstring Completeness (WARNING)**
   - Missing docstrings on private methods
   - Incomplete docstrings (missing optional sections)
   - **Action:** Warning in PR, fix recommended

3. **Type Hints (WARNING)**
   - Missing type hints on private methods
   - `Any` usage with justification comment
   - **Action:** Warning in PR, improve recommended

4. **Sonar Code Smells (WARNING)**
   - Minor code smells (not bugs/vulnerabilities)
   - Maintainability issues (non-critical)
   - **Action:** Warning in PR, technical debt

5. **Dependency Vulnerabilities (WARNING)**
   - Low/Medium severity vulnerabilities
   - Outdated dependencies (non-critical)
   - **Action:** Warning in PR, update recommended

#### 3.6.3 CI Status Summary

| Check | Status | Action |
|-------|--------|--------|
| Format check fails | **FAILS CI** | Block merge, must fix |
| Lint errors | **FAILS CI** | Block merge, must fix |
| Type errors | **FAILS CI** | Block merge, must fix |
| Test failures | **FAILS CI** | Block merge, must fix |
| Coverage < 85% | **FAILS CI** | Block merge, must add tests |
| Secrets detected | **FAILS CI** | Block merge, must remove |
| Sonar gate failed | **FAILS CI** | Block merge, must fix |
| Complexity > 15 | **Warning** | Review recommended |
| Missing private docstrings | **Warning** | Improve recommended |
| Code smells (minor) | **Warning** | Technical debt |

#### 3.6.4 Example CI Output

**FAILING CI (Blocked):**
```
Format check: FAILED
   - src/core/rag/rag_system.py:15:1 - Line too long
   - src/core/agent/agent.py:42:3 - Import not sorted

Lint check: FAILED
   - src/core/gateway/gateway.py:23 - Unused import 'os'
   - src/core/cache/cache.py:45 - Undefined name 'dragonfly_client'

Type check: FAILED
   - src/core/rag/rag_system.py:67 - Missing return type annotation

Coverage: FAILED
   - New code coverage: 65% (required: 85%)
   - Missing coverage in: src/core/rag/retriever.py

→ PR BLOCKED: Must fix all failures before merge
```

**PASSING CI (with warnings):**
```
Format check: PASSED
Lint check: PASSED
Type check: PASSED
Tests: PASSED (120 tests, 0 failures)
Coverage: PASSED (85% new code coverage)
Security: PASSED (no secrets, no high vulnerabilities)
Sonar: PASSED (Quality Gate: PASSED)

Warnings:
   - src/core/agent/agent.py:234 - Function complexity: 12 (recommended: ≤10)
   - src/core/rag/rag_system.py:156 - Missing docstring on private method
   - Sonar: 3 minor code smells detected

→ PR APPROVED: Can merge (warnings are non-blocking)
```

---

## 4) Coverage Gate (85%) - Mandatory (with examples)

### 4.1 Coverage threshold (mandatory)
- **Coverage on New Code ≥ 85%** (Sonar gate)
- CI must enforce `--cov-fail-under=85` for immediate feedback.
- This threshold is 5% higher than the previous standard to align with organizational best practices.

**Repo current-state note**
- `pytest-cov` exists, but `test-cov` does not enforce threshold today.

### 4.2 Update Makefile (drop-in replacement)
Replace `test-cov` with:

```make
test-cov: ## Run tests with coverage report + enforce threshold
	$(PYTHON) -m pytest $(TESTS_DIR) \
		--cov=$(SRC_DIR) --cov-report=term-missing --cov-report=xml \
		--cov-fail-under=85
```

### 4.3 Example: what "good coverage" means
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

#### 5.1.1 Cognitive Complexity Thresholds

**Python AI SDK Standard:**

| Cognitive Complexity | Action | Status |
|---------------------|--------|--------|
| **≤ 10** | Ideal - No issues | **PASS** |
| **11-15** | Warning - Review recommended | **WARN** (non-blocking) |
| **> 15** | Must refactor or get waiver | **FAIL** (blocks merge) |

**Python Team Quality Bar:**
- The blocking threshold is 15, with a warning at 10 to encourage simpler, more maintainable code for AI/ML operations.

**Rationale for Threshold 15:**
- Industry best practice for maintainability
- Complex AI algorithms may legitimately approach this limit
- Balances code quality with practical development needs
- Functions > 15 are difficult to test and maintain

#### 5.1.2 Additional Complexity Limits

- **Cyclomatic complexity per function: ≤ 10** (recommended)
- **Function length soft limit: ≤ 80 LOC** (warning at 80-120, blocks at >120)
- **Nesting depth: ≤ 4 levels** (deeply nested code is hard to understand)

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

## 6) Security Rules (mandatory) - secrets, unsafe eval, dependency risk

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

## 7) PR Rules (mandatory) - templates and checkpoints

### 7.1 PR requirements (merge-blocking)
- [ ] No direct commits to `main`
- [ ] PR has description + risk assessment
- [ ] CI green
- [ ] Sonar gate green
- [ ] Coverage ≥ 85% new code
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
- [ ] coverage >= 85%
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

## 7.5 SDK-Specific Coding Patterns (Mandatory)

### 7.5.1 Async-First Pattern

**Rule:** All I/O operations (database, HTTP, LLM calls) must use async/await.

**Bad (synchronous blocking):**
```python
# BAD (blocks event loop)
def query_rag(self, query: str) -> dict:
    result = self.db.execute_query(query)  # Blocks
    return result
```

**Good (async):**
```python
# GOOD (non-blocking)
async def query_rag_async(self, query: str) -> dict[str, Any]:
    result = await self.db.execute_query_async(query)
    return result
```

**Example from SDK (RAG System):**
```python
# src/core/rag/rag_system.py
async def query_async(
    self,
    query_text: str,
    top_k: int = 5,
    tenant_id: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Async query method - required for production."""
    # All I/O is async
    embeddings = await self.gateway.embed_async(query_text, model=self.embedding_model)
    results = await self.vector_ops.search_async(embeddings[0], top_k=top_k, tenant_id=tenant_id)
    # ...
```

### 7.5.2 Tenant Isolation Pattern

**Rule:** All components must support `tenant_id` parameter for multi-tenant isolation.

**Bad (no tenant isolation):**
```python
# BAD (no tenant context)
def get_cache(self, key: str) -> Any:
    return self.cache.get(key)  # No tenant isolation
```

**Good (tenant-scoped):**
```python
# GOOD (tenant isolation)
def get_cache(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
    if not tenant_id:
        raise ValueError("tenant_id is required for multi-tenant operations")
    return self.cache.get(key, tenant_id=tenant_id)
```

**Example from SDK (Cache Mechanism):**
```python
# src/core/cache_mechanism/cache.py
def _namespaced_key(self, key: str, tenant_id: Optional[str] = None) -> str:
    """Create namespaced cache key with optional tenant isolation."""
    if tenant_id:
        return f"{self.config.namespace}:{tenant_id}:{key}"
    return f"{self.config.namespace}:{key}"

def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
    namespaced = self._namespaced_key(key, tenant_id=tenant_id)
    # ...
```

### 7.5.3 Dependency Injection Pattern

**Rule:** Components receive dependencies via constructor injection, not global imports.

**Bad (tight coupling):**
```python
# BAD (hard dependency)
from src.core.litellm_gateway import LiteLLMGateway

class Agent:
    def __init__(self):
        self.gateway = LiteLLMGateway()  # Hard dependency
```

**Good (dependency injection):**
```python
# GOOD (injected dependency)
class Agent:
    def __init__(self, gateway: LiteLLMGateway, tenant_id: Optional[str] = None):
        self.gateway = gateway  # Injected
        self.tenant_id = tenant_id
```

**Example from SDK (Agent Framework):**
```python
# src/core/agno_agent_framework/agent.py
class Agent(BaseModel):
    gateway: Optional[Any] = None  # LiteLLM Gateway instance (injected)
    tenant_id: Optional[str] = None  # Tenant context for multi-tenant SaaS
    
    async def execute_task(self, task: AgentTask) -> Any:
        # Uses injected gateway
        response = await self.gateway.generate_async(
            prompt=task.prompt,
            model=self.llm_model,
            tenant_id=self.tenant_id or task.tenant_id,
        )
```

### 7.5.4 Factory Function Pattern

**Rule:** Use factory functions for component creation (not direct class instantiation).

**Bad (direct instantiation):**
```python
# BAD (complex initialization)
gateway = LiteLLMGateway(
    api_key=os.getenv("API_KEY"),
    provider="openai",
    default_model="gpt-4",
    enable_caching=True,
    cache_ttl=3600,
    # ... many parameters
)
```

**Good (factory function):**
```python
# GOOD (simplified creation)
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(
    api_key=os.getenv("API_KEY"),
    provider="openai",
    default_model="gpt-4"
)
```

**Example from SDK (Gateway Factory):**
```python
# src/core/litellm_gateway/functions.py
def create_gateway(
    api_key: str,
    provider: str = "openai",
    default_model: str = "gpt-4",
    **kwargs: Any
) -> LiteLLMGateway:
    """Factory function to create a LiteLLM Gateway instance."""
    config = GatewayConfig(
        enable_caching=kwargs.get("enable_caching", True),
        cache_ttl=kwargs.get("cache_ttl", 3600),
        # ... sensible defaults
    )
    return LiteLLMGateway(api_key=api_key, provider=provider, default_model=default_model, config=config)
```

### 7.5.5 Error Handling Pattern

**Rule:** Use custom exception hierarchy, never bare `except:`.

**Bad (bare except):**
```python
# BAD (swallows all errors)
try:
    result = await gateway.generate_async(prompt)
except:
    return None  # Lost error context
```

**Good (specific exceptions):**
```python
# GOOD (specific error handling)
from src.core.exceptions import GatewayError, RateLimitError

try:
    result = await gateway.generate_async(prompt, tenant_id=tenant_id)
except RateLimitError as e:
    logger.warning(f"Rate limit exceeded for tenant {tenant_id}: {e}")
    raise  # Re-raise with context
except GatewayError as e:
    logger.error(f"Gateway error for tenant {tenant_id}: {e}")
    raise
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise GatewayError(f"Unexpected error: {e}") from e
```

**Example from SDK (Exception Hierarchy):**
```python
# src/core/agno_agent_framework/exceptions.py
class AgentError(Exception):
    """Base exception for agent errors."""
    pass

class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""
    pass

class AgentConfigurationError(AgentError):
    """Raised when agent configuration is invalid."""
    pass
```

### 7.5.6 Type Hints for Public APIs

**Rule:** All public methods must have complete type hints (no `Any` unless justified).

**Bad (missing types):**
```python
# BAD (no type hints)
def query(self, query, top_k=5, **kwargs):
    # ...
```

**Good (complete types):**
```python
# GOOD (complete type hints)
from typing import Dict, Any, Optional, List

async def query_async(
    self,
    query_text: str,
    top_k: int = 5,
    tenant_id: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Query RAG system with type hints."""
    # ...
```

**Example from SDK (RAG System):**
```python
# src/core/rag/rag_system.py
async def query_async(
    self,
    query_text: str,
    top_k: int = 5,
    tenant_id: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Query RAG system asynchronously."""
    # All parameters and return types are explicit
```

### 7.5.7 Logging Pattern

**Rule:** Use structured logging with context (tenant_id, request_id, etc.).

**Bad (unstructured logging):**
```python
# BAD (no context)
print(f"Processing request: {request}")
```

**Good (structured logging):**
```python
# GOOD (structured with context)
import logging

logger = logging.getLogger(__name__)

logger.info(
    "Processing RAG query",
    extra={
        "tenant_id": tenant_id,
        "query": query_text,
        "top_k": top_k,
        "component": "rag_system"
    }
)
```

**Example from SDK:**
```python
# src/core/rag/rag_system.py
logger = logging.getLogger(__name__)

async def query_async(self, query_text: str, tenant_id: Optional[str] = None, **kwargs):
    logger.info(
        "RAG query initiated",
        extra={"tenant_id": tenant_id, "query_length": len(query_text)}
    )
    # ...
```

---

## 8) Component-Specific Quality Gates (Mandatory)

Each component in the SDK has specific rules and patterns that must be followed.

### 8.1 Agent Framework Component Rules

**Location:** `src/core/agno_agent_framework/`

#### 8.1.1 Mandatory Rules

1. **Agent State Management:**
   - All agents must track status (`idle`, `running`, `paused`, `stopped`, `error`)
   - State transitions must be thread-safe (use `asyncio.Lock`)

2. **Memory Management:**
   - Agents must support optional memory (episodic, semantic, short-term, long-term)
   - Memory must be tenant-scoped
   - Memory persistence must be optional (in-memory or database-backed)

3. **Tool Execution:**
   - All tools must be registered via `ToolRegistry`
   - Tool execution must be async
   - Tool errors must not crash the agent

4. **Gateway Dependency:**
   - Agents must receive `LiteLLMGateway` via dependency injection
   - All LLM calls must go through the gateway (never direct provider calls)

#### 8.1.2 Code Examples

**Good Agent Implementation:**
```python
# src/core/agno_agent_framework/agent.py
from typing import Optional, Dict, Any
from pydantic import BaseModel
from ..litellm_gateway import LiteLLMGateway
from .exceptions import AgentExecutionError, AgentStateError

class Agent(BaseModel):
    agent_id: str
    tenant_id: Optional[str] = None
    name: str
    gateway: Optional[LiteLLMGateway] = None  # Injected dependency
    status: AgentStatus = AgentStatus.IDLE
    memory: Optional[AgentMemory] = None
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute agent task with proper error handling."""
        if self.status != AgentStatus.IDLE:
            raise AgentStateError(f"Agent {self.agent_id} is not idle")
        
        if not self.gateway:
            raise AgentConfigurationError("Gateway is required")
        
        try:
            self.status = AgentStatus.RUNNING
            # Use gateway for LLM calls
            response = await self.gateway.generate_async(
                prompt=task.prompt,
                model=self.llm_model,
                tenant_id=self.tenant_id,
            )
            # Store in memory if configured
            if self.memory:
                await self.memory.add_episodic(
                    content=response.text,
                    metadata={"task_id": task.task_id}
                )
            return {"result": response.text, "task_id": task.task_id}
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.exception(f"Agent {self.agent_id} execution failed: {e}")
            raise AgentExecutionError(f"Task execution failed: {e}") from e
        finally:
            self.status = AgentStatus.IDLE
```

**Bad Agent Implementation:**
```python
# BAD (violates multiple rules)
class Agent:
    def __init__(self):
        self.gateway = LiteLLMGateway()  # Hard dependency, no injection
        self.status = "idle"  # String, not enum
    
    def execute_task(self, task):  # Not async
        try:
            result = self.gateway.generate(task.prompt)  # Sync call, no tenant_id
            return result
        except:  # Bare except
            return None  # Swallows errors
```

#### 8.1.3 Testing Requirements

**Unit Tests Must Cover:**
- Agent state transitions
- Task execution with success/failure paths
- Memory operations (add, retrieve, clear)
- Tool execution and error handling
- Gateway integration (mocked)

**Example Test:**
```python
# src/tests/unit_tests/test_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.core.agno_agent_framework import create_agent, AgentStatus

@pytest.mark.asyncio
async def test_agent_execute_task_success():
    """Test successful task execution."""
    gateway = MagicMock()
    gateway.generate_async = AsyncMock(return_value=MagicMock(text="Result"))
    
    agent = create_agent(
        agent_id="test_agent",
        name="Test Agent",
        gateway=gateway,
        tenant_id="tenant_123"
    )
    
    task = AgentTask(task_id="task_1", task_type="test", parameters={"prompt": "Hello"})
    result = await agent.execute_task(task)
    
    assert result["result"] == "Result"
    assert agent.status == AgentStatus.IDLE
    gateway.generate_async.assert_called_once()
```

### 8.2 RAG System Component Rules

**Location:** `src/core/rag/`

#### 8.2.1 Mandatory Rules

1. **Document Processing:**
   - All document ingestion must be async
   - Documents must be chunked with configurable strategy
   - Metadata extraction must be optional but recommended

2. **Vector Operations:**
   - All vector searches must be tenant-scoped
   - Embeddings must be cached (via CacheMechanism)
   - Vector index management must be handled by `VectorIndexManager`

3. **Gateway Integration:**
   - Embedding generation must use gateway
   - Text generation must use gateway
   - All gateway calls must include `tenant_id`

4. **Error Handling:**
   - Document processing errors must not crash the system
   - Invalid queries must return empty results, not exceptions

#### 8.2.2 Code Examples

**Good RAG Implementation:**
```python
# src/core/rag/rag_system.py
from typing import Optional, Dict, Any, List
from ..litellm_gateway import LiteLLMGateway
from ..postgresql_database.connection import DatabaseConnection
from ..cache_mechanism import CacheMechanism

class RAGSystem:
    def __init__(
        self,
        db: DatabaseConnection,
        gateway: LiteLLMGateway,  # Required dependency
        embedding_model: str = "text-embedding-3-small",
        cache: Optional[CacheMechanism] = None,
        **kwargs: Any
    ):
        self.db = db
        self.gateway = gateway
        self.embedding_model = embedding_model
        self.cache = cache or CacheMechanism()
    
    async def query_async(
        self,
        query_text: str,
        top_k: int = 5,
        tenant_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Query RAG system with proper tenant isolation."""
        if not tenant_id:
            raise ValueError("tenant_id is required for multi-tenant operations")
        
        # Check cache first
        cache_key = f"rag_query:{hash(query_text)}"
        cached = self.cache.get(cache_key, tenant_id=tenant_id)
        if cached:
            logger.info("RAG query cache hit", extra={"tenant_id": tenant_id})
            return cached
        
        try:
            # Generate embeddings via gateway
            embeddings = await self.gateway.embed_async(
                query_text,
                model=self.embedding_model,
                tenant_id=tenant_id
            )
            
            # Vector search (tenant-scoped)
            results = await self.vector_ops.search_async(
                embeddings[0],
                top_k=top_k,
                tenant_id=tenant_id
            )
            
            # Generate response via gateway
            context = "\n".join([r["content"] for r in results])
            response = await self.gateway.generate_async(
                prompt=f"Context: {context}\n\nQuestion: {query_text}",
                tenant_id=tenant_id
            )
            
            result = {
                "answer": response.text,
                "sources": results,
                "metadata": {"top_k": top_k, "model": self.embedding_model}
            }
            
            # Cache result
            self.cache.set(cache_key, result, tenant_id=tenant_id, ttl=3600)
            return result
            
        except Exception as e:
            logger.exception(f"RAG query failed for tenant {tenant_id}: {e}")
            return {"answer": "", "sources": [], "error": str(e)}
```

**Bad RAG Implementation:**
```python
# BAD (violates multiple rules)
class RAGSystem:
    def query(self, query):  # Not async, no tenant_id
        # Direct API call (bypasses gateway)
        embeddings = openai.Embedding.create(input=query)
        # No tenant isolation
        results = db.search(embeddings)
        return results  # No error handling
```

#### 8.2.3 Testing Requirements

**Unit Tests Must Cover:**
- Document ingestion (sync and async)
- Query processing with cache hits/misses
- Vector search operations
- Gateway integration (mocked)
- Tenant isolation
- Error handling (invalid queries, gateway failures)

### 8.3 Gateway Component Rules

**Location:** `src/core/litellm_gateway/`

#### 8.3.1 Mandatory Rules

1. **Provider Abstraction:**
   - Never use provider SDKs directly (always via LiteLLM)
   - Support multiple providers (OpenAI, Anthropic, Google, etc.)
   - Provider selection must be configurable

2. **Caching:**
   - Response caching must be enabled by default
   - Cache keys must include tenant_id
   - Cache TTL must be configurable

3. **Rate Limiting:**
   - Rate limiting must be per-tenant
   - Rate limit configuration must be flexible
   - Rate limit errors must be specific exceptions

4. **Circuit Breaker:**
   - Circuit breaker must be enabled for external calls
   - Circuit breaker state must be logged
   - Fallback providers must be supported

5. **LLMOps Tracking:**
   - All LLM calls must be logged for cost tracking
   - Token usage must be recorded
   - Response times must be measured

#### 8.3.2 Code Examples

**Good Gateway Implementation:**
```python
# src/core/litellm_gateway/gateway.py
from typing import Optional, Dict, Any
from ..cache_mechanism import CacheMechanism
from ..utils.circuit_breaker import CircuitBreaker
from .rate_limiter import RateLimiter

class LiteLLMGateway:
    def __init__(
        self,
        api_key: str,
        provider: str = "openai",
        default_model: str = "gpt-4",
        cache: Optional[CacheMechanism] = None,
        enable_rate_limiting: bool = True,
        **kwargs: Any
    ):
        self.api_key = api_key
        self.provider = provider
        self.default_model = default_model
        self.cache = cache or CacheMechanism()
        self.circuit_breaker = CircuitBreaker(name=f"gateway_{provider}")
        self.rate_limiter = RateLimiter() if enable_rate_limiting else None
    
    async def generate_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs: Any
    ) -> GenerateResponse:
        """Generate text with caching, rate limiting, and circuit breaker."""
        if not tenant_id:
            raise ValueError("tenant_id is required")
        
        model = model or self.default_model
        
        # Check cache
        cache_key = f"gateway:{model}:{hash(prompt)}"
        cached = self.cache.get(cache_key, tenant_id=tenant_id)
        if cached:
            return GenerateResponse(**cached)
        
        # Rate limiting
        if self.rate_limiter:
            await self.rate_limiter.acquire(tenant_id=tenant_id)
        
        # Circuit breaker protection
        async def _call_llm():
            from litellm import acompletion
            response = await acompletion(
                model=f"{self.provider}/{model}",
                messages=[{"role": "user", "content": prompt}],
                api_key=self.api_key,
                **kwargs
            )
            return response
        
        try:
            response = await self.circuit_breaker.call(_call_llm)
            
            result = GenerateResponse(
                text=response.choices[0].message.content,
                model=model,
                usage=response.usage.dict() if hasattr(response, 'usage') else None
            )
            
            # Cache result
            self.cache.set(
                cache_key,
                result.dict(),
                tenant_id=tenant_id,
                ttl=3600
            )
            
            # LLMOps tracking
            self._track_llm_operation(tenant_id, model, response.usage)
            
            return result
            
        except Exception as e:
            logger.exception(f"Gateway generation failed for tenant {tenant_id}: {e}")
            raise GatewayError(f"Generation failed: {e}") from e
```

**Bad Gateway Implementation:**
```python
# BAD (violates multiple rules)
import openai

class Gateway:
    def generate(self, prompt):  # Not async, no tenant_id
        # Direct provider call (no abstraction)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content  # No caching, no error handling
```

#### 8.3.3 Testing Requirements

**Unit Tests Must Cover:**
- Provider abstraction (multiple providers)
- Caching (hit/miss scenarios)
- Rate limiting (per-tenant)
- Circuit breaker (open/closed/half-open states)
- LLMOps tracking (token counts, costs)
- Error handling (provider failures, rate limits)

### 8.4 Cache Mechanism Component Rules

**Location:** `src/core/cache_mechanism/`

#### 8.4.1 Mandatory Rules

1. **Backend Abstraction:**
   - Support multiple backends (memory, Dragonfly)
   - Backend selection must be configurable
   - Backend failures must not crash the application

2. **Tenant Isolation:**
   - All cache keys must be tenant-scoped
   - Cache operations must include tenant_id parameter
   - Pattern invalidation must respect tenant boundaries

3. **TTL Management:**
   - TTL must be configurable per operation
   - Default TTL must be set
   - Expired entries must be automatically removed

4. **Memory Backend:**
   - LRU eviction must be implemented
   - Max size must be configurable
   - Memory usage must be monitored

#### 8.4.2 Code Examples

**Good Cache Implementation:**
```python
# src/core/cache_mechanism/cache.py
from typing import Optional, Any
from dataclasses import dataclass

@dataclass
class CacheConfig:
    backend: str = "memory"  # "memory" or "dragonfly"
    default_ttl: int = 300
    max_size: int = 1024
    dragonfly_url: Optional[str] = None
    namespace: str = "sdk_cache"

class CacheMechanism:
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.backend = self.config.backend
        # Initialize backend...
    
    def _namespaced_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """Create tenant-scoped cache key."""
        if tenant_id:
            return f"{self.config.namespace}:{tenant_id}:{key}"
        return f"{self.config.namespace}:{key}"
    
    def set(
        self,
        key: str,
        value: Any,
        tenant_id: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> None:
        """Set cache value with tenant isolation."""
        if not tenant_id:
            raise ValueError("tenant_id is required for multi-tenant operations")
        
        ttl = ttl or self.config.default_ttl
        namespaced_key = self._namespaced_key(key, tenant_id=tenant_id)
        
        if self.backend == "dragonfly":
            self._dragonfly_client.set(namespaced_key, value, ex=ttl)
        else:
            # Memory backend with LRU
            self._store[namespaced_key] = (value, time.time() + ttl)
            self._store.move_to_end(namespaced_key)
            self._evict_if_needed()
    
    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
        """Get cache value with tenant isolation."""
        if not tenant_id:
            raise ValueError("tenant_id is required")
        
        namespaced_key = self._namespaced_key(key, tenant_id=tenant_id)
        # Implementation...
```

#### 8.4.3 Testing Requirements

**Unit Tests Must Cover:**
- Backend abstraction (memory and Dragonfly)
- Tenant isolation (keys don't collide)
- TTL expiration
- LRU eviction (memory backend)
- Pattern invalidation
- Error handling (backend failures)

### 8.5 FaaS Services Component Rules

**Location:** `src/faas/services/`

#### 8.5.1 Mandatory Rules

1. **Stateless Design:**
   - Services must not hold client state between requests
   - All state must be in database or cache
   - Service instances must be interchangeable

2. **HTTP Client:**
   - Inter-service communication must use `ServiceHTTPClient`
   - Retry logic must be implemented
   - Circuit breakers must be used

3. **Request Validation:**
   - All requests must be validated with Pydantic models
   - Tenant ID must be extracted from headers
   - Invalid requests must return 400 errors

4. **Error Handling:**
   - All errors must return proper HTTP status codes
   - Error responses must be JSON
   - Internal errors must not expose implementation details

#### 8.5.2 Code Examples

**Good FaaS Service Implementation:**
```python
# src/faas/services/rag_service/service.py
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from ...shared.http_client import ServiceHTTPClient
from ...shared.database import get_db_connection

app = FastAPI()

class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5

class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    metadata: dict

@app.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID")
) -> RAGQueryResponse:
    """Query RAG service with tenant isolation."""
    try:
        # Get database connection (stateless)
        db = await get_db_connection()
        
        # Create RAG system (stateless)
        rag = create_rag_system(db=db, gateway=gateway_client, tenant_id=x_tenant_id)
        
        # Execute query
        result = await rag.query_async(
            query_text=request.query,
            top_k=request.top_k,
            tenant_id=x_tenant_id
        )
        
        return RAGQueryResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"RAG query failed for tenant {x_tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

**Bad FaaS Service Implementation:**
```python
# BAD (stateful, no validation)
app = FastAPI()
rag_systems = {}  # State in memory (violates stateless)

@app.post("/query")
async def query_rag(query: str):  # No validation, no tenant_id
    # Stateful (stores in memory)
    if "tenant_123" not in rag_systems:
        rag_systems["tenant_123"] = create_rag_system(...)
    
    return rag_systems["tenant_123"].query(query)  # No error handling
```

#### 8.5.3 Testing Requirements

**Unit Tests Must Cover:**
- Request validation (Pydantic models)
- Tenant ID extraction from headers
- Stateless behavior (multiple requests)
- Error handling (400, 500 responses)
- Service-to-service communication (mocked)

### 8.6 Machine Learning Component Rules

**Location:** `src/core/machine_learning/`

#### 8.6.1 Mandatory Rules

1. **Model Management:**
   - Models must be versioned
   - Model metadata must be stored in database
   - Model loading must be lazy (on-demand)

2. **Training:**
   - Training must be async
   - Training progress must be trackable
   - Training data must be tenant-scoped

3. **Inference:**
   - Inference must be async
   - Batch inference must be supported
   - Inference results must be cached

4. **MLOps Integration:**
   - Model metrics must be logged
   - Model performance must be monitored
   - Model versioning must be tracked

#### 8.6.2 Code Examples

**Good ML Component Implementation:**
```python
# src/core/machine_learning/ml_framework/model.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class MLModel(BaseModel):
    model_id: str
    tenant_id: Optional[str] = None
    version: str
    model_type: str
    model_path: Optional[str] = None
    
    async def train_async(
        self,
        training_data: List[Dict[str, Any]],
        tenant_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Train model asynchronously with tenant isolation."""
        if not tenant_id:
            raise ValueError("tenant_id is required")
        
        # Filter training data by tenant
        tenant_data = [d for d in training_data if d.get("tenant_id") == tenant_id]
        
        # Training logic...
        metrics = await self._train_model(tenant_data, **kwargs)
        
        # Store model metadata
        await self._save_model_metadata(tenant_id, metrics)
        
        return metrics
    
    async def predict_async(
        self,
        input_data: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Predict with tenant-scoped model."""
        if not tenant_id:
            raise ValueError("tenant_id is required")
        
        # Load model if needed (lazy loading)
        if not self._model_loaded:
            await self._load_model(tenant_id)
        
        # Prediction logic...
        result = await self._run_inference(input_data)
        
        return result
```

#### 8.6.3 Testing Requirements

**Unit Tests Must Cover:**
- Model training (async)
- Model inference (async, batch)
- Model versioning
- Tenant isolation
- MLOps tracking
- Error handling

### 8.7 Component Gate Checklist (Required Per Component Touched)

A "component" is any top-level functional module under `src/` (e.g., `src/core/agno_agent_framework`, `src/core/rag`, `src/core/litellm_gateway`, `src/faas/services/agent_service`).

For every component modified, PR must include:
- [ ] **Unit tests** for new/changed logic (≥85% coverage)
- [ ] **Integration tests** if component touches external dependency (database, HTTP, LLM)
- [ ] **Component-specific rules** followed (see sections 8.1-8.6)
- [ ] **Tenant isolation** implemented (if applicable)
- [ ] **Async methods** used for I/O operations
- [ ] **Dependency injection** used (no hard dependencies)
- [ ] **Error handling** with custom exceptions
- [ ] **Type hints** complete for all public APIs
- [ ] **Logging** with structured context (tenant_id, request_id)
- [ ] Updated **component docs** (README.md) when behavior changes
- [ ] **API contract** stability (or migration notes if breaking)
- [ ] **Observability** expectations met (logs/metrics)

### 8.8 Component Documentation Template

Every component must have a `README.md` file with the following structure:

```markdown
# Component: <Component Name> — Motadata Python AI SDK

## Purpose
Clear description of what this component does and when to use it.

## Architecture
- How it fits into the SDK
- Dependencies (what it needs)
- Dependents (what uses it)

## Public API
### Factory Functions
- `create_<component>()` - Main factory function
- Parameters and return types

### Classes
- Main classes with key methods
- Method signatures with type hints

## Configuration
- Environment variables
- Configuration options
- Default values

## Usage Examples
### Basic Usage
```python
# Copy-paste runnable example
```

### Advanced Usage
```python
# Advanced configuration example
```

## Multi-Tenancy
- How tenant isolation works
- Required parameters
- Tenant-scoped operations

## Error Handling
- What exceptions are raised
- When they occur
- How to handle them

## Performance Considerations
- Caching behavior
- Cost implications
- Best practices

## Testing
- Unit tests: `src/tests/unit_tests/test_<component>.py`
- Integration tests: `src/tests/integration_tests/test_<component>.py`

## Related Components
- Links to related components
- Integration patterns
```

### 8.9 Component-Specific Testing Examples

See sections 8.1.3, 8.2.3, 8.3.3, 8.4.3, 8.5.3, and 8.6.3 for component-specific testing requirements and examples.

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
          pytest -q src/tests --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=85

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
    - pytest -q src/tests --cov=src --cov-report=xml --cov-fail-under=85
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
pytest -q src/tests --cov=src --cov-report=xml --cov-fail-under=85
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
- Tests + coverage fail-under 85
- Secret scan
- Bandit
- Pip-audit
- Complexity gate
- Build + smoke import (optional but recommended)
- Sonar Quality Gate pass

---

*End of document.*
