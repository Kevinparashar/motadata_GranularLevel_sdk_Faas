# Agent Framework Troubleshooting Guide

This guide helps diagnose and resolve common issues encountered when using the Agent Framework.

## Table of Contents

1. [Agent Execution Failures](#agent-execution-failures)
2. [Circuit Breaker Issues](#circuit-breaker-issues)
3. [Health Check Problems](#health-check-problems)
4. [Tool Execution Errors](#tool-execution-errors)
5. [Memory Issues](#memory-issues)
6. [LLM Gateway Connection Problems](#llm-gateway-connection-problems)
7. [Performance Issues](#performance-issues)

## Agent Execution Failures

### Problem: Agent fails to execute tasks

**Symptoms:**
- Agent status remains `IDLE` or changes to `ERROR`
- Tasks are not being processed
- Error messages in logs

**Diagnosis:**
1. Check agent status:
```python
agent_status = agent.status
print(f"Agent status: {agent_status}")
```

2. Check health:
```python
health = await agent.get_health()
print(health)
```

3. Review error logs for specific error messages

**Solutions:**

1. **Gateway Not Configured:**
   - Ensure LiteLLM Gateway is properly initialized
   - Verify API keys are set correctly
   - Check gateway configuration

2. **Agent in Error State:**
   - Reset agent status:
   ```python
   agent.status = AgentStatus.IDLE
   ```

3. **Task Queue Full:**
   - Clear task queue if needed
   - Increase queue size limits

### Problem: Agent hangs during task execution

**Symptoms:**
- Agent status is `RUNNING` but no progress
- Task execution times out
- High CPU usage

**Diagnosis:**
1. Check for infinite loops in tool calling
2. Verify `max_tool_iterations` is set appropriately
3. Check for blocking operations

**Solutions:**

1. **Reduce Tool Iterations:**
   ```python
   agent.max_tool_iterations = 5  # Reduce from default 10
   ```

2. **Add Timeout:**
   ```python
   import asyncio
   result = await asyncio.wait_for(
       agent.execute_task(task),
       timeout=30.0
   )
   ```

3. **Check Tool Execution:**
   - Ensure tools don't block indefinitely
   - Add timeouts to external API calls

## Circuit Breaker Issues

### Problem: Circuit breaker is OPEN

**Symptoms:**
- All requests are rejected immediately
- Error: "Circuit breaker is OPEN"
- Service unavailable errors

**Diagnosis:**
```python
if agent.circuit_breaker:
    stats = agent.circuit_breaker.get_stats()
    print(f"Circuit state: {stats['state']}")
    print(f"Failures: {stats['failures']}")
    print(f"Last failure: {stats['last_failure_time']}")
```

**Solutions:**

1. **Wait for Recovery:**
   - Circuit breaker will automatically transition to HALF_OPEN after timeout
   - Default timeout is 60 seconds

2. **Manual Reset (if safe):**
   ```python
   if agent.circuit_breaker:
       agent.circuit_breaker.reset()
   ```

3. **Check Underlying Service:**
   - Verify LLM Gateway is operational
   - Check network connectivity
   - Verify API keys and quotas

4. **Adjust Circuit Breaker Configuration:**
   ```python
   from src.core.utils.circuit_breaker import CircuitBreakerConfig
   
   config = CircuitBreakerConfig(
       failure_threshold=10,  # Increase threshold
       success_threshold=3,   # Require more successes
       timeout=120.0          # Longer recovery time
   )
   agent.attach_circuit_breaker(config)
   ```

## Health Check Problems

### Problem: Health check reports UNHEALTHY

**Symptoms:**
- Health check status is `unhealthy`
- Agent operations fail
- Degraded performance

**Diagnosis:**
```python
health = await agent.get_health()
print(health)
```

**Solutions:**

1. **Gateway Unavailable:**
   - Check LiteLLM Gateway configuration
   - Verify gateway is initialized
   - Test gateway connectivity

2. **Memory Issues:**
   - If memory is not configured, this is expected (status: DEGRADED)
   - To fix, attach memory:
   ```python
   from src.core.agno_agent_framework.memory import AgentMemory, MemoryType
   
   memory = AgentMemory(
       memory_type=MemoryType.SHORT_TERM,
       max_entries=1000
   )
   agent.attach_memory(memory)
   ```

3. **Agent in Error State:**
   - Check agent status
   - Review error logs
   - Reset agent if needed

## Tool Execution Errors

### Problem: Tool execution fails

**Symptoms:**
- `ToolInvocationError` exceptions
- Tool calls return errors
- Agent cannot complete tasks requiring tools

**Diagnosis:**
1. Check tool registration:
```python
tools = agent.tool_registry.get_tools_schema()
print(f"Registered tools: {[t['name'] for t in tools]}")
```

2. Verify tool parameters:
```python
# Check tool schema
tool = agent.tool_registry.get_tool_by_name("tool_name")
print(tool.parameters)
```

**Solutions:**

1. **Tool Not Found:**
   - Ensure tool is registered:
   ```python
   from src.core.agno_agent_framework.tools import Tool, ToolParameter
   
   tool = Tool(
       tool_id="my_tool",
       name="my_tool",
       description="Tool description",
       function=my_function,
       parameters=[
           ToolParameter(
               name="param1",
               type="string",
               description="Parameter description",
               required=True
           )
       ]
   )
   agent.tool_registry.register_tool(tool)
   ```

2. **Parameter Validation Errors:**
   - Check required parameters are provided
   - Verify parameter types match
   - Review tool function signature

3. **Tool Function Errors:**
   - Add error handling in tool functions
   - Ensure tool functions don't raise unexpected exceptions
   - Test tool functions independently

## Memory Issues

### Problem: Memory operations fail

**Symptoms:**
- `MemoryWriteError` exceptions
- Memory not storing data
- Memory retrieval returns None

**Diagnosis:**
```python
if agent.memory:
    # Check memory configuration
    print(f"Memory type: {agent.memory.memory_type}")
    print(f"Max entries: {agent.memory.max_entries}")
```

**Solutions:**

1. **Memory Not Attached:**
   - Attach memory to agent:
   ```python
   agent.attach_memory(memory)
   ```

2. **Memory Full:**
   - Increase `max_entries`
   - Clear old entries
   - Use different memory type (e.g., LONG_TERM)

3. **Token Budget Exceeded:**
   - Reduce `max_tokens` in memory configuration
   - Clear old memories
   - Use more efficient memory storage

## LLM Gateway Connection Problems

### Problem: Cannot connect to LLM Gateway

**Symptoms:**
- Connection errors
- Timeout errors
- API key errors

**Diagnosis:**
1. Check gateway health:
```python
gateway_health = await agent.gateway.get_health()
print(gateway_health)
```

2. Test gateway directly:
```python
response = await agent.gateway.generate_async(
    prompt="Test",
    model="gpt-4"
)
```

**Solutions:**

1. **API Key Issues:**
   - Verify API keys are set in environment
   - Check key permissions
   - Ensure keys are not expired

2. **Network Issues:**
   - Check internet connectivity
   - Verify firewall rules
   - Test with different network

3. **Rate Limiting:**
   - Check rate limit status
   - Wait for rate limit reset
   - Use rate limiter configuration

4. **Provider Issues:**
   - Check provider status page
   - Try different provider/model
   - Verify provider API is operational

## Performance Issues

### Problem: Agent is slow

**Symptoms:**
- Long task execution times
- High latency
- Timeout errors

**Diagnosis:**
1. Check task execution time:
```python
import time
start = time.time()
result = await agent.execute_task(task)
duration = time.time() - start
print(f"Task took {duration} seconds")
```

2. Check health metrics:
```python
health = await agent.get_health()
print(f"Response time: {health.get('last_result', {}).get('response_time_ms')}")
```

**Solutions:**

1. **Reduce Tool Iterations:**
   ```python
   agent.max_tool_iterations = 3  # Reduce iterations
   ```

2. **Optimize Prompts:**
   - Reduce prompt length
   - Use more efficient templates
   - Enable prompt optimization

3. **Enable Caching:**
   - Use cache for repeated queries
   - Cache tool results when possible

4. **Use Faster Models:**
   - Switch to faster LLM models
   - Use smaller models for simple tasks

5. **Parallel Processing:**
   - Execute independent tasks in parallel
   - Use async operations

## Best Practices

1. **Always Check Health:**
   ```python
   health = await agent.get_health()
   if health['status'] != 'healthy':
       # Handle unhealthy state
   ```

2. **Monitor Circuit Breaker:**
   ```python
   if agent.circuit_breaker:
       stats = agent.circuit_breaker.get_stats()
       if stats['state'] == 'open':
           # Handle open circuit
   ```

3. **Handle Errors Gracefully:**
   ```python
   try:
       result = await agent.execute_task(task)
   except AgentExecutionError as e:
       # Handle execution error
   except Exception as e:
       # Handle other errors
   ```

4. **Use Timeouts:**
   ```python
   result = await asyncio.wait_for(
       agent.execute_task(task),
       timeout=30.0
   )
   ```

5. **Log Everything:**
   - Enable detailed logging
   - Log all errors and warnings
   - Monitor agent metrics

## Getting Help

If you continue to experience issues:

1. Check the logs for detailed error messages
2. Review the Agent Framework documentation
3. Verify your configuration matches the examples
4. Test with minimal configuration to isolate issues
5. Check GitHub issues for known problems


