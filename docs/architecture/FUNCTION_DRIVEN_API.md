# MOTADATA - FUNCTION-DRIVEN API

The SDK follows a **function-driven API** style to make onboarding easy.

## What it means

Instead of forcing users to construct many classes manually, the SDK provides:

- `create_*` factory functions (easy defaults)
- helper functions like `*_async` wrappers where needed

## Why this is used

- simpler onboarding for new developers
- consistent configuration patterns
- easy dependency injection (you can pass your own instances)

## Where to look in code

Common factory locations:

- `src/core/agno_agent_framework/functions.py`
- `src/core/litellm_gateway/functions.py`
- `src/core/rag/functions.py`
- `src/core/cache_mechanism/functions.py`
- `src/core/data_ingestion/functions.py`


