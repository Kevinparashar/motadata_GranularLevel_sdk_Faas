# Complete Azure DevOps Repository Workflow Guide - Beginner's Guide

## Overview

This guide explains how to work with **Azure DevOps Git Repository** from scratch, following industrial standards for SDK development. Azure DevOps uses Git, but has its own interface and workflow.

**Important**: Since the SDK is in development phase, we follow this order:
1. **First**: Establish `develop` branch (foundation)
2. **Second**: Create feature branches FROM develop (component work)
3. **Third**: Merge feature branches TO develop (integration)
4. **Last**: Merge develop TO main (only when ready for release)

---

## Part 1: Understanding Azure DevOps Repository

### What is Azure DevOps Repository?

Azure DevOps Repository is Microsoft's Git hosting service. It's like GitHub, but integrated with Azure DevOps work items, pipelines, and boards.

**Key Concepts:**
- **Repository (Repo)**: Your code storage in Azure DevOps
- **Branches**: Different versions of your code
- **Pull Requests (PRs)**: Request to merge code from one branch to another
- **Work Items**: Your user stories (Agent #12, RAG #13, Gateway #14, Prompt #15)
- **Commits**: Saved changes in your code

---

## Part 2: Initial Setup - Connecting to Azure DevOps

### Step 1: Get Your Azure DevOps Repository URL

1. Go to: `https://dev.azure.com/Motadata`
2. Click on your project (e.g., "NextGen")
3. Click: **"Repos"** (left sidebar)
4. Click: **"Files"**
5. You'll see your repository URL at the top
   - Example: `https://dev.azure.com/Motadata/NextGen/_git/motadata-python-ai-sdk`

### Step 2: Check if Repository is Already Connected

```bash
# Check if remote repository is configured
git remote -v

# If you see output like:
# origin  https://dev.azure.com/Motadata/.../_git/motadata-python-ai-sdk (fetch)
# origin  https://dev.azure.com/Motadata/.../_git/motadata-python-ai-sdk (push)
# Then repository is already connected!
```

### Step 3: Connect to Azure DevOps Repository (If Not Connected)

```bash
# Option 1: If repository exists in Azure DevOps
git remote add origin https://dev.azure.com/Motadata/[ProjectName]/_git/[RepoName]

# Option 2: If starting fresh
# Clone the repository
git clone https://dev.azure.com/Motadata/[ProjectName]/_git/[RepoName]
cd [RepoName]

# Option 3: If you have local code, connect it
git remote add origin https://dev.azure.com/Motadata/[ProjectName]/_git/[RepoName]
git branch -M main  # Rename branch to main if needed
git push -u origin main
```

**Replace:**
- `[ProjectName]` with your project name (e.g., "NextGen")
- `[RepoName]` with your repository name (e.g., "motadata-python-ai-sdk")

---

## Part 3: Setting Up Branch Structure - DEVELOP BRANCH FIRST

### ⚠️ IMPORTANT: Develop is the Integration Branch

Since the SDK is in development phase, **develop branch is the integration branch where all feature work is merged first**. All component files are developed on feature branches, then merged into develop via pull requests. The main branch remains stable and contains only baseline repository files until the first release.

### Step 1: Create Develop Branch in Azure DevOps

**Option A: Using Azure DevOps Web Interface (Easiest)**

1. Go to: Azure DevOps → Repos → Branches
2. Click: **"New branch"**
3. Set:
   - **Name**: `develop`
   - **Based on**: `main` (or `master`)
4. Click: **"Create branch"**

**Option B: Using Git Commands**

```bash
# Ensure you're on main
git checkout main
git pull origin main

# Create develop branch locally
git checkout -b develop

# Push develop to Azure DevOps
# This establishes the integration branch where all feature work will be merged
git push -u origin develop
```

### Step 2: Verify Branches in Azure DevOps

1. Go to: Azure DevOps → Repos → Branches
2. You should see:
   - `main` (or `master`) - Stable, contains only baseline repository files until first release
   - `develop` (newly created) - **This is the integration branch where all feature work is merged first**

---

## Part 4: Component 1 - LiteLLM Gateway (User Story #14)

### Complete File List for LiteLLM Gateway Component

**Component Files (MUST PUSH):**
- `src/core/litellm_gateway/__init__.py`
- `src/core/litellm_gateway/gateway.py`
- `src/core/litellm_gateway/functions.py`
- `src/core/litellm_gateway/README.md`

**Test Files (MUST PUSH):**
- `src/tests/unit_tests/test_litellm_gateway.py`
- `src/tests/unit_tests/test_litellm_gateway_functions.py`

**Shared Files (First Component Only - Commit Again if Modified Later):**
- `src/core/interfaces.py` (if exists)
- `src/core/__init__.py` (if you're adding Gateway exports)
- `pyproject.toml`
- `README.md` (main project README)
- `.gitignore`

**Note**: Shared files should only be committed again in later components if they are modified. For example, if `pyproject.toml` is updated in a later component, it should be staged and committed again.

**Files NOT to Push:**
- `__pycache__/` directories (auto-generated)
- `.pyc` files (compiled Python)
- `venv/` or virtual environment folders
- `.vscode/` or IDE settings
- `.env` files (environment variables)
- Any local configuration files

### Complete Azure DevOps Workflow

#### Step 1: Prepare Local Repository

```bash
# Navigate to your SDK folder
cd /home/kevin-parashar/Desktop/motadata-python-ai-sdk

# Check current status
git status

# Ensure you're on develop and it's up to date
# Develop is the integration branch where all feature work is merged first
git checkout develop
git pull origin develop

# Verify you're on develop
git branch
# Should show: * develop
```

#### Step 2: Create Feature Branch FROM Develop

```bash
# Create feature branch FROM develop
git checkout -b feature/litellm-gateway-implementation

# Verify
git branch
# Should show: * feature/litellm-gateway-implementation
```

#### Step 3: Stage Files for Gateway Component

```bash
# ============================================
# STAGE COMPONENT FILES
# ============================================
# Stage entire Gateway component directory
git add src/core/litellm_gateway/

# ============================================
# STAGE TEST FILES
# ============================================
git add src/tests/unit_tests/test_litellm_gateway.py
git add src/tests/unit_tests/test_litellm_gateway_functions.py

# ============================================
# STAGE SHARED FILES (FIRST COMPONENT ONLY)
# ============================================
# These files are committed with the first component
# Note: If these files are modified in later components, they should be committed again
git add src/core/interfaces.py  # If exists
git add src/core/__init__.py     # If you're adding Gateway exports
git add pyproject.toml
git add README.md
git add .gitignore

# ============================================
# VERIFY WHAT'S STAGED
# ============================================
git status

# You should see:
# - src/core/litellm_gateway/ (all files)
# - src/tests/unit_tests/test_litellm_gateway.py
# - src/tests/unit_tests/test_litellm_gateway_functions.py
# - Shared files (interfaces.py, __init__.py, pyproject.toml, README.md, .gitignore)
```

#### Step 4: Commit Changes

```bash
git commit -m "feat: Implement LiteLLM Gateway component (User Story #14)

- Add LiteLLM Gateway with multi-provider support
- Implement factory and convenience functions
- Add comprehensive unit tests
- Add component documentation

Related: Azure DevOps User Story #14"
```

#### Step 5: Push Feature Branch to Azure DevOps

```bash
# Push feature branch to Azure DevOps
# This creates the branch in Azure DevOps
git push -u origin feature/litellm-gateway-implementation
```

**What happens:**
- Your branch is now in Azure DevOps
- You can see it in: Azure DevOps → Repos → Branches
- Code is ready for PR creation

#### Step 6: Create Pull Request in Azure DevOps

**In Azure DevOps Web Interface:**

1. **Go to**: `https://dev.azure.com/Motadata/[ProjectName]/_git/[RepoName]`
2. **Click**: **"Pull requests"** (left sidebar)
3. **Click**: **"New Pull Request"** button
4. **Set Pull Request Details:**
   - **Source branch**: `feature/litellm-gateway-implementation`
   - **Target branch**: `develop` ← **IMPORTANT: Target develop, not main**
   - **Title**: `feat: LiteLLM Gateway Implementation (User Story #14)`
   - **Description**:
     ```markdown
     ## Component: LiteLLM Gateway
     
     ### User Story
     Links to: [Azure DevOps User Story #14](link-to-work-item)
     
     ### Changes
     - [x] LiteLLM Gateway implementation
     - [x] Factory functions (create_gateway, configure_gateway)
     - [x] Convenience functions (generate_text, generate_embeddings)
     - [x] Unit tests
     - [x] Documentation
     
     ### Files Changed
     - `src/core/litellm_gateway/` (all files)
     - `src/tests/unit_tests/test_litellm_gateway.py`
     - `src/tests/unit_tests/test_litellm_gateway_functions.py`
     - Shared files (interfaces.py, __init__.py, pyproject.toml, README.md, .gitignore)
     
     ### Testing
     - [x] Unit tests pass
     - [x] Manual testing completed
     
     ### Checklist
     - [x] Code follows SDK patterns
     - [x] Tests added
     - [x] Documentation updated
     ```
5. **Link Work Item:**
   - Click: **"Add a work item"**
   - Search for: **User Story #14** (LiteLLM Gateway)
   - Select it
6. **Click**: **"Create"**

#### Step 7: After PR is Approved and Merged

```bash
# Switch back to develop
git checkout develop

# Pull latest changes (includes your merged PR)
# NOW GATEWAY IS IN DEVELOP BRANCH
git pull origin develop

# Verify Gateway is now in develop
ls src/core/litellm_gateway/
# Should show: __init__.py, gateway.py, functions.py, README.md

# Delete local feature branch (cleanup)
git branch -d feature/litellm-gateway-implementation
```

**What happens:**
- Your PR is merged to `develop` branch in Azure DevOps
- Gateway component is now in develop (first component pushed)
- You can see it in: Azure DevOps → Repos → Commits
- Your work item #14 can be marked as "Done"

---

## Part 5: Component 2 - Prompt Context Management (User Story #15)

### Complete File List for Prompt Context Management Component

**Component Files (MUST PUSH):**
- `src/core/prompt_context_management/__init__.py`
- `src/core/prompt_context_management/prompt_manager.py`
- `src/core/prompt_context_management/functions.py`
- `src/core/prompt_context_management/README.md`

**Test Files (MUST PUSH):**
- `src/tests/unit_tests/test_prompt_context_functions.py`

**Shared Files (ONLY IF MODIFIED):**
- `src/core/__init__.py` (only if you're adding Prompt exports)
- `README.md` (only if you updated main README with Prompt info)

**Files NOT to Push:**
- Same as Gateway component (no `__pycache__`, `.pyc`, `venv/`, etc.)

### Complete Azure DevOps Workflow

#### Step 1: Prepare from Updated Develop

```bash
# Switch to develop
git checkout develop

# Get latest (includes Gateway if merged)
git pull origin develop

# Verify you're on develop
git branch
# Should show: * develop
```

#### Step 2: Create Feature Branch FROM Develop

```bash
# Create feature branch FROM develop
git checkout -b feature/prompt-context-management-implementation
```

#### Step 3: Stage Prompt Component Files

```bash
# ============================================
# STAGE COMPONENT FILES
# ============================================
# Stage entire Prompt component directory
git add src/core/prompt_context_management/

# ============================================
# STAGE TEST FILES
# ============================================
git add src/tests/unit_tests/test_prompt_context_functions.py

# ============================================
# STAGE UPDATED SHARED FILES (IF MODIFIED)
# ============================================
# Only stage if you actually modified these files
git add src/core/__init__.py  # Only if you added Prompt exports
git add README.md              # Only if you updated main README

# ============================================
# VERIFY WHAT'S STAGED
# ============================================
git status

# You should see:
# - src/core/prompt_context_management/ (all files)
# - src/tests/unit_tests/test_prompt_context_functions.py
# - Updated shared files (if modified)
```

#### Step 4: Commit

```bash
git commit -m "feat: Implement Prompt Context Management component (User Story #15)

- Add Prompt Context Manager with template support
- Implement context window management
- Add factory and convenience functions
- Add comprehensive unit tests
- Add component documentation

Related: Azure DevOps User Story #15"
```

#### Step 5: Push to Azure DevOps

```bash
git push -u origin feature/prompt-context-management-implementation
```

#### Step 6: Create Pull Request in Azure DevOps

1. Go to: **Pull requests** → **New Pull Request**
2. **Source**: `feature/prompt-context-management-implementation`
3. **Target**: `develop` ← **Target develop, not main**
4. **Title**: `feat: Prompt Context Management Implementation (User Story #15)`
5. **Link Work Item**: User Story #15
6. **Create**

#### Step 7: After Merge

```bash
git checkout develop
git pull origin develop  # Now includes Gateway + Prompt
git branch -d feature/prompt-context-management-implementation
```

---

## Part 6: Component 3 - Agent Framework (User Story #12)

### Complete File List for Agent Framework Component

**Component Files (MUST PUSH):**
- `src/core/agno_agent_framework/__init__.py`
- `src/core/agno_agent_framework/agent.py`
- `src/core/agno_agent_framework/memory.py`
- `src/core/agno_agent_framework/session.py`
- `src/core/agno_agent_framework/tools.py`
- `src/core/agno_agent_framework/plugins.py`
- `src/core/agno_agent_framework/orchestration.py`
- `src/core/agno_agent_framework/functions.py`
- `src/core/agno_agent_framework/README.md`
- `src/core/agno_agent_framework/agents/__init__.py`
- `src/core/agno_agent_framework/agents/README.md`

**Test Files (MUST PUSH):**
- `src/tests/unit_tests/test_agent.py`
- `src/tests/unit_tests/test_agent_functions.py`

**Shared Files (ONLY IF MODIFIED):**
- `src/core/__init__.py` (only if you're adding Agent exports)
- `README.md` (only if you updated main README with Agent info)

**Files NOT to Push:**
- `src/core/agno_agent_framework/__pycache__/` (auto-generated)
- Same exclusions as other components

### Complete Azure DevOps Workflow

#### Step 1: Prepare from Updated Develop

```bash
git checkout develop
git pull origin develop  # Now includes Gateway, Prompt if merged
```

#### Step 2: Create Feature Branch FROM Develop

```bash
git checkout -b feature/agent-framework-implementation
```

#### Step 3: Stage Agent Component Files

```bash
# ============================================
# STAGE COMPONENT FILES
# ============================================
# Stage entire Agent component directory (includes agents/ subdirectory)
git add src/core/agno_agent_framework/

# ============================================
# STAGE TEST FILES
# ============================================
git add src/tests/unit_tests/test_agent.py
git add src/tests/unit_tests/test_agent_functions.py

# ============================================
# STAGE UPDATED SHARED FILES (IF MODIFIED)
# ============================================
git add src/core/__init__.py  # Only if you added Agent exports
git add README.md              # Only if you updated main README

# ============================================
# VERIFY WHAT'S STAGED
# ============================================
git status

# You should see:
# - src/core/agno_agent_framework/ (all files including agents/)
# - src/tests/unit_tests/test_agent.py
# - src/tests/unit_tests/test_agent_functions.py
# - Updated shared files (if modified)
```

#### Step 4: Commit

```bash
git commit -m "feat: Implement Agno Agent Framework component (User Story #12)

- Add Agent Framework with multi-agent support
- Implement agent orchestration and workflows
- Add memory and session management
- Add tools and plugins system
- Add factory and convenience functions
- Add comprehensive unit tests
- Add component documentation

Dependencies: LiteLLM Gateway (User Story #14)
Related: Azure DevOps User Story #12"
```

#### Step 5: Push to Azure DevOps

```bash
git push -u origin feature/agent-framework-implementation
```

#### Step 6: Create Pull Request in Azure DevOps

1. **Source**: `feature/agent-framework-implementation`
2. **Target**: `develop` ← **Target develop, not main**
3. **Title**: `feat: Agent Framework Implementation (User Story #12)`
4. **Link Work Item**: User Story #12
5. **Note in Description**: "Depends on LiteLLM Gateway (User Story #14)"
6. **Create**

#### Step 7: After Merge

```bash
git checkout develop
git pull origin develop  # Now includes Gateway, Prompt, Agent
git branch -d feature/agent-framework-implementation
```

---

## Part 7: Component 4 - RAG System (User Story #13)

### Complete File List for RAG System Component

**Component Files (MUST PUSH):**
- `src/core/rag/__init__.py`
- `src/core/rag/rag_system.py`
- `src/core/rag/document_processor.py`
- `src/core/rag/retriever.py`
- `src/core/rag/generator.py`
- `src/core/rag/functions.py`
- `src/core/rag/README.md`

**Test Files (MUST PUSH):**
- `src/tests/unit_tests/test_rag.py`
- `src/tests/unit_tests/test_rag_functions.py`

**Shared Files (ONLY IF MODIFIED):**
- `src/core/__init__.py` (only if you're adding RAG exports)
- `README.md` (only if you updated main README with RAG info)

**Files NOT to Push:**
- Same exclusions as other components

### Complete Azure DevOps Workflow

#### Step 1: Prepare from Updated Develop

```bash
git checkout develop
git pull origin develop  # Now includes Gateway, Prompt, Agent if merged
```

#### Step 2: Create Feature Branch FROM Develop

```bash
git checkout -b feature/rag-system-implementation
```

#### Step 3: Stage RAG Component Files

```bash
# ============================================
# STAGE COMPONENT FILES
# ============================================
# Stage entire RAG component directory
git add src/core/rag/

# ============================================
# STAGE TEST FILES
# ============================================
git add src/tests/unit_tests/test_rag.py
git add src/tests/unit_tests/test_rag_functions.py

# ============================================
# STAGE UPDATED SHARED FILES (IF MODIFIED)
# ============================================
git add src/core/__init__.py  # Only if you added RAG exports
git add README.md              # Only if you updated main README

# ============================================
# VERIFY WHAT'S STAGED
# ============================================
git status

# You should see:
# - src/core/rag/ (all files)
# - src/tests/unit_tests/test_rag.py
# - src/tests/unit_tests/test_rag_functions.py
# - Updated shared files (if modified)
```

#### Step 4: Commit

```bash
git commit -m "feat: Implement RAG System component (User Story #13)

- Add RAG System with document ingestion
- Implement hybrid retrieval (vector + keyword)
- Add query optimization (rewriting, caching)
- Add document management (update, delete)
- Add batch processing support
- Add factory and convenience functions
- Add comprehensive unit tests
- Add component documentation

Dependencies: LiteLLM Gateway (User Story #14), PostgreSQL Database
Related: Azure DevOps User Story #13"
```

#### Step 5: Push to Azure DevOps

```bash
git push -u origin feature/rag-system-implementation
```

#### Step 6: Create Pull Request in Azure DevOps

1. **Source**: `feature/rag-system-implementation`
2. **Target**: `develop` ← **Target develop, not main**
3. **Title**: `feat: RAG System Implementation (User Story #13)`
4. **Link Work Item**: User Story #13
5. **Note in Description**: "Depends on LiteLLM Gateway (User Story #14) and PostgreSQL Database"
6. **Create**

#### Step 7: After Merge

```bash
git checkout develop
git pull origin develop  # Now includes all 4 components
git branch -d feature/rag-system-implementation
```

---

## Part 8: Understanding Azure DevOps Interface

### Key Areas in Azure DevOps:

1. **Repos** (Code):
   - **Files**: View code files
   - **Commits**: See commit history
   - **Branches**: See all branches
   - **Pull Requests**: Create and review PRs

2. **Boards** (Work Items):
   - **Work Items**: Your user stories (#12, #13, #14, #15)
   - **Backlogs**: List of work items
   - **Sprints**: Sprint planning

3. **Pipelines** (CI/CD):
   - Build pipelines
   - Release pipelines

### Navigating to Your Repository:

```
Azure DevOps → Your Project → Repos → Files
```

---

## Part 9: Complete Workflow Summary

### Visual Flow:

```
┌─────────────────────────────────────────┐
│  MAIN BRANCH                            │
│  (Stable, contains only baseline        │
│   repository files until first release) │
│  - Only gets code when releasing        │
└──────────────┬──────────────────────────┘
               │ Step 1: Create develop
               │ git checkout -b develop
               │ git push origin develop
               ▼
┌─────────────────────────────────────────┐
│  DEVELOP BRANCH                         │
│  (Integration Branch - All feature work │
│   is merged here first)                 │
│  - All features merge here              │
│  - Integration testing happens here     │
└──────────────┬──────────────────────────┘
               │ Step 2: Create feature branches
               │ git checkout develop
               │ git checkout -b feature/component
               │ (Work on component)
               │ git push origin feature/component
               │ (Create PR: feature → develop)
               ▼
┌─────────────────────────────────────────┐
│  FEATURE BRANCHES                      │
│  (Component Development)                │
│  - feature/litellm-gateway             │
│  - feature/prompt-context               │
│  - feature/agent-framework             │
│  - feature/rag-system                 │
│                                         │
│  Each branch:                           │
│  1. Created FROM develop                │
│  2. Component code added                │
│  3. Pushed to Azure DevOps              │
│  4. PR created (feature → develop)      │
│  5. Merged TO develop                    │
└─────────────────────────────────────────┘
```

---

## Part 10: Complete Step-by-Step Commands for Each Component

### Component 1: LiteLLM Gateway (User Story #14)

```bash
# ============================================
# COMPLETE WORKFLOW: LiteLLM Gateway
# ============================================

# 1. Navigate to SDK folder
cd /home/kevin-parashar/Desktop/motadata-python-ai-sdk

# 2. Check current status
git status

# 3. Switch to develop and update
# Develop is the integration branch where all feature work is merged first
git checkout develop
git pull origin develop

# 4. Create feature branch FROM develop
git checkout -b feature/litellm-gateway-implementation

# 5. Stage Gateway component files
git add src/core/litellm_gateway/

# 6. Stage Gateway test files
git add src/tests/unit_tests/test_litellm_gateway.py
git add src/tests/unit_tests/test_litellm_gateway_functions.py

# 7. Stage shared files (first component only)
git add src/core/interfaces.py  # If exists
git add src/core/__init__.py
git add pyproject.toml
git add README.md
git add .gitignore

# 8. Verify what's staged
git status

# 9. Commit
git commit -m "feat: Implement LiteLLM Gateway component (User Story #14)

- Add LiteLLM Gateway with multi-provider support
- Implement factory and convenience functions
- Add comprehensive unit tests
- Add component documentation

Related: Azure DevOps User Story #14"

# 10. Push to Azure DevOps
git push -u origin feature/litellm-gateway-implementation

# 11. Go to Azure DevOps and create PR
# - Source: feature/litellm-gateway-implementation
# - Target: develop
# - Link to User Story #14

# 12. After PR is merged
git checkout develop
git pull origin develop
git branch -d feature/litellm-gateway-implementation
```

---

### Component 2: Prompt Context Management (User Story #15)

```bash
# ============================================
# COMPLETE WORKFLOW: Prompt Context Management
# ============================================

# 1. Update develop
git checkout develop
git pull origin develop

# 2. Create feature branch FROM develop
git checkout -b feature/prompt-context-management-implementation

# 3. Stage Prompt component files
git add src/core/prompt_context_management/

# 4. Stage Prompt test files
git add src/tests/unit_tests/test_prompt_context_functions.py

# 5. Stage updated shared files (if modified)
git add src/core/__init__.py  # Only if updated
git add README.md              # Only if updated

# 6. Verify
git status

# 7. Commit
git commit -m "feat: Implement Prompt Context Management (User Story #15)

- Add Prompt Context Manager with template support
- Implement context window management
- Add factory and convenience functions
- Add comprehensive unit tests
- Add component documentation

Related: Azure DevOps User Story #15"

# 8. Push to Azure DevOps
git push -u origin feature/prompt-context-management-implementation

# 9. Create PR in Azure DevOps
# - Source: feature/prompt-context-management-implementation
# - Target: develop
# - Link to User Story #15

# 10. After merge
git checkout develop
git pull origin develop
git branch -d feature/prompt-context-management-implementation
```

---

### Component 3: Agent Framework (User Story #12)

```bash
# ============================================
# COMPLETE WORKFLOW: Agent Framework
# ============================================

# 1. Update develop
git checkout develop
git pull origin develop

# 2. Create feature branch FROM develop
git checkout -b feature/agent-framework-implementation

# 3. Stage Agent component files
git add src/core/agno_agent_framework/

# 4. Stage Agent test files
git add src/tests/unit_tests/test_agent.py
git add src/tests/unit_tests/test_agent_functions.py

# 5. Stage updated shared files (if modified)
git add src/core/__init__.py  # Only if updated
git add README.md              # Only if updated

# 6. Verify
git status

# 7. Commit
git commit -m "feat: Implement Agent Framework (User Story #12)

- Add Agent Framework with multi-agent support
- Implement agent orchestration and workflows
- Add memory and session management
- Add tools and plugins system
- Add factory and convenience functions
- Add comprehensive unit tests
- Add component documentation

Dependencies: LiteLLM Gateway (User Story #14)
Related: Azure DevOps User Story #12"

# 8. Push to Azure DevOps
git push -u origin feature/agent-framework-implementation

# 9. Create PR in Azure DevOps
# - Source: feature/agent-framework-implementation
# - Target: develop
# - Link to User Story #12
# - Note: Depends on Gateway (User Story #14)

# 10. After merge
git checkout develop
git pull origin develop
git branch -d feature/agent-framework-implementation
```

---

### Component 4: RAG System (User Story #13)

```bash
# ============================================
# COMPLETE WORKFLOW: RAG System
# ============================================

# 1. Update develop
git checkout develop
git pull origin develop

# 2. Create feature branch FROM develop
git checkout -b feature/rag-system-implementation

# 3. Stage RAG component files
git add src/core/rag/

# 4. Stage RAG test files
git add src/tests/unit_tests/test_rag.py
git add src/tests/unit_tests/test_rag_functions.py

# 5. Stage updated shared files (if modified)
git add src/core/__init__.py  # Only if updated
git add README.md              # Only if updated

# 6. Verify
git status

# 7. Commit
git commit -m "feat: Implement RAG System (User Story #13)

- Add RAG System with document ingestion
- Implement hybrid retrieval (vector + keyword)
- Add query optimization (rewriting, caching)
- Add document management (update, delete)
- Add batch processing support
- Add factory and convenience functions
- Add comprehensive unit tests
- Add component documentation

Dependencies: LiteLLM Gateway (User Story #14), PostgreSQL Database
Related: Azure DevOps User Story #13"

# 8. Push to Azure DevOps
git push -u origin feature/rag-system-implementation

# 9. Create PR in Azure DevOps
# - Source: feature/rag-system-implementation
# - Target: develop
# - Link to User Story #13
# - Note: Depends on Gateway (User Story #14) and Database

# 10. After merge
git checkout develop
git pull origin develop
git branch -d feature/rag-system-implementation
```

---

## Part 11: Files NOT to Push - Complete List

### ⚠️ IMPORTANT: Never Push These Files

**Auto-Generated Files:**
- `__pycache__/` directories (anywhere in the project)
- `*.pyc` files (compiled Python bytecode)
- `*.pyo` files (optimized bytecode)
- `.Python` files

**Development Environment:**
- `venv/` or `virtualenv/` directories
- `.venv/` directories
- `env/` directories
- `ENV/` directories

**IDE/Editor Files:**
- `.vscode/` directory
- `.idea/` directory (JetBrains IDEs)
- `*.swp` files (Vim)
- `*.swo` files (Vim)
- `.DS_Store` (macOS)

**Configuration Files (Sensitive):**
- `.env` files (environment variables)
- `.env.local` files
- `config.local.py` files
- Any files containing API keys, passwords, or secrets

**Build/Output Files:**
- `dist/` directory
- `build/` directory
- `*.egg-info/` directories
- `.pytest_cache/` directory
- `.coverage` files

**Documentation Build:**
- `docs/_build/` directory
- `site/` directory (if using static site generators)

**Temporary Files:**
- `*.log` files (unless specifically needed)
- `*.tmp` files
- `*.bak` files

**OS Files:**
- `Thumbs.db` (Windows)
- `.DS_Store` (macOS)
- `.directory` (Linux)

### How to Verify Before Pushing

```bash
# Check what will be pushed
git status

# If you see any of the above files, unstage them:
git reset HEAD path/to/unwanted/file

# Or check .gitignore is working:
git check-ignore -v path/to/file
```

---

## Part 12: Azure DevOps Specific Features

### 1. Linking PR to Work Item

**In Pull Request:**
1. Click: **"Add a work item"** (in PR description)
2. Search for: Your user story number (#12, #13, #14, #15)
3. Select it
4. Work item is now linked to PR

**Benefits:**
- PR shows in work item
- Work item shows PR link
- Easy to track progress

### 2. Viewing Changes in Azure DevOps

**In Pull Request:**
- **Files** tab: See all changed files
- **Commits** tab: See commit history
- **Updates** tab: See PR activity

### 3. Reviewing Code in Azure DevOps

**In Pull Request:**
- Click on any file to see changes
- Add comments on specific lines
- Approve or request changes
- Complete PR when approved

### 4. Branch Policies (If Configured)

Azure DevOps may have branch policies:
- **Required reviewers**: Must have approvals
- **Build validation**: Must pass builds
- **Work item linking**: Must link work item

---

## Part 13: After All Components are Merged

### Step 1: Integration Testing on Develop

```bash
# Work on develop branch
git checkout develop
git pull origin develop

# Test all components together
# Fix any integration issues
# Make commits to develop (or create fix branches)

# If allowed by repository policy, tag the development version
# Note: Some teams restrict tag creation or only allow tags on main
git tag -a v0.1.0-dev -m "SDK v0.1.0-dev - Development version"
git push origin v0.1.0-dev
```

### Step 2: Release to Main (When Ready)

**Create Release Pull Request:**

1. Go to: **Pull requests** → **New Pull Request**
2. **Source**: `develop`
3. **Target**: `main` ← **First time merging to main**
4. **Title**: `Release: SDK v0.1.0 - All Core Components`
5. **Description**: List all components included
6. **Create and merge**

**After Merge:**

```bash
git checkout main
git pull origin main

# If allowed by repository policy, tag the release version
# Note: Some teams restrict tag creation or require specific tag formats
git tag -a v0.1.0 -m "SDK v0.1.0 - First stable release"
git push origin v0.1.0
```

---

## Part 14: Common Issues and Solutions

### Issue: "Repository not found"

**Solution:**
```bash
# Check remote URL
git remote -v

# If wrong, update it
git remote set-url origin https://dev.azure.com/Motadata/[Project]/_git/[Repo]

# Test connection
git fetch origin
```

### Issue: "Authentication failed"

**Solution:**
- Azure DevOps uses Personal Access Token (PAT)
- Generate PAT: Azure DevOps → User Settings → Personal Access Tokens
- Use PAT as password when pushing

### Issue: "Branch already exists in Azure DevOps"

**Solution:**
```bash
# Delete remote branch
git push origin --delete feature/old-branch-name

# Or use different branch name
git checkout -b feature/component-name-v2
```

### Issue: "Can't push - need to pull first"

**Solution:**
```bash
# Pull latest changes
git pull origin develop

# Resolve any conflicts
# Then push again
git push origin feature/your-branch
```

---

## Summary

### Your Azure DevOps Workflow:

1. **Develop Branch**: Integration branch - **All feature work is merged here first**
2. **Feature Branches**: One per component, created FROM develop
3. **Pull Requests**: Created in Azure DevOps (feature → develop)
4. **Work Items**: Linked to PRs in Azure DevOps
5. **Main Branch**: Release branch (contains only baseline repository files until first release)

### Process:

1. **First**: Create develop branch (foundation)
2. **Second**: Create feature branch FROM develop
3. **Third**: Develop component on feature branch
4. **Fourth**: Commit and push feature branch to Azure DevOps
5. **Fifth**: Create PR in Azure DevOps (feature → develop)
6. **Sixth**: Link to work item in Azure DevOps
7. **Seventh**: After merge, repeat for next component
8. **Eighth**: When all merged, test on develop
9. **Ninth**: Release: develop → main (via PR in Azure DevOps)

### This Follows Industrial Standards:

- ✅ Git Flow branching strategy
- ✅ Azure DevOps best practices
- ✅ Work item integration
- ✅ Code review process
- ✅ Staged releases
- ✅ Develop branch as foundation

---

**Remember**: 
- **Develop is the integration branch where all feature work is merged first**
- Always push to Azure DevOps repository
- Always create PRs in Azure DevOps web interface
- Always link PRs to work items
- Always target `develop` branch for component PRs
- Never push `__pycache__`, `venv/`, `.env`, or other excluded files
- Shared files should only be committed again if modified in later components
