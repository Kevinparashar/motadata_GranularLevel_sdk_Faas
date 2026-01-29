# PYTHON_SDK_DEV_ENVIRONMENT_SETUP_GUIDE.md
## Motadata Python AI SDK – Developer Environment Setup Guide

---

## Purpose of This Document

This document provides a **complete, copy‑paste runnable guide** to set up a local development environment for the **Motadata Python AI SDK**.

It is intended for:
- SDK contributors
- Core maintainers
- CI/debugging engineers

This guide is **strictly about environment setup and local execution**.  
Architecture, component design, and quality gates are covered in separate documents.

---

## 1. Supported & Mandatory Python Version

### 1.1 Python Version (Pinned)

The Motadata Python AI SDK **must** be developed using:

```
Python 3.8.x
```

**Why**
- Matches current `mypy` and tooling configuration
- Ensures compatibility with production environments

### 1.2 Verify Python Version

```bash
python3 --version
```
Expected output:
```
Python 3.8.x
```

If multiple Python versions are installed, explicitly use:
```bash
python3.8 --version
```

---

## 2. Virtual Environment Strategy (Standardized)

### 2.1 Chosen Tool: `venv` (Standard)

The SDK **standardizes on Python built‑in `venv`**.

Reasons:
- Zero external dependency
- CI‑friendly
- Matches current SDK tooling
- Simplest for contributors

> ❌ Poetry and pip‑tools are intentionally **not used** for this SDK.

---

## 3. Repository Clone & Initial Setup

### 3.1 Clone the Repository

```bash
git clone <REPO_URL>
cd motadata-python-ai-sdk
```

---

### 3.2 Create Virtual Environment

```bash
python3.8 -m venv .venv
```

### 3.3 Activate Virtual Environment

**Linux / macOS**
```bash
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
```

Verify:
```bash
which python
python --version
```

---

## 4. Dependency Installation

### 4.1 Upgrade pip

```bash
pip install --upgrade pip
```

### 4.2 Install SDK in Editable Mode

```bash
pip install -e ".[dev]"
```

This installs:
- SDK source in editable mode
- All development dependencies:
  - pytest
  - pytest-cov
  - black
  - isort
  - mypy

---

## 5. Repository Structure (What You’ll Work With)

```
motadata-python-ai-sdk/
├── src/
│   ├── core/
│   ├── faas/
│   ├── integrations/
│   └── tests/
│       ├── unit_tests/
│       ├── integration_tests/
│       └── benchmarks/
├── pyproject.toml
├── Makefile
└── README.md
```

---

## 6. Local Development Commands (Mandatory)

All developers **must use Makefile targets** for consistency.

### 6.1 Code Formatting

```bash
make format
```

Checks formatting only:
```bash
make format-check
```

---

### 6.2 Linting (Current SDK State)

> ⚠️ Note: Linting is not yet enforced in the SDK.
> This is expected to be added as part of Quality Gate enforcement.

---

### 6.3 Type Checking

```bash
make type-check
```

Runs:
- `mypy` against `src/`

---

### 6.4 Running Tests

#### Unit Tests
```bash
make test-unit
```

#### Integration Tests
```bash
make test-integration
```

#### All Tests
```bash
make test
```

---

### 6.5 Coverage Report

```bash
make test-cov
```

Generates:
- Terminal coverage output
- HTML report

> Coverage threshold enforcement is handled via CI (see Quality Gate document).

---

## 7. Running Sonar Locally (Optional)

> Sonar analysis is **primarily enforced in CI**.
> Local execution is optional and intended for maintainers.

### 7.1 Prerequisites

- Java 11+
- SonarQube server access OR SonarCloud account
- `sonar-scanner` installed

### 7.2 Install Sonar Scanner

**Linux/macOS**
```bash
brew install sonar-scanner
# OR
sudo apt install sonar-scanner
```

### 7.3 Generate Coverage XML

```bash
pytest --cov=src --cov-report=xml
```

### 7.4 Run Sonar Scanner

```bash
sonar-scanner   -Dsonar.projectKey=motadata_python_ai_sdk   -Dsonar.sources=src   -Dsonar.tests=src/tests   -Dsonar.python.coverage.reportPaths=coverage.xml
```

> CI will fail the build if the Sonar Quality Gate fails.

---

## 8. Common Setup Validation Checklist

Run these commands after setup:

```bash
python --version
make format-check
make type-check
make test-unit
make test
make test-cov
```

If all pass, your environment is correctly set up.

---

## 9. Troubleshooting

### Virtual Environment Not Activating
- Ensure you are in repo root
- Delete `.venv` and recreate

### Dependency Issues
```bash
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
```

### Test Failures
- Run unit tests first
- Verify environment variables for integration tests

---

## 10. Final Notes

- This document is **mandatory reading** for contributors.
- Do not bypass Makefile commands.
- CI mirrors these exact steps.

---

**End of Document**
