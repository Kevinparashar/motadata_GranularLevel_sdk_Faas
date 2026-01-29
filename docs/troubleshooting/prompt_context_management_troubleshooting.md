# Motadata Prompt Context Management Troubleshooting Guide

This guide helps diagnose and resolve common issues encountered when using the Prompt Context Management component.

## Table of Contents

1. [Template Not Found Errors](#template-not-found-errors)
2. [Template Rendering Issues](#template-rendering-issues)
3. [Context Window Problems](#context-window-problems)
4. [Token Limit Exceeded](#token-limit-exceeded)
5. [Version Management Issues](#version-management-issues)
6. [Dynamic Prompting Problems](#dynamic-prompting-problems)
7. [Optimization Issues](#optimization-issues)
8. [Fallback Template Problems](#fallback-template-problems)

## Template Not Found Errors

### Problem: Template not found

**Symptoms:**
- `ValueError: Template 'name' not found`
- Template retrieval returns None
- Template not accessible for tenant

**Diagnosis:**
```python
# Check template exists
template = manager.store.get("template_name", tenant_id="tenant_123")
if not template:
    print("Template not found")
```

**Solutions:**

1. **Verify Template is Added:**
   ```python
   manager.add_template(
       name="template_name",
       version="1.0",
       content="Template content {variable}",
       tenant_id="tenant_123"
   )
   ```

2. **Check Tenant ID:**
   - Ensure tenant_id matches when adding and retrieving
   - Use None for global templates
   - Verify tenant isolation

3. **Check Template Name:**
   - Verify exact name match (case-sensitive)
   - Check for typos
   - Use consistent naming

4. **Verify Template Version:**
   ```python
   # Get specific version
   template = manager.render(
       "template_name",
       {},
       tenant_id="tenant_123",
       version="1.0"
   )
   ```

## Template Rendering Issues

### Problem: Template rendering fails

**Symptoms:**
- `KeyError` during rendering
- Missing variable errors
- Incorrect variable substitution
- Template format errors

**Diagnosis:**
```python
try:
    prompt = manager.render(
        "template_name",
        {"variable": "value"},
        tenant_id="tenant_123"
    )
except KeyError as e:
    print(f"Missing variable: {e}")
except ValueError as e:
    print(f"Template error: {e}")
```

**Solutions:**

1. **Provide All Required Variables:**
   ```python
   # Check template variables
   template = manager.store.get("template_name")
   # Template content: "Hello {name}, welcome to {service}!"

   # Provide all variables
   prompt = manager.render(
       "template_name",
       {
           "name": "John",
           "service": "AI SDK"
       }
   )
   ```

2. **Validate Variable Types:**
   - Ensure variable types match expected format
   - Convert types if needed
   - Check for None values

3. **Escape Special Characters:**
   - Escape braces if needed: `{{` and `}}`
   - Handle special characters in variables
   - Validate template format

4. **Check Template Format:**
   - Use Python format-style: `{variable}`
   - Verify template syntax
   - Test template separately

## Context Window Problems

### Problem: Context window issues

**Symptoms:**
- Context truncated unexpectedly
- Important context missing
- Context building fails
- Token estimation inaccurate

**Diagnosis:**
```python
# Check context window configuration
print(f"Max tokens: {manager.window.max_tokens}")
print(f"Safety margin: {manager.window.safety_margin}")

# Estimate tokens
tokens = manager.window.estimate_tokens(text)
print(f"Estimated tokens: {tokens}")
```

**Solutions:**

1. **Increase Context Window:**
   ```python
   manager = create_prompt_manager(
       max_tokens=8000,  # Increase max tokens
       safety_margin=400
   )
   ```

2. **Adjust Safety Margin:**
   ```python
   manager = create_prompt_manager(
       max_tokens=4000,
       safety_margin=200  # Reduce safety margin
   )
   ```

3. **Optimize Context Building:**
   ```python
   # Build context with history
   context = manager.build_context_with_history(
       "new message",
       max_tokens=2000
   )
   ```

4. **Check Token Estimation:**
   - Verify token estimation accuracy
   - Adjust estimation if needed
   - Monitor actual token usage

## Token Limit Exceeded

### Problem: Token limit exceeded

**Symptoms:**
- Prompts truncated
- Context cut off
- Token limit errors
- Incomplete responses

**Diagnosis:**
```python
# Check token usage
tokens = manager.window.estimate_tokens(prompt)
max_tokens = manager.window.max_tokens
print(f"Tokens: {tokens}/{max_tokens}")

if tokens > max_tokens:
    print("Token limit exceeded")
```

**Solutions:**

1. **Increase Max Tokens:**
   ```python
   manager = create_prompt_manager(max_tokens=16000)
   ```

2. **Reduce Context Size:**
   ```python
   # Truncate prompt
   truncated = manager.truncate_prompt(prompt, max_tokens=2000)
   ```

3. **Optimize Prompt Length:**
   - Remove unnecessary content
   - Summarize long context
   - Use more concise templates

4. **Adjust Safety Margin:**
   ```python
   manager = create_prompt_manager(
       max_tokens=4000,
       safety_margin=100  # Reduce margin
   )
   ```

## Version Management Issues

### Problem: Version management problems

**Symptoms:**
- Wrong version retrieved
- Version not found
- Latest version not working
- Version conflicts

**Diagnosis:**
```python
# Check available versions
tenant_templates = manager.store._templates.get("tenant_123", {})
versions = tenant_templates.get("template_name", {})
print(f"Available versions: {list(versions.keys())}")
```

**Solutions:**

1. **Specify Version Explicitly:**
   ```python
   prompt = manager.render(
       "template_name",
       {},
       tenant_id="tenant_123",
       version="1.0"  # Specify version
   )
   ```

2. **Check Version Format:**
   - Use consistent version format
   - Semantic versioning recommended
   - Verify version exists

3. **Get Latest Version:**
   ```python
   # Latest version is retrieved by default
   prompt = manager.render("template_name", {})
   ```

4. **Manage Versions:**
   - Keep track of versions
   - Document version changes
   - Test versions before deployment

## Dynamic Prompting Problems

### Problem: Dynamic prompting not working

**Symptoms:**
- Prompts not adapting to context
- Context adapters not applied
- Dynamic adjustments missing
- Adapter errors

**Diagnosis:**
```python
from src.core.prompt_context_management.prompt_enhancements import DynamicPromptBuilder

builder = DynamicPromptBuilder(manager.store)
# Check adapters
print(f"Adapters: {len(builder.context_adapters)}")
```

**Solutions:**

1. **Add Context Adapters:**
   ```python
   def custom_adapter(prompt, context, variables):
       if context.get("urgency") == "high":
           prompt = f"[URGENT] {prompt}"
       return prompt

   builder.add_context_adapter(custom_adapter)
   ```

2. **Provide Context:**
   ```python
   prompt = builder.build_dynamic_prompt(
       "template_name",
       {"input": "test"},
       context={
           "user_role": "admin",
           "urgency": "high"
       },
       tenant_id="tenant_123"
   )
   ```

3. **Handle Adapter Errors:**
   - Add error handling in adapters
   - Test adapters separately
   - Verify adapter logic

## Optimization Issues

### Problem: Prompt optimization not working

**Symptoms:**
- Optimization not applied
- Prompts not improved
- Optimization errors
- Performance not improved

**Diagnosis:**
```python
from src.core.prompt_context_management.prompt_enhancements import PromptOptimizer

optimizer = PromptOptimizer()
# Check optimization rules
print(f"Rules: {len(optimizer.optimization_rules)}")
```

**Solutions:**

1. **Add Optimization Rules:**
   ```python
   def clarity_rule(prompt):
       # Improve clarity
       return prompt.replace("analyze", "thoroughly analyze")

   optimizer.add_optimization_rule(clarity_rule)
   ```

2. **Apply Optimization:**
   ```python
   optimized = optimizer.optimize(
       prompt,
       context={"domain": "technical"}
   )
   ```

3. **Review Optimization History:**
   ```python
   history = optimizer.optimization_history
   # Review optimization results
   ```

## Fallback Template Problems

### Problem: Fallback templates not working

**Symptoms:**
- Fallback not triggered
- Template not found even with fallback
- Fallback chain not working
- Fallback errors

**Diagnosis:**
```python
from src.core.prompt_context_management.prompt_enhancements import FallbackTemplateManager

fallback_manager = FallbackTemplateManager(
    manager.store,
    fallback_chain=["primary", "secondary", "default"]
)
```

**Solutions:**

1. **Configure Fallback Chain:**
   ```python
   fallback_manager = FallbackTemplateManager(
       manager.store,
       fallback_chain=[
           "custom_template",
           "default_template",
           "basic_template"
       ]
   )
   ```

2. **Ensure Fallback Templates Exist:**
   ```python
   # Add fallback templates
   manager.add_template("default_template", "1.0", "Default content")
   manager.add_template("basic_template", "1.0", "Basic content")
   ```

3. **Test Fallback:**
   ```python
   # Try to render non-existent template
   prompt = fallback_manager.render_with_fallback(
       "nonexistent_template",
       {},
       tenant_id="tenant_123"
   )
   ```

## Best Practices

1. **Validate Templates:**
   ```python
   # Test template before use
   try:
       prompt = manager.render("template_name", {})
   except Exception as e:
       logger.error(f"Template error: {e}")
   ```

2. **Monitor Token Usage:**
   - Track token usage
   - Optimize prompt length
   - Adjust context window

3. **Use Versioning:**
   - Version all templates
   - Document changes
   - Test versions

4. **Handle Errors:**
   ```python
   try:
       prompt = manager.render("template_name", {})
   except ValueError as e:
       # Handle template not found
   except KeyError as e:
       # Handle missing variable
   ```

5. **Optimize Context:**
   - Build context efficiently
   - Use appropriate token limits
   - Monitor context size

## Getting Help

If you continue to experience issues:

1. Check the logs for detailed error messages
2. Review the Prompt Context Management documentation
3. Verify your configuration matches the examples
4. Test templates separately
5. Check template format and variables
6. Review GitHub issues for known problems

