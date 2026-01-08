"""
Validation and Guardrails Framework

Ensures LLM outputs are safe, relevant, and compliant with ITSM requirements.
"""

from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import re


class ValidationLevel(str, Enum):
    """Validation levels."""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


class ValidationResult(BaseModel):
    """Validation result."""
    is_valid: bool
    level: ValidationLevel
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    score: float = Field(default=1.0, ge=0.0, le=1.0)  # Confidence score
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Guardrail:
    """
    Guardrail for validating LLM outputs.
    
    Ensures outputs meet safety, quality, and compliance requirements.
    """
    
    def __init__(
        self,
        level: ValidationLevel = ValidationLevel.MODERATE,
        enable_content_filter: bool = True,
        enable_format_validation: bool = True,
        enable_compliance_check: bool = True
    ):
        """
        Initialize guardrail.
        
        Args:
            level: Validation level
            enable_content_filter: Enable content filtering
            enable_format_validation: Enable format validation
            enable_compliance_check: Enable compliance checking
        """
        self.level = level
        self.enable_content_filter = enable_content_filter
        self.enable_format_validation = enable_format_validation
        self.enable_compliance_check = enable_compliance_check
        
        # Content filters
        self.blocked_patterns: List[str] = [
            r"password\s*[:=]\s*\S+",  # Passwords
            r"api[_-]?key\s*[:=]\s*\S+",  # API keys
            r"token\s*[:=]\s*[a-zA-Z0-9]{20,}",  # Tokens
            r"secret\s*[:=]\s*\S+",  # Secrets
        ]
        
        # ITSM-specific validations
        self.itsm_required_fields = ["incident_id", "status", "priority"]
        self.itsm_status_values = ["open", "in_progress", "resolved", "closed", "cancelled"]
        self.itsm_priority_values = ["low", "medium", "high", "critical"]
        
        # Custom validators
        self.custom_validators: List[Callable[[str], Tuple[bool, str]]] = []
    
    def validate(
        self,
        output: str,
        context: Optional[Dict[str, Any]] = None,
        output_type: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate LLM output.
        
        Args:
            output: LLM output to validate
            context: Optional context
            output_type: Optional output type (e.g., "incident", "ticket", "response")
        
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        score = 1.0
        
        # Content filtering
        if self.enable_content_filter:
            content_result = self._validate_content(output)
            if not content_result["is_valid"]:
                errors.extend(content_result["errors"])
                score *= 0.5
            warnings.extend(content_result["warnings"])
        
        # Format validation
        if self.enable_format_validation and output_type:
            format_result = self._validate_format(output, output_type)
            if not format_result["is_valid"]:
                errors.extend(format_result["errors"])
                score *= 0.7
            warnings.extend(format_result["warnings"])
        
        # Compliance check
        if self.enable_compliance_check:
            compliance_result = self._validate_compliance(output, context)
            if not compliance_result["is_valid"]:
                errors.extend(compliance_result["errors"])
                score *= 0.6
            warnings.extend(compliance_result["warnings"])
        
        # Custom validators
        for validator in self.custom_validators:
            try:
                is_valid, message = validator(output)
                if not is_valid:
                    if self.level == ValidationLevel.STRICT:
                        errors.append(message)
                        score *= 0.5
                    else:
                        warnings.append(message)
            except Exception:
                # Ignore validator errors
                pass
        
        # Adjust score based on level
        if self.level == ValidationLevel.LENIENT:
            # More lenient - reduce error impact
            score = min(1.0, score + 0.2)
        elif self.level == ValidationLevel.STRICT:
            # More strict - any error reduces score significantly
            if errors:
                score *= 0.3
        
        is_valid = len(errors) == 0 or self.level == ValidationLevel.LENIENT
        
        return ValidationResult(
            is_valid=is_valid,
            level=self.level,
            errors=errors,
            warnings=warnings,
            score=score,
            metadata={
                "output_length": len(output),
                "output_type": output_type,
                "validation_timestamp": datetime.now().isoformat()
            }
        )
    
    def _validate_content(self, output: str) -> Dict[str, Any]:
        """Validate content for safety."""
        errors = []
        warnings = []
        
        # Check for blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                errors.append(f"Blocked pattern detected: {pattern}")
        
        # Check for empty or too short output
        if len(output.strip()) == 0:
            errors.append("Output is empty")
        elif len(output.strip()) < 10:
            warnings.append("Output is very short")
        
        # Check for suspicious content
        suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"onerror\s*=",
            r"eval\s*\(",
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                errors.append(f"Suspicious content detected: {pattern}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_format(self, output: str, output_type: str) -> Dict[str, Any]:
        """Validate output format."""
        errors = []
        warnings = []
        
        if output_type == "incident" or output_type == "ticket":
            # Validate ITSM format
            if "incident_id" not in output.lower() and "ticket_id" not in output.lower():
                warnings.append("Missing incident/ticket ID")
            
            # Check for status
            has_status = any(status in output.lower() for status in self.itsm_status_values)
            if not has_status:
                warnings.append("Missing or invalid status")
        
        # Check for JSON format if expected
        if output_type and "json" in output_type.lower():
            try:
                import json
                json.loads(output)
            except json.JSONDecodeError:
                errors.append("Invalid JSON format")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_compliance(self, output: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate compliance with ITSM requirements."""
        errors = []
        warnings = []
        
        # Check for PII (basic check)
        pii_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b",  # Credit card
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email (context-dependent)
        ]
        
        # Only flag if context indicates PII should not be present
        if context and context.get("allow_pii", False) is False:
            for pattern in pii_patterns:
                if re.search(pattern, output):
                    warnings.append(f"Potential PII detected: {pattern}")
        
        # Check for compliance with ITIL best practices
        if context and context.get("require_itil_compliance", False):
            # Basic ITIL compliance checks
            if "incident" in output.lower() or "problem" in output.lower():
                if "root cause" not in output.lower() and "resolution" not in output.lower():
                    warnings.append("Missing root cause or resolution information")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def add_validator(self, validator: Callable[[str], Tuple[bool, str]]) -> None:
        """
        Add custom validator.
        
        Args:
            validator: Function that takes output and returns (is_valid, message)
        """
        self.custom_validators.append(validator)
    
    def add_blocked_pattern(self, pattern: str) -> None:
        """
        Add blocked pattern.
        
        Args:
            pattern: Regex pattern to block
        """
        self.blocked_patterns.append(pattern)


class ValidationManager:
    """
    Manages validation and guardrails for LLM operations.
    """
    
    def __init__(
        self,
        default_level: ValidationLevel = ValidationLevel.MODERATE
    ):
        """
        Initialize validation manager.
        
        Args:
            default_level: Default validation level
        """
        self.default_level = default_level
        self.guardrails: Dict[str, Guardrail] = {}
        self.default_guardrail = Guardrail(level=default_level)
    
    def get_guardrail(
        self,
        name: Optional[str] = None,
        level: Optional[ValidationLevel] = None
    ) -> Guardrail:
        """
        Get guardrail instance.
        
        Args:
            name: Optional guardrail name
            level: Optional validation level
        
        Returns:
            Guardrail instance
        """
        if name and name in self.guardrails:
            return self.guardrails[name]
        
        if level:
            return Guardrail(level=level)
        
        return self.default_guardrail
    
    def register_guardrail(
        self,
        name: str,
        guardrail: Guardrail
    ) -> None:
        """
        Register a named guardrail.
        
        Args:
            name: Guardrail name
            guardrail: Guardrail instance
        """
        self.guardrails[name] = guardrail
    
    def validate_output(
        self,
        output: str,
        context: Optional[Dict[str, Any]] = None,
        output_type: Optional[str] = None,
        guardrail_name: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate output using appropriate guardrail.
        
        Args:
            output: Output to validate
            context: Optional context
            output_type: Optional output type
            guardrail_name: Optional guardrail name
        
        Returns:
            ValidationResult
        """
        guardrail = self.get_guardrail(name=guardrail_name)
        return guardrail.validate(output, context, output_type)


