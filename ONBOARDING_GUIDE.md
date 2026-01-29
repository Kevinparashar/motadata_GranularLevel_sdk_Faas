# ONBOARDING_GUIDE — Motadata Python AI SDK

This is the **START HERE** document for new engineers working with the Motadata Python AI SDK.

It is intentionally practical:
- what this SDK is really for
- where to find things fast
- how to run the “golden path”
- how to add new capability without creating platform debt

If you follow this guide, you’ll be productive **and** you won’t accidentally break the SDK’s core guarantees.

---

## What this SDK does (in one minute)

This SDK is a governed foundation for building AI-native functionality using strict boundaries:

- **Gateway**: one integration surface for LLM providers/models (`src/core/litellm_gateway/`)
- **Agents**: decision layer (reason/plan/format outputs) (`src/core/agno_agent_framework/agent.py`)
- **Tools**: execution layer (API/DB/files, side effects) (`src/core/agno_agent_framework/tools.py`)
- **Prompt-based generator**: create agents/tools from intent, with guardrails (`src/core/prompt_based_generator/`)
- **RAG**: grounded answers from documents (`src/core/rag/`)
- **FaaS services**: SDK capabilities exposed as HTTP services (`src/faas/services/`)

### What this SDK is **not**
- Not a “prompt playground”
- Not a place to call APIs directly from agents
- Not a framework where generated code runs ungoverned

**North star:** predictable outputs, replaceable components, safe execution, multi-tenant readiness.

---

## Quick start (local validation)

### 1) Install dependencies
```bash
pip install -r requirements.txt
```

If you’re contributing to the SDK (not just using it):
```bash
make install-dev
```

### 2) Provide an API key
The quickstart examples auto-detect one of:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`

Example:
```bash
export OPENAI_API_KEY="your-key"
```

Optional `.env` support (examples try to load it if `python-dotenv` is installed):
```bash
pip install python-dotenv
echo "OPENAI_API_KEY=your-key" > .env
```

### 3) Run Hello World
```bash
python examples/hello_world.py
```

**What success looks like**
- It prints “Gateway created successfully”
- It prints an AI response
- It prints model + token usage

If it fails, jump to [Troubleshooting](#troubleshooting).

---

## Repo navigation (where things live)

### High-impact folders
| Area | What it’s for | When you touch it |
|---|---|---|
| `src/core/` | SDK primitives (gateway, agent runtime, generator, cache, RAG) | When building platform capability |
| `src/faas/` | FastAPI services exposing SDK over HTTP | When you need SDK-as-a-service |
| `src/services/` | Integration adapters and external system clients | When you’re wiring real APIs/DBs |
| `src/integrations/` | Optional integrations (NATS, OTEL, CODEC) | When enabling platform integrations |
| `examples/` | Runnable “how to use the SDK” reference | Always—this is the golden path |
| `docs/` | Architecture + component guides | When you want deeper context |
| `src/tests/` | Unit/integration tests | When you ship anything real |

### Core component map (`src/core/`)
You will see many modules. The ones most contributors touch are:

- **Gateway:** `litellm_gateway/`  
- **Agent runtime:** `agno_agent_framework/`  
- **Prompt-based generation:** `prompt_based_generator/`  
- **Cache abstraction:** `cache_mechanism/`  
- **RAG:** `rag/`  
- **Utilities:** `utils/`, `validation/`, `error_handler`-style helpers

Other modules exist for platform expansion (data ingestion, ML, evaluation/observability, DB wrappers). Don’t edit them unless your change is intentional and reviewed.

---

## The “golden path” (learn this once)

Everything in this SDK is designed around one operational pattern:

```
Input → Agent (decides) → Tool (acts) → Agent (formats) → Structured output
```

If you collapse these layers, you’ll create systems that are hard to debug, hard to secure, and expensive to maintain.

### Gateway: your LLM access boundary
Hello World uses this entry point:
```python
from src.core.litellm_gateway import create_gateway
```

The gateway standardizes provider/model selection and response format. It is also where reliability hooks live.

### Tools: side effects happen here
Tools execute real operations. Typical examples:
- fetch ticket details
- call an internal API
- query a database
- trigger an action

Tools should return **structured** results (dict/list), not prose.

### Agents: reasoning happens here
Agents:
- interpret input
- decide which tool(s) to call
- format outputs for downstream systems

Agents should return **structured** output (JSON/dict) and must not perform I/O.

---

## How to run the SDK as services (FaaS)

If you want “SDK as a service” (multi-tenant HTTP access), use `src/faas/services/`.

### Run a service
```bash
make run-service SERVICE=gateway_service PORT=8080
```

Available services (from the Makefile):
- `agent_service`
- `rag_service`
- `gateway_service`
- `ml_service`
- `cache_service`
- `prompt_service`
- `data_ingestion_service`
- `prompt_generator_service`
- `llmops_service`

### Learn by example
Start here:
- `examples/faas/README.md`
- `examples/faas/complete_workflow_example.py`

**Practical note:** FaaS services expect headers (tenant/correlation style). See `src/faas/shared/contracts.py` and `src/faas/shared/middleware.py`.

---

## Common contribution tasks (do it the SDK way)

### A) Add a new Tool
**Where it belongs**
- Reusable tool logic: `src/services/` (preferred)
- Registry wiring: `src/core/agno_agent_framework/tools.py` usage or component-level `functions.py`
- Example: `examples/basic_usage/` or `examples/integration/`

**Minimum quality bar**
- typed inputs
- structured output
- strict timeout for network calls
- structured error return or typed exception
- unit test covering success + failure

**Registering a pure function tool**
```python
from src.core.agno_agent_framework.tools import ToolRegistry

