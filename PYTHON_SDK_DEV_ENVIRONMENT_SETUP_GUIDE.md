# MOTADATA - DEVELOPER ENVIRONMENT SETUP GUIDE

**Complete, copy-paste runnable guide to set up a local development environment for the Motadata Python AI SDK and get productive from scratch.**

---

### What This Guide Covers

This guide provides **step-by-step instructions** for:

- ✅ **Python 3.11 installation** and virtual environment setup
- ✅ **Repository clone** and dependency installation
- ✅ **Environment variables** configuration
- ✅ **Basic IDE setup** (VS Code recommended)
- ✅ **Pre-commit hooks** and code quality tools
- ✅ **Validation checklist** and common troubleshooting
- ✅ **Optional features** (cache, messaging, observability)

### What This Guide Does NOT Cover

This guide focuses **exclusively on local development setup**. For other topics, see:

- ❌ **Architecture and design patterns** → See [Developer Integration Guide](docs/guide/DEVELOPER_INTEGRATION_GUIDE.md)
- ❌ **Component usage and API reference** → See [Quick Reference](docs/guide/QUICK_REFERENCE.md)  
- ❌ **Quality gates and standards** → See [Quality Gate Rules](PYTHON_SDK_QUALITY_GATE_RULES_AND_DEVELOPMENT_GUIDELINE_DOCUMENT.md)
- ❌ **End-user SDK usage** → See [README Quick Start](README.md)
- ❌ **Contributing guidelines** → See [Onboarding Guide](docs/guide/ONBOARDING_GUIDE.md)

---

### Quick Navigation

