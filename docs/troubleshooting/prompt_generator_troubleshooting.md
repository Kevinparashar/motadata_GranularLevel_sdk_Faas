# MOTADATA - PROMPT GENERATOR TROUBLESHOOTING

**Troubleshooting guide for diagnosing and resolving common issues with the Prompt Generator.**

## Common Issues and Solutions

### Issue: Prompt Interpretation Fails

**Symptoms:**
- Error: `PromptInterpretationError`
- LLM returns invalid JSON

**Solutions:**
1. Simplify your prompt
2. Be more explicit about requirements
3. Check API key and gateway configuration
4. Try rephrasing the prompt

### Issue: Generated Agent Doesn't Work as Expected

**Symptoms:**
- Agent behavior doesn't match prompt
- Missing capabilities

**Solutions:**
1. Review generated agent configuration
2. Provide more detailed prompt with examples
3. Test with sample tasks
4. Provide feedback to improve generation

### Issue: Tool Code Validation Fails

**Symptoms:**
- Error: `CodeValidationError`
- Generated code has syntax errors

**Solutions:**
1. Be more specific about code requirements
2. Provide example code structure
3. Review generated code manually
4. Report issue with prompt for improvement

### Issue: Permission Denied

**Symptoms:**
- Error: `AccessControlError`
- Cannot access agent/tool

**Solutions:**
1. Check user permissions
2. Grant appropriate permissions
3. Verify tenant_id matches
4. Contact administrator

### Issue: Slow Generation

**Symptoms:**
- Takes >10 seconds to generate
- High latency

**Solutions:**
1. Check cache - similar prompts are cached
2. Use cached configurations when possible
3. Optimize prompt length
4. Check LLM provider status

### Issue: Memory Issues

**Symptoms:**
- Too many agents/tools
- Resource exhaustion

**Solutions:**
1. Clean up unused agents/tools
2. Set appropriate limits per tenant
3. Use memory pooling
4. Monitor resource usage

## Getting Help

- Check [Component Documentation](../../src/core/prompt_based_generator/README.md)
- Review [User Guide](../components/prompt_based_creation_guide.md)
- See [Examples](../../examples/prompt_based/)

