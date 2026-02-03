"""
Validation and Guardrails Framework

Ensures LLM outputs are safe, relevant, and compliant with ITSM requirements.
"""


import re
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


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
        enable_compliance_check: bool = True,
    ):
        """
        Initialize guardrail.
        
        Args:
            level (ValidationLevel): Input parameter for this operation.
            enable_content_filter (bool): Flag to enable or disable content filter.
            enable_format_validation (bool): Flag to enable or disable format validation.
            enable_compliance_check (bool): Flag to enable or disable compliance check.
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

    def _apply_content_validation(
        self, output: str, errors: List[str], warnings: List[str], score: float
    ) -> float:
        """
        Apply content filtering validation.
        
        Args:
            output (str): Input parameter for this operation.
            errors (List[str]): Input parameter for this operation.
            warnings (List[str]): Input parameter for this operation.
            score (float): Input parameter for this operation.
        
        Returns:
            float: Result of the operation.
        """
        if not self.enable_content_filter:
            return score

        content_result = self._validate_content(output)
        if not content_result["is_valid"]:
            errors.extend(content_result["errors"])
            score *= 0.5
        warnings.extend(content_result["warnings"])
        return score

    def _apply_format_validation(
        self, output: str, output_type: Optional[str], errors: List[str], warnings: List[str], score: float
    ) -> float:
        """
        Apply format validation.
        
        Args:
            output (str): Input parameter for this operation.
            output_type (Optional[str]): Input parameter for this operation.
            errors (List[str]): Input parameter for this operation.
            warnings (List[str]): Input parameter for this operation.
            score (float): Input parameter for this operation.
        
        Returns:
            float: Result of the operation.
        """
        if not self.enable_format_validation or not output_type:
            return score

        format_result = self._validate_format(output, output_type)
        if not format_result["is_valid"]:
            errors.extend(format_result["errors"])
            score *= 0.7
        warnings.extend(format_result["warnings"])
        return score

    def _apply_compliance_validation(
        self, output: str, context: Optional[Dict[str, Any]], errors: List[str], warnings: List[str], score: float
    ) -> float:
        """
        Apply compliance check validation.
        
        Args:
            output (str): Input parameter for this operation.
            context (Optional[Dict[str, Any]]): Input parameter for this operation.
            errors (List[str]): Input parameter for this operation.
            warnings (List[str]): Input parameter for this operation.
            score (float): Input parameter for this operation.
        
        Returns:
            float: Result of the operation.
        """
        if not self.enable_compliance_check:
            return score

        compliance_result = self._validate_compliance(output, context)
        if not compliance_result["is_valid"]:
            errors.extend(compliance_result["errors"])
            score *= 0.6
        warnings.extend(compliance_result["warnings"])
        return score

    def _apply_custom_validators(
        self, output: str, errors: List[str], warnings: List[str], score: float
    ) -> float:
        """
        Apply custom validators.
        
        Args:
            output (str): Input parameter for this operation.
            errors (List[str]): Input parameter for this operation.
            warnings (List[str]): Input parameter for this operation.
            score (float): Input parameter for this operation.
        
        Returns:
            float: Result of the operation.
        """
        import logging
        logger = logging.getLogger(__name__)

        for validator in self.custom_validators:
            try:
                is_valid, message = validator(output)
                if not is_valid:
                    if self.level == ValidationLevel.STRICT:
                        errors.append(message)
                        score *= 0.5
                    else:
                        warnings.append(message)
            except (AttributeError, TypeError, ValueError) as e:
                logger.debug(f"Validator error ignored: {e}")
        return score

    def _adjust_score_by_level(self, score: float, errors: List[str]) -> float:
        """
        Adjust validation score based on validation level.
        
        Args:
            score (float): Input parameter for this operation.
            errors (List[str]): Input parameter for this operation.
        
        Returns:
            float: Result of the operation.
        """
        if self.level == ValidationLevel.LENIENT:
            return min(1.0, score + 0.2)
        elif self.level == ValidationLevel.STRICT and errors:
            return score * 0.3
        return score

    def validate(
        self,
        output: str,
        context: Optional[Dict[str, Any]] = None,
        output_type: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate LLM output.
        
        Args:
            output (str): Input parameter for this operation.
            context (Optional[Dict[str, Any]]): Input parameter for this operation.
            output_type (Optional[str]): Input parameter for this operation.
        
        Returns:
            ValidationResult: Result of the operation.
        """
        errors: List[str] = []
        warnings: List[str] = []
        score = 1.0

        score = self._apply_content_validation(output, errors, warnings, score)
        score = self._apply_format_validation(output, output_type, errors, warnings, score)
        score = self._apply_compliance_validation(output, context, errors, warnings, score)
        score = self._apply_custom_validators(output, errors, warnings, score)
        score = self._adjust_score_by_level(score, errors)

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
                "validation_timestamp": datetime.now().isoformat(),
            },
        )

    def _validate_content(self, output: str) -> Dict[str, Any]:
        """
        Validate content for safety.
        
        Args:
            output (str): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
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

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _validate_format(self, output: str, output_type: str) -> Dict[str, Any]:
        """
        Validate output format.
        
        Args:
            output (str): Input parameter for this operation.
            output_type (str): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
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

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _check_pii_patterns(self, output: str) -> List[str]:
        """
        Check for PII patterns in output.
        
        Args:
            output (str): Input parameter for this operation.
        
        Returns:
            List[str]: List result of the operation.
        """
        warnings = []
        pii_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b",  # Credit card
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        ]
        
        for pattern in pii_patterns:
            if re.search(pattern, output):
                warnings.append(f"Potential PII detected: {pattern}")
        
        return warnings

    def _check_itil_compliance(self, output: str) -> List[str]:
        """
        Check ITIL compliance requirements.
        
        Args:
            output (str): Input parameter for this operation.
        
        Returns:
            List[str]: List result of the operation.
        """
        warnings = []
        output_lower = output.lower()
        
        if "incident" in output_lower or "problem" in output_lower:
            if "root cause" not in output_lower and "resolution" not in output_lower:
                warnings.append("Missing root cause or resolution information")
        
        return warnings

    def _validate_compliance(
        self, output: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate compliance with ITSM requirements.
        
        Args:
            output (str): Input parameter for this operation.
            context (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Check for PII if not allowed
        if context and context.get("allow_pii", False) is False:
            warnings.extend(self._check_pii_patterns(output))

        # Check for ITIL compliance if required
        if context and context.get("require_itil_compliance", False):
            warnings.extend(self._check_itil_compliance(output))

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def add_validator(self, validator: Callable[[str], Tuple[bool, str]]) -> None:
        """
        Add custom validator.
        
        Args:
            validator (Callable[[str], Tuple[bool, str]]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        self.custom_validators.append(validator)

    def add_blocked_pattern(self, pattern: str) -> None:
        """
        Add blocked pattern.
        
        Args:
            pattern (str): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        self.blocked_patterns.append(pattern)


class ValidationManager:
    """
    Manages validation and guardrails for LLM operations.
    """

    def __init__(self, default_level: ValidationLevel = ValidationLevel.MODERATE):
        """
        Initialize validation manager.
        
        Args:
            default_level (ValidationLevel): Input parameter for this operation.
        """
        self.default_level = default_level
        self.guardrails: Dict[str, Guardrail] = {}
        self.default_guardrail = Guardrail(level=default_level)

    def get_guardrail(
        self, name: Optional[str] = None, level: Optional[ValidationLevel] = None
    ) -> Guardrail:
        """
        Get guardrail instance.
        
        Args:
            name (Optional[str]): Name value.
            level (Optional[ValidationLevel]): Input parameter for this operation.
        
        Returns:
            Guardrail: Result of the operation.
        """
        if name and name in self.guardrails:
            return self.guardrails[name]

        if level:
            return Guardrail(level=level)

        return self.default_guardrail

    def register_guardrail(self, name: str, guardrail: Guardrail) -> None:
        """
        Register a named guardrail.
        
        Args:
            name (str): Name value.
            guardrail (Guardrail): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        self.guardrails[name] = guardrail

    def validate_output(
        self,
        output: str,
        context: Optional[Dict[str, Any]] = None,
        output_type: Optional[str] = None,
        guardrail_name: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate output using appropriate guardrail.
        
        Args:
            output (str): Input parameter for this operation.
            context (Optional[Dict[str, Any]]): Input parameter for this operation.
            output_type (Optional[str]): Input parameter for this operation.
            guardrail_name (Optional[str]): Input parameter for this operation.
        
        Returns:
            ValidationResult: Result of the operation.
        """
        guardrail = self.get_guardrail(name=guardrail_name)
        return guardrail.validate(output, context, output_type)
