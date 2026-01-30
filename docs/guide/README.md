# MOTADATA - SDK DOCUMENTATION

**Documentation hub for the Motadata Python AI SDK with navigation and quick access to all guides.**

---

---

## 🚀 Quick Start

- **[Onboarding Guide](ONBOARDING_GUIDE.md)** - **START HERE** - Complete guide for new team members
- **[Documentation Index](guide/DOCUMENTATION_INDEX.md)** - Complete navigation guide
- **[Quick Reference](guide/QUICK_REFERENCE.md)** - Common tasks and APIs
- **[Navigation Helper](guide/NAVIGATION_HELPER.md)** - Find information fast
- **[Main README](../README.md)** - Project overview and installation

---

## 📚 Documentation Structure

### Getting Started
- **[Onboarding Guide](ONBOARDING_GUIDE.md)** - **START HERE** - Complete guide for understanding the SDK
- **[Quick Start Guide](../README.md#quick-start-5-minutes)** - Get up and running in 5 minutes
- **[Installation Guide](../README.md#installation)** - Detailed installation
- **[Hello World Example](../examples/hello_world.py)** - Simplest example

### Core Documentation

#### 📖 Guides
- **[Onboarding Guide](ONBOARDING_GUIDE.md)** - Complete guide for new team members
- **[Developer Integration Guide](DEVELOPER_INTEGRATION_GUIDE.md)** - **FOR DEVELOPERS** - Component development and integration patterns
- **[Prompt-Based Creation Guide](prompt_based_creation_guide.md)** - Create agents/tools from prompts

#### 🏗️ Architecture
- **[SDK Architecture](architecture/SDK_ARCHITECTURE.md)** - Overall architecture
- **[AI Architecture Design](architecture/AI_ARCHITECTURE_DESIGN.md)** - AI-specific design
- **[REST/FastAPI Architecture](architecture/REST_FASTAPI_ARCHITECTURE.md)** - API layer design
- **[FaaS Architecture](architecture/FAAS_IMPLEMENTATION_GUIDE.md)** - FaaS services-based architecture

#### 🔧 Components
- **[All Components](components/README.md)** - Component overview
- **[Agent Framework](components/agno_agent_framework_explanation.md)** - Agent system
- **[LiteLLM Gateway](components/litellm_gateway_explanation.md)** - LLM gateway
- **[RAG System](components/rag_system_explanation.md)** - RAG system
- **[Prompt Generator](components/prompt_based_generator_explanation.md)** - Prompt-based generation

#### 🔌 Integration
- **[Integration Guides](integration_guides/README.md)** - Integration overview
- **[NATS Integration](integration_guides/nats_integration_guide.md)** - Messaging integration
- **[OTEL Integration](integration_guides/otel_integration_guide.md)** - Observability integration
- **[CODEC Integration](integration_guides/codec_integration_guide.md)** - Serialization integration
- **[FaaS Integrations](../src/faas/integrations/README.md)** - NATS, OTEL, CODEC for FaaS services

#### ☁️ FaaS Services
- **[FaaS Overview](../src/faas/README.md)** - FaaS architecture and services
- **[FaaS Implementation Guide](architecture/FAAS_IMPLEMENTATION_GUIDE.md)** - Complete implementation guide
- **[FaaS Examples](../../examples/faas/)** - FaaS service usage examples
- **[FaaS Deployment](../deployment/)** - Docker, Kubernetes, AWS Lambda guides

#### 🐛 Troubleshooting
- **[Troubleshooting Index](troubleshooting/README.md)** - All troubleshooting guides
- **[Agent Troubleshooting](troubleshooting/agent_troubleshooting.md)**
- **[Gateway Troubleshooting](troubleshooting/litellm_gateway_troubleshooting.md)**
- **[RAG Troubleshooting](troubleshooting/rag_system_troubleshooting.md)**

---

## 🔍 Finding Information

### By Topic
Use the **[Documentation Index](guide/DOCUMENTATION_INDEX.md)** to find documentation by:
- Functionality (creating agents, configuration, error handling)
- Use case (customer support, document Q&A, multi-agent systems)
- Component type (core, infrastructure)

### By Task
Use the **[Quick Reference](guide/QUICK_REFERENCE.md)** for:
- Common code snippets
- Configuration examples
- Error handling patterns
- API quick lookup

### By Navigation
Use the **[Navigation Helper](guide/NAVIGATION_HELPER.md)** for:
- Document maps and sizes
- Search strategies
- Cross-reference maps
- Common navigation paths

---

## 📋 Quick Links

### Most Used
- **[Documentation Index](guide/DOCUMENTATION_INDEX.md)** - Complete navigation
- **[Quick Reference](guide/QUICK_REFERENCE.md)** - Common tasks
- **[Navigation Helper](guide/NAVIGATION_HELPER.md)** - Find information fast
- **[Troubleshooting Index](troubleshooting/README.md)** - Fix issues
- **[Main README](../README.md)** - Project overview

### Component Documentation
- [Agent Framework](../src/core/agno_agent_framework/README.md)
- [Gateway](../src/core/litellm_gateway/README.md)
- [RAG System](../src/core/rag/README.md)
- [Prompt Generator](../src/core/prompt_based_generator/README.md)

### Examples
- [Examples Directory](../examples/)
- [Basic Usage Examples](../examples/basic_usage/)
- [FaaS Examples](../examples/faas/) - FaaS service examples
- [Integration Examples](../examples/integration/)
- [Use Cases](../examples/use_cases/)

---

## 🎯 Common Tasks

### Create an Agent
```python
from src.core.agno_agent_framework import create_agent
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(api_keys={"openai": "sk-..."})
agent = create_agent("agent1", "My Agent", gateway)
```
📖 [Full Guide](../src/core/agno_agent_framework/README.md)

### Discover Configuration
```python
from src.core.utils import print_config_options

print_config_options('agent')  # See all options
```
📖 [Full Guide](../src/core/utils/config_discovery.py)

### Handle Errors
```python
from src.core.agno_agent_framework.exceptions import AgentExecutionError

try:
    result = await agent.execute_task(task)
except AgentExecutionError as e:
    print(f"Error: {e.message}")
    print(f"Suggestion: {e.suggestion}")
```
📖 [Full Guide](../README.md#error-handling)

---

## 📖 Documentation Features

### ✅ Search & Navigation
- **Documentation Index** - Complete topic-based index
- **Quick Reference** - Fast lookup for common tasks
- **Navigation Helper** - Search strategies and document maps
- **Cross-references** - Links between related documents

### ✅ Organization
- **By component** - Component-specific documentation
- **By topic** - Topic-based organization
- **By use case** - Use case examples
- **By task** - Task-based guides

### ✅ Accessibility
- **Table of contents** - In large documents
- **Quick links** - Fast access to common docs
- **Code examples** - In every guide
- **Cross-references** - Links to related content

---

## 🆘 Need Help?

1. **New to the SDK?** Start with [Onboarding Guide](ONBOARDING_GUIDE.md)
2. **Quick Start:** [README Quick Start](../README.md#quick-start-5-minutes)
3. **Examples:** [Examples Directory](../examples/)
4. **Troubleshooting:** [Troubleshooting Index](troubleshooting/README.md)
5. **Search:** [Documentation Index](guide/DOCUMENTATION_INDEX.md)

---

**Last Updated:** 2025-01-XX  
**SDK Version:** 0.1.0
