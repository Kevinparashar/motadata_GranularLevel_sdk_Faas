# MOTADATA - REST/FASTAPI ARCHITECTURE

**Architecture guide explaining where REST/FastAPI is needed in the SDK architecture and what responsibilities it handles.**

## Overview

This document explains where REST/FastAPI is needed in the SDK architecture and what responsibilities it handles, given that authentication and authorization are handled before requests reach the AI layer (via JWT at AWS API Gateway or similar).

---

## Architecture Layers & Where REST/FastAPI Fits

### Layer 1: Edge Layer (AWS API Gateway)
- **What**: HTTP endpoint, JWT validation, routing
- **Technology**: AWS API Gateway
- **REST/FastAPI**: <span style="color: red; font-size: 1.5em; font-weight: bold;">❌ **NOT NEEDED HERE**</span>
- **Responsibilities**:
  - Validates JWT tokens
  - Extracts `tenant_id`, `user_id` from JWT
  - Routes requests to backend services
  - Handles CORS, rate limiting (edge level)
  - Request/response transformation (basic)

### Layer 2: Application/Service Layer (Your Backend)
- **What**: Business logic, request processing, SDK orchestration
- **Technology**: FastAPI/REST API (or Lambda, or your service)
- **REST/FastAPI**: ✅ **NEEDED HERE**
- **Responsibilities**:
  - Receives authenticated requests from AWS API Gateway
  - Extracts `tenant_id`, `user_id` from headers/JWT claims
  - Validates request payloads (business rules)
  - Orchestrates SDK components (Agent + RAG + Gateway)
  - Handles request/response transformation
  - Manages error handling and status codes
  - Returns structured responses

### Layer 3: SDK Layer (Library Components)
- **What**: AI capabilities (Agent, RAG, Gateway, etc.)
- **Technology**: Python library components
- **REST/FastAPI**: <span style="color: red; font-size: 1.5em; font-weight: bold;">❌ **NOT NEEDED HERE**</span>
- **Responsibilities**:
  - Execute AI operations
  - Handle caching, database, LLM calls
  - Internal component communication

### Layer 4: Infrastructure Layer
- **What**: NATS, OTEL, CODEC, Database, Cache
- **Technology**: External services
- **REST/FastAPI**: <span style="color: red; font-size: 1.5em; font-weight: bold;">❌ **NOT NEEDED HERE**</span>

---

## Where You Need REST/FastAPI

### Location: Application/Service Layer (Between AWS API Gateway and SDK)

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: AWS API Gateway (Edge)                        │
│  - JWT Validation                                        │
│  - Routing                                               │
│  - <span style="color: red; font-size: 1.3em; font-weight: bold;">NO REST/FASTAPI HERE</span>                                 │
└─────────────────────────────────────────────────────────┘
                    ↓ (HTTP Request)
┌─────────────────────────────────────────────────────────┐
│  Layer 2: FastAPI/REST API (Application Layer)          │
│  ✅ THIS IS WHERE YOU NEED REST/FASTAPI                 │
│  - Receives authenticated requests                      │
│  - Business logic orchestration                         │
│  - SDK component coordination                           │
└─────────────────────────────────────────────────────────┘
                    ↓ (Python function calls)
┌─────────────────────────────────────────────────────────┐
│  Layer 3: SDK Components (Library)                      │
│  - Agent Framework                                      │
│  - RAG System                                           │
│  - LiteLLM Gateway                                      │
│  - <span style="color: red; font-size: 1.3em; font-weight: bold;">NO REST/FASTAPI HERE</span>                                 │
└─────────────────────────────────────────────────────────┘
```

---

## What REST/FastAPI Does in Your Architecture

### 1. HTTP Request Handling
- Receives HTTP requests from AWS API Gateway
- Parses request body, query parameters, headers
- Extracts `tenant_id`, `user_id` from JWT claims (passed by API Gateway)
- Validates HTTP method, content-type, payload structure

### 2. Request Validation & Business Logic
- Validates business rules (e.g., incident fields, document formats)
- Transforms external API format to internal SDK format
- Applies tenant-specific rules and permissions
- Handles request deduplication, idempotency

### 3. SDK Component Orchestration
- Creates SDK component instances (Agent, RAG, Gateway)
- Passes `tenant_id` to SDK components
- Coordinates multiple SDK components for complex workflows
- Example: RAG retrieval → Agent processing → LLM generation

### 4. Error Handling & Response Formatting
- Catches SDK exceptions and converts to HTTP status codes
- Formats error responses consistently
- Handles timeouts, retries, circuit breakers
- Returns structured JSON responses

### 5. Integration with NATS/OTEL/CODEC
- Publishes events to NATS after processing
- Starts OTEL traces for requests
- Encodes/decodes messages using CODEC
- Propagates trace context to SDK components

---

## Detailed Flow Example: Incident Triage Use Case

### Step-by-Step with REST/FastAPI Role:

```
1. Client sends HTTP POST to AWS API Gateway
   POST /api/v1/incidents/triage
   Headers: Authorization: Bearer <JWT>
   Body: { "incident_id": "123", "description": "..." }

