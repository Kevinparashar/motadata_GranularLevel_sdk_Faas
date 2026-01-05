"""
Basic Prompt Context Management Example

Demonstrates how to use the Prompt Context Management component
for template-based prompts with versioning.

Dependencies: Agent Framework, Evaluation & Observability
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from src.core.prompt_context_management import (
    PromptTemplate,
    PromptManager,
    ContextBuilder
)


def main():
    """Demonstrate basic prompt context management."""
    
    # 1. Create Prompt Templates
    print("=== Prompt Templates ===")
    
    template = PromptTemplate(
        name="qa_template",
        version="1.0.0",
        template="""
You are a helpful assistant. Answer the following question based on the context provided.

Context: {context}

Question: {question}

Answer:
        """.strip(),
        variables=["context", "question"]
    )
    
    print(f"Created template: {template.name} v{template.version}")
    print(f"Variables: {template.variables}")
    
    # 2. Render Template
    print("\n=== Template Rendering ===")
    
    rendered = template.render(
        context="Python is a programming language.",
        question="What is Python?"
    )
    
    print("Rendered prompt:")
    print(rendered)
    
    # 3. Prompt Manager
    print("\n=== Prompt Manager ===")
    
    manager = PromptManager()
    
    # Register templates
    manager.register_template(template)
    
    # Create another version
    template_v2 = PromptTemplate(
        name="qa_template",
        version="2.0.0",
        template="""
Based on the context below, provide a clear and concise answer to the question.

Context: {context}

Question: {question}

Please provide your answer:
        """.strip(),
        variables=["context", "question"]
    )
    
    manager.register_template(template_v2)
    
    # Get template by name and version
    template_1 = manager.get_template("qa_template", version="1.0.0")
    template_2 = manager.get_template("qa_template", version="2.0.0")
    
    print(f"Template v1.0.0: {template_1.name}")
    print(f"Template v2.0.0: {template_2.name}")
    
    # List all versions
    versions = manager.list_versions("qa_template")
    print(f"Available versions: {versions}")
    
    # 4. Context Building
    print("\n=== Context Building ===")
    
    context_builder = ContextBuilder()
    
    # Add context items
    context_builder.add_item("user_name", "John Doe")
    context_builder.add_item("user_role", "developer")
    context_builder.add_item("conversation_history", [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! How can I help?"}
    ])
    
    # Build context
    context = context_builder.build()
    print(f"Built context with {len(context)} items")
    
    # 5. Template with Context
    print("\n=== Template with Context ===")
    
    personalized_template = PromptTemplate(
        name="personalized_template",
        version="1.0.0",
        template="""
Hello {user_name}! You are a {user_role}.

Previous conversation:
{conversation_history}

How can I assist you today?
        """.strip(),
        variables=["user_name", "user_role", "conversation_history"]
    )
    
    # Format conversation history
    history_str = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in context["conversation_history"]
    ])
    
    personalized_prompt = personalized_template.render(
        user_name=context["user_name"],
        user_role=context["user_role"],
        conversation_history=history_str
    )
    
    print("Personalized prompt:")
    print(personalized_prompt)
    
    # 6. A/B Testing Support
    print("\n=== A/B Testing ===")
    
    # Get template for A/B test
    test_template = manager.get_template("qa_template", version="2.0.0")
    
    # Track usage
    manager.track_usage("qa_template", "2.0.0", success=True)
    manager.track_usage("qa_template", "1.0.0", success=True)
    
    # Get usage statistics
    stats = manager.get_usage_stats("qa_template")
    print(f"Usage stats: {stats}")
    
    print("\n✅ Prompt context management example completed successfully!")


if __name__ == "__main__":
    main()

