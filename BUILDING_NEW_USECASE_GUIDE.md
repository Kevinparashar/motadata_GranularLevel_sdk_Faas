# Building New Use Cases with the SDK - Developer Guide

## Overview

This guide explains how developers can build new use cases using the SDK, following established patterns and validation practices.

## 🎯 Process Overview

```
New Use Case Request
    ↓
1. Understand Requirements
    ↓
2. Identify SDK Components Needed
    ↓
3. Study SDK Examples & Patterns
    ↓
4. Design Implementation
    ↓
5. Implement Using SDK Components
    ↓
6. Validate Implementation
    ↓
7. Document & Review
```

---

## Step 1: Understand Requirements

### Questions to Ask

1. **What is the use case?**
   - What problem does it solve?
   - What are the inputs and outputs?
   - What are the success criteria?

2. **What AI capabilities are needed?**
   - Text generation?
   - Document retrieval (RAG)?
   - Agent-based reasoning?
   - Embeddings?
   - Multi-step workflows?

3. **What are the integration points?**
   - External APIs?
   - Databases?
   - User interfaces?
   - Other systems?

### Example: Customer Support Chatbot

**Requirements:**
- Answer customer questions using knowledge base
- Handle multi-turn conversations
- Escalate to human when needed
- Track conversation history

**AI Capabilities Needed:**
- RAG for knowledge base retrieval
- Agent for conversation management
- LLM for response generation

---

## Step 2: Identify SDK Components Needed

### Component Selection Matrix

| Use Case Need | SDK Component | Example |
|--------------|---------------|---------|
| Answer questions from documents | RAG System | `src/core/rag/` |
| Multi-turn conversations | Agent Framework | `src/core/agno_agent_framework/` |
| LLM operations | LiteLLM Gateway | `src/core/litellm_gateway/` |
| Store conversations | PostgreSQL Database | `src/core/postgresql_database/` |
| Cache responses | Cache Mechanism | `src/core/cache_mechanism/` |
| REST API | API Backend | `src/core/api_backend_services/` |
| Monitoring | Observability | `src/core/evaluation_observability/` |
| Prompt templates | Prompt Context | `src/core/prompt_context_management/` |

### Example: Customer Support Chatbot Components

**Required Components:**
1. **RAG System** - For knowledge base retrieval
2. **Agent Framework** - For conversation management
3. **LiteLLM Gateway** - For LLM operations
4. **PostgreSQL Database** - For conversation storage
5. **API Backend** - For REST endpoints
6. **Observability** - For monitoring

**Optional Components:**
- **Cache** - For response caching
- **Prompt Context Management** - For prompt templates

---

## Step 3: Study SDK Examples & Patterns

### Where to Find Examples

1. **Basic Usage Examples**: `examples/basic_usage/`
   - See how each component works individually
   - Understand component APIs and usage patterns

2. **Integration Examples**: `examples/integration/`
   - See how components work together
   - Learn integration patterns

3. **End-to-End Examples**: `examples/end_to_end/`
   - See complete workflows
   - Understand full system architecture

### Example Study Path for Customer Support Chatbot

```bash
# Step 1: Study RAG system
python examples/basic_usage/09_rag_basic.py

# Step 2: Study Agent framework
python examples/basic_usage/07_agent_basic.py

# Step 3: Study integration
python examples/integration/agent_with_rag.py

# Step 4: Study complete system
python examples/end_to_end/complete_qa_system.py
```

### Key Patterns to Learn

1. **Component Initialization Pattern**
   ```python
   # From examples/basic_usage/09_rag_basic.py
   gateway = LiteLLMGateway(api_key=api_key, provider=provider)
   db = PostgreSQLDatabase(**db_config)
   db.connect()
   rag = RAGSystem(db=db, gateway=gateway, ...)
   ```

2. **Error Handling Pattern**
   ```python
   try:
       result = rag.query(query)
   except Exception as e:
       logger.error(f"RAG query failed: {e}")
       # Handle error appropriately
   ```

3. **Observability Pattern**
   ```python
   with observability.start_trace("operation_name") as span:
       span.set_attribute("key", "value")
       # Your operation
   ```

