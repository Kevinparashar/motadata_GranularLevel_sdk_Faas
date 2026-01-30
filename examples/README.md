# MOTADATA - SDK EXAMPLES

**Working code examples for all SDK components, organized by component and complexity level.**

This directory contains working code examples for all SDK components, organized by component and complexity level.

## Structure

```
examples/
├── hello_world.py           # Quick Start example (start here!)
├── basic_usage/              # Simple, single-component examples
├── integration/              # Multi-component integration examples
├── faas/                    # FaaS service examples (NEW!)
│   ├── README.md           # FaaS examples guide
│   ├── agent_service_example.py
│   ├── rag_service_example.py
│   ├── gateway_service_example.py
│   └── complete_workflow_example.py
├── end_to_end/              # Complete end-to-end workflows
└── use_cases/               # Real-world use case implementations
    ├── README.md            # Use cases index
    ├── template/            # Template for new use cases
    └── [use_case_name]/     # Individual use cases
```

See [USE_CASES_STRUCTURE.md](USE_CASES_STRUCTURE.md) for detailed use case structure and management guidelines.

## Quick Start Example

**New to the SDK?** Start here:

```bash
# Run the Hello World example (5 minutes)
python examples/hello_world.py
```

This simple example demonstrates:
- Creating a gateway connection
- Making your first AI call
- Getting a response

See the [root README.md](../../README.md#-quick-start-5-minutes) for full Quick Start instructions.

---

## Running Examples

### Prerequisites

1. **Set up environment:**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   Create a `.env` file in the project root with:
   ```bash
   OPENAI_API_KEY=your-key-here
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=motadata_sdk
   POSTGRES_USER=your-user
   POSTGRES_PASSWORD=your-password
   ```

3. **Set up PostgreSQL with pgvector:**
   ```bash
   psql -U your-user -d motadata_sdk -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

### Running an Example

```bash
# From project root
python examples/basic_usage/observability_basic.py
```

## Component Order

Examples are organized following the component dependency order:

1. **Foundation Layer** (No dependencies)
   - Evaluation & Observability

2. **Infrastructure Layer**
   - PostgreSQL Database
   - LiteLLM Gateway

3. **Core Layer**
   - Cache
   - Agent
   - Prompt Context Management
   - RAG

4. **Application Layer**
   - API Backend

## Example Categories

### Basic Usage
Simple examples showing how to use each component independently.

### FaaS Services
Examples demonstrating how to use AI components as REST API services:
- `agent_service_example.py` - Using Agent Service via HTTP API
- `rag_service_example.py` - Using RAG Service via HTTP API
- `gateway_service_example.py` - Using Gateway Service via HTTP API
- `complete_workflow_example.py` - Complete workflow using multiple FaaS services

See [faas/README.md](faas/README.md) for detailed FaaS examples documentation.

### Integration
Examples showing how multiple components work together:
- `agent_with_rag.py` - Agent using RAG for context
- `api_with_agent.py` - API exposing agent functionality
- `multi_agent_orchestration.py` - Multi-agent workflows, coordination patterns, task delegation

### End-to-End
Complete workflows from start to finish, demonstrating real-world use cases.

### Use Cases
Real-world use case implementations built using the SDK. Each use case is a complete, self-contained implementation with:
- Full implementation code
- Comprehensive tests
- Complete documentation
- Configuration management

See [use_cases/README.md](use_cases/README.md) for the use cases index.

## Learning Path

1. **Start here**: Run `hello_world.py` to verify your setup and make your first AI call
2. Start with **basic_usage** examples to understand each component
3. Study **integration** examples to see component interactions
4. **For microservices**: Explore **faas/** examples to see how to use components as services
5. Review **end_to_end** examples for complete system understanding
6. Explore **use_cases** to see real-world implementations
7. Use **use_cases/template** to build your own use cases

## Creating New Use Cases

When a new use case is needed:

1. **Create Folder**: Use `snake_case` naming (e.g., `customer_support_chatbot`)
2. **Copy Template**: Copy files from `use_cases/template/`
3. **Implement**: Follow SDK patterns (see [BUILDING_NEW_USECASE_GUIDE.md](../BUILDING_NEW_USECASE_GUIDE.md))
4. **Test**: Add comprehensive tests
5. **Document**: Complete README.md
6. **Register**: Add entry to `use_cases/README.md`

See [USE_CASES_STRUCTURE.md](USE_CASES_STRUCTURE.md) for detailed guidelines on:
- Folder structure
- Naming conventions
- File organization
- Management practices

