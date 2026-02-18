# MOTADATA - ARCHITECTURE OVERVIEW

This is a **quick, beginner-friendly overview** of how the SDK is structured and how data flows through it.

## Layers

- **Core layer (`src/core/`)**: SDK library components (Gateway, Agents, RAG, Cache, ML, etc.)
- **FaaS layer (`src/faas/`)**: Optional FastAPI services that wrap core components
- **Docs (`docs/`)**: Architecture, components, guides, troubleshooting

## Typical flow

1. Your app (or FaaS service) receives a request and extracts `tenant_id`
2. Gateway calls the LLM provider (generate / embed)
3. Cache stores repeated results (when enabled)
4. RAG retrieves relevant documents and generates an answer (if used)
5. Agents orchestrate multi-step workflows (if used)
6. Observability tracks metrics/traces/logs for production debugging

## Where to go next

- Full architecture: [`docs/architecture/SDK_ARCHITECTURE.md`](architecture/SDK_ARCHITECTURE.md)
- Onboarding: [`docs/guide/ONBOARDING_GUIDE.md`](guide/ONBOARDING_GUIDE.md)
- Integration story: [`docs/components/CORE_COMPONENTS_INTEGRATION_STORY.md`](components/CORE_COMPONENTS_INTEGRATION_STORY.md)


