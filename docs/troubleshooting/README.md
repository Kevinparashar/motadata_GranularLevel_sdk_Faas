# Motadata Troubleshooting Guides

This directory contains comprehensive troubleshooting guides for all components of the Motadata Python AI SDK. Each guide provides detailed solutions for common issues, diagnostic steps, and best practices.

## Available Troubleshooting Guides

### Core Components

1. **[Data Ingestion Service Troubleshooting](data_ingestion_troubleshooting.md)**
   - File upload failures
   - Format validation errors
   - Processing errors
   - Multi-modal loading issues
   - RAG ingestion failures
   - Cache integration problems
   - Batch processing errors

2. **[Agent Framework Troubleshooting](agent_troubleshooting.md)**
   - Agent execution failures
   - Circuit breaker issues
   - Health check problems
   - Tool execution errors
   - Memory issues
   - LLM Gateway connection problems
   - Performance issues

3. **[LiteLLM Gateway Troubleshooting](litellm_gateway_troubleshooting.md)**
   - Connection failures
   - Rate limiting issues
   - Circuit breaker problems
   - Provider failures
   - Request deduplication issues
   - Request batching problems
   - Health check failures
   - Validation errors
   - Performance issues

4. **[RAG System Troubleshooting](rag_system_troubleshooting.md)**
   - Document ingestion failures
   - Retrieval issues
   - Generation errors
   - Embedding problems
   - Database connection issues
   - Chunking problems
   - Performance issues
   - Cache issues

5. **[Cache Mechanism Troubleshooting](cache_mechanism_troubleshooting.md)**
   - Cache misses
   - Memory backend issues
   - Redis backend issues
   - Cache invalidation problems
   - Performance issues
   - Memory pressure
   - Cache warming issues
   - Sharding problems

6. **[Prompt Context Management Troubleshooting](prompt_context_management_troubleshooting.md)**
   - Template not found errors
   - Template rendering issues
   - Context window problems
   - Token limit exceeded
   - Version management issues
   - Dynamic prompting problems
   - Optimization issues
   - Fallback template problems

7. **[PostgreSQL Database Troubleshooting](postgresql_database_troubleshooting.md)**
   - Connection failures
   - Connection pool issues
   - Query execution errors
   - Vector operations problems
   - pgvector extension issues
   - Transaction problems
   - Performance issues

8. **[Evaluation & Observability Troubleshooting](evaluation_observability_troubleshooting.md)**
   - Tracing issues
   - Logging problems
   - Metrics collection issues
   - Export failures
   - Performance impact
   - Configuration problems

9. **[API Backend Services Troubleshooting](api_backend_services_troubleshooting.md)**
   - API startup issues
   - Request validation errors
   - Authentication problems
   - CORS issues
   - Endpoint not found
   - Response formatting problems
   - Performance issues
   - Error handling issues

### Machine Learning Components

9. **[ML Framework Troubleshooting](ml_framework_troubleshooting.md)**
   - Training failures
   - Prediction errors
   - Model loading issues
   - Memory management problems
   - Data processing errors
   - Model registration issues
   - Performance issues

10. **[MLOps Pipeline Troubleshooting](mlops_troubleshooting.md)**
    - Experiment tracking issues
    - Model deployment failures
    - Model monitoring problems
    - Drift detection issues
    - Pipeline execution errors

11. **[ML Data Management Troubleshooting](ml_data_management_troubleshooting.md)**
    - Data loading issues
    - Data validation failures
    - Feature store problems
    - Data pipeline errors
    - Data ingestion issues

12. **[Model Serving Troubleshooting](model_serving_troubleshooting.md)**
    - Server startup issues
    - API request failures
    - Batch processing problems
    - Real-time prediction issues
    - Performance problems

### Core Platform Integrations

13. **[NATS Integration Troubleshooting](nats_integration_troubleshooting.md)**
    - Connection failures
    - Message publishing issues
    - Subscription problems
    - Performance issues
    - Error handling

14. **[OTEL Integration Troubleshooting](otel_integration_troubleshooting.md)**
    - Tracing issues
    - Metrics collection problems
    - Performance overhead
    - Export failures
    - Configuration problems

15. **[CODEC Integration Troubleshooting](codec_integration_troubleshooting.md)**
    - Encoding/decoding failures
    - Schema validation issues
    - Version migration problems
    - Performance issues

### FaaS Services

16. **FaaS Services Troubleshooting** (General)
    - Service startup issues
    - Service-to-service communication failures
    - HTTP endpoint errors
    - Configuration problems
    - Deployment issues
    - See individual service documentation for component-specific issues:
      - [Agent Service](../../src/faas/services/agent_service/README.md)
      - [RAG Service](../../src/faas/services/rag_service/)
      - [Gateway Service](../../src/faas/services/gateway_service/)
      - [FaaS Deployment Guides](../deployment/) - Docker, Kubernetes, Lambda troubleshooting