def compute_priority(urgency: int, impact: int) -> dict:
    score = max(1, min(5, round((urgency + impact) / 2)))
    return {"priority": score}

registry = ToolRegistry()
registry.register_function(
    name="compute_priority",
    function=compute_priority,
    description="Compute ticket priority from urgency and impact."
)
```

### B) Add a new Agent
**Where it belongs**
- Agent runtime is in `src/core/agno_agent_framework/`
- Agent creation via prompt is in `src/core/prompt_based_generator/functions.py`
- Example-driven learning: `examples/prompt_based/`

**Minimum quality bar**
- explicit prompt contract (role/objective/constraints)
- strict output schema (JSON)
- “missing data” rule (no hallucinations)
- unit test verifying output structure

### C) Add a new `src/core/<component>/`
Use the SDK component structure (documented in `PYTHON_SDK_DEVELOPMENT_ENVIRONMENT_SETUP_GUIDE.md` and `PYTHON_SDK_QUALITY_GATE_RULES_AND_DEVELOPMENT_GUIDELINE_DOCUMENT.md`):
```
src/core/your_component/
├── __init__.py
├── README.md
├── your_component.py
├── functions.py
└── interfaces.py
```

**Rule:** if a feature is meant for consumers, it must be discoverable (clean imports) and documented (README + example).

### D) Add or update a FaaS service
**Where it belongs**
- `src/faas/services/<service_name>/service.py` (FastAPI app)
- Shared behavior: `src/faas/shared/`

**Minimum quality bar**
- consistent headers and response envelopes
- no secrets in logs
- predictable error mapping
- example client under `examples/faas/`

---

## Local quality gates (before you ask for review)

Run these:
```bash
make format-check
make type-check
make lint
make test-unit
```

If you changed service wiring or cross-module behavior:
```bash
make test-integration
```

If you changed examples or public entry points:
- run the example(s) you touched, start-to-finish

---

## Troubleshooting

### “No API key found”
Set one of:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`

### “Import errors / missing dependency”
Run:
```bash
pip install -r requirements.txt
```

### “Service won’t start”
Use:
```bash
make run-service SERVICE=gateway_service PORT=8080
```

If it still fails:
- confirm `uvicorn` is installed
- confirm you’re in the correct venv

### “Agent output is messy / not JSON”
Fix the prompt:
- explicitly require strict JSON output
- explicitly forbid prose
- validate output in tests

### “Tool is slow / blocks execution”
Tools are sync in many places. If a tool does heavy I/O, enforce:
- strict timeout
- bounded retries
- offload heavy work to threads *explicitly* (don’t block the async loop)

More help:
- `docs/troubleshooting/` (repo troubleshooting library)
- `docs/guide/DOCUMENTATION_INDEX.md` (where to look next)

---

## What to read next (high ROI)
- `docs/guide/DOCUMENTATION_INDEX.md` — fast navigation
- `docs/guide/DEVELOPER_INTEGRATION_GUIDE.md` — how components integrate
- `PYTHON_SDK_DEVELOPMENT_ENVIRONMENT_SETUP_GUIDE.md` — development environment setup
- `PYTHON_SDK_QUALITY_GATE_RULES_AND_DEVELOPMENT_GUIDELINE_DOCUMENT.md` — quality gates and development guidelines
- `CONTRIBUTING.md` — contribution process and standards

---

## Final expectations (tell it like it is)
If you commit code that:
- blurs agent/tool boundaries
- hides secrets in logs
- returns unstructured output
- breaks examples
- ships without tests

…it will not merge. That’s not politics—it’s platform hygiene.