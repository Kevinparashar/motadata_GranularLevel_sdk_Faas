# MOTADATA - VALIDATION & GUARDRAILS FRAMEWORK

**Ensures LLM outputs are safe, relevant, and compliant with requirements through comprehensive validation and guardrails.**

## When to Use This Component

**✅ Use Validation & Guardrails when:**
- You need to ensure LLM outputs are safe and secure
- You want to validate output formats (JSON, ITSM, etc.)
- You need compliance checking (ITIL, security policies)
- You're building production AI applications
- You need to filter sensitive information (PII, secrets)
- You want to enforce output quality standards

**❌ Don't use Validation & Guardrails when:**
- You're just prototyping or testing
- You don't need output validation
- You're building simple scripts
- Validation overhead is too high for your use case

**Simple Example:**
```python
from src.core.validation import ValidationManager, ValidationLevel

# Create validation manager
validator = ValidationManager(level=ValidationLevel.STRICT)

# Validate output
result = await validator.validate(
    output="AI generated response",
    output_type="text"
)

if result.is_valid:
    print("Output is valid")
else:
    print(f"Validation errors: {result.errors}")
```

**Impact:** Validation can prevent 80-95% of security and compliance issues in LLM outputs.

---

## Overview

The Validation & Guardrails Framework provides comprehensive validation for LLM outputs, ensuring they meet safety, quality, format, and compliance requirements. It supports multiple validation levels and customizable validation rules.

## Purpose and Functionality

The Validation & Guardrails Framework enables:

- **Content Filtering**: Block outputs containing sensitive information or blocked patterns
- **Format Validation**: Validate JSON, ITSM-specific formats, and custom formats
- **Compliance Checking**: Ensure ITIL and security policy compliance
- **Custom Validators**: Support for custom validation rules
- **Validation Levels**: Three levels (STRICT, MODERATE, LENIENT) for different use cases
- **Multi-Tenant Support**: Tenant-specific validation rules

## Connection to Other Components

### Integration with LiteLLM Gateway

The **LiteLLM Gateway** (`src/core/litellm_gateway/`) integrates with the Validation & Guardrails Framework to validate all LLM outputs before returning them to users. The gateway can be configured with validation levels and custom validators.

**Integration Point:** `gateway.validation_manager`

### Integration with RAG System

The **RAG System** (`src/core/rag/`) can use validation to ensure generated responses meet quality and compliance standards.

### Integration with Agno Agent Framework

The **Agno Agent Framework** (`src/core/agno_agent_framework/`) can validate agent responses to ensure they meet requirements before returning to users.

## Validation Levels

The framework supports three validation levels:

### 1. STRICT

Maximum validation with all checks enabled:

```python
from src.core.validation import ValidationManager, ValidationLevel

validator = ValidationManager(level=ValidationLevel.STRICT)
```

**Checks:**
- Content filtering (PII, secrets, blocked patterns)
- Format validation (JSON, ITSM formats)
- Compliance checking (ITIL, security policies)
- Custom validators

### 2. MODERATE

Balanced validation with essential checks:

```python
validator = ValidationManager(level=ValidationLevel.MODERATE)
```

**Checks:**
- Content filtering (essential patterns only)
- Format validation (basic checks)
- Custom validators

### 3. LENIENT

Minimal validation with basic checks:

```python
validator = ValidationManager(level=ValidationLevel.LENIENT)
```

**Checks:**
- Basic content filtering
- Custom validators only

## Key Components

### ValidationManager

Main validation manager:

```python
from src.core.validation import ValidationManager, ValidationLevel

# Create validation manager
validator = ValidationManager(
    level=ValidationLevel.STRICT,
    enable_content_filter=True,
    enable_format_validation=True,
    enable_compliance_check=True
)

# Validate output
result = await validator.validate(
    output="AI generated response",
    output_type="text",
    context={"tenant_id": "tenant_123"}
)

if result.is_valid:
    print("Output is valid")
else:
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
    print(f"Score: {result.score}")
```

### Guardrail

Individual guardrail for validation:

```python
from src.core.validation import Guardrail, ValidationLevel

# Create guardrail
guardrail = Guardrail(
    level=ValidationLevel.STRICT,
    enable_content_filter=True,
    enable_format_validation=True,
    enable_compliance_check=True
)

# Add custom validator
guardrail.add_validator(
    lambda output: (
        "incident_id" in output.lower(),
        "Missing incident_id in response"
    )
)

# Validate
result = await guardrail.validate(
    output="Response text",
    output_type="itsm"
)
```

### ValidationResult

Validation result with details:

```python
from src.core.validation import ValidationResult

result = ValidationResult(
    is_valid=True,
    level=ValidationLevel.STRICT,
    errors=[],
    warnings=["Minor formatting issue"],
    score=0.95,
    metadata={"validation_time_ms": 10.5}
)
```

## Function-Driven API

### Basic Validation

