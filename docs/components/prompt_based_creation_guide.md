# Prompt-Based Creation User Guide

## Introduction

This guide helps you effectively use the prompt-based system for creating agents and tools. Learn best practices for writing prompts and understanding system capabilities.

## Writing Effective Prompts

### For Agents

**Good Prompt:**
```
Create a customer support agent that:
- Categorizes tickets by type (technical, billing, general)
- Suggests solutions from knowledge base
- Escalates complex issues to human agents
- Tracks resolution time and customer satisfaction
```

**Bad Prompt:**
```
Make an agent
```

### For Tools

**Good Prompt:**
```
Create a tool that calculates ticket priority.
Inputs:
- urgency: integer 1-5 (1=low, 5=critical)
- impact: integer 1-5 (1=low, 5=high)
- customer_tier: string (bronze, silver, gold, platinum)
Output: Priority score 1-5
Formula: (urgency * 0.4) + (impact * 0.4) + (tier_multiplier * 0.2)
```

**Bad Prompt:**
```
Calculate priority
```

## Best Practices

1. **Be Specific**: Include detailed requirements
2. **List Capabilities**: Clearly state what the agent/tool should do
3. **Define Inputs/Outputs**: For tools, specify parameters and return types
4. **Provide Examples**: Include example use cases when helpful
5. **Test and Iterate**: Review generated results and refine prompts

## Common Use Cases

### Customer Support Agent

```
Create a customer support agent that handles support tickets:
- Categorizes tickets automatically
- Retrieves relevant solutions from knowledge base
- Escalates to human agents when confidence is low
- Tracks metrics: response time, resolution time, satisfaction
```

### Data Analysis Tool

```
Create a tool that analyzes ticket data.
Inputs: ticket_data (dict with fields: created_at, resolved_at, category, priority)
Output: dict with metrics: average_resolution_time, category_distribution, priority_trends
```

## Troubleshooting

### Issue: Generated agent doesn't match requirements

**Solution**: Be more specific in your prompt. Include examples and edge cases.

### Issue: Tool code has errors

**Solution**: The system validates code, but review generated code before production use.

### Issue: Slow generation

**Solution**: Use caching - similar prompts are cached for faster generation.

## Next Steps

- Read [Component Explanation](../components/prompt_based_generator_explanation.md)
- Try [Examples](../../examples/prompt_based/)
- Check [Troubleshooting Guide](../troubleshooting/prompt_generator_troubleshooting.md)