---

## Step 4: Design Implementation

### Design Checklist

- [ ] **Component Selection**: Which SDK components to use?
- [ ] **Data Flow**: How does data flow through components?
- [ ] **Error Handling**: How to handle errors at each step?
- [ ] **Observability**: What to trace and log?
- [ ] **Testing Strategy**: How to test the implementation?

### Design Document Template

```markdown
## Use Case: [Name]

### Components Used
- Component 1: Purpose
- Component 2: Purpose

### Data Flow
1. Input → Component 1
2. Component 1 → Component 2
3. Component 2 → Output

### Error Handling
- Component 1 errors: [handling strategy]
- Component 2 errors: [handling strategy]

### Observability
- Traces: [what to trace]
- Metrics: [what to measure]
- Logs: [what to log]
```

### Example: Customer Support Chatbot Design

```markdown
## Use Case: Customer Support Chatbot

### Components Used
- RAG System: Knowledge base retrieval
- Agent Framework: Conversation management
- LiteLLM Gateway: Response generation
- PostgreSQL Database: Conversation storage
- API Backend: REST endpoints

### Data Flow
1. User Query → API Backend
2. API Backend → Agent Framework
3. Agent Framework → RAG System (if needed)
4. RAG System → LiteLLM Gateway
5. LiteLLM Gateway → Agent Framework
6. Agent Framework → API Backend
7. API Backend → User Response

### Error Handling
- RAG errors: Return cached response or default message
- Agent errors: Log and return error message
- Gateway errors: Retry with fallback model
```

---

## Step 5: Implement Using SDK Components

### Implementation Steps

#### 5.1 Create Project Structure

**Location**: `examples/use_cases/[use_case_name]/`

**Naming**: Use `snake_case` (e.g., `customer_support_chatbot`)

```bash
# Navigate to use cases directory
cd examples/use_cases

# Create use case folder
mkdir customer_support_chatbot
cd customer_support_chatbot

# Create standard structure
mkdir tests docs
touch README.md main.py config.py models.py requirements.txt .env.example
touch tests/__init__.py tests/test_main.py tests/test_integration.py
touch docs/architecture.md
```

**Or use template**:
```bash
# Copy from template
cp -r template customer_support_chatbot
cd customer_support_chatbot
# Remove .template extensions and update files
```

**Standard Structure**:
```
use_cases/
└── [use_case_name]/
    ├── README.md              # Use case documentation
    ├── main.py                # Main implementation
    ├── config.py              # Configuration
    ├── models.py              # Data models
    ├── requirements.txt       # Dependencies
    ├── .env.example           # Environment template
    ├── tests/                 # Tests
    │   ├── __init__.py
    │   ├── test_main.py
    │   └── test_integration.py
    └── docs/                  # Documentation
        └── architecture.md
```

See [examples/USE_CASES_STRUCTURE.md](../examples/USE_CASES_STRUCTURE.md) for complete structure guidelines.

#### 5.2 Initialize SDK Components

```python
# main.py
import os
from dotenv import load_dotenv
from src.core.litellm_gateway import LiteLLMGateway
from src.core.rag import RAGSystem
from src.core.postgresql_database import PostgreSQLDatabase
from src.core.agno_agent_framework import Agent, AgentManager
from src.core.evaluation_observability import ObservabilityManager

# Load configuration
load_dotenv()

# Initialize observability
observability = ObservabilityManager(
    service_name="customer-support-chatbot",
    environment="production"
)
logger = observability.get_logger("chatbot")

# Initialize gateway
gateway = LiteLLMGateway(
    api_key=os.getenv("OPENAI_API_KEY"),
    provider="openai"
)

# Initialize database
db = PostgreSQLDatabase(
    host=os.getenv("POSTGRES_HOST"),
    port=int(os.getenv("POSTGRES_PORT", 5432)),
    database=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)
db.connect()

# Initialize RAG system
rag = RAGSystem(
    db=db,
    gateway=gateway,
    embedding_model="text-embedding-3-small",
    generation_model="gpt-4"
)

# Initialize agent
agent = Agent(
    agent_id="support-agent-001",
    name="Customer Support Agent",
    description="Handles customer support queries",
    gateway=gateway,
    llm_model="gpt-4"
)
```

