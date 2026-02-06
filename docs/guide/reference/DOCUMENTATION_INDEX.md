# MOTADATA - DOCUMENTATION INDEX & SEARCH GUIDE

**Complete navigation and search guide to find documentation quickly by topic, functionality, use case, or component type.**

---

## 📚 Documentation Structure

### Getting Started
- **[Onboarding Guide](ONBOARDING_GUIDE.md)** - **START HERE** - Complete guide for new team members
- **[Developer Integration Guide](DEVELOPER_INTEGRATION_GUIDE.md)** - **FOR DEVELOPERS** - Component development and integration guide
- **[Development Environment Setup Guide](../../PYTHON_SDK_DEV_ENVIRONMENT_SETUP_GUIDE.md)** - **FOR CONTRIBUTORS** - Complete setup guide for local development
- **[Quality Gate Rules & Development Guidelines](../../PYTHON_SDK_QUALITY_GATE_RULES_AND_DEVELOPMENT_GUIDELINE_DOCUMENT.md)** - **FOR CONTRIBUTORS** - Quality gates, coding standards, and development guidelines
- **[Quick Start Guide](../../README.md#quick-start-5-minutes)** - Get up and running in 5 minutes
- **[Installation Guide](../../README.md#installation)** - Detailed installation instructions
- **[Hello World Example](../../examples/hello_world.py)** - Simplest possible example

### Core Components

#### Data Ingestion Service
- **[Data Ingestion Overview](../../src/core/data_ingestion/README.md)** - Simple file upload interface
- **[Data Ingestion Explanation](../components/data_ingestion_explanation.md)** - Comprehensive component guide
- **[Multi-Modal Processing](../components/multimodal_data_processing.md)** - Format support details

#### Agent Framework
- **[Agent Framework Overview](../../src/core/agno_agent_framework/README.md)** - Complete agent framework guide
- **[Agent Functions](../../src/core/agno_agent_framework/functions.py)** - Factory and convenience functions
- **[Agent Explanation](../components/agno_agent_framework_explanation.md)** - Detailed component explanation
- **[Agent Troubleshooting](../troubleshooting/agent_troubleshooting.md)** - Common issues and solutions

#### Prompt-Based Generator
- **[Prompt Generator Guide](../components/prompt_based_creation_guide.md)** - How to create agents/tools from prompts
- **[Prompt Generator Explanation](../components/prompt_based_generator_explanation.md)** - Component details
- **[Prompt Generator Troubleshooting](../troubleshooting/prompt_generator_troubleshooting.md)** - Troubleshooting guide

#### LiteLLM Gateway
- **[Gateway Overview](../../src/core/litellm_gateway/README.md)** - Gateway documentation
- **[Gateway Explanation](../components/litellm_gateway_explanation.md)** - Detailed explanation
- **[Gateway Troubleshooting](../troubleshooting/litellm_gateway_troubleshooting.md)** - Common issues

#### RAG System
- **[RAG Overview](../../src/core/rag/README.md)** - RAG system documentation
- **[RAG Explanation](../components/rag_system_explanation.md)** - Component details
- **[RAG Troubleshooting](../troubleshooting/rag_system_troubleshooting.md)** - Troubleshooting

### Architecture & Design
- **[Onboarding Guide](ONBOARDING_GUIDE.md)** - Complete architecture overview and component integration
- **[SDK Architecture](../architecture/SDK_ARCHITECTURE.md)** - Overall architecture
- **[AI Architecture Design](../architecture/AI_ARCHITECTURE_DESIGN.md)** - AI-specific architecture
- **[REST/FastAPI Architecture](../architecture/REST_FASTAPI_ARCHITECTURE.md)** - API layer design
- **[FaaS Architecture](../architecture/FAAS_IMPLEMENTATION_GUIDE.md)** - FaaS services-based architecture
- **[FaaS Structure Summary](../architecture/FAAS_STRUCTURE_SUMMARY.md)** - FaaS folder structure and organization
- **[FaaS Completion Summary](../architecture/FAAS_COMPLETION_SUMMARY.md)** - FaaS implementation status
- **[FaaS Stateless Implementation](../architecture/FAAS_STATELESS_IMPLEMENTATION.md)** - Stateless architecture and HTTP client utilities

### FaaS Services
- **[FaaS Overview](../../src/faas/README.md)** - FaaS architecture and services overview
- **[FaaS Implementation Guide](../architecture/FAAS_IMPLEMENTATION_GUIDE.md)** - Complete FaaS implementation guide
- **[Agent Service](../../src/faas/services/agent_service/README.md)** - Agent Framework as a service
- **[RAG Service](../../src/faas/services/rag_service/)** - RAG System as a service
- **[Gateway Service](../../src/faas/services/gateway_service/)** - LiteLLM Gateway as a service
- **[Prompt Generator Service](../../src/faas/services/prompt_generator_service/)** - Prompt-Based Generator as a service
- **[LLMOps Service](../../src/faas/services/llmops_service/)** - LLMOps as a service
- **[FaaS Examples](../../examples/faas/)** - FaaS service usage examples
- **[FaaS Deployment](../deployment/)** - Docker, Kubernetes, AWS Lambda deployment guides

### Integration Guides
- **[Integration Guides Overview](../integration_guides/README.md)** - Integration overview
- **[NATS Integration](../integration_guides/nats_integration_guide.md)** - NATS messaging integration
- **[OTEL Integration](../integration_guides/otel_integration_guide.md)** - OpenTelemetry integration
- **[CODEC Integration](../integration_guides/codec_integration_guide.md)** - Serialization integration
- **[FaaS Integrations](../../src/faas/integrations/README.md)** - NATS, OTEL, CODEC for FaaS services

### Advanced Features
- **[Advanced Features Overview](../components/advanced_features.md)** - Vector indexes, KV cache, hallucination detection
- **[Vector Index Management](../components/advanced_features.md#vector-index-management)** - IVFFlat and HNSW index management
- **[KV Cache](../components/advanced_features.md#kv-cache-for-llm-generation)** - Attention key-value caching for LLM optimization
- **[Hallucination Detection](../components/advanced_features.md#hallucination-detection)** - Grounding verification for RAG responses

### Troubleshooting
- **[Troubleshooting Index](../troubleshooting/README.md)** - All troubleshooting guides
- **[Agent Troubleshooting](../troubleshooting/agent_troubleshooting.md)**
- **[Gateway Troubleshooting](../troubleshooting/litellm_gateway_troubleshooting.md)**
- **[RAG Troubleshooting](../troubleshooting/rag_system_troubleshooting.md)**

---

## 🔍 Quick Search by Topic

### By Functionality

#### Creating Agents
- **From scratch:** [Agent Framework README](../../src/core/agno_agent_framework/README.md#creating-agents)
- **From prompts:** [Prompt-Based Creation Guide](../components/prompt_based_creation_guide.md)
- **With memory:** [Agent with Memory](../../src/core/agno_agent_framework/functions.py#create_agent_with_memory)
- **With tools:** [Agent with Tools](../../src/core/agno_agent_framework/functions.py#create_agent_with_tools)

#### Configuration
- **Agent config:** [Agent Config Options](../../src/core/utils/config_discovery.py#get_agent_config_options)
- **Gateway config:** [Gateway Config Options](../../src/core/utils/config_discovery.py#get_gateway_config_options)
- **RAG config:** [RAG Config Options](../../src/core/utils/config_discovery.py#get_rag_config_options)
- **Config validation:** [Config Validator](../../src/core/utils/config_validator.py)

#### Error Handling
- **Error types:** [Exception Hierarchy](../../README.md#error-handling)
- **Error utilities:** [Error Handler](../../src/core/utils/error_handler.py)
- **Common errors:** [Troubleshooting Guides](../troubleshooting/README.md)

#### Integration
- **NATS:** [NATS Integration Guide](../integration_guides/nats_integration_guide.md)
- **OTEL:** [OTEL Integration Guide](../integration_guides/otel_integration_guide.md)
- **CODEC:** [CODEC Integration Guide](../integration_guides/codec_integration_guide.md)

### By Use Case

#### Customer Support
- **Agent creation:** [Agent Framework](../../src/core/agno_agent_framework/README.md)
- **RAG for knowledge base:** [RAG System](../../src/core/rag/README.md)
- **Prompt management:** [Prompt Context Management](../../src/core/prompt_context_management/README.md)

#### Document Q&A
- **RAG setup:** [RAG System](../../src/core/rag/README.md)
- **Document processing:** [RAG Document Processing](../../src/core/rag/README.md#document-processing)
- **Query examples:** [RAG Examples](../../examples/basic_usage/07_rag_basic.py)

#### Multi-Agent Systems
- **Agent orchestration:** [Agent Orchestrator](../../src/core/agno_agent_framework/orchestration.py)
- **Agent communication:** [Agent Framework](../../src/core/agno_agent_framework/README.md#agent-communication)
- **Integration patterns:** [Onboarding Guide](../ONBOARDING_GUIDE.md#integration-patterns)

### By Component Type

#### Core Components
- **Agent Framework:** [Agent Framework](../../src/core/agno_agent_framework/README.md)
- **LiteLLM Gateway:** [Gateway](../../src/core/litellm_gateway/README.md)
- **RAG System:** [RAG](../../src/core/rag/README.md)
- **Prompt Generator:** [Prompt Generator](../components/prompt_based_generator_explanation.md)

#### Infrastructure
- **Database:** [PostgreSQL Database](../../src/core/postgresql_database/README.md)
- **Cache:** [Cache Mechanism](../../src/core/cache_mechanism/README.md)
- **Observability:** [Evaluation & Observability](../../src/core/evaluation_observability/README.md)

---

## 🗂️ Documentation by Category

### 📖 Guides & Tutorials
- **[Onboarding Guide](ONBOARDING_GUIDE.md)** - **START HERE** - Complete guide for new team members
- [Prompt-Based Creation Guide](../components/prompt_based_creation_guide.md) - Create agents/tools from prompts

### 🏗️ Architecture
- [Onboarding Guide](ONBOARDING_GUIDE.md) - Architecture overview and component integration
- [Developer Integration Guide](DEVELOPER_INTEGRATION_GUIDE.md) - Component development and integration patterns
- [Development Environment Setup Guide](../../PYTHON_SDK_DEV_ENVIRONMENT_SETUP_GUIDE.md) - Local development setup
- [Quality Gate Rules & Development Guidelines](../../PYTHON_SDK_QUALITY_GATE_RULES_AND_DEVELOPMENT_GUIDELINE_DOCUMENT.md) - Quality standards and coding guidelines
- [SDK Architecture](../architecture/SDK_ARCHITECTURE.md) - Overall architecture
- [AI Architecture Design](../architecture/AI_ARCHITECTURE_DESIGN.md) - AI-specific architecture
- [REST/FastAPI Architecture](../architecture/REST_FASTAPI_ARCHITECTURE.md) - API layer design
- [FaaS Implementation Guide](../architecture/FAAS_IMPLEMENTATION_GUIDE.md) - FaaS services architecture
- [FaaS Structure Summary](../architecture/FAAS_STRUCTURE_SUMMARY.md) - FaaS organization

### 🔧 Components
- [Agent Framework](../components/agno_agent_framework_explanation.md)
- [LiteLLM Gateway](../components/litellm_gateway_explanation.md)
- [RAG System](../components/rag_system_explanation.md)
- [Prompt Generator](../components/prompt_based_generator_explanation.md)
- [All Components](../components/README.md)

### 🔌 Integration
- [Integration Guides Overview](../integration_guides/README.md)
- [NATS Integration](../integration_guides/nats_integration_guide.md)
- [OTEL Integration](../integration_guides/otel_integration_guide.md)
- [CODEC Integration](../integration_guides/codec_integration_guide.md)

### ☁️ FaaS Services
- [FaaS Overview](../../src/faas/README.md) - Services-based architecture
- [FaaS Implementation Guide](../architecture/FAAS_IMPLEMENTATION_GUIDE.md) - Complete guide
- [FaaS Examples](../../examples/faas/) - Usage examples
- [FaaS Deployment](../deployment/) - Deployment guides

### 🐛 Troubleshooting
- [Troubleshooting Index](../troubleshooting/README.md)
- [Agent Issues](../troubleshooting/agent_troubleshooting.md)
- [Gateway Issues](../troubleshooting/litellm_gateway_troubleshooting.md)
- [RAG Issues](../troubleshooting/rag_system_troubleshooting.md)

---

## 🔎 Search Tips

### Finding Code Examples
1. Check `examples/` directory
2. Look for "Example" sections in component READMEs
3. Search for function names in component files

### Finding Configuration Options
1. Use `print_config_options('component_name')` in Python
2. Check component README files
3. See [Config Discovery](../../src/core/utils/config_discovery.py)

### Finding Error Solutions
1. Check [Troubleshooting Index](../troubleshooting/README.md)
2. Search for error message in troubleshooting guides
3. Check component-specific troubleshooting files

### Finding API Reference
1. Check component `functions.py` files
2. See component README files
3. Check [Onboarding Guide](ONBOARDING_GUIDE.md) for integration patterns

---

## 📋 Quick Reference

### Common Tasks

#### Create an Agent
```python
from src.core.agno_agent_framework import create_agent
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(api_keys={"openai": "sk-..."})
agent = create_agent("agent1", "My Agent", gateway)
```
📖 [Full Guide](../../src/core/agno_agent_framework/README.md#creating-agents)

#### Create Agent from Prompt
```python
from src.core.prompt_based_generator import create_agent_from_prompt

agent = await create_agent_from_prompt(
    "Create a customer support agent",
    gateway=gateway
)
```
📖 [Full Guide](../components/prompt_based_creation_guide.md)

#### Setup RAG System
```python
from src.core.rag import create_rag_system

rag = create_rag_system(db, gateway, tenant_id="tenant_123")
```
📖 [Full Guide](../../src/core/rag/README.md)

#### Discover Configuration
```python
from src.core.utils import print_config_options

print_config_options('agent')  # See all agent config options
```
📖 [Full Guide](../../src/core/utils/config_discovery.py)

---

## 🔗 Cross-References

### Related Documentation
- **[Onboarding Guide](ONBOARDING_GUIDE.md)** - **START HERE** - Complete guide for new team members
- **[Main README](../../README.md)** - Project overview and quick start
- **[Developer Guide](../../PYTHON_SDK_DEV_ENVIRONMENT_SETUP_GUIDE.md)** - Development guidelines
- **[Professional Evaluation](../PROFESSIONAL_SDK_EVALUATION.md)** - SDK quality assessment

### External Resources
- **[Examples Directory](../../examples/)** - Code examples
- **[Tests Directory](../../src/tests/)** - Test files and benchmarks
- **[Component Source](../../src/core/)** - Source code

---

## 📝 Document Sizes & Navigation

### Large Documents (Use TOC)
- [Onboarding Guide](ONBOARDING_GUIDE.md) - Complete overview
- [Agent Framework Explanation](../components/agno_agent_framework_explanation.md) - 1540 lines
- [SDK Architecture](../architecture/SDK_ARCHITECTURE.md) - Large document
- [AI Architecture Design](../architecture/AI_ARCHITECTURE_DESIGN.md) - Large document

**Tip:** Use your editor's outline/TOC feature or search within document (Ctrl+F / Cmd+F)

### Medium Documents
- Most component READMEs
- Integration guides
- Troubleshooting guides

### Quick Reference Documents
- This index
- Quick start guides
- Function reference files

---

## 🆘 Need Help?

1. **New to the SDK?** Start with [Onboarding Guide](ONBOARDING_GUIDE.md)
2. **Quick Start:** [README Quick Start](../../README.md#quick-start-5-minutes)
3. **Examples:** [Examples Directory](../../examples/)
4. **Troubleshooting:** [Troubleshooting Index](../troubleshooting/README.md)
5. **Component Help:** Check component-specific README files

---

**Last Updated:** 2025-01-XX  
**SDK Version:** 0.1.0

## Related

- [Onboarding Guide](ONBOARDING_GUIDE.md) - Complete guide for new team members
- [Main README](../../README.md) - Project overview and quick start
- [Developer Integration Guide](DEVELOPER_INTEGRATION_GUIDE.md) - Component development and integration
- [Quick Reference](QUICK_REFERENCE.md) - Common tasks and APIs
- [Navigation Helper](NAVIGATION_HELPER.md) - Search strategies

## Feedback

If you find gaps in this index or have suggestions for improvement, raise an issue or PR with your edits.

