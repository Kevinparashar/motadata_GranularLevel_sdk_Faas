# SDK Examples

This directory contains working code examples for all SDK components, organized by component and complexity level.

## Structure

```
examples/
├── basic_usage/              # Simple, single-component examples
├── integration/              # Multi-component integration examples
├── end_to_end/              # Complete end-to-end workflows
└── use_cases/               # Real-world use case implementations
    ├── README.md            # Use cases index
    ├── template/            # Template for new use cases
    └── [use_case_name]/     # Individual use cases
```

See [USE_CASES_STRUCTURE.md](USE_CASES_STRUCTURE.md) for detailed use case structure and management guidelines.

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
   - Pool Implementation

2. **Infrastructure Layer**
   - PostgreSQL Database
   - Connectivity
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

### Integration
Examples showing how multiple components work together.

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

1. Start with **basic_usage** examples to understand each component
2. Study **integration** examples to see component interactions
3. Review **end_to_end** examples for complete system understanding
4. Explore **use_cases** to see real-world implementations
5. Use **use_cases/template** to build your own use cases

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