#### 5.3 Implement Use Case Logic

```python
# main.py (continued)

class CustomerSupportChatbot:
    """Customer support chatbot using SDK components."""
    
    def __init__(self, rag, agent, observability):
        self.rag = rag
        self.agent = agent
        self.observability = observability
        self.logger = observability.get_logger("chatbot")
    
    async def handle_query(self, user_query: str, conversation_id: str) -> dict:
        """
        Handle customer support query.
        
        Args:
            user_query: User's question
            conversation_id: Conversation identifier
        
        Returns:
            Response dictionary with answer and metadata
        """
        with self.observability.start_trace("handle_query") as span:
            span.set_attribute("conversation_id", conversation_id)
            span.set_attribute("query", user_query)
            
            try:
                # Step 1: Query RAG system for knowledge base
                self.logger.info("Querying knowledge base", extra={
                    "conversation_id": conversation_id,
                    "query": user_query
                })
                
                rag_result = self.rag.query(
                    query=user_query,
                    top_k=3,
                    threshold=0.7,
                    max_tokens=500
                )
                
                span.set_attribute("rag_documents_found", rag_result["num_documents"])
                
                # Step 2: Use agent to generate response
                self.logger.info("Generating response via agent")
                
                context = "\n".join([
                    f"- {doc.get('title', 'Unknown')}: {doc.get('content', '')[:200]}"
                    for doc in rag_result["retrieved_documents"]
                ])
                
                prompt = f"""
You are a customer support agent. Answer the customer's question using the provided context.

Context from knowledge base:
{context}

Customer Question: {user_query}

Provide a helpful, accurate answer:
                """.strip()
                
                # Use agent to generate response
                task_id = self.agent.add_task(
                    task_type="generate_response",
                    parameters={
                        "prompt": prompt,
                        "model": "gpt-4",
                        "max_tokens": 500
                    },
                    priority=1
                )
                
                task = self.agent.task_queue[-1]
                result = await self.agent.execute_task(task)
                
                response_text = result.get("result", "I apologize, I couldn't generate a response.")
                
                # Step 3: Return response
                response = {
                    "answer": response_text,
                    "sources": [doc.get("title") for doc in rag_result["retrieved_documents"]],
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat()
                }
                
                span.set_attribute("response_generated", True)
                self.logger.info("Response generated successfully", extra={
                    "conversation_id": conversation_id
                })
                
                return response
                
            except Exception as e:
                span.set_attribute("error", str(e))
                self.logger.error("Error handling query", extra={
                    "conversation_id": conversation_id,
                    "error": str(e)
                })
                self.observability.capture_exception(e)
                
                # Return error response
                return {
                    "answer": "I apologize, I encountered an error. Please try again or contact support.",
                    "error": str(e),
                    "conversation_id": conversation_id
                }
```

#### 5.4 Create API Endpoint (if needed)

```python
# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main import CustomerSupportChatbot

app = FastAPI(title="Customer Support Chatbot API")

# Initialize chatbot
chatbot = CustomerSupportChatbot(rag, agent, observability)

class QueryRequest(BaseModel):
    query: str
    conversation_id: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    conversation_id: str

@app.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest):
    """Handle customer support query."""
    try:
        result = await chatbot.handle_query(
            user_query=request.query,
            conversation_id=request.conversation_id
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Step 6: Validate Implementation

### 6.1 Unit Testing

Create unit tests following SDK patterns:

```python
# tests/test_main.py
import pytest
from unittest.mock import Mock, MagicMock, patch
from main import CustomerSupportChatbot

