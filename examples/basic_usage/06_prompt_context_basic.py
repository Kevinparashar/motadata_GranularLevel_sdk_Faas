"""
Basic Prompt Context Management Example

Demonstrates how to use the Prompt Context Management component
for template-based prompts with versioning.

Dependencies: Agent Framework, Evaluation & Observability
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from src.core.prompt_context_management import (
    ContextWindowManager,
    PromptContextManager,
    PromptTemplate,
)


def main():
    """Demonstrate basic prompt context management."""

    # 1. Create Prompt Templates
    print("=== Prompt Templates ===")

    template = PromptTemplate(
        name="qa_template",
        version="1.0.0",
        content="""You are a helpful assistant. Answer the following question based on the context provided.

Context: {context}

Question: {question}

Answer:""",
    )

    print(f"Created template: {template.name} v{template.version}")

    # 2. Prompt Manager with Templates
    print("\n=== Prompt Manager ===")

    manager = PromptContextManager(max_tokens=4000)

    # Add templates
    manager.add_template(
        name="qa_template",
        version="1.0.0",
        content="""You are a helpful assistant. Answer the following question based on the context provided.

Context: {context}

Question: {question}

Answer:""",
    )

    manager.add_template(
        name="qa_template",
        version="2.0.0",
        content="""Based on the context below, provide a clear and concise answer to the question.

Context: {context}

Question: {question}

Please provide your answer:""",
    )

    print("Registered 2 template versions")

    # 3. Template Rendering
    print("\n=== Template Rendering ===")

    rendered = manager.render(
        template_name="qa_template",
        version="1.0.0",
        variables={"context": "Python is a programming language.", "question": "What is Python?"},
    )

    print("Rendered prompt:")
    print(rendered)

    # 4. Context Window Management
    print("\n=== Context Window Management ===")

    window_manager = ContextWindowManager(max_tokens=1000, safety_margin=100)

    # Estimate tokens
    sample_text = "This is a sample text for token estimation."
    tokens = window_manager.estimate_tokens(sample_text)
    print(f"Estimated tokens: {tokens}")

    # Truncate long text
    long_text = " ".join(["word"] * 2000)
    truncated = window_manager.truncate(long_text, max_tokens=500)
    print(f"Truncated from {len(long_text.split())} to {len(truncated.split())} words")

    # 5. Context Building from Messages
    print("\n=== Context Building ===")

    messages = [
        "User: Hello",
        "Assistant: Hi! How can I help?",
        "User: Tell me about Python",
        "Assistant: Python is a high-level programming language...",
    ]

    context = window_manager.build_context(messages, max_tokens=100)
    print("Built context from messages:")
    print(context)

    # 6. Template with Context Variables
    print("\n=== Template with Variables ===")

    manager.add_template(
        name="personalized_template",
        version="1.0.0",
        content="""Hello {user_name}! You are a {user_role}.

How can I assist you today?""",
    )

    personalized_prompt = manager.render(
        template_name="personalized_template",
        version="1.0.0",
        variables={"user_name": "John Doe", "user_role": "developer"},
    )

    print("Personalized prompt:")
    print(personalized_prompt)

    # 7. Prompt History
    print("\n=== Prompt History ===")

    manager.record_history("First prompt")
    manager.record_history("Second prompt")
    manager.record_history("Third prompt")

    print(f"Prompt history count: {len(manager.history)}")
    print(f"Latest prompts: {manager.history[-2:]}")

    print("\n✅ Prompt context management example completed successfully!")


if __name__ == "__main__":
    main()
