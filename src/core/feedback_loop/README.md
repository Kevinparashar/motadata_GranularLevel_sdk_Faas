# MOTADATA - FEEDBACK LOOP SYSTEM

**Continuous learning and improvement system for AI applications through user feedback collection and processing.**

## When to Use This Component

**✅ Use Feedback Loop when:**
- You want to improve AI responses based on user feedback
- You need to track user corrections and ratings
- You want to learn from user interactions
- You're building production AI applications
- You need to monitor AI quality and user satisfaction
- You want to implement continuous improvement mechanisms

**❌ Don't use Feedback Loop when:**
- You're just prototyping or testing
- You don't have user feedback mechanisms
- You're building one-off scripts
- Feedback collection would be too complex for your use case

**Simple Example:**
```python
from src.core.feedback_loop import FeedbackLoop, FeedbackType

feedback_loop = FeedbackLoop(storage_path="feedback.json")
await feedback_loop.initialize()

# Record feedback
feedback_id = await feedback_loop.record_feedback(
    query="What is AI?",
    response="AI is artificial intelligence...",
    feedback_type=FeedbackType.CORRECTION,
    content="Actually, AI is the simulation of human intelligence...",
    tenant_id="tenant_123"
)
```

**Impact:** Feedback loops can improve AI response quality by 20-40% over time through continuous learning.

---

## Overview

The Feedback Loop System provides mechanisms for collecting, processing, and learning from user feedback in AI applications. It supports multiple feedback types (corrections, ratings, usefulness, improvements, errors) and enables continuous improvement of AI systems.

## Purpose and Functionality

The Feedback Loop System enables:

- **Feedback Collection**: Collect user feedback on AI responses
- **Feedback Processing**: Process feedback with customizable callbacks
- **Learning Insights**: Extract insights from feedback for improvement
- **Persistent Storage**: Store feedback for analysis and learning
- **Multi-Tenant Support**: Tenant-isolated feedback collection
- **Agent/Tool Feedback**: Support for agent and tool-specific feedback

## Connection to Other Components

### Integration with LiteLLM Gateway

The **LiteLLM Gateway** (`src/core/litellm_gateway/`) integrates with the Feedback Loop System to collect feedback on LLM responses. The gateway can record feedback automatically when users provide corrections or ratings.

**Integration Point:** `gateway.feedback_loop`

### Integration with Agno Agent Framework

The **Agno Agent Framework** (`src/core/agno_agent_framework/`) can use the Feedback Loop System to collect feedback on agent responses and task execution. This enables agents to learn from user interactions.

### Integration with RAG System

The **RAG System** (`src/core/rag/`) can collect feedback on retrieved documents and generated responses, enabling continuous improvement of retrieval and generation quality.

## Feedback Types

The system supports five types of feedback:

### 1. Correction (`FeedbackType.CORRECTION`)

User provides corrected information:

```python
await feedback_loop.record_feedback(
    query="What is the capital of France?",
    response="The capital is Paris.",
    feedback_type=FeedbackType.CORRECTION,
    content="Actually, the capital is Paris, France.",
    tenant_id="tenant_123"
)
```

### 2. Rating (`FeedbackType.RATING`)

User rates the response (e.g., 1-5 stars):

```python
await feedback_loop.record_feedback(
    query="Explain quantum computing",
    response="Quantum computing is...",
    feedback_type=FeedbackType.RATING,
    content="5",  # Rating value
    tenant_id="tenant_123"
)
```

### 3. Useful (`FeedbackType.USEFUL`)

User marks response as useful or not useful:

```python
await feedback_loop.record_feedback(
    query="How do I reset my password?",
    response="You can reset...",
    feedback_type=FeedbackType.USEFUL,
    content="true",  # or "false"
    tenant_id="tenant_123"
)
```

### 4. Improvement (`FeedbackType.IMPROVEMENT`)

User suggests improvements:

```python
await feedback_loop.record_feedback(
    query="Analyze this data",
    response="The data shows...",
    feedback_type=FeedbackType.IMPROVEMENT,
    content="Could you provide more visualizations?",
    tenant_id="tenant_123"
)
```

### 5. Error (`FeedbackType.ERROR`)

User reports an error:

```python
await feedback_loop.record_feedback(
    query="Process this file",
    response="Processing...",
    feedback_type=FeedbackType.ERROR,
    content="The system crashed when processing large files",
    tenant_id="tenant_123"
)
```

## Key Components

### FeedbackLoop

Main feedback loop system:

```python
from src.core.feedback_loop import FeedbackLoop, FeedbackType, FeedbackItem

# Create feedback loop
feedback_loop = FeedbackLoop(
    storage_path="feedback.json",
    auto_process=True  # Automatically process feedback
)

# Initialize (loads persisted feedback)
await feedback_loop.initialize()

# Record feedback
feedback_id = await feedback_loop.record_feedback(
    query="What is AI?",
    response="AI is...",
    feedback_type=FeedbackType.CORRECTION,
    content="Corrected information",
    tenant_id="tenant_123",
    agent_id="agent_001"
)

# Process feedback manually
await feedback_loop.process_feedback(feedback_id)
```

### FeedbackItem

Individual feedback item:

```python
from src.core.feedback_loop import FeedbackItem, FeedbackType, FeedbackStatus

feedback = FeedbackItem(
    feedback_id="feedback_123",
    query="What is AI?",
    response="AI is...",
    feedback_type=FeedbackType.CORRECTION,
    content="Corrected information",
    tenant_id="tenant_123",
    agent_id="agent_001",
    status=FeedbackStatus.PENDING
)
```