class TestCustomerSupportChatbot:
    """Unit tests for CustomerSupportChatbot."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components."""
        mock_rag = MagicMock()
        mock_agent = MagicMock()
        mock_observability = MagicMock()
        
        chatbot = CustomerSupportChatbot(
            rag=mock_rag,
            agent=mock_agent,
            observability=mock_observability
        )
        
        return chatbot, mock_rag, mock_agent, mock_observability
    
    @pytest.mark.asyncio
    async def test_handle_query_success(self, mock_components):
        """Test successful query handling."""
        chatbot, mock_rag, mock_agent, mock_observability = mock_components
        
        # Mock RAG result
        mock_rag.query.return_value = {
            "answer": "Test answer",
            "retrieved_documents": [
                {"title": "Doc1", "content": "Content1"}
            ],
            "num_documents": 1
        }
        
        # Mock agent result
        mock_agent.execute_task.return_value = {
            "result": "Generated response"
        }
        
        # Execute
        result = await chatbot.handle_query(
            user_query="Test question",
            conversation_id="conv-001"
        )
        
        # Assertions
        assert "answer" in result
        assert result["conversation_id"] == "conv-001"
        mock_rag.query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_query_error(self, mock_components):
        """Test error handling."""
        chatbot, mock_rag, mock_agent, mock_observability = mock_components
        
        # Mock error
        mock_rag.query.side_effect = Exception("RAG error")
        
        # Execute
        result = await chatbot.handle_query(
            user_query="Test question",
            conversation_id="conv-001"
        )
        
        # Assertions
        assert "error" in result
        assert "I apologize" in result["answer"]
```

### 6.2 Integration Testing

Test component interactions:

```python
# tests/test_integration.py
import pytest
from main import CustomerSupportChatbot

@pytest.mark.integration
class TestChatbotIntegration:
    """Integration tests for CustomerSupportChatbot."""
    
    @pytest.mark.asyncio
    async def test_rag_agent_integration(self):
        """Test RAG and Agent integration."""
        # Use real components (with test database)
        # Test end-to-end flow
        pass
```

### 6.3 Validation Checklist

Use this checklist to validate your implementation:

#### Code Quality
- [ ] **Follows SDK Patterns**: Uses SDK components correctly
- [ ] **Type Hints**: All functions have type hints
- [ ] **Error Handling**: Comprehensive error handling
- [ ] **Logging**: Proper logging at key points
- [ ] **Observability**: Traces and metrics implemented

#### Functionality
- [ ] **Requirements Met**: All requirements implemented
- [ ] **Component Integration**: Components work together
- [ ] **Edge Cases**: Edge cases handled
- [ ] **Error Scenarios**: Error scenarios tested

#### Testing
- [ ] **Unit Tests**: Unit tests for all functions (>80% coverage)
- [ ] **Integration Tests**: Integration tests for workflows
- [ ] **Test Documentation**: Tests are documented
- [ ] **Test Data**: Test data and fixtures created

#### Documentation
- [ ] **README**: README with usage instructions
- [ ] **Code Comments**: Code is well-commented
- [ ] **API Documentation**: API endpoints documented
- [ ] **Examples**: Usage examples provided

### 6.4 Validation Process

#### Step 1: Self-Validation
```bash
# Run tests
pytest tests/ -v

# Check code quality
black --check .
mypy .

# Run linter
ruff check .
```

#### Step 2: Component Validation
```bash
# Test each SDK component integration
pytest tests/test_main.py::TestCustomerSupportChatbot::test_handle_query_success -v
```

#### Step 3: Integration Validation
```bash
# Test complete workflow
pytest tests/test_integration.py -v -m integration
```

#### Step 4: End-to-End Validation
```bash
# Test complete system
python -m pytest tests/ --cov=. --cov-report=html
```

### 6.5 Validation Examples

#### Example 1: Validate RAG Integration

```python
def test_rag_integration():
    """Validate RAG system integration."""
    # 1. Ingest test document
    doc_id = rag.ingest_document(
        title="Test Document",
        content="Test content for validation"
    )
    assert doc_id is not None
    
    # 2. Query RAG system
    result = rag.query("Test query", top_k=1)
    assert "answer" in result
    assert result["num_documents"] > 0
    
    # 3. Verify response quality
    assert len(result["answer"]) > 0
