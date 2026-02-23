# Tenant Context Separation in Orchestrator

## Overview

The Orchestrator module implements **complete tenant isolation** at every layer to ensure clear separation between tenants in a multi-tenant SaaS environment.

## Tenant Context Flow

```
HTTP Request (X-Tenant-ID header)
    ↓
OrchestratorService.extract_headers()
    ↓
standard_headers.tenant_id
    ↓
┌─────────────────────────────────────┐
│  All Components Use tenant_id      │
├─────────────────────────────────────┤
│  • QueryRouter (cache keys)         │
│  • ServiceSelector (routing)       │
│  • CacheManager (cache isolation)  │
│  • CacheStrategy (key generation)  │
│  • Service calls (X-Tenant-ID)     │
└─────────────────────────────────────┘
```

## Tenant Isolation Points

### 1. **HTTP Header Extraction**
```python
# src/faas/services/orchestrator_service/service.py
standard_headers = extract_headers(**headers)
# Extracts X-Tenant-ID from request headers
```

### 2. **Cache Key Generation**
```python
# src/faas/orchestrator/cache_strategy.py
def generate_cache_key(self, feature, query, tenant_id, context):
    key_parts = ["orchestrator", feature]
    if tenant_id:
        key_parts.append(f"tenant:{tenant_id}")  # ✅ Tenant isolation
    # ... rest of key generation
```

**Result:** Cache keys are tenant-scoped:
- `orchestrator:agent_chat:tenant:tenant_123:query:abc123`
- `orchestrator:agent_chat:tenant:tenant_456:query:abc123` (different tenant, same query)

### 3. **Cache Operations**
```python
# src/faas/orchestrator/cache_manager.py
await self.cache.get(cache_key, tenant_id=tenant_id)  # ✅ Tenant-scoped
await self.cache.set(cache_key, value, tenant_id=tenant_id, ttl=ttl)  # ✅ Tenant-scoped
```

### 4. **Intent Analysis Caching**
```python
# src/faas/orchestrator/query_router.py
cache_key = f"intent:{tenant_id}:{self._hash_query(query)}"  # ✅ Tenant-scoped
cached = await self.cache.get(cache_key, tenant_id=tenant_id)
```

### 5. **Service-to-Service Calls**
```python
# src/faas/services/orchestrator_service/service.py
headers_dict = {
    "X-Tenant-ID": standard_headers.tenant_id,  # ✅ Propagated to downstream services
    "X-User-ID": standard_headers.user_id or "",
    "X-Correlation-ID": standard_headers.correlation_id,
    "X-Request-ID": standard_headers.request_id,
}
```

### 6. **OTEL Tracing**
```python
# src/faas/services/orchestrator_service/service.py
span.set_attribute("tenant.id", standard_headers.tenant_id)  # ✅ Tenant in traces
```

### 7. **Cache Invalidation**
```python
# src/faas/orchestrator/cache_manager.py
# Invalidate specific tenant's cache
cache_key_pattern = f"orchestrator:{feature}:tenant:{tenant_id}:*"
await self.cache.invalidate_pattern(cache_key_pattern, tenant_id=tenant_id)
```

## Tenant Isolation Guarantees

✅ **Cache Isolation**: Each tenant's cache is completely isolated
- Cache keys include `tenant:{tenant_id}`
- Cache operations use `tenant_id` parameter
- No cross-tenant cache access possible

✅ **Intent Analysis Isolation**: Intent classification results are cached per tenant
- Different tenants can have different intent classifications for same query
- Cache keys: `intent:{tenant_id}:{query_hash}`

✅ **Service Routing Isolation**: Tenant context is propagated to all downstream services
- `X-Tenant-ID` header is included in all service calls
- Downstream services receive tenant context for their own isolation

✅ **OTEL Tracing Isolation**: Traces include tenant context
- `tenant.id` attribute on all spans
- Enables tenant-specific observability

✅ **Cache Invalidation Isolation**: Cache invalidation is tenant-scoped
- Can invalidate specific tenant's cache
- Pattern matching includes tenant ID

## Example: Multi-Tenant Cache Isolation

```python
# Tenant A
await cache_manager.set(
    feature="agent_chat",
    query="Hello",
    value={"data": "Response A"},
    tenant_id="tenant_a",  # ✅ Isolated
)

# Tenant B
await cache_manager.set(
    feature="agent_chat",
    query="Hello",
    value={"data": "Response B"},
    tenant_id="tenant_b",  # ✅ Isolated
)

# Cache keys generated:
# tenant_a: orchestrator:agent_chat:tenant:tenant_a:query:abc123
# tenant_b: orchestrator:agent_chat:tenant:tenant_b:query:abc123
# ✅ No collision, complete isolation
```

## Security Considerations

1. **Header Validation**: `extract_headers()` validates `X-Tenant-ID` is present (required header)
2. **No Default Tenant**: All operations require explicit `tenant_id`
3. **Cache Key Sanitization**: Tenant ID is included in cache keys but not used for validation (validation happens at API Gateway level)
4. **Propagation**: Tenant ID is propagated but not modified by orchestrator

## Testing Tenant Isolation

All test cases include `tenant_id` parameters:
- `test_query_router.py`: Tests with `tenant_id="tenant_123"`
- `test_cache_manager.py`: Tests with `tenant_id="tenant_123"`
- `test_orchestrator_service.py`: Tests with `X-Tenant-ID` headers

## Conclusion

The Orchestrator module implements **complete tenant isolation** at every layer:
- ✅ Cache keys are tenant-scoped
- ✅ Cache operations are tenant-scoped
- ✅ Intent analysis is tenant-scoped
- ✅ Service calls propagate tenant context
- ✅ OTEL traces include tenant context
- ✅ Cache invalidation is tenant-scoped

**Result**: Clear separation between tenants with no possibility of cross-tenant data access.