2. AWS API Gateway (Edge Layer)
   ✅ Validates JWT
   ✅ Extracts tenant_id: "tenant_abc", user_id: "user_123"
   ✅ Routes to backend service
   → Forwards request with headers:
      X-Tenant-ID: tenant_abc
      X-User-ID: user_123
      Authorization: Bearer <JWT>

3. FastAPI/REST API (Application Layer) ← YOU NEED IT HERE
   ✅ Receives authenticated request
   ✅ Extracts tenant_id from X-Tenant-ID header
   ✅ Validates request body structure
   ✅ Starts OTEL trace
   ✅ Decodes request using CODEC (if needed)
   
   ✅ Orchestrates SDK components:
      - Creates Agent instance with tenant_id
      - Calls RAG.retrieve() to get relevant docs
      - Calls Agent.execute_task() with incident data
      - Agent internally uses LiteLLM Gateway
   
   ✅ Handles response:
      - Formats AI analysis result
      - Encodes response using CODEC
      - Publishes to NATS (ai.incident.triage.response.{tenant_id})
      - Ends OTEL trace
      - Returns HTTP 200 with JSON response

4. SDK Components (Library Layer)
   - Agent Framework executes task
   - RAG System retrieves documents
   - LiteLLM Gateway calls LLM API
   - All components use tenant_id for isolation

5. Response flows back:
   SDK → FastAPI → AWS API Gateway → Client
```

---

## What REST/FastAPI Does NOT Do (Because Auth is Handled Before)

### ❌ Does NOT Do:
- **JWT validation** (AWS API Gateway does this)
- **User authentication** (handled before)
- **Authorization checks** (handled before, but can do additional business-level checks)
- **Edge-level rate limiting** (AWS API Gateway does this)

### ✅ Does Do:
- Business logic validation
- SDK component orchestration
- Request/response transformation
- Error handling and formatting
- NATS/OTEL/CODEC integration
- Tenant context propagation

---

## Alternative Architectures (Where REST/FastAPI Might Not Be Needed)

### Option 1: Pure Message-Driven (No HTTP)
```
External Service (with JWT auth)
    ↓
NATS Message (ai.incident.triage.request.{tenant_id})
    ↓
SDK Components (subscribed to NATS)
    - Direct component calls
    - <span style="color: red; font-size: 1.3em; font-weight: bold;">NO REST/FASTAPI NEEDED</span>
    - Components handle messages directly
```
<span style="color: red; font-size: 1.3em; font-weight: bold;">**NO REST/FASTAPI NEEDED**</span> — pure messaging architecture.

### Option 2: AWS Lambda (Serverless)
```
AWS API Gateway (JWT auth)
    ↓
AWS Lambda Function
    - Imports SDK as library
    - Direct component calls
    - Returns response
```
<span style="color: red; font-size: 1.3em; font-weight: bold;">**NO FASTAPI NEEDED**</span> — Lambda handles HTTP layer.

### Option 3: Your Own Service (Not SDK's FastAPI)
```
AWS API Gateway (JWT auth)
    ↓
Your Custom FastAPI Service
    - Imports SDK as library
    - Your own business logic
    - Uses SDK components
```
**You build FastAPI**, not the SDK — SDK remains pure library.

---

## REST/FastAPI Responsibilities Breakdown

### Request Processing Flow:

| Step | Responsibility | Technology |
|------|---------------|------------|
| **1. Receive Request** | Parse HTTP request from API Gateway | FastAPI request handler |
| **2. Extract Context** | Get `tenant_id`, `user_id` from headers | FastAPI header extraction |
| **3. Validate Input** | Business rule validation, payload structure | Pydantic models, custom validators |
| **4. Start Observability** | Initialize OTEL trace, extract trace context | OTEL integration |
| **5. Decode Message** | CODEC decode if message-driven | CODEC integration |
| **6. Orchestrate SDK** | Create and coordinate SDK components | SDK component calls |
| **7. Process Response** | Format SDK results, encode if needed | Response transformation |
| **8. Publish Events** | Publish to NATS topics | NATS integration |
| **9. End Observability** | Complete OTEL trace | OTEL integration |
| **10. Return Response** | HTTP response with proper status code | FastAPI response |

---

## Code Example: FastAPI Handler Structure

### Example FastAPI Endpoint (Theoretical):

```python
from fastapi import FastAPI, Header, HTTPException
from motadata_ai_sdk import create_agent, create_rag_system
from motadata_ai_sdk.integrations import NATSClient, OTELTracer, CodecSerializer

app = FastAPI()