**For different audiences:**
- 🆕 **First-time contributors:** Follow sections 1-8 in order
- 🔧 **Experienced developers:** Jump to [Quick Setup](#quick-setup-for-experienced-developers)
- 🐛 **Having issues:** Go to [Troubleshooting](#troubleshooting-common-issues)

---

## 📋 Table of Contents

### Getting Started
1. [Prerequisites](#1-prerequisites-mandatory)
2. [Quick Setup (Experienced Developers)](#2-quick-setup-for-experienced-developers)
3. [Setup Overview](#3-setup-overview)

### Core Setup
4. [Virtual Environment](#4-virtual-environment-setup)
5. [Repository Setup](#5-repository-clone--git-workflow)
6. [Dependency Installation](#6-dependency-installation)
7. [Environment Variables](#7-environment-variables-configuration)

### Development Tools
8. [Repository Structure](#8-repository-structure-orientation)
9. [Make Commands](#9-make-commands-development-workflow)
10. [IDE Setup](#10-ide-setup-recommended)
11. [Pre-commit Hooks](#11-pre-commit-hooks-setup)

### Optional & Standards
12. [Optional Dependencies](#12-optional-dependencies-advanced-features)
13. [Development Standards](#13-development-standards)

### Validation & Help
14. [Validation](#14-validation-checklist)
15. [Troubleshooting](#15-troubleshooting-common-issues)

### Reference
16. [Related Documentation](#16-related-documentation)
17. [Quick Links Summary](#17-quick-links-summary)

---

## When to Use This Guide

**Use this guide if you are:**
- 🆕 A new SDK contributor setting up for the first time
- 🔧 A core maintainer configuring development workflows
- 🐛 A CI/debugging engineer validating setup
- 🔄 Updating your environment after a long break

**This guide is for:**
- Local development and testing
- Running the full test suite
- Debugging SDK components
- Contributing code changes

**For other purposes, see:**
- **Using the SDK:** [README Quick Start](README.md#quick-start-5-minutes)
- **Understanding architecture:** [Onboarding Guide](docs/guide/ONBOARDING_GUIDE.md)
- **Production deployment:** [Deployment Guides](docs/deployment/)

---

## 1. Prerequisites (Mandatory)

> **📌 Note:** If you're an experienced Python developer, see [Quick Setup](#2-quick-setup-for-experienced-developers) for a faster path.

### 1.1 Operating System
- Linux (Ubuntu 20.04+ recommended)
- macOS
- Windows (WSL2 recommended)

### 1.2 Python Version Policy

**Development Baseline:** Python 3.11.x  
**Runtime Support:** Python 3.8+

The SDK **requires Python 3.11 for development** (enforced by `.python-version`), but supports Python 3.8+ for runtime deployment.

**Why 3.11 for development?**
- Better type checking support
- Improved async performance (20-30% faster)
- Modern language features

**Verify Python version:**
```bash
python3.11 --version
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

> **💡 Tip:** The repository includes `.python-version` file that tools like `pyenv` will automatically respect.

---

### 1.3 System Requirements

**Minimum (Basic SDK Usage):**
- **RAM:** 4 GB
- **Disk:** 2 GB free space
- **CPU:** 2 cores
- **Network:** Stable internet for LLM API calls

**Recommended (Full Development):**
- **RAM:** 8 GB (16 GB if using ML components)
- **Disk:** 10 GB free space
- **CPU:** 4+ cores
- **Network:** Stable internet with sufficient bandwidth for LLM API calls

> **💡 Note:** ML model training and caching require additional RAM.

### 1.4 Required Tools

| Tool | Version | Purpose | Verification |
|------|---------|---------|--------------|
| **Git** | 2.30+ | Source control | `git --version` |
| **Python** | 3.11.x | Development runtime | `python3.11 --version` |
| **pip** | Latest | Package management | `pip --version` |
| **make** | Any | Build automation | `make --version` |

**All commands in this guide assume Python 3.11 is installed and available as `python3.11`**

---

## 2. Quick Setup (For Experienced Developers)

> **⚡ Fast Track:** If you're familiar with Python development and just want to get started quickly, follow these steps. For detailed explanations, see [Detailed Setup](#3-detailed-environment-setup).

### 2.1 One-Command Setup (5 Minutes)

```bash
# Clone the Motadata Python AI SDK repository
# Replace with your actual repository URL from your Git provider
git clone https://github.com/motadata/motadata-python-ai-sdk.git motadata-python-ai-sdk
cd motadata-python-ai-sdk

# Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -e ".[dev]"

# Run tests to verify
make test
```

### 2.2 Verification Only

After basic setup, verify installation:

### 2.3 Verification Checklist

After quick setup, verify everything works:

```bash
# ✅ Python version correct
python --version  # Should be 3.11.x

# ✅ Imports work
python -c "from src.core import create_gateway; print('✓')"

# ✅ Tests pass
pytest src/tests/unit_tests --maxfail=1

# ✅ Type checking passes
mypy src

# ✅ Formatting is correct
black --check src
```

**Expected Result:** All checks pass ✅

**If any check fails:** See [Troubleshooting](#15-troubleshooting-common-issues) or continue with [Detailed Setup](#3-setup-overview) below.

---

## 3. Setup Overview

Follow these steps in order for a complete development environment:

**Core Setup (Required):**
1. **Virtual Environment** → Isolated Python environment
2. **Repository Clone** → Get the source code
3. **Dependencies** → Install required packages
4. **Environment Variables** → Configure API keys and settings

**Development Tools (Recommended):**
5. **Repository Structure** → Understand the codebase layout
6. **Make Commands** → Learn the development workflow
7. **IDE Setup** → Configure your code editor
8. **Pre-commit Hooks** → Automated code quality checks

**Optional:**
9. **Optional Dependencies** → Cache, messaging (if needed)
10. **Development Standards** → Code quality & workflow requirements

**Verify:**
11. **Validation Checklist** → Ensure everything works

> **⏱️ Estimated Time:** 30-60 minutes for complete setup

---

## 4. Virtual Environment Setup

### 4.1 Chosen Tool: `venv`

The SDK **standardizes on Python built‑in `venv`** for virtual environment management.

> ❌ **Not Used:** Poetry and pip‑tools are intentionally avoided for simplicity and standardization.
> ⚠️ **CRITICAL:** Never commit `venv/` or `.venv/` directories to Git. They are excluded in `.gitignore`.

### 4.2 Create Virtual Environment

```bash
python3.11 -m venv .venv
```

### 4.3 Activate Virtual Environment

```bash
# Linux/macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat
```

### 4.4 Verify Virtual Environment

```bash
# Check Python path (should be in .venv)
which python  # Linux/macOS
where python  # Windows

# Expected output: /path/to/motadata-python-ai-sdk/.venv/bin/python

# Verify Python version
python --version
# Expected output: Python 3.11.x
```

---

## 5. Repository Clone & Git Workflow

### 5.1 Clone the Repository

```bash
# Clone the Motadata Python AI SDK
# Note: Replace URL with your organization's actual repository URL
git clone https://github.com/motadata/motadata-python-ai-sdk.git motadata-python-ai-sdk
cd motadata-python-ai-sdk
```

### 5.2 Branching Strategy (Mandatory)

**Rules:**
- ❌ **No direct commits to `main`**
- ✅ **All work via feature branches**
- ✅ **All merges via Pull Requests only**

**Branch Naming Convention:**

| Purpose | Pattern | Example |
|---------|---------|---------|
| **Feature** | `feature/<desc>` | `feature/add-tenant-cache` |
| **Bug fix** | `fix/<desc>` | `fix/memory-leak-agent` |
| **Documentation** | `docs/<desc>` | `docs/update-api-guide` |
| **Chore** | `chore/<desc>` | `chore/update-dependencies` |
| **Hotfix** | `hotfix/<desc>` | `hotfix/security-patch` |

**Example Workflow:**
```bash
# Create feature branch
git checkout -b feature/add-tenant-cache

# Make changes, commit
git add .
git commit -m "feat: add tenant-level cache support"

# Push and create PR
git push origin feature/add-tenant-cache
# Then create Pull Request on GitHub/GitLab
```

### 5.3 Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance tasks

**Examples:**
```bash
git commit -m "feat(rag): add multimodal document support"
git commit -m "fix(gateway): resolve connection timeout issue"
git commit -m "docs: update environment setup guide"
```

---

## 6. Dependency Installation

### 6.1 Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### 6.2 Install SDK in Development Mode

```bash
pip install -e ".[dev]"
```

**What this installs:**
- Core SDK packages
- Development dependencies (pytest, mypy, black, etc.)
- Optional dependencies for full functionality

### 6.3 Verify Installation

```bash
# Check installed packages
pip list | grep motadata

# Verify core imports
python -c "from src.core.litellm_gateway import create_gateway; print('✓ Gateway')"
python -c "from src.core.rag import create_rag_system; print('✓ RAG')"
python -c "from src.core.agno_agent_framework import create_agent; print('✓ Agent')"
```

**Expected output:**
```
✓ Gateway
✓ RAG
✓ Agent
```

**If imports fail:** See [Troubleshooting - Import Errors](#issue-4-import-errors-after-installation)

---

## 7. Environment Variables Configuration

> **🔐 Security:** Never commit `.env` files to Git. They're already in `.gitignore`.

### 7.1 Create Environment File

The repository includes `.env.example` with all available variables:

```bash
# Copy the template
cp .env.example .env

# Edit with your actual values
nano .env  # or use your preferred editor
```

### 7.2 Required vs Optional Variables

**REQUIRED (at minimum):**
- `OPENAI_API_KEY` (or another LLM provider key)

**OPTIONAL (feature-specific):**
- `DRAGONFLY_URL` or `REDIS_URL` → Only if using cache features  
- `OTEL_*` → Only if using observability features
- `NATS_URL` → Only if developing FaaS services

**See `.env.example` for complete variable list with documentation.**

### 7.3 Minimum Working Configuration

For basic LLM functionality, you only need:

```bash
# Minimum .env for LLM functionality
OPENAI_API_KEY=sk-your-actual-key-here
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

**That's it!** All other variables are optional and feature-specific.

### 7.4 Load Environment Variables

**Option 1: Manual (per session)**
```bash
export $(cat .env | grep -v '^#' | xargs)
```

**Option 2: Using python-dotenv (automatic)**
```python
# Already configured in SDK - no action needed
from dotenv import load_dotenv
load_dotenv()
```

**Option 3: Using direnv (recommended for frequent development)**
```bash
# Install direnv
sudo apt install direnv  # Ubuntu
# brew install direnv     # macOS

# Create .envrc
echo 'dotenv' > .envrc
direnv allow

# Now variables load automatically when you cd into directory
```

### 7.5 Verify Environment Variables

```bash
# Check if required variable is loaded
echo $OPENAI_API_KEY

# Or use Python
python -c "import os; print('✓ API Key loaded' if os.getenv('OPENAI_API_KEY') else '✗ API Key missing')"
```

> **📖 Full Reference:** See `.env.example` in the repository root for all available variables with documentation.

### 7.6 Component Dependency Matrix

**Which SDK components require which dependencies for development:**

| Component | LLM API Key | Cache (Dragonfly) | NATS | OpenTelemetry | Notes |
|-----------|-------------|-------------------|------|---------------|-------|
| **LiteLLM Gateway** | ✅ Required | ❌ No | ❌ No | ⚠️ Optional | Core LLM functionality |
| **Agent Framework** | ✅ Required | ✅ Required | ❌ No | ⚠️ Optional | Requires cache for memory |
| **RAG System** | ✅ Required | ✅ Required | ❌ No | ⚠️ Optional | Requires cache for embeddings |
| **Cache Mechanism** | ❌ No | ✅ Required | ❌ No | ❌ No | Standalone caching |
| **FaaS Services** | ✅ Required | ✅ Required | ✅ Required | ⚠️ Optional | Full stack needed |
| **Observability** | ❌ No | ❌ No | ❌ No | ✅ Required | Telemetry only |

**Environment Variable Mapping:**

| Component Feature | Environment Variable | Default | When Needed |
|------------------|---------------------|---------|-------------|
| LLM Calls | `OPENAI_API_KEY` | None | Always (or another provider) |
| Cache Storage | `DRAGONFLY_URL` | `redis://localhost:6379` | Agent, RAG, Cache |
| Message Broker | `NATS_URL` | `nats://localhost:4222` | FaaS services only |
| Observability | `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | When debugging |
| Environment | `ENVIRONMENT` | `development` | Always recommended |
| Logging | `LOG_LEVEL` | `INFO` | Always recommended |

**Quick Setup Paths:**

```bash
# Path 1: Basic LLM Development (Gateway only)
# Required: OPENAI_API_KEY
# Optional dependencies: None
make test-unit  # All unit tests work

# Path 2: Agent/RAG Development
# Required: OPENAI_API_KEY, Dragonfly
# Optional dependencies: Dragonfly
docker run -d --name dragonfly -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly
make test-integration  # Integration tests work

# Path 3: FaaS Services Development
# Required: OPENAI_API_KEY, Dragonfly, NATS
# Optional dependencies: Dragonfly + NATS
docker run -d --name nats -p 4222:4222 nats:latest
make test-all  # All tests work

# Path 4: Performance Debugging
# Required: OPENAI_API_KEY + OpenTelemetry
# Optional dependencies: OpenTelemetry Collector
# See Section 12.3 for OpenTelemetry setup
```

---

## 8. Repository Structure (Orientation)

```
motadata-python-ai-sdk/
├── src/
│   ├── core/                      # Core SDK components
│   │   ├── agno_agent_framework/  # Agent system
│   │   ├── litellm_gateway/       # LLM gateway
│   │   ├── rag/                   # RAG system
│   │   ├── database/              # Database operations
│   │   ├── cache/                 # Caching layer
│   │   └── utils/                 # Utilities
│   ├── faas/                      # FaaS services
│   └── tests/                     # Test suite
│       ├── unit_tests/            # Unit tests
│       ├── integration_tests/     # Integration tests
│       └── benchmarks/            # Performance tests
├── examples/                      # Usage examples
├── docs/                          # Documentation
├── .env.example                   # Environment template
├── Makefile                       # Build commands
├── pyproject.toml                # Project metadata
├── setup.py                       # Package setup
└── README.md                      # Project overview
```

---

## 9. Make Commands (Development Workflow)

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `make format` | Auto-format code (black + isort) | Before committing |
| `make format-check` | Check formatting without changes | In CI, pre-commit |
| `make type-check` | Run mypy type checking | Before PR |
| `make lint` | Run all linters (ruff) | Before PR |
| `make test` | Run all tests | After changes |
| `make test-unit` | Run unit tests only | Fast feedback |
| `make test-integration` | Run integration tests | Before PR |
| `make test-cov` | Run tests with coverage report | Weekly check |
| `make check` | Run format + type + lint checks | Before committing |
| `make ci` | Run full CI pipeline locally | Before pushing |
| `make clean` | Clean build artifacts | Troubleshooting |

### 9.1 Common Workflows

**Before committing:**
```bash
make format && make check
```

**Before creating PR:**
```bash
make ci
```

**After pulling main:**
```bash
pip install -e ".[dev]" && make test
```

**Quick test feedback loop:**
```bash
# Run specific test file
pytest src/tests/unit_tests/test_agent.py -v

# Run specific test
pytest src/tests/unit_tests/test_agent.py::test_create_agent -v

# Run with debugger on failure
pytest --pdb src/tests/unit_tests/test_agent.py
```

### 9.2 Testing Strategy Guide

**Understanding Test Types:**

The SDK uses three distinct test categories, each with different dependency requirements:

| Test Type | Location | Requires External Services | Run With | Speed | Purpose |
|-----------|----------|---------------------------|----------|-------|---------|
| **Unit Tests** | `src/tests/unit_tests/` | ❌ No (uses mocks) | `make test-unit` | ⚡ Fast (seconds) | Verify component logic in isolation |
| **Integration Tests** | `src/tests/integration_tests/` | ✅ Yes (cache, NATS) | `make test-integration` | 🐢 Slower (minutes) | Verify component interactions |
| **Benchmark Tests** | `src/tests/benchmark_tests/` | ✅ Yes (full stack) | `make benchmark` | 🐌 Slowest (10+ min) | Performance testing |

**Dependency Requirements by Test Type:**

```bash
# Unit Tests - No external dependencies
make test-unit
# ✅ Works with: Just LLM API key
# ✅ No services needed
# ✅ Uses mocks for cache, NATS, etc.

# Integration Tests - Requires running services
make test-integration
# ⚠️ Requires:
#   - Dragonfly/Redis (cache)
#   - NATS (for FaaS tests)
#   - LLM API key
# Start services:
docker run -d --name dragonfly -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly
docker run -d --name nats -p 4222:4222 nats:latest

# Benchmark Tests - Requires full stack + load testing
make benchmark
# ⚠️ Requires: All integration test dependencies + stable system
```

**Test Selection Strategy:**

```bash
# 1. During Active Development (Fast Feedback)
# Run ONLY related unit tests
pytest src/tests/unit_tests/test_agent.py -v

# 2. Before Committing (Verify Changes)
# Run all unit tests (fast, no dependencies)
make test-unit

# 3. Before Creating PR (Full Validation)
# Run unit + integration tests
make test
# Or: make test-unit && make test-integration

# 4. Before Release (Performance Validation)
# Run all tests including benchmarks
make test-all
```

**Component-Specific Testing:**

```bash
# Gateway Development (LLM calls only)
pytest src/tests/unit_tests/test_litellm_gateway.py
pytest src/tests/integration_tests/test_gateway*.py
# Dependencies: LLM API key only

# Agent Development
pytest src/tests/unit_tests/test_agent*.py
pytest src/tests/integration_tests/test_agent*.py
# Dependencies: LLM API key + Cache (Dragonfly)

# RAG Development
pytest src/tests/unit_tests/test_rag*.py
pytest src/tests/integration_tests/test_rag*.py
# Dependencies: LLM API key + Cache

# FaaS Services Development
pytest src/tests/integration_tests/test_*_integration.py
pytest src/tests/faas/
# Dependencies: LLM API key + Cache + NATS

# Cache Development
pytest src/tests/unit_tests/test_cache*.py
pytest src/tests/integration_tests/test_cache*.py
# Dependencies: Dragonfly/Redis only
```

**Test Execution Patterns:**

```bash
# Pattern 1: Watch mode (continuous testing during development)
pytest-watch src/tests/unit_tests/test_agent.py

# Pattern 2: Parallel execution (faster)
pytest -n auto src/tests/unit_tests/

# Pattern 3: Verbose with coverage
pytest -v --cov=src --cov-report=term-missing src/tests/unit_tests/

# Pattern 4: Only failed tests (after fixing)
pytest --lf  # --last-failed

# Pattern 5: Stop on first failure (debugging)
pytest -x src/tests/

# Pattern 6: Run specific marker
pytest -m "not slow" src/tests/
```

**Mock vs Real Dependencies Decision Tree:**

```
Are you testing...
├─ Business logic / algorithms?
│  └─> Use UNIT tests (mocks) ✅
│
├─ Component interactions?
│  └─> Use INTEGRATION tests (real services) ✅
│
├─ Performance characteristics?
│  └─> Use BENCHMARK tests (real services) ✅
│
└─ End-to-end workflows?
   └─> Use INTEGRATION tests (real services) ✅
```

**Troubleshooting Test Failures:**

```bash
# Issue: Integration tests fail with connection errors
# Solution: Ensure services are running
docker ps  # Should show dragonfly, nats
docker logs dragonfly  # Check service logs

# Issue: Tests pass locally but fail in CI
# Solution: Check environment variable differences
env | grep -E "(OPENAI|CACHE|NATS)"  # Verify local env
# Compare with CI environment

# Issue: Random test failures (flaky tests)
# Solution: Run test multiple times to confirm
pytest --count=10 src/tests/unit_tests/test_flaky.py

# Issue: Slow test suite
# Solution: Run only changed tests or use markers
pytest --testmon  # Only test changed code
pytest -m "not slow"  # Skip slow tests
```

---

## 10. IDE Setup (Recommended)

> **📝 Note:** Use any text editor you prefer. VS Code is recommended for its Python support.

### VS Code Setup (Optional but Recommended)

**Install VS Code:** https://code.visualstudio.com/

**Install Python Extensions:**
```bash
code --install-extension ms-python.python
code --install-extension ms-python.black-formatter
code --install-extension charliermarsh.ruff
```

**Basic Configuration:** Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "python.testing.pytestEnabled": true,
  "editor.rulers": [100]
}
```

**Verification:**
```bash
# Open the project in VS Code
code .

# Test that formatter works (Ctrl+Shift+I or Cmd+Shift+I)
# Test that tests are discovered in the testing panel
```

> **💡 Tip:** See [IDE Configuration Guide](docs/guides/IDE_SETUP.md) for advanced configuration, PyCharm setup, and debugging configurations

---

## 11. Pre-commit Hooks Setup (Mandatory)

> **🎯 Purpose:** Automatically check code quality before every commit. **This is mandatory, not optional.**

The repository includes `.pre-commit-config.yaml` with all required hooks configured.

### 11.1 Install pre-commit

```bash
pip install pre-commit
```

### 11.2 Install Git Hooks

```bash
# Install hooks for this repository
pre-commit install
```

**Output:**
```
pre-commit installed at .git/hooks/pre-commit
```

> **📁 What's included:** The `.pre-commit-config.yaml` file in the repository configures black, isort, mypy, and secrets detection.

### 11.3 Test Pre-commit Hooks

```bash
# Run hooks on all files (first time)
pre-commit run --all-files

# Or test on staged files
git add .
pre-commit run
```

### 11.4 Skipping Hooks (Emergency Only)

```bash
# Skip all hooks (use sparingly!)
git commit --no-verify -m "emergency fix"

# Skip specific hook
SKIP=mypy git commit -m "commit message"
```

> **⚠️ Warning:** Only skip hooks when absolutely necessary. Pre-commit hooks are there to catch issues early!

---

## 12. Optional Dependencies (Advanced Features)

> **📦 Note:** These dependencies are optional and only needed if you're working on specific SDK features.

### Component Dependency Matrix

**Which SDK components require which optional dependencies:**

| SDK Component | Requires Dragonfly/Redis | Requires NATS | Requires OpenTelemetry |
|---------------|-------------------------|---------------|------------------------|
| **LiteLLM Gateway** | ❌ No | ❌ No | ✅ Yes (optional) |
| **Agent Framework** | ✅ Yes (for caching) | ❌ No | ✅ Yes (optional) |
| **RAG System** | ✅ Yes (for caching) | ❌ No | ✅ Yes (optional) |
| **Cache Mechanism** | ✅ **Yes (required)** | ❌ No | ❌ No |
| **FaaS Services** | ✅ Yes | ✅ **Yes (required)** | ✅ Yes (optional) |
| **Observability** | ❌ No | ❌ No | ✅ **Yes (required)** |

> **💡 Quick Decision:**
> - **Just testing LLM calls?** → No optional deps needed
> - **Working on RAG/Agent features?** → Install Dragonfly (cache)
> - **Developing FaaS services?** → Install NATS + Dragonfly
> - **Debugging performance?** → Install OpenTelemetry

### 12.1 Dragonfly Cache (Recommended for Cache Development)

**Purpose:** High-performance, Redis-compatible in-memory cache used by the SDK.

**Installation (Docker - Recommended):**
```bash
docker run -d \
  --name dragonfly \
  -p 6379:6379 \
  docker.dragonflydb.io/dragonflydb/dragonfly
```

**Installation (Binary):**
```bash
# Ubuntu/Debian
wget https://dragonflydb.io/downloads/dragonfly-latest-linux-amd64.tar.gz
tar -xzf dragonfly-latest-linux-amd64.tar.gz
sudo mv dragonfly /usr/local/bin/
dragonfly --logtostderr

# macOS
brew install dragonflydb/dragonfly/dragonfly
brew services start dragonfly
```

**Verify Installation:**
```bash
redis-cli ping
# Expected output: PONG
```

**Environment Variable:**
```bash
DRAGONFLY_URL=dragonfly://localhost:6379/0
```

### 12.2 NATS Messaging (For FaaS Services Development)

**Purpose:** Message broker for inter-service communication in FaaS architecture.

**Installation (Docker - Recommended):**
```bash
docker run -d \
  --name nats \
  -p 4222:4222 \
  -p 8222:8222 \
  nats:latest
```

**Installation (Binary):**
```bash
# Linux
wget https://github.com/nats-io/nats-server/releases/download/v2.10.7/nats-server-v2.10.7-linux-amd64.tar.gz
tar -xzf nats-server-v2.10.7-linux-amd64.tar.gz
sudo mv nats-server-v2.10.7-linux-amd64/nats-server /usr/local/bin/
nats-server

# macOS
brew install nats-server
nats-server
```

**Verify Installation:**
```bash
curl http://localhost:8222/varz
# Should return JSON with server info
```

**Environment Variable:**
```bash
NATS_URL=nats://localhost:4222
```

### 12.3 OpenTelemetry Collector (For Observability Development)

**Purpose:** Telemetry data collection for monitoring and tracing.

**Installation (Docker - Recommended):**
```bash
# Create config file
cat > otel-collector-config.yaml << 'EOF'
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

exporters:
  logging:
    loglevel: debug

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [logging]
    metrics:
      receivers: [otlp]
      exporters: [logging]
EOF

# Run collector
docker run -d \
  --name otel-collector \
  -p 4317:4317 \
  -p 4318:4318 \
  -v $(pwd)/otel-collector-config.yaml:/etc/otel-collector-config.yaml \
  otel/opentelemetry-collector:latest \
  --config=/etc/otel-collector-config.yaml
```

**Environment Variable:**
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### 12.4 Quick All-in-One Setup (Docker Compose)

For convenience, install all optional dependencies at once:

**Create `docker-compose.dev.yml`:**
```yaml
version: '3.8'

services:
  dragonfly:
    image: docker.dragonflydb.io/dragonflydb/dragonfly
    ports:
      - "6379:6379"

  nats:
    image: nats:latest
    ports:
      - "4222:4222"
      - "8222:8222"

  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    ports:
      - "4317:4317"
      - "4318:4318"
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
```

**Start all services:**
```bash
docker compose -f docker-compose.dev.yml up -d
```

**Stop all services:**
```bash
docker compose -f docker-compose.dev.yml down
```

### 12.5 FaaS Development Setup

**Purpose:** Set up the complete environment for developing and testing FaaS (Function-as-a-Service) components.

#### What are FaaS Services?

FaaS services in this SDK are **message-driven, stateless microservices** that:
- Process requests via NATS messaging
- Use standard SDK components (Gateway, RAG, Agent, Cache)
- Run independently and can be deployed separately
- Enable scalable, event-driven architectures

**Located at:** `src/faas/`

#### Prerequisites for FaaS Development

```bash
# 1. Core SDK setup (already completed in previous sections)
# 2. Running services:
#    - NATS (message broker)
#    - Dragonfly (cache)
#    - LLM API key

# Verify services are running
docker ps | grep -E "(nats|dragonfly)"
```

#### Quick Start: Run Your First FaaS Service

**Step 1: Start Required Services**
```bash
# NATS (message broker)
docker run -d --name nats -p 4222:4222 -p 8222:8222 nats:latest

# Dragonfly (cache)
docker run -d --name dragonfly -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly

# Verify they're running
curl http://localhost:8222/varz  # NATS info
redis-cli ping  # Should return PONG
```

**Step 2: Set Environment Variables**
```bash
# Add to .env
cat >> .env << EOF
NATS_URL=nats://localhost:4222
DRAGONFLY_URL=redis://localhost:6379
OPENAI_API_KEY=your-key-here
EOF

# Load variables
set -a; source .env; set +a
```

**Step 3: Run a FaaS Service (Example)**
```bash
# Agent service example
python src/faas/services/agent_service.py

# Expected output:
# ✓ Connected to NATS at nats://localhost:4222
# ✓ Subscribed to: agent.invoke
# ✓ Agent service ready
```

#### FaaS Architecture Overview

```
Client Application
      ↓
   [NATS Message Broker]  ← Pub/Sub messaging
      ↓
 ┌────┴────┬─────────┬──────────┐
 │         │         │          │
Agent    RAG    Gateway    Custom
Service  Service Service  Service
 │         │         │          │
 └────┬────┴────┬────┴──────────┘
      ↓         ↓
  [Dragonfly]  [LiteLLM]
   (Cache)      (LLM API)
```

#### Developing Your Own FaaS Service

**Template for a new service:**

```python
# src/faas/services/my_service.py
import asyncio
from nats.aio.client import Client as NATS
from src.core.litellm_gateway import create_gateway
from src.core.cache import create_cache

async def handle_request(msg):
    """Handle incoming NATS message"""
    data = msg.data.decode()
    # Process request using SDK components
    result = await process(data)
    # Send response back
    await msg.respond(result.encode())

async def main():
    # Connect to NATS
    nc = NATS()
    await nc.connect("nats://localhost:4222")
    
    # Subscribe to subject
    await nc.subscribe("my.service", cb=handle_request)
    
    print("✓ My service ready")
    
    # Keep running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
```

#### Testing FaaS Services

**Unit Tests (No NATS needed):**
```bash
# Test service logic with mocks
pytest src/tests/unit_tests/test_faas/ -v
```

**Integration Tests (Requires NATS + Dragonfly):**
```bash
# Ensure services are running
docker ps | grep -E "(nats|dragonfly)"

# Run FaaS integration tests
pytest src/tests/integration_tests/test_nats_integration.py -v
pytest src/tests/integration_tests/test_agent_service.py -v
```

#### Message Protocol

**Request Format:**
```json
{
  "action": "invoke",
  "payload": {
    "query": "What is AI?",
    "context": {}
  },
  "request_id": "uuid-here"
}
```

**Response Format:**
```json
{
  "status": "success",
  "result": "AI stands for...",
  "request_id": "uuid-here",
  "timestamp": "2026-02-02T10:00:00Z"
}
```

#### Available FaaS Services

| Service | NATS Subject | Purpose | Dependencies |
|---------|--------------|---------|--------------|
| **Agent Service** | `agent.invoke` | Execute agent workflows | Gateway, Cache |
| **RAG Service** | `rag.query` | RAG query processing | Gateway, Cache |
| **Gateway Service** | `gateway.completion` | LLM completions | LLM API key |
| **Cache Service** | `cache.*` | Distributed caching | Dragonfly |

#### Debugging FaaS Services

**Enable Debug Logging:**
```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
python src/faas/services/agent_service.py
```

**Monitor NATS Messages:**
```bash
# Install NATS CLI
go install github.com/nats-io/natscli/nats@latest

# Subscribe to all messages (debug)
nats sub ">"

# Subscribe to specific service
nats sub "agent.invoke"

# Publish test message
nats pub "agent.invoke" '{"action":"test"}'
```

**Common Issues:**

```bash
# Issue: Cannot connect to NATS
# Solution: Check NATS is running
docker logs nats
telnet localhost 4222

# Issue: Service doesn't receive messages
# Solution: Check subscription subject matches
nats sub "your.subject"  # Monitor if messages arrive

# Issue: Service crashes on message
# Solution: Check payload format and error logs
export DEBUG=true
python src/faas/services/your_service.py
```

#### Production Considerations

**For production deployment (not covered in this guide):**
- Use NATS JetStream for persistence
- Implement proper error handling and retries
- Add OpenTelemetry instrumentation
- Configure resource limits
- Set up monitoring and alerting

See [FaaS Production Guide](docs/deployment/FAAS_DEPLOYMENT.md) for details.

---

## 13. Development Standards

### 13.1 Supported Environment

| Component | Requirement | Enforcement |
|-----------|-------------|-------------|
| **OS** | Linux, macOS, Windows (WSL2) | Recommended |
| **Python** | 3.11.x for development | `.python-version` file |
| **Runtime** | Python 3.8+ supported | `pyproject.toml` |
| **Package Manager** | pip (via `pyproject.toml`) | Required |
| **Virtual Environment** | `venv` (NOT Poetry/pipenv) | Standardized |

### 13.2 Code Quality Standards

**Enforced via pre-commit hooks (mandatory):**
- **Formatting:** Black (line length 100)
- **Import sorting:** isort (Black-compatible)
- **Type checking:** MyPy
- **Secrets detection:** detect-secrets

**Run before every commit:**
```bash
make check  # Runs format-check + type-check + lint
```

### 13.3 Commit Standards

**Format:** [Conventional Commits](https://www.conventionalcommits.org/)

```
<type>(<scope>): <description>
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

**Example:**
```bash
git commit -m "feat(rag): add multimodal support"
```

### 13.4 Branching Strategy

- ❌ No direct commits to `main`
- ✅ All work via feature branches
- ✅ Branch naming: `feature/`, `fix/`, `docs/`, `chore/`
- ✅ All merges via Pull Requests

### 13.5 Testing Requirements

**Before creating a PR:**
```bash
make ci  # Runs full CI pipeline locally
```

**Minimum coverage:** 80% (enforced in CI)

---

## 14. Validation Checklist (Copy-Paste Runnable)

### 14.1 General Environment Validation

**Run this complete validation script:**

```bash
#!/bin/bash
# Motadata Python AI SDK - Setup Validation
# Run this script to verify your development environment

set -e  # Exit on any error

echo "════════════════════════════════════════"
echo "  Motadata Python AI SDK"
echo "  Environment Validation"
echo "════════════════════════════════════════"
echo ""

# 1. Python version
echo "[ 1/8 ] Checking Python version..."
python --version | grep "3.11"
echo "✓ Python 3.11 detected"
echo ""

# 2. Virtual environment
echo "[ 2/8 ] Checking virtual environment..."
which python | grep ".venv"
echo "✓ Virtual environment active"
echo ""

# 3. Package installation
echo "[ 3/8 ] Checking package installation..."
python -c "import src.core" 2>/dev/null
echo "✓ Package installed correctly"
echo ""

# 4. Core imports
echo "[ 4/8 ] Testing core imports..."
python -c "from src.core.litellm_gateway import create_gateway; print('  ✓ Gateway')"
python -c "from src.core.rag import create_rag_system; print('  ✓ RAG')"
python -c "from src.core.agno_agent_framework import create_agent; print('  ✓ Agent')"
echo ""

# 5. Code formatting
echo "[ 5/8 ] Checking code formatting..."
make format-check
echo "✓ Code formatting correct"
echo ""

# 6. Type checking
echo "[ 6/8 ] Running type checks..."
make type-check
echo "✓ Type checking passed"
echo ""

# 7. Unit tests
echo "[ 7/8 ] Running unit tests..."
make test-unit
echo "✓ Unit tests passed"
echo ""

# 8. Pre-commit hooks
echo "[ 8/8 ] Checking pre-commit installation..."
pre-commit run --all-files || echo "⚠️  Pre-commit hooks need fixing (run 'make format')"
echo ""

echo "════════════════════════════════════════"
echo "✅ ALL VALIDATION CHECKS PASSED!"
echo "════════════════════════════════════════"
echo ""
echo "Your development environment is ready!"
echo ""
```

**Copy the script above and run it.**

**Expected result:** All 8 checks should pass with ✓

### 14.2 Component-Specific Validation

After the general setup validation passes, validate individual SDK components to ensure they work correctly with their dependencies.

#### Gateway Component Validation

**Test basic LLM connectivity:**

```bash
python << 'EOF'
from src.core.litellm_gateway import create_gateway
import asyncio

async def test_gateway():
    gateway = create_gateway()
    response = await gateway.completion(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'Gateway OK'"}]
    )
    print(f"✓ Gateway response: {response.choices[0].message.content}")

asyncio.run(test_gateway())
EOF
```

**Expected:** `✓ Gateway response: Gateway OK`

**If fails:** Check `OPENAI_API_KEY` is set and valid.

---

#### Cache Component Validation

**Test cache connectivity:**

```bash
python << 'EOF'
from src.core.cache import create_cache
import asyncio

async def test_cache():
    cache = create_cache()
    await cache.set("test_key", "test_value", ttl=60)
    value = await cache.get("test_key")
    assert value == "test_value", f"Expected 'test_value', got {value}"
    print("✓ Cache working correctly")

asyncio.run(test_cache())
EOF
```

**Expected:** `✓ Cache working correctly`

**If fails:**
```bash
# Check Dragonfly is running
docker ps | grep dragonfly
# Start if not running
docker run -d --name dragonfly -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly
```

---

#### Agent Component Validation

**Test agent creation and basic execution:**

```bash
python << 'EOF'
from src.core.agno_agent_framework import create_agent
import asyncio

async def test_agent():
    agent = create_agent(
        name="test_agent",
        description="Test agent for validation"
    )
    response = await agent.run("What is 2+2?")
    print(f"✓ Agent response received: {len(response)} characters")

asyncio.run(test_agent())
EOF
```

**Expected:** `✓ Agent response received: X characters`

**If fails:** Ensure both Gateway and Cache are working.

---

#### RAG Component Validation

**Test RAG system initialization:**

```bash
python << 'EOF'
from src.core.rag import create_rag_system
import asyncio

async def test_rag():
    rag = create_rag_system()
    
    # Add a test document
    await rag.add_documents([
        {"content": "The sky is blue.", "metadata": {"source": "test"}}
    ])
    
    # Query it
    result = await rag.query("What color is the sky?")
    print(f"✓ RAG system working, retrieved {len(result.documents)} documents")

asyncio.run(test_rag())
EOF
```

**Expected:** `✓ RAG system working, retrieved X documents`

**If fails:** Ensure Gateway and Cache are working.

---

#### FaaS Integration Validation

**Test NATS connectivity and message passing:**

```bash
python << 'EOF'
from nats.aio.client import Client as NATS
import asyncio

async def test_nats():
    nc = NATS()
    await nc.connect("nats://localhost:4222")
    
    # Test pub/sub
    received = []
    async def message_handler(msg):
        received.append(msg.data.decode())
    
    await nc.subscribe("test.subject", cb=message_handler)
    await nc.publish("test.subject", b"test_message")
    await nc.flush()
    await asyncio.sleep(0.1)
    
    assert len(received) == 1, f"Expected 1 message, got {len(received)}"
    print("✓ NATS messaging working correctly")
    
    await nc.close()

asyncio.run(test_nats())
EOF
```

**Expected:** `✓ NATS messaging working correctly`

**If fails:**
```bash
# Check NATS is running
docker ps | grep nats
# Start if not running
docker run -d --name nats -p 4222:4222 nats:latest
```

---

#### Observability Validation (Optional)

**Test OpenTelemetry instrumentation:**

```bash
python << 'EOF'
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# Setup tracing
provider = TracerProvider()
processor = SimpleSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("test_span"):
    print("✓ OpenTelemetry instrumentation working")
EOF
```

**Expected:** `✓ OpenTelemetry instrumentation working` + span export

---

#### Complete Component Matrix Validation

**Run all component validations at once:**

```bash
#!/bin/bash
# Complete Component Validation Script

echo "════════════════════════════════════════"
echo "  Component-Specific Validation"
echo "════════════════════════════════════════"
echo ""

# 1. Gateway
echo "[ 1/5 ] Testing Gateway..."
python -c "from src.core.litellm_gateway import create_gateway; print('✓ Gateway import OK')" || echo "✗ Gateway import failed"

# 2. Cache
echo "[ 2/5 ] Testing Cache..."
python -c "from src.core.cache import create_cache; print('✓ Cache import OK')" || echo "✗ Cache import failed"

# 3. Agent
echo "[ 3/5 ] Testing Agent..."
python -c "from src.core.agno_agent_framework import create_agent; print('✓ Agent import OK')" || echo "✗ Agent import failed"

# 4. RAG
echo "[ 4/5 ] Testing RAG..."
python -c "from src.core.rag import create_rag_system; print('✓ RAG import OK')" || echo "✗ RAG import failed"

# 5. FaaS (if NATS available)
echo "[ 5/5 ] Testing FaaS..."
if docker ps | grep -q nats; then
  python -c "from nats.aio.client import Client; print('✓ NATS client available')" || echo "✗ NATS client import failed"
else
  echo "⚠️  NATS not running (optional for FaaS)"
fi

echo ""
echo "════════════════════════════════════════"
echo "✅ Component validation complete!"
echo "════════════════════════════════════════"
```

**Save as `validate_components.sh` and run:**
```bash
chmod +x validate_components.sh
./validate_components.sh
```

---

#### Troubleshooting Component Validation Failures

**Gateway fails:**
- Check `OPENAI_API_KEY` is set: `echo $OPENAI_API_KEY`
- Verify network connectivity to OpenAI API
- Try alternative provider (Anthropic, Groq, etc.)

**Cache fails:**
- Check Dragonfly is running: `docker ps | grep dragonfly`
- Test connection: `redis-cli ping`
- Check `DRAGONFLY_URL` in `.env`

**Agent fails:**
- Agent requires both Gateway + Cache working
- Validate Gateway first, then Cache
- Check logs: `export LOG_LEVEL=DEBUG`

**RAG fails:**
- RAG requires Gateway + Cache
- Validate components individually first
- Check embedding model availability

**FaaS fails:**
- Check NATS is running: `docker ps | grep nats`
- Test NATS: `curl http://localhost:8222/varz`
- Check `NATS_URL` in `.env`

---

---

## 15. Troubleshooting SDK-Specific Issues

### 15.1 LLM Gateway Connection Failure

**Symptom:**
```
Error: LiteLLM call failed: AuthenticationError
```

**Solution:**
```bash
# Verify API key is set correctly
echo $OPENAI_API_KEY  # Should show your key

# If empty, add to .env
echo "OPENAI_API_KEY=your-actual-key-here" >> .env

# Reload environment
source .venv/bin/activate
set -a; source .env; set +a

# Test connection
python -c "from src.core.litellm_gateway import create_gateway; g = create_gateway(); print(g)"
```

### 15.2 Cache Connection Failures

**Symptom:**
```
ConnectionError: Error connecting to Redis
```

**Solution:**
```bash
# Check if Dragonfly/Redis is running
docker ps | grep dragonfly

# If not running, start it
docker run -d --name dragonfly -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly

# Test connection
redis-cli ping  # Should return "PONG"

# Verify CACHE_URL in .env
echo "CACHE_URL=redis://localhost:6379" >> .env
```

### 15.3 NATS Connection Issues (FaaS Services)

**Symptom:**
```
Error: Could not connect to NATS server
```

**Solution:**
```bash
# Check NATS is running
docker ps | grep nats

# If not running, start it
docker run -d --name nats -p 4222:4222 nats:latest

# Verify connection
telnet localhost 4222  # Should connect

# Set NATS_URL in .env
echo "NATS_URL=nats://localhost:4222" >> .env
```

### 15.4 Import Errors (ModuleNotFoundError)

**Symptom:**
```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall in editable mode
pip install -e ".[dev]"

# Add PYTHONPATH for running scripts directly
export PYTHONPATH="${PWD}:${PYTHONPATH}"
```

### 15.5 Type Checking Failures

**Symptom:**
```
make type-check fails with multiple errors
```

**Solution:**
```bash
# Ensure mypy and pyright are installed
pip install mypy pyright

# Check pyrightconfig.json exists
ls pyrightconfig.json

# Run type check with verbose output
mypy src/ --show-error-codes
```

### 15.6 Pre-commit Hooks Block Commits

**Symptom:**
```
black...............................................................Failed
```

**Solution:**
```bash
# Run formatters manually
make format

# Re-run pre-commit
pre-commit run --all-files

# If still failing, skip once (emergency only)
git commit --no-verify -m "message"
```

### 15.7 Test Failures Due to Missing Dependencies

**Symptom:**
```
Integration tests fail: Cache not available
```

**Solution:**
```bash
# Check which tests you're running
make test-unit        # No external dependencies needed
make test-integration # Requires cache, DB, NATS

# For integration tests, ensure services are running:
docker ps  # Should show dragonfly, postgres, nats (if testing FaaS)

# Or run only unit tests
pytest src/tests/unit_tests/
```

### Getting Help

If issues persist:

1. **Run full validation:** `make check`
2. **Check service status:**
   ```bash
   docker ps  # Check running services
   echo $OPENAI_API_KEY  # Verify environment variables
   ```
3. **Enable debug logging:**
   ```bash
   export DEBUG=true
   export LOG_LEVEL=DEBUG
   ```
4. **Ask for help:**
   - Slack: `#motadata-sdk-support`
   - GitHub Issues: https://github.com/motadata/motadata-python-ai-sdk/issues
   - Email: sdk-support@motadata.com

---

---

## 16. Related Documentation

### 16.1 Core Documentation
- 📖 [Main README](README.md) - Project overview and quick start
- 🎓 [Onboarding Guide](docs/guide/ONBOARDING_GUIDE.md) - Complete SDK overview and learning path
- 🔧 [Developer Integration Guide](docs/guide/DEVELOPER_INTEGRATION_GUIDE.md) - Component development patterns
- ⚡ [Quick Reference](docs/guide/QUICK_REFERENCE.md) - API quick reference for experienced developers

### 16.2 Standards & Guidelines
- ✅ [Quality Gate Rules](PYTHON_SDK_QUALITY_GATE_RULES_AND_DEVELOPMENT_GUIDELINE_DOCUMENT.md) - Coding standards and quality requirements
- 📋 [Compatibility Matrix](docs/guide/COMPATIBILITY_MATRIX_FINAL.md) - Supported versions and dependencies
- 📚 [SDK Dependencies Guide](docs/guide/SDK_DEPENDENCIES_AND_LIBRARIES..md) - Complete dependency documentation

### 16.3 Navigation & Support
- 🗺️ [Navigation Helper](docs/guide/NAVIGATION_HELPER.md) - How to navigate documentation
- 🏗️ [Architecture Documentation](docs/architecture/) - System architecture and design
- 📝 [Examples](examples/) - Working code examples
- 🐛 [GitHub Issues](https://github.com/motadata/motadata-python-ai-sdk/issues) - Bug reports and feature requests

---

## 17. Quick Links Summary

### 17.1 Essential Setup (Do these in order)
1. [Prerequisites](#1-prerequisites-mandatory) - Python 3.11, Git, Make
2. [Virtual Environment](#4-virtual-environment-setup) - Create isolated environment
3. [Repository Clone](#5-repository-clone--git-workflow) - Get the code
4. [Dependencies](#6-dependency-installation) - Install packages
5. [Environment Variables](#7-environment-variables-configuration) - Configure API keys
6. [Validation](#14-validation-checklist) - Verify setup

### 17.2 Development Workflow
- [Make Commands](#9-make-commands-development-workflow) - Common development tasks
- [Pre-commit Hooks](#11-pre-commit-hooks-setup) - Automated code quality
- [Troubleshooting](#15-troubleshooting-common-issues) - Common issues

### 17.3 Optional Components
- [IDE Setup](#10-ide-setup-recommended) - VS Code configuration
- [Optional Dependencies](#12-optional-dependencies-advanced-features) - Cache, messaging
- [Development Standards](#13-development-standards) - Code quality requirements

---
