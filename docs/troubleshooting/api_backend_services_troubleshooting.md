# MOTADATA - API BACKEND SERVICES TROUBLESHOOTING

**Troubleshooting guide for diagnosing and resolving common issues with the API Backend Services component.**

## Table of Contents

1. [API Startup Issues](#api-startup-issues)
2. [Request Validation Errors](#request-validation-errors)
3. [Authentication Problems](#authentication-problems)
4. [CORS Issues](#cors-issues)
5. [Endpoint Not Found](#endpoint-not-found)
6. [Response Formatting Problems](#response-formatting-problems)
7. [Performance Issues](#performance-issues)
8. [Error Handling Issues](#error-handling-issues)

## API Startup Issues

### Problem: API fails to start

**Symptoms:**
- Application won't start
- Port already in use
- Import errors
- Configuration errors

**Diagnosis:**
```python
from src.core.api_backend_services import create_api_app

try:
    app = create_api_app()
    print("API app created successfully")
except Exception as e:
    print(f"Error: {e}")
```

**Solutions:**

1. **Check Port Availability:**
   ```python
   import socket

   def is_port_available(port):
       with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
           return s.connect_ex(('localhost', port)) != 0

   if not is_port_available(8000):
       print("Port 8000 is already in use")
   ```

2. **Verify Dependencies:**
   - Check FastAPI is installed
   - Verify uvicorn is installed
   - Check all dependencies

3. **Check Configuration:**
   ```python
   app = create_api_app(
       title="My API",
       version="1.0.0"
   )
   ```

4. **Test Minimal Configuration:**
   ```python
   # Start with minimal config
   app = create_api_app()
   ```

## Request Validation Errors

### Problem: Request validation fails

**Symptoms:**
- 422 Unprocessable Entity errors
- Validation error messages
- Missing required fields
- Type validation errors

**Diagnosis:**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class RequestModel(BaseModel):
    field: str

@app.post("/endpoint")
async def endpoint(request: RequestModel):
    return {"status": "ok"}
```

**Solutions:**

1. **Check Request Model:**
   ```python
   class RequestModel(BaseModel):
       field: str  # Required field
       optional_field: Optional[str] = None  # Optional field
   ```

2. **Validate Request Data:**
   - Check request body format
   - Verify field types
   - Ensure required fields present

3. **Handle Validation Errors:**
   ```python
   from fastapi.exceptions import RequestValidationError

   @app.exception_handler(RequestValidationError)
   async def validation_exception_handler(request, exc):
       return JSONResponse(
           status_code=422,
           content={"detail": exc.errors()}
       )
   ```

4. **Test Request Format:**
   - Use API documentation
   - Test with curl or Postman
   - Verify JSON format

## Authentication Problems

### Problem: Authentication failures

**Symptoms:**
- 401 Unauthorized errors
- Authentication token invalid
- Missing authentication
- Permission denied

**Diagnosis:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/protected")
async def protected_route(token: str = Depends(security)):
    # Validate token
    if not validate_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

**Solutions:**

1. **Verify Token Format:**
   - Check token format
   - Verify token signature
   - Check token expiration

2. **Check Authentication Middleware:**
   ```python
   from fastapi.middleware.auth import AuthMiddleware

   app.add_middleware(AuthMiddleware)
   ```

3. **Validate Credentials:**
   - Check API keys
   - Verify OAuth tokens
   - Validate JWT tokens

4. **Handle Authentication Errors:**
   ```python
   @app.exception_handler(HTTPException)
   async def auth_exception_handler(request, exc):
       if exc.status_code == 401:
           return JSONResponse(
               status_code=401,
               content={"detail": "Authentication required"}
           )
   ```

## CORS Issues

### Problem: CORS errors

**Symptoms:**
- CORS policy errors
- Cross-origin requests blocked
- Preflight request failures
- Access-Control-Allow-Origin errors

**Diagnosis:**
```python
# Check CORS configuration
app = create_api_app(enable_cors=True, cors_origins=["http://localhost:3000"])
```

**Solutions:**

1. **Enable CORS:**
   ```python
   from fastapi.middleware.cors import CORSMiddleware

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Configure CORS Origins:**
   ```python
   app = create_api_app(
       enable_cors=True,
       cors_origins=[
           "http://localhost:3000",
           "https://app.example.com"
       ]
   )
   ```

3. **Handle Preflight Requests:**
   - CORS middleware handles automatically
   - Verify OPTIONS method allowed
   - Check preflight response

4. **Test CORS:**
   - Test from browser
   - Check browser console
   - Verify CORS headers

## Endpoint Not Found

### Problem: 404 Not Found errors

**Symptoms:**
- Endpoint not found
- Route not registered
- URL path incorrect
- Method not allowed

**Diagnosis:**
```python
# Check registered routes
for route in app.routes:
    print(f"{route.methods} {route.path}")
```

**Solutions:**

1. **Verify Route Registration:**
   ```python
   @app.get("/endpoint")
   async def endpoint():
       return {"status": "ok"}
   ```

2. **Check Router Registration:**
   ```python
   from src.core.api_backend_services import create_api_router, register_router

   router = create_api_router(prefix="/api/v1")
   router.get("/endpoint")(endpoint)
   register_router(app, router)
   ```

3. **Verify URL Path:**
   - Check path matches exactly
   - Verify prefix is correct
   - Test with API documentation

4. **Check HTTP Method:**
   - Use correct HTTP method
   - Verify method matches route
   - Test with different methods

## Response Formatting Problems

### Problem: Response format issues

**Symptoms:**
- Incorrect response format
- Missing response fields
- Serialization errors
- Content-Type errors

**Diagnosis:**
```python
from fastapi.responses import JSONResponse

@app.get("/endpoint")
async def endpoint():
    return JSONResponse(
        content={"status": "ok"},
        status_code=200
    )
```

**Solutions:**

1. **Use Response Models:**
   ```python
   from pydantic import BaseModel

   class ResponseModel(BaseModel):
       status: str
       data: dict

   @app.get("/endpoint", response_model=ResponseModel)
   async def endpoint():
       return ResponseModel(status="ok", data={})
   ```

2. **Format Responses Consistently:**
   ```python
   def format_response(data, status="success"):
       return {
           "status": status,
           "data": data,
           "timestamp": datetime.now().isoformat()
       }
   ```

3. **Handle Serialization:**
   - Use Pydantic models
   - Handle custom types
   - Check serialization errors

## Performance Issues

### Problem: API is slow

**Symptoms:**
- High latency
- Slow response times
- Timeout errors
- High resource usage

**Diagnosis:**
```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

**Solutions:**

1. **Enable Caching:**
   ```python
   from fastapi_cache import FastAPICache
   from fastapi_cache.backends.dragonfly import DragonflyBackend

   FastAPICache.init(DragonflyBackend())

   @app.get("/endpoint")
   @cache(expire=60)
   async def endpoint():
       return {"data": "value"}
   ```

2. **Optimize Database Queries:**
   - Use connection pooling
   - Optimize queries
   - Use indexes

3. **Use Async Operations:**
   ```python
   @app.get("/endpoint")
   async def endpoint():
       result = await async_operation()
       return result
   ```

4. **Monitor Performance:**
   - Track response times
   - Monitor resource usage
   - Identify bottlenecks

## Error Handling Issues

### Problem: Errors not handled properly

**Symptoms:**
- Unhandled exceptions
- Generic error messages
- Error details exposed
- Error status codes incorrect

**Diagnosis:**
```python
from fastapi import HTTPException, status

@app.get("/endpoint")
async def endpoint():
    try:
        # Operation
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

**Solutions:**

1. **Create Error Handlers:**
   ```python
   @app.exception_handler(Exception)
   async def global_exception_handler(request, exc):
       return JSONResponse(
           status_code=500,
           content={
               "error": "Internal server error",
               "detail": str(exc) if DEBUG else None
           }
       )
   ```

2. **Use HTTP Exceptions:**
   ```python
   from fastapi import HTTPException, status

   raise HTTPException(
       status_code=status.HTTP_404_NOT_FOUND,
       detail="Resource not found"
   )
   ```

3. **Handle Specific Exceptions:**
   ```python
   @app.exception_handler(ValueError)
   async def value_error_handler(request, exc):
       return JSONResponse(
           status_code=400,
           content={"error": "Invalid value", "detail": str(exc)}
       )
   ```

4. **Log Errors:**
   ```python
   import logging

   logger = logging.getLogger(__name__)

   try:
       # Operation
   except Exception as e:
       logger.error(f"Error: {e}", exc_info=True)
       raise HTTPException(status_code=500, detail="Internal error")
   ```

## Best Practices

1. **Validate All Requests:**
   - Use Pydantic models
   - Validate input data
   - Handle validation errors

2. **Handle Errors Gracefully:**
   - Use exception handlers
   - Return appropriate status codes
   - Don't expose internal details

3. **Monitor Performance:**
   - Track response times
   - Monitor error rates
   - Use observability

4. **Secure APIs:**
   - Implement authentication
   - Use HTTPS
   - Validate inputs

5. **Document APIs:**
   - Use OpenAPI/Swagger
   - Document endpoints
   - Provide examples

## Getting Help

If you continue to experience issues:

1. Check the logs for detailed error messages
2. Review the API Backend Services documentation
3. Verify your configuration matches the examples
4. Test with minimal configuration
5. Check FastAPI and uvicorn documentation
6. Review GitHub issues for known problems

