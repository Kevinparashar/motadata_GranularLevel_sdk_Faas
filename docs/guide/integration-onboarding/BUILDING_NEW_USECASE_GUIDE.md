# BUILDING NEW USE CASES (Guide)

This guide explains how to add a **new use case** to the SDK examples in a clean and consistent way.

## Where use cases live

Use cases are organised under:

- `examples/use_cases/`

## Recommended steps

### 1) Pick the use case folder name

Create a new folder under `examples/use_cases/`, for example:

- `examples/use_cases/ticket_summarizer/`

### 2) Add a README for the use case

Add `examples/use_cases/<your_use_case>/README.md` with:

- what the use case does
- required environment variables
- how to run it (exact command)
- expected output
- common failures and fixes

### 3) Keep the flow consistent with SDK components

In most use cases, the flow is:

- **Gateway** for model calls
- **Cache** for repeated calls
- **RAG** if documents/knowledge are involved
- **Agent** if multi-step orchestration or tools are needed

### 4) Add a minimal runnable script

Add at least one runnable script in the use case folder, like:

- `run.py`

### 5) Link back to architecture and integration story

For the “big picture”, also link:

- `CORE_COMPONENTS_INTEGRATION_STORY.md`
- `docs/architecture/SDK_ARCHITECTURE.md`


