# PYTHON_SDK_DEV_ENVIRONMENT_SETUP_GUIDE.md
## Motadata Python AI SDK – Developer Environment Setup Guide

---

## Purpose of This Document

This document provides a **complete, copy‑paste runnable guide** to set up a local development environment for the **Motadata Python AI SDK**.

It is intended for:
- SDK contributors
- Core maintainers
- CI/debugging engineers

This guide focuses on **getting a developer productive from scratch**:
environment setup, local execution, and validation.

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
Python 3.8.x
```

Verify:
```bash
python3 --version
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

```bash
python3.8 -m venv .venv
source .venv/bin/activate
```

---

## 5. Dependency Installation

```bash
pip install --upgrade pip
pip install -e ".[dev]"
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

```bash
make format
make format-check
make type-check
make test
make test-cov
```

---

## 8. Running Sonar Locally (Optional)

```bash
pytest --cov=src --cov-report=xml
sonar-scanner   -Dsonar.projectKey=motadata_python_ai_sdk   -Dsonar.sources=src   -Dsonar.tests=src/tests   -Dsonar.python.coverage.reportPaths=coverage.xml
```

---

## 9. Validation Checklist

```bash
python --version
make format-check
make type-check
make test
make test-cov
```

---

**End of Document**