## Function-Driven API

### Recording Feedback

```python
from src.core.feedback_loop import FeedbackLoop, FeedbackType

feedback_loop = FeedbackLoop()
await feedback_loop.initialize()

# Record different types of feedback
feedback_id = await feedback_loop.record_feedback(
    query="User query",
    response="AI response",
    feedback_type=FeedbackType.CORRECTION,
    content="Correction text",
    tenant_id="tenant_123"
)
```

### Processing Feedback

```python
# Automatic processing (if auto_process=True)
feedback_id = await feedback_loop.record_feedback(...)

# Manual processing
await feedback_loop.process_feedback(feedback_id)

# Process all pending feedback
await feedback_loop.process_all_feedback()
```

### Callbacks

Register callbacks to handle feedback:

```python
async def handle_correction(feedback: FeedbackItem):
    """Handle correction feedback."""
    # Update knowledge base
    # Retrain model
    # Log correction
    pass

# Register callback
feedback_loop.register_callback(
    FeedbackType.CORRECTION,
    handle_correction
)
```

### Learning Insights

Extract insights from feedback:

```python
# Get learning insights
insights = feedback_loop.get_learning_insights(
    tenant_id="tenant_123",
    time_range_hours=24
)

print(f"Average rating: {insights['average_rating']}")
print(f"Common corrections: {insights['common_corrections']}")
print(f"Improvement suggestions: {insights['improvement_suggestions']}")
```

## Usage Examples

### Basic Feedback Collection

```python
from src.core.feedback_loop import FeedbackLoop, FeedbackType

# Create and initialize
feedback_loop = FeedbackLoop(storage_path="feedback.json")
await feedback_loop.initialize()

# Record feedback
feedback_id = await feedback_loop.record_feedback(
    query="What is machine learning?",
    response="Machine learning is a subset of AI...",
    feedback_type=FeedbackType.RATING,
    content="4",  # 4 out of 5 stars
    tenant_id="tenant_123"
)
```

### Feedback with Callbacks

```python
from src.core.feedback_loop import FeedbackLoop, FeedbackType, FeedbackItem

feedback_loop = FeedbackLoop()
await feedback_loop.initialize()

# Register callback for corrections
async def handle_correction(feedback: FeedbackItem):
    print(f"Correction received: {feedback.content}")
    # Update knowledge base or retrain model

feedback_loop.register_callback(
    FeedbackType.CORRECTION,
    handle_correction
)

# Record feedback (callback is automatically called)
await feedback_loop.record_feedback(
    query="What is AI?",
    response="AI is...",
    feedback_type=FeedbackType.CORRECTION,
    content="Corrected information"
)
```

### Learning Insights

```python
# Get insights for tenant
insights = feedback_loop.get_learning_insights(
    tenant_id="tenant_123",
    time_range_hours=168  # Last week
)

# Analyze insights
print(f"Total feedback: {insights['total_feedback']}")
print(f"Average rating: {insights['average_rating']:.2f}")
print(f"Correction rate: {insights['correction_rate']:.2%}")

# Get common corrections
for correction in insights['common_corrections'][:5]:
    print(f"- {correction['query']}: {correction['content']}")
```

### Integration with Gateway

```python
from src.core.litellm_gateway import LiteLLMGateway
from src.core.feedback_loop import FeedbackLoop, FeedbackType

# Create gateway with feedback loop
feedback_loop = FeedbackLoop()
gateway = LiteLLMGateway(
    config=GatewayConfig(
        feedback_loop=feedback_loop
    )
)

# Generate response
response = await gateway.generate_async("What is AI?")

# User provides feedback
await gateway.record_feedback(
    query="What is AI?",
    response=response.text,
    feedback_type=FeedbackType.RATING,
    content="5",
    tenant_id="tenant_123"
)
```

## Configuration

### Storage Path

```python
# File-based storage
feedback_loop = FeedbackLoop(storage_path="feedback.json")

# In-memory only (no persistence)
feedback_loop = FeedbackLoop()
```

### Auto-Processing

```python
# Automatic processing
feedback_loop = FeedbackLoop(auto_process=True)

# Manual processing
feedback_loop = FeedbackLoop(auto_process=False)
await feedback_loop.process_feedback(feedback_id)
```

## Error Handling

The Feedback Loop System implements robust error handling:

- **Graceful Degradation**: Continues operating even if storage fails
- **Error Isolation**: Feedback errors don't affect core functionality
- **Retry Logic**: Implements retry logic for storage operations
- **Validation**: Validates feedback data before processing

## Best Practices

1. **Initialize Before Use**: Always call `await initialize()` after creating FeedbackLoop
2. **Use Callbacks**: Register callbacks to handle feedback automatically
3. **Persist Feedback**: Use storage_path for production deployments
4. **Process Regularly**: Process feedback regularly to extract insights
5. **Monitor Feedback**: Track feedback metrics to monitor AI quality
6. **Tenant Isolation**: Always provide tenant_id for multi-tenant applications
7. **Feedback Types**: Use appropriate feedback types for different scenarios

## See Also

- **[LiteLLM Gateway](../litellm_gateway/README.md)** - Gateway integration with feedback loop
- **[Agno Agent Framework](../agno_agent_framework/README.md)** - Agent feedback collection
- **[RAG System](../rag/README.md)** - RAG feedback collection