```

#### Example 2: Validate Agent Integration

```python
async def test_agent_integration():
    """Validate agent framework integration."""
    # 1. Create agent
    agent = Agent(agent_id="test-agent", name="Test Agent", gateway=gateway)
    assert agent.agent_id == "test-agent"
    
    # 2. Add task
    task_id = agent.add_task(
        task_type="test_task",
        parameters={"key": "value"}
    )
    assert task_id is not None
    
    # 3. Execute task
    task = agent.task_queue[0]
    result = await agent.execute_task(task)
    assert result is not None
```

---

## Step 7: Document & Review

### 7.1 Create Documentation

```markdown
# Customer Support Chatbot

## Overview
Customer support chatbot using SDK components.

## Components Used
- RAG System: Knowledge base retrieval
- Agent Framework: Conversation management
- LiteLLM Gateway: Response generation

## Usage
```python
from main import CustomerSupportChatbot

chatbot = CustomerSupportChatbot(rag, agent, observability)
result = await chatbot.handle_query("How do I reset my password?", "conv-001")
```

## Testing
```bash
pytest tests/ -v
```

## Examples
See `examples/` directory for usage examples.
```

### 7.2 Code Review Checklist

- [ ] **SDK Patterns**: Follows SDK patterns
- [ ] **Code Quality**: Meets quality standards
- [ ] **Tests**: Comprehensive test coverage
- [ ] **Documentation**: Complete documentation
- [ ] **Performance**: Performance considerations
- [ ] **Security**: Security best practices

---

## 📋 Quick Reference

### SDK Component Import Patterns

```python
# Gateway
from src.core.litellm_gateway import LiteLLMGateway

# RAG
from src.core.rag import RAGSystem

# Agent
from src.core.agno_agent_framework import Agent, AgentManager

# Database
from src.core.postgresql_database import PostgreSQLDatabase

# Observability
from src.core.evaluation_observability import ObservabilityManager

# Cache
from src.core.cache_mechanism import CacheManager, CacheBackend
```

### Common Patterns

```python
# Initialization Pattern
component = Component(config=config, dependencies=deps)

# Error Handling Pattern
try:
    result = component.operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    # Handle error

# Observability Pattern
with observability.start_trace("operation") as span:
    span.set_attribute("key", "value")
    # Operation
```

### Testing Patterns

```python
# Mock Pattern
@patch('module.component')
def test_function(mock_component):
    mock_component.return_value = expected_value
    result = function_under_test()
    assert result == expected_value

# Integration Test Pattern
@pytest.mark.integration
def test_integration():
    # Use real components
    result = real_component.operation()
    assert result is not None
```

---

## 🎯 Summary

### Building New Use Case: 7 Steps

1. **Understand Requirements** - What needs to be built?
2. **Identify Components** - Which SDK components to use?
3. **Study Examples** - Learn from SDK examples
4. **Design Implementation** - Plan the implementation
5. **Implement** - Build using SDK components
6. **Validate** - Test and validate implementation
7. **Document** - Document and review

### Validation: 4 Levels

1. **Self-Validation** - Run tests and checks
2. **Component Validation** - Test component integration
3. **Integration Validation** - Test workflows
4. **End-to-End Validation** - Test complete system

### Key Success Factors

- ✅ **Follow SDK Patterns** - Use established patterns
- ✅ **Comprehensive Testing** - Test all scenarios
- ✅ **Proper Documentation** - Document everything
- ✅ **Code Quality** - Maintain high quality standards
- ✅ **Observability** - Add tracing and logging

---

## 📚 Additional Resources

- **Examples**: `examples/README.md`
- **Use Cases Structure**: `examples/USE_CASES_STRUCTURE.md`
- **Use Cases Index**: `examples/use_cases/README.md`
- **Use Cases Template**: `examples/use_cases/template/`
- **Tests**: `src/tests/unit_tests/README.md`
- **Component Docs**: Individual component READMEs
- **Developer Guide**: `README_DEVELOPER.md`
- **Workflows**: `src/workflows.md`

---

**Remember**: The SDK provides the foundation - you build the use case on top of it, following established patterns and validation practices.

