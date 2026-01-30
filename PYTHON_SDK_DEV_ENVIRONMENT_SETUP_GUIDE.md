# MOTADATA - DEVELOPER ENVIRONMENT SETUP GUIDE

**Complete, copy-paste runnable guide to set up a local development environment for the Motadata Python AI SDK and get productive from scratch.**

---

## Table of Contents

- [When to Use This](#when-to-use-this)
- [Prerequisites](#1-prerequisites-mandatory)
- [Virtual Environment Strategy](#2-virtual-environment-strategy-standardized)
- [Repository Clone & Branch Strategy](#3-repository-clone--branch-strategy)
- [Installation Steps](#4-installation-steps)
- [Local Commands](#5-local-commands)
- [Validation](#6-validation)
- [Troubleshooting](#7-troubleshooting)
- [Related](#related)
- [Feedback](#feedback)

## When to Use This

This guide is for:
- SDK contributors setting up their local environment
- Core maintainers configuring development workflows
- CI/debugging engineers validating setup

This guide focuses on **getting a developer productive from scratch**: environment setup, local execution, and validation.

Architecture, component design, and quality gates are covered in separate documents.

---

## 1. Prerequisites (Mandatory)

### 1.1 Operating System
- Linux (Ubuntu 20.04+ recommended)
- macOS (development only)
- Windows (development only, WSL2 recommended)

### 1.2 Python Version (Pinned)

The Motadata Python AI SDK **must** be developed using:

```
Python 3.11.x
```

**Why 3.11?** While the SDK supports Python 3.8+, development uses 3.11 for:
- Better type checking support
- Improved async performance
- Modern language features

**Verify Python version:**
```bash
python3 --version
# Expected output: Python 3.11.x
```

**If Python 3.11 is not installed:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# macOS (using Homebrew)
brew install python@3.11

# Verify installation
python3.11 --version
```

---

### 1.3 Required Tools

| Tool | Purpose |
|---|---|
git | Source control |
python3.8 | Runtime |
pip | Dependency management |
make | Standardized commands |
java 11+ | Sonar (optional, local) |

---

## 2. Virtual Environment Strategy (Standardized)

### Chosen Tool: `venv`

The SDK **standardizes on Python built‑in `venv`**.

> ❌ Poetry and pip‑tools are intentionally **not used**.

---

## 3. Repository Clone & Branch Strategy

### 3.1 Clone the Repository

```bash
git clone <REPO_URL>
cd motadata-python-ai-sdk
```

### 3.2 Branching Strategy (Mandatory)

- ❌ No direct commits to `main`
- ✅ All work via feature branches

**Branch naming**

| Purpose | Pattern |
|---|---|
Feature | `feature/<desc>` |
Bug fix | `fix/<desc>` |
Docs | `docs/<desc>` |
Chore | `chore/<desc>` |

Example:
```bash
git checkout -b feature/add-tenant-cache
```

All branches are merged via Pull Requests only.

---

## 4. Create & Activate Virtual Environment

**Create virtual environment:**
```bash
python3.11 -m venv .venv
```

**Activate virtual environment:**
```bash
# Linux/macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat
```

**Verify activation:**
```bash
which python  # Should show: /path/to/.venv/bin/python
python --version  # Should show: Python 3.11.x
```

---

## 5. Dependency Installation

**Upgrade pip:**
```bash
pip install --upgrade pip setuptools wheel
```

**Install SDK in development mode:**
```bash
pip install -e ".[dev]"
```

**Verify installation:**
```bash
# Check installed packages
pip list | grep motadata

# Verify imports work
python -c "from src.core.litellm_gateway import create_gateway; print('✓ Gateway import successful')"
python -c "from src.core.rag import create_rag_system; print('✓ RAG import successful')"
python -c "from src.core.agno_agent_framework import create_agent; print('✓ Agent import successful')"
```

**Expected output:**
```
✓ Gateway import successful
✓ RAG import successful
✓ Agent import successful
```

---

## 6. Repository Structure (Orientation)

```
src/
├── core/
├── faas/
├── integrations/
└── tests/
```

---

## 7. Running the SDK Locally

**Format code:**
```bash
make format
```

**Check code formatting (without changes):**
```bash
make format-check
```

**Type checking:**
```bash
make type-check
```

**Run all tests:**
```bash
make test
```

**Run tests with coverage:**
```bash
make test-cov
# Coverage report available at: htmlcov/index.html
```

**Run unit tests only:**
```bash
make test-unit
```

**Run integration tests only:**
```bash
make test-integration
```

**Run all checks (format, type, lint):**
```bash
make check
```

**Run full CI pipeline locally:**
```bash
make ci
```

---

## 8. Running Sonar Locally (Optional)

**Prerequisites:**
- Java 11+ installed
- SonarQube server running (or SonarCloud account)
- SonarScanner installed

**Install SonarScanner:**
```bash
# Linux/macOS
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-5.0.1.3006-linux.zip
unzip sonar-scanner-cli-5.0.1.3006-linux.zip
export PATH=$PATH:$(pwd)/sonar-scanner-5.0.1.3006-linux/bin

# macOS (using Homebrew)
brew install sonar-scanner
```

**Generate coverage report:**
```bash
pytest --cov=src --cov-report=xml --cov-report=term
```

**Run SonarScanner:**
```bash
sonar-scanner \
  -Dsonar.projectKey=motadata_python_ai_sdk \
  -Dsonar.sources=src \
  -Dsonar.tests=src/tests \
  -Dsonar.python.coverage.reportPaths=coverage.xml \
  -Dsonar.python.version=3.11 \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=YOUR_SONAR_TOKEN
```

**For SonarCloud:**
```bash
sonar-scanner \
  -Dsonar.projectKey=motadata_python_ai_sdk \
  -Dsonar.organization=YOUR_ORG \
  -Dsonar.sources=src \
  -Dsonar.tests=src/tests \
  -Dsonar.python.coverage.reportPaths=coverage.xml \
  -Dsonar.python.version=3.11 \
  -Dsonar.login=YOUR_SONAR_TOKEN
```

**Note:** Replace `YOUR_SONAR_TOKEN` with your actual SonarQube/SonarCloud token.

---

## 9. Validation Checklist

**Run this complete validation checklist:**

```bash
# 1. Verify Python version
python --version
# Expected: Python 3.11.x

# 2. Verify virtual environment is active
which python
# Should show path to .venv/bin/python

# 3. Check code formatting
make format-check

# 4. Type checking
make type-check

# 5. Run all tests
make test

# 6. Run tests with coverage
make test-cov

# 7. Verify imports work
python -c "from src.core import *; print('✓ All core imports successful')"

# 8. Verify FaaS services can be imported
python -c "from src.faas.services import *; print('✓ All FaaS imports successful')"
```

**Expected result:** All commands should complete without errors.

---

## 10. Quick Start Example

**Test the SDK with a simple example:**

```bash
# Set your API key (if needed)
export OPENAI_API_KEY='your-api-key-here'

# Run hello world example
python examples/hello_world.py
```

**Expected output:**
```
🚀 Motadata AI SDK - Hello World Example
✅ API key found
📡 Creating gateway connection...
✅ Gateway created successfully
🤖 Sending request to AI...
============================================================
AI Response: Hello! I'm an AI assistant ready to help you.
============================================================
✅ Success! SDK is working correctly.
```

---

## 11. Troubleshooting

### Issue: `python3.11: command not found`
**Solution:** Install Python 3.11 (see section 1.2)

### Issue: `pip: command not found`
**Solution:** 
```bash
python3.11 -m ensurepip --upgrade
```

### Issue: Import errors after installation
**Solution:**
```bash
# Reinstall in development mode
pip install -e ".[dev]" --force-reinstall
```

### Issue: Tests failing
**Solution:**
```bash
# Check test dependencies
pip install -e ".[dev]"

# Run tests with verbose output
pytest -v src/tests
```

### Issue: Type checking errors
**Solution:**
```bash
# Update mypy
pip install --upgrade mypy

# Run type check with more details
mypy src --show-error-codes
```

## Related

- [Onboarding Guide](ONBOARDING_GUIDE.md) - Complete SDK overview and component integration
- [Quality Gate Rules](PYTHON_SDK_QUALITY_GATE_RULES_AND_DEVELOPMENT_GUIDELINE_DOCUMENT.md) - Quality standards and coding guidelines
- [Developer Integration Guide](docs/guide/DEVELOPER_INTEGRATION_GUIDE.md) - Component development and integration patterns
- [Main README](README.md) - Project overview
- [Documentation Index](docs/guide/DOCUMENTATION_INDEX.md) - Complete navigation

## Feedback

If you find gaps in this guide or have suggestions for improvement, raise an issue or PR with your edits.
