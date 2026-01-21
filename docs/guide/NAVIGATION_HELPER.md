# Documentation Navigation Helper

**Quick navigation aids for finding information fast**

---

## 🗺️ Document Map

### By Document Size

#### 📘 Large Documents (>500 lines)
Use these navigation aids:
- **[Component Categorization](architecture/COMPONENT_CATEGORIZATION.md)** - Use outline/TOC in your editor
- **[Agent Framework Explanation](components/agno_agent_framework_explanation.md)** - Use outline/TOC
- **[SDK Architecture](architecture/SDK_ARCHITECTURE.md)** - Use outline/TOC
- **[AI Architecture Design](architecture/AI_ARCHITECTURE_DESIGN.md)** - Use outline/TOC

**Tip:** Most editors support outline view (VS Code: `Ctrl+Shift+O`, PyCharm: `Alt+7`)

#### 📗 Medium Documents (100-500 lines)
- Component READMEs
- Integration guides
- Architecture documents

#### 📕 Quick Reference (<100 lines)
- [Quick Reference Guide](QUICK_REFERENCE.md)
- [Documentation Index](DOCUMENTATION_INDEX.md)
- Getting started guides

---

## 🔍 Search Strategies

### 1. By Function Name
If you know the function name:
1. Search in component's `functions.py` file
2. Check component README for examples
3. See [Function-Driven API](architecture/FUNCTION_DRIVEN_API.md)

### 2. By Error Message
If you have an error:
1. Check [Troubleshooting Index](troubleshooting/README.md)
2. Search error message in troubleshooting guides
3. Check component-specific troubleshooting file

### 3. By Use Case
If you know what you want to do:
1. Check [Documentation Index](DOCUMENTATION_INDEX.md) - "By Use Case" section
2. Look in [Examples](../examples/) directory
3. Check component README files

### 4. By Component
If you know the component:
1. Go to component's README in `src/core/component_name/README.md`
2. Check component explanation in `docs/components/`
3. Check component troubleshooting in `docs/troubleshooting/`

---

## 📑 Table of Contents Quick Access

### Large Documents TOC

#### Component Categorization
See [Component Categorization](../architecture/COMPONENT_CATEGORIZATION.md) - Use outline/TOC in your editor

#### Agent Framework Explanation
See [Agent Framework Explanation](../components/agno_agent_framework_explanation.md) - Use outline/TOC in your editor

**Tip:** Use your editor's "Go to Symbol" feature (VS Code: `Ctrl+Shift+O`) to jump to sections

---

## 🔗 Cross-Reference Map

### Component → Documentation

| Component | README | Explanation | Troubleshooting | Examples |
|-----------|--------|-------------|-----------------|----------|
| Agent Framework | [README](../../src/core/agno_agent_framework/README.md) | [Explanation](../components/agno_agent_framework_explanation.md) | [Troubleshooting](../troubleshooting/agent_troubleshooting.md) | [Examples](../../examples/basic_usage/05_agent_basic.py) |
| Gateway | [README](../../src/core/litellm_gateway/README.md) | [Explanation](../components/litellm_gateway_explanation.md) | [Troubleshooting](../troubleshooting/litellm_gateway_troubleshooting.md) | [Examples](../../examples/basic_usage/03_litellm_gateway_basic.py) |
| RAG | [README](../../src/core/rag/README.md) | [Explanation](../components/rag_system_explanation.md) | [Troubleshooting](../troubleshooting/rag_system_troubleshooting.md) | [Examples](../../examples/basic_usage/07_rag_basic.py) |
| Prompt Generator | [README](../../src/core/prompt_based_generator/README.md) | [Explanation](../components/prompt_based_generator_explanation.md) | [Troubleshooting](../troubleshooting/prompt_generator_troubleshooting.md) | [Examples](../../examples/prompt_based/) |

---

## 🎯 Common Navigation Paths

