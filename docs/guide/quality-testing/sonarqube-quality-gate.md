# SonarQube Quality Gate

## Purpose
Define a **clear and enforceable SonarQube Quality Gate for Golang / Java / Python / React.js projects**, focused only on **mandatory rules and thresholds** required for production readiness.

---

## Scope
- Language: **Go (Golang) / Java / Python / React.js**
- Based on: **Official SonarQube ruleset**

---

## Quality Gate Conditions (Mandatory)

A build **must fail** if any condition below is violated:

| Category | Threshold  | 
|----------|------------|
| New Bugs | **0**      |
| New Vulnerabilities | **0**      | 
| New Security Hotspots (Unreviewed) | **0**      |
| New Critical Code Smells | **0**      | 
| New Major Code Smells | **0**      | 
| Reliability Rating | **A**      |
| Security Rating | **A**      |
| Maintainability Rating | **A or B** |
| Overall Code Coverage | **≥ 85%**  |
| Coverage on New Code | **≥ 85%**  |
| Duplications on New Code | **≤ 3%**   |

---

## Enforced Rule Categories

### 1. Reliability (Bugs)
- No unreachable or dead code
- No identical logic in conditional branches
- No duplicate conditions in `if / else if`
- No self-assigned variables
- No useless `if(true)` / `if(false)` blocks
- No nil pointer dereference risks
- No infinite loops

**Gate Rule:** `New Bugs = 0`

---

### 2. Security

#### Vulnerabilities
- No SQL injection vulnerabilities
- No command injection vulnerabilities
- No path traversal vulnerabilities

#### Security Hotspots
- Hard-coded credentials are not allowed
- Hard-coded IP addresses are not allowed
- Weak cryptographic algorithms are flagged
- Insecure random number generation is flagged

**Gate Rule:** `New Vulnerabilities = 0`, `Unreviewed Hotspots = 0`

---

### 3. Maintainability & Complexity
- Function cognitive complexity within acceptable limits (recommended ≤ 15)
- Deeply nested `if`, `for`, `switch` statements are not allowed
- Overly complex expressions are not allowed

**Gate Rule:** No new Critical or Major complexity issues

---

### 4. Function & File Constraints

#### Functions
| Constraint | Threshold | Enforcement |
|------------|-----------|-------------|
| Empty functions | Not allowed | **Blocker** |
| Identical implementations | Not allowed | **Blocker** |
| Maximum parameters | 5 | **Blocker** |
| Maximum lines | 80 | **Blocker** |

#### Files
| Constraint | Threshold | Enforcement |
|------------|-----------|-------------|
| Maximum lines | 1000 | **Blocker** (except generated code) |
| Maximum line length | 150 characters | Warning |

---

### 5. Coding Standards & Hygiene

#### Naming & Style
- Naming must follow language standards
- No redundant boolean checks (`if flag == true`)
- No empty nested blocks
- No redundant parentheses
- Statements must be on separate lines

#### Code Duplication
- No duplicated string literals (< 3 occurrences)
- No duplicated code blocks (< 10 lines)

#### Comments & Documentation
- `TODO` / `FIXME` usage must be tracked (with issue reference)
- License headers must be present in all source files
- Exported functions should have documentation comments

#### Prohibited Patterns
- No octal values (use explicit notation if needed)
- No magic numbers (use named constants)
- No `panic()` or exception in library code (only in main or unrecoverable situations)

---

## Final Quality Gate Summary

```
QUALITY GATE: Production Gate

FAIL IF:
├── Reliability
│   ├── New Bugs > 0
│   └── Reliability Rating < A
├── Security
│   ├── New Vulnerabilities > 0
│   ├── Unreviewed Security Hotspots > 0
│   └── Security Rating < A
├── Maintainability
│   ├── New Critical Code Smells > 0
│   ├── New Major Code Smells > 0
│   ├── Maintainability Rating < B
├── Coverage
│   ├── Overall Code Coverage < 85%
│   └── Coverage on New Code < 85%
└── Duplication
    └── Duplications on New Code > 3%
```

---