@app.post("/api/v1/incidents/triage")
async def triage_incident(
    request: IncidentTriageRequest,
    x_tenant_id: str = Header(...),  # From API Gateway
    x_user_id: str = Header(...),     # From API Gateway
    authorization: str = Header(...)   # JWT (already validated)
):
    # 1. Extract context (already authenticated)
    tenant_id = x_tenant_id
    user_id = x_user_id
    
    # 2. Start OTEL trace
    tracer = OTELTracer()
    with tracer.start_span("incident_triage") as span:
        span.set_attribute("tenant_id", tenant_id)
        span.set_attribute("incident_id", request.incident_id)
        
        try:
            # 3. Decode request (if using CODEC)
            codec = CodecSerializer()
            decoded_data = codec.decode(request.body) if codec_needed else request.dict()
            
            # 4. Orchestrate SDK components
            agent = create_agent(tenant_id=tenant_id)
            rag = create_rag_system(tenant_id=tenant_id)
            
            # 5. Execute workflow
            relevant_docs = await rag.retrieve(decoded_data["description"])
            result = await agent.execute_task(
                task="triage_incident",
                context={"incident": decoded_data, "docs": relevant_docs}
            )
            
            # 6. Encode response (if using CODEC)
            encoded_response = codec.encode(result) if codec_needed else result
            
            # 7. Publish to NATS
            nats = NATSClient()
            await nats.publish(
                subject=f"ai.incident.triage.response.{tenant_id}",
                payload=encoded_response
            )
            
            # 8. Return HTTP response
            return {
                "status": "success",
                "incident_id": request.incident_id,
                "analysis": result
            }
            
        except Exception as e:
            # 9. Error handling
            span.record_exception(e)
            raise HTTPException(status_code=500, detail=str(e))
```

---

## Key Responsibilities Summary

### REST/FastAPI Handles:

1. **HTTP Layer**
   - Receives HTTP requests
   - Parses request data
   - Returns HTTP responses

2. **Business Logic**
   - Request validation
   - Business rule enforcement
   - Workflow orchestration

3. **SDK Coordination**
   - Creates SDK component instances
   - Coordinates component calls
   - Manages component lifecycle

4. **Integration Points**
   - NATS message publishing
   - OTEL trace management
   - CODEC encoding/decoding

5. **Error Management**
   - Exception handling
   - Error response formatting
   - Status code mapping

6. **Context Propagation**
   - Tenant ID extraction
   - User context passing
   - Trace context propagation

### REST/FastAPI Does NOT Handle:

1. **Authentication** (JWT validation) — AWS API Gateway
2. **Authorization** (user permissions) — Handled before
3. **Edge Routing** — AWS API Gateway
4. **Edge Rate Limiting** — AWS API Gateway
5. **AI Operations** — SDK components handle this

---

## Deployment Models

### Model 1: SDK Provides FastAPI Component
- SDK includes FastAPI service
- Deploy SDK's FastAPI as container/service
- AWS API Gateway routes to SDK's FastAPI
- **Pros**: Ready-to-use, consistent API
- **Cons**: Less flexibility

### Model 2: Application Builds FastAPI
- SDK is pure library (no FastAPI)
- Application imports SDK and builds own FastAPI
- AWS API Gateway routes to application's FastAPI
- **Pros**: Full control, flexibility
- **Cons**: More application code needed

### Model 3: Hybrid Approach
- SDK provides optional FastAPI component
- Applications can use SDK's FastAPI or build their own
- **Pros**: Best of both worlds
- **Cons**: More code to maintain

---

## Summary

### Where REST/FastAPI is Needed:
- **Location**: Application/Service Layer (between AWS API Gateway and SDK components)
- **Deployment**: ECS/Fargate container, EC2 instance, or serverless function

### What REST/FastAPI Does:
1. **HTTP request handling** (receives from API Gateway)
2. **Request validation** (business rules, payload structure)
3. **SDK orchestration** (creates and coordinates SDK components)
4. **Response formatting** (converts SDK results to HTTP responses)
5. **Integration coordination** (NATS publishing, OTEL tracing, CODEC encoding)
6. **Error handling** (catches exceptions, returns proper HTTP status codes)
7. **Tenant context propagation** (passes `tenant_id` to SDK components)

### What REST/FastAPI Does NOT Do:
- JWT validation (AWS API Gateway handles this)
- User authentication (handled before)
- Edge routing (AWS API Gateway handles this)

### Key Takeaway:
REST/FastAPI is needed in the **Application Layer** to:
- Bridge HTTP (from AWS API Gateway) to Python SDK components
- Orchestrate multiple SDK components for complex workflows
- Handle business logic and validation
- Format responses and handle errors
- Integrate with NATS/OTEL/CODEC

Without it, you'd need to handle HTTP-to-Python bridging elsewhere (Lambda, your own service, or pure messaging).

---

*This document explains the theoretical architecture. Implementation details may vary based on specific deployment models and requirements.*

