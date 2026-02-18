# Unit Tests Directory Structure

This directory contains unit tests organized by component/module for better maintainability and navigation.

## Directory Structure

```
tests/unit_tests/
├── agent/              # Agent framework tests
│   ├── test_agent.py
│   ├── test_agent_codec.py
│   ├── test_agent_exceptions.py
│   ├── test_agent_functions.py
│   ├── test_memory.py
│   ├── test_orchestration.py
│   ├── test_plugins.py
│   ├── test_session.py
│   └── test_tools.py
├── cache/              # Cache-related tests
│   ├── test_cache.py
│   ├── test_cache_enhancements.py
│   ├── test_cache_functions.py
│   └── test_kv_cache.py
├── codec/              # Codec integration tests
│   ├── test_codec.py
│   ├── test_codec_functions.py
│   ├── test_codec_registry_migration.py
│   └── test_codec_serializer.py
├── config/             # Configuration tests
│   ├── test_config_builders.py
│   ├── test_config_discovery.py
│   └── test_config_validator.py
├── database/           # Database tests
│   └── test_postgresql_database.py
├── error_handler/      # Error handling tests
│   └── test_error_handler.py
├── feedback/           # Feedback system tests
│   └── test_feedback_system.py
├── gateway/            # LiteLLM Gateway tests
│   ├── test_litellm_gateway.py
│   └── test_litellm_gateway_functions.py
├── health_check/       # Health check tests
│   └── test_health_check.py
├── llmops/             # LLMOps tests
│   └── test_llmops.py
├── observability/      # Observability tests
│   ├── test_observability.py
│   └── test_otel.py
├── prompt/             # Prompt-related tests
│   ├── test_prompt_based_generator.py
│   ├── test_prompt_context_functions.py
│   └── test_prompt_enhancements.py
├── rag/                # RAG system tests
│   ├── test_rag.py
│   ├── test_rag_exceptions.py
│   └── test_rag_functions.py
├── test_faas/          # FaaS service tests
│   └── (various service tests)
├── type_helpers/       # Type helper tests
│   └── test_type_helpers.py
└── utils/              # Utility function tests
    ├── test_data_ingestion.py
    ├── test_guardrails.py
    ├── test_hallucination_detector.py
    ├── test_nats.py
    └── test_rate_limiter.py
```

## Running Tests

### Run all unit tests
```bash
pytest tests/unit_tests/
```

### Run tests for a specific component
```bash
pytest tests/unit_tests/agent/
pytest tests/unit_tests/codec/
pytest tests/unit_tests/rag/
```

### Run specific test file
```bash
pytest tests/unit_tests/codec/test_codec_serializer.py
```

### Run with coverage
```bash
pytest tests/unit_tests/ --cov=src --cov-report=term
```

## Test Discovery

Pytest automatically discovers all test files recursively in subdirectories. The configuration in `pyproject.toml` ensures:
- Test files matching `test_*.py` pattern are discovered
- Test classes matching `Test*` pattern are discovered
- Test functions matching `test_*` pattern are discovered

## Notes

- Each subdirectory contains an `__init__.py` file to make it a Python package
- Test imports should use absolute imports from `src/` (e.g., `from src.core.codec_integration import ...`)
- The Azure DevOps pipeline and SonarQube configuration support this structure automatically