```python
from src.core.validation import ValidationManager, ValidationLevel

# Create validator
validator = ValidationManager(level=ValidationLevel.STRICT)

# Validate output
result = await validator.validate(
    output="AI response",
    output_type="text"
)

# Check result
if result.is_valid:
    # Use output
    pass
else:
    # Handle errors
    for error in result.errors:
        print(f"Error: {error}")
```

### Custom Validators

```python
# Add custom validator
def validate_incident_id(output: str) -> tuple[bool, str]:
    """Validate that output contains incident_id."""
    has_id = "incident_id" in output.lower()
    message = "Missing incident_id" if not has_id else ""
    return has_id, message

validator.add_validator(validate_incident_id)

# Validate
result = await validator.validate(output="Response", output_type="itsm")
```

### Content Filtering

```python
# Add blocked pattern
validator.add_blocked_pattern(r"password\s*[:=]\s*\S+")

# Validate (will block outputs with passwords)
result = await validator.validate(
    output="User password: secret123",
    output_type="text"
)

if not result.is_valid:
    print("Output blocked: contains password")
```

## Usage Examples

### Basic Validation

```python
from src.core.validation import ValidationManager, ValidationLevel

# Create validator
validator = ValidationManager(level=ValidationLevel.STRICT)

# Validate LLM output
result = await validator.validate(
    output="The incident ID is INC-12345 and status is open.",
    output_type="itsm"
)

if result.is_valid:
    print("Output is valid and compliant")
else:
    print(f"Validation failed: {result.errors}")
```

### Integration with Gateway

```python
from src.core.litellm_gateway import LiteLLMGateway, GatewayConfig
from src.core.validation import ValidationManager, ValidationLevel

# Create validator
validator = ValidationManager(level=ValidationLevel.STRICT)

# Configure gateway with validation
gateway = LiteLLMGateway(
    config=GatewayConfig(
        enable_validation=True,
        validation_level=ValidationLevel.STRICT,
        validation_manager=validator
    )
)

# Generate with automatic validation
response = await gateway.generate_async("What is the incident status?")
# Response is automatically validated before returning
```

### Custom Validators

```python
from src.core.validation import ValidationManager, ValidationLevel

validator = ValidationManager(level=ValidationLevel.MODERATE)

# Add custom validator for ITSM format
def validate_itsm_format(output: str) -> tuple[bool, str]:
    """Validate ITSM response format."""
    required_fields = ["incident_id", "status", "priority"]
    missing = [field for field in required_fields if field not in output.lower()]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, ""

validator.add_validator(validate_itsm_format)

# Validate
result = await validator.validate(
    output="Incident ID: INC-123, Status: Open, Priority: High",
    output_type="itsm"
)
```

### Format Validation

```python
# Validate JSON format
result = await validator.validate(
    output='{"key": "value"}',
    output_type="json"
)

# Validate ITSM format
result = await validator.validate(
    output="Incident ID: INC-123, Status: Open",
    output_type="itsm"
)
```

## Configuration

### Validation Levels

```python
from src.core.validation import ValidationManager, ValidationLevel

# STRICT: All checks enabled
validator_strict = ValidationManager(level=ValidationLevel.STRICT)

# MODERATE: Essential checks
validator_moderate = ValidationManager(level=ValidationLevel.MODERATE)

# LENIENT: Basic checks only
validator_lenient = ValidationManager(level=ValidationLevel.LENIENT)
```

### Custom Configuration

```python
validator = ValidationManager(
    level=ValidationLevel.STRICT,
    enable_content_filter=True,
    enable_format_validation=True,
    enable_compliance_check=True
)

# Add blocked patterns
validator.add_blocked_pattern(r"api[_-]?key\s*[:=]\s*\S+")
validator.add_blocked_pattern(r"token\s*[:=]\s*[a-zA-Z0-9]{20,}")

# Add custom validators
validator.add_validator(custom_validator_function)
```

## Error Handling

The Validation & Guardrails Framework implements robust error handling:

- **Graceful Degradation**: Continues operating even if validation fails
- **Error Isolation**: Validation errors don't affect core functionality
- **Detailed Errors**: Provides detailed error messages for debugging
- **Warning System**: Distinguishes between errors and warnings

## Best Practices

1. **Choose Appropriate Level**: Use STRICT for production, MODERATE for development
2. **Custom Validators**: Add custom validators for domain-specific requirements
3. **Blocked Patterns**: Configure blocked patterns for sensitive information
4. **Format Validation**: Enable format validation for structured outputs
5. **Compliance Checking**: Enable compliance checking for regulated industries
6. **Monitor Validation**: Track validation results to improve rules
7. **Tenant-Specific Rules**: Use tenant context for tenant-specific validation

## See Also

- **[LiteLLM Gateway](../litellm_gateway/README.md)** - Gateway integration with validation
- **[RAG System](../rag/README.md)** - RAG validation
- **[Agno Agent Framework](../agno_agent_framework/README.md)** - Agent response validation