### "I want to create an agent"
1. [Quick Start](../../README.md#quick-start-5-minutes)
2. [Agent Framework README](../../src/core/agno_agent_framework/README.md#creating-agents)
3. [Agent Examples](../../examples/basic_usage/05_agent_basic.py)

### "I want to configure something"
1. [Quick Reference - Configuration](QUICK_REFERENCE.md#configuration)
2. [Config Discovery](../../src/core/utils/config_discovery.py)
3. Component-specific README

### "I'm getting an error"
1. [Troubleshooting Index](../troubleshooting/README.md)
2. Component-specific troubleshooting
3. [Error Handling Guide](../../README.md#error-handling)

### "I want to integrate X"
1. [Integration Guides](../integration_guides/README.md)
2. [Core Components Integration](../components/CORE_COMPONENTS_INTEGRATION_STORY.md)
3. Component-specific integration docs

### "I want to understand architecture"
1. [SDK Architecture](../architecture/SDK_ARCHITECTURE.md)
2. [AI Architecture Design](../architecture/AI_ARCHITECTURE_DESIGN.md)
3. [FaaS Architecture](../architecture/FAAS_IMPLEMENTATION_GUIDE.md)
4. [Component Dependencies](../architecture/COMPONENT_DEPENDENCIES.md)

### "I want to deploy as services"
1. [FaaS Overview](../../src/faas/README.md)
2. [FaaS Implementation Guide](../architecture/FAAS_IMPLEMENTATION_GUIDE.md)
3. [Docker Deployment](../deployment/DOCKER_DEPLOYMENT.md)
4. [Kubernetes Deployment](../deployment/KUBERNETES_DEPLOYMENT.md)
5. [AWS Lambda Deployment](../deployment/AWS_LAMBDA_DEPLOYMENT.md)

---

## 🔎 Search Within Documents

### Using Your Editor

#### VS Code
- **Search in file:** `Ctrl+F`
- **Search in folder:** `Ctrl+Shift+F`
- **Go to symbol:** `Ctrl+Shift+O` (for headings/functions)
- **Outline view:** `Ctrl+Shift+O` then click outline icon

#### PyCharm
- **Search in file:** `Ctrl+F`
- **Search everywhere:** `Double Shift`
- **Go to symbol:** `Ctrl+Alt+Shift+N`
- **Structure view:** `Alt+7`

#### Vim/Neovim
- **Search:** `/pattern`
- **Next:** `n`
- **Previous:** `N`
- **Outline:** Use LSP or plugins

### Using Command Line

```bash
# Search for text in all docs
grep -r "search term" docs/

# Search in specific file
grep "search term" docs/README.md

# Search with context
grep -A 5 -B 5 "search term" docs/README.md
```

---

## 📋 Document Index by Topic

### Configuration
- [Config Discovery](../../src/core/utils/config_discovery.py)
- [Config Validator](../../src/core/utils/config_validator.py)
- [Config Builders](../../src/core/utils/config_builders.py)
- [Quick Reference - Configuration](QUICK_REFERENCE.md#configuration)

### Error Handling
- [Error Handler](../../src/core/utils/error_handler.py)
- [Exception Hierarchy](../../README.md#error-handling)
- [Troubleshooting Guides](../troubleshooting/README.md)

### Type Safety
- [Type Helpers](../../src/core/utils/type_helpers.py)
- [Mypy Configuration](../../pyproject.toml#toolmypy)

### Integration
- [NATS Integration](../integration_guides/nats_integration_guide.md)
- [OTEL Integration](../integration_guides/otel_integration_guide.md)
- [CODEC Integration](../integration_guides/codec_integration_guide.md)

---

## 🚀 Quick Access Links

### Most Common Documents
1. **[Documentation Index](DOCUMENTATION_INDEX.md)** - Start here
2. **[Quick Reference](QUICK_REFERENCE.md)** - Common tasks
3. **[Main README](../README.md)** - Project overview
4. **[Troubleshooting Index](troubleshooting/README.md)** - Fix issues

### Component Documentation
- [Agent Framework](../../src/core/agno_agent_framework/README.md)
- [Gateway](../../src/core/litellm_gateway/README.md)
- [RAG System](../../src/core/rag/README.md)
- [Prompt Generator](../../src/core/prompt_based_generator/README.md)

---

## 💡 Pro Tips

1. **Bookmark this page** - Quick access to navigation
2. **Use editor outline** - Jump to sections quickly
3. **Search before asking** - Most answers are in docs
4. **Check examples** - Code examples in `examples/` directory
5. **Use cross-references** - Documents link to related content

---

**Last Updated:** 2025-01-XX