## How to Use These Guides

### Step 1: Identify the Component

Determine which component is experiencing issues:
- **Data Ingestion Service**: Issues with file uploads, processing, format validation, multi-modal loading
- **Agent Framework**: Issues with agent execution, tools, memory
- **LiteLLM Gateway**: Issues with LLM API calls, rate limiting, providers
- **RAG System**: Issues with document ingestion, retrieval, generation, multi-modal processing
- **Cache Mechanism**: Issues with caching, Redis, memory
- **Prompt Context Management**: Issues with templates, context, tokens
- **PostgreSQL Database**: Issues with database connections, queries, vectors
- **Evaluation & Observability**: Issues with tracing, logging, metrics
- **API Backend Services**: Issues with API endpoints, requests, responses
- **ML Framework**: Issues with training, inference, model management
- **MLOps Pipeline**: Issues with experiments, deployment, monitoring
- **ML Data Management**: Issues with data loading, validation, feature store
- **Model Serving**: Issues with API server, batch processing, predictions
- **NATS Integration**: Issues with messaging, connections, performance
- **OTEL Integration**: Issues with tracing, metrics, observability
- **CODEC Integration**: Issues with serialization, schema validation, versioning
- **FaaS Services**: Issues with service deployment, HTTP endpoints, service-to-service communication

### Step 2: Find the Problem

Each troubleshooting guide is organized by problem type. Look for symptoms that match your issue:
- **Connection Failures**: Cannot connect to services
- **Performance Issues**: Slow operations, high latency
- **Configuration Problems**: Settings not working
- **Error Handling**: Exceptions, validation errors

### Step 3: Follow Diagnostic Steps

Each problem includes:
1. **Symptoms**: What you're experiencing
2. **Diagnosis**: How to identify the issue
3. **Solutions**: Step-by-step fixes

### Step 4: Apply Solutions

Follow the solutions in order:
1. Start with the most common fixes
2. Test after each change
3. Check logs for detailed errors
4. Verify configuration matches examples

## Common Troubleshooting Patterns

### Connection Issues

Most connection issues follow similar patterns:
1. Check service is running
2. Verify network connectivity
3. Check credentials/authentication
4. Review configuration

### Performance Issues

Performance problems often require:
1. Monitor resource usage
2. Check configuration limits
3. Optimize queries/operations
4. Enable caching

### Configuration Problems

Configuration issues typically need:
1. Verify configuration format
2. Check environment variables
3. Test with minimal config
4. Review documentation

## Best Practices

1. **Check Logs First**: Always review logs for detailed error messages
2. **Test Incrementally**: Make one change at a time and test
3. **Use Minimal Config**: Test with minimal configuration to isolate issues
4. **Verify Examples**: Compare your code with documentation examples
5. **Monitor Metrics**: Use observability tools to track issues

## Getting Additional Help

If you continue to experience issues after following these guides:

1. **Review Component Documentation**: Check the main component README files
2. **Check Examples**: Review example code in the `examples/` directory
3. **Search Issues**: Look for similar issues in GitHub
4. **Review Logs**: Check detailed error logs for specific error messages
5. **Test Isolation**: Test components independently to isolate issues

## Troubleshooting Checklist

Before seeking help, ensure you've:

- [ ] Checked the relevant troubleshooting guide
- [ ] Reviewed component documentation
- [ ] Verified configuration matches examples
- [ ] Tested with minimal configuration
- [ ] Checked logs for detailed errors
- [ ] Verified all dependencies are installed
- [ ] Tested connectivity to external services
- [ ] Reviewed recent changes to code/configuration

## Quick Reference

### Common Error Codes

- **401 Unauthorized**: Authentication/authorization issues
- **404 Not Found**: Resource/endpoint not found
- **422 Unprocessable Entity**: Validation errors
- **429 Too Many Requests**: Rate limiting
- **500 Internal Server Error**: Server-side errors
- **503 Service Unavailable**: Service unavailable (circuit breaker)

### Common Diagnostic Commands

```python
# Check component health
health = await component.get_health()
print(health)

# Test connectivity
try:
    result = await component.operation()
except Exception as e:
    print(f"Error: {e}")

# Check configuration
print(component.config)
```

## Contributing

If you find solutions to issues not covered in these guides, please consider:
1. Documenting the issue and solution
2. Adding it to the appropriate troubleshooting guide
3. Sharing with the community

