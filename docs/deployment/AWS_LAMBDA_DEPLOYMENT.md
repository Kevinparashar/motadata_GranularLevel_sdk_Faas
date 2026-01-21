# AWS Lambda Deployment Guide for FaaS Services

## Overview

This guide explains how to deploy FaaS services as AWS Lambda functions.

## Prerequisites

- AWS CLI configured
- Serverless Framework or AWS SAM
- AWS Lambda runtime Python 3.12
- API Gateway (for HTTP endpoints)

## Lambda Function Structure

### Function Handler

Each service needs a Lambda handler:

```python
# lambda_handler.py
from src.faas.services.agent_service import create_agent_service

# Create service instance (cached across invocations)
_service = None

def handler(event, context):
    """Lambda handler for Agent Service."""
    global _service
    
    if _service is None:
        _service = create_agent_service(
            service_name="agent-service",
            config_overrides={
                "database_url": os.environ.get("DATABASE_URL"),
                "gateway_service_url": os.environ.get("GATEWAY_SERVICE_URL"),
            }
        )
    
    # Convert Lambda event to FastAPI request
    from mangum import Mangum
    app = Mangum(_service.app)
    return app(event, context)
```

## Serverless Framework Deployment

### serverless.yml

```yaml
service: motadata-ai-services

provider:
  name: aws
  runtime: python3.12
  region: us-east-1
  memorySize: 512
  timeout: 30
  environment:
    DATABASE_URL: ${env:DATABASE_URL}
    REDIS_URL: ${env:REDIS_URL}
    GATEWAY_SERVICE_URL: ${env:GATEWAY_SERVICE_URL}
    CACHE_SERVICE_URL: ${env:CACHE_SERVICE_URL}
    RAG_SERVICE_URL: ${env:RAG_SERVICE_URL}
    ENABLE_NATS: "false"
    ENABLE_OTEL: "false"

functions:
  agent-service:
    handler: lambda_handlers.agent.handler
    events:
      - http:
          path: /api/v1/agents/{proxy+}
          method: ANY
          cors: true
    environment:
      SERVICE_NAME: agent-service
      SERVICE_PORT: 8080

  rag-service:
    handler: lambda_handlers.rag.handler
    events:
      - http:
          path: /api/v1/rag/{proxy+}
          method: ANY
          cors: true
    environment:
      SERVICE_NAME: rag-service
      SERVICE_PORT: 8082

  gateway-service:
    handler: lambda_handlers.gateway.handler
    events:
      - http:
          path: /api/v1/gateway/{proxy+}
          method: ANY
          cors: true
    environment:
      SERVICE_NAME: gateway-service
      SERVICE_PORT: 8080
    memorySize: 1024
    timeout: 60

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
    layer: true
```

## AWS SAM Deployment

### template.yaml

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  AgentServiceFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/faas/services/agent_service/
      Handler: lambda_handler.handler
      Runtime: python3.12
      MemorySize: 512
      Timeout: 30
      Environment:
        Variables:
          SERVICE_NAME: agent-service
          DATABASE_URL: !Ref DatabaseUrl
          GATEWAY_SERVICE_URL: !GetAtt GatewayServiceApi.ApiGatewayRestApiId
      Events:
        AgentApi:
          Type: Api
          Properties:
            Path: /api/v1/agents/{proxy+}
            Method: ANY

  AgentServiceApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      Cors:
        AllowMethods: "'*'"
        AllowHeaders: "'*'"
        AllowOrigin: "'*'"
```

## Deployment Steps

### Using Serverless Framework

```bash
# Install Serverless Framework
npm install -g serverless

# Install plugin
npm install --save-dev serverless-python-requirements

# Deploy
serverless deploy

# Deploy specific function
serverless deploy function -f agent-service
```

### Using AWS SAM

```bash
# Build
sam build

# Deploy
sam deploy --guided

# Deploy with parameters
sam deploy --parameter-overrides DatabaseUrl=postgresql://...
```

## Lambda Layers

For shared dependencies, use Lambda Layers:

```bash
# Create layer
mkdir -p python/lib/python3.12/site-packages
pip install -r requirements.txt -t python/lib/python3.12/site-packages/
zip -r layer.zip python/

# Upload layer
aws lambda publish-layer-version \
  --layer-name motadata-ai-sdk \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.12
```

## API Gateway Integration

### API Gateway Configuration

```yaml
# API Gateway routes to Lambda functions
Routes:
  - Path: /api/v1/agents/{proxy+}
    Method: ANY
    Integration: Lambda
    LambdaFunction: agent-service-function
    
  - Path: /api/v1/rag/{proxy+}
    Method: ANY
    Integration: Lambda
    LambdaFunction: rag-service-function
    
  - Path: /api/v1/gateway/{proxy+}
    Method: ANY
    Integration: Lambda
    LambdaFunction: gateway-service-function
```

## Environment Variables

Set environment variables in Lambda configuration:

```bash
# Via AWS CLI
aws lambda update-function-configuration \
  --function-name agent-service \
  --environment Variables={
    SERVICE_NAME=agent-service,
    DATABASE_URL=postgresql://...,
    GATEWAY_SERVICE_URL=https://...
  }
```

## Cold Start Optimization

1. **Use Lambda Layers** for shared dependencies
2. **Keep Functions Warm** (provisioned concurrency)
3. **Optimize Package Size** (remove unused dependencies)
4. **Use Connection Pooling** (for database connections)

## Monitoring

### CloudWatch Metrics

- Invocations
- Duration
- Errors
- Throttles

### CloudWatch Logs

All Lambda logs are automatically sent to CloudWatch Logs.

## Cost Optimization

1. **Right-size Memory** (balance memory and CPU)
2. **Use Provisioned Concurrency** (for predictable workloads)
3. **Optimize Timeout** (set appropriate timeouts)
4. **Use Reserved Concurrency** (prevent cost overruns)

## Limitations

- **15-minute timeout** maximum
- **10GB memory** maximum
- **512MB /tmp storage** maximum
- **Cold starts** can add latency

## Best Practices

1. **Keep Functions Stateless** (use external state storage)
2. **Optimize Package Size** (minimize dependencies)
3. **Use Environment Variables** (for configuration)
4. **Enable X-Ray Tracing** (for observability)
5. **Set Appropriate Timeouts** (prevent unnecessary costs)

