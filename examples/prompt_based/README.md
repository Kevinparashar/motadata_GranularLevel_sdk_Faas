# MOTADATA - PROMPT-BASED CREATION EXAMPLES

**Examples demonstrating how to use the prompt-based generator to create agents and tools from natural language prompts.**

This directory contains examples demonstrating how to use the prompt-based generator to create agents and tools from natural language prompts.

## Examples

### 1. `create_agent_from_prompt.py`

Demonstrates creating an AI agent from a natural language description.

**Key Features:**
- Create agent from prompt
- Configure agent capabilities
- Execute tasks with the agent

**Run:**
```bash
python examples/prompt_based/create_agent_from_prompt.py
```

### 2. `create_tool_from_prompt.py`

Demonstrates creating a tool from a natural language description.

**Key Features:**
- Create tool from prompt
- Generate executable code
- Test tool functionality

**Run:**
```bash
python examples/prompt_based/create_tool_from_prompt.py
```

### 3. `feedback_example.py`

Demonstrates collecting and viewing feedback for agents and tools.

**Key Features:**
- Rate agents and tools
- View feedback statistics
- Track effectiveness

**Run:**
```bash
python examples/prompt_based/feedback_example.py
```

## Prerequisites

1. Set up environment variables:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   # Or
   export ANTHROPIC_API_KEY="your-api-key"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage Tips

1. **Clear Prompts**: Be specific about what you want the agent/tool to do
2. **Test Thoroughly**: Always test generated agents/tools before production use
3. **Provide Feedback**: Rate agents/tools to improve generation quality
4. **Review Code**: Check generated tool code for security and correctness

## Next Steps

- Read the [component documentation](../../src/core/prompt_based_generator/README.md)
- Check the [user guide](../../docs/components/prompt_based_creation_guide.md)
- Explore [troubleshooting guide](../../../docs/troubleshooting/prompt_generator_troubleshooting.md)

