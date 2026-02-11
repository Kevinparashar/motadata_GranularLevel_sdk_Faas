"""
Unit Tests for Guardrails and Validation Framework

Tests validation and guardrails for LLM outputs.
"""

import asyncio

import pytest

from src.core.validation.guardrails import (
    Guardrail,
    ValidationLevel,
    ValidationManager,
    ValidationResult,
)


class TestValidationLevel:
    """Test ValidationLevel enum."""

    def test_validation_level_values(self):
        """Test ValidationLevel enum values."""
        assert ValidationLevel.STRICT == "strict"
        assert ValidationLevel.MODERATE == "moderate"
        assert ValidationLevel.LENIENT == "lenient"


class TestValidationResult:
    """Test ValidationResult model."""

    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        result = ValidationResult(
            is_valid=True,
            level=ValidationLevel.MODERATE,
            errors=[],
            warnings=[],
            score=1.0,
        )
        assert result.is_valid is True
        assert result.level == ValidationLevel.MODERATE
        assert result.errors == []
        assert result.warnings == []
        assert abs(result.score - 1.0) < 0.001

    def test_validation_result_with_errors(self):
        """Test ValidationResult with errors."""
        result = ValidationResult(
            is_valid=False,
            level=ValidationLevel.STRICT,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
            score=0.5,
        )
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert abs(result.score - 0.5) < 0.001

    def test_validation_result_defaults(self):
        """Test ValidationResult with defaults."""
        result = ValidationResult(is_valid=True, level=ValidationLevel.MODERATE)
        assert result.errors == []
        assert result.warnings == []
        assert abs(result.score - 1.0) < 0.001
        assert result.metadata == {}


class TestGuardrail:
    """Test Guardrail class."""

    def test_guardrail_initialization_defaults(self):
        """Test Guardrail initialization with defaults."""
        guardrail = Guardrail()
        assert guardrail.level == ValidationLevel.MODERATE
        assert guardrail.enable_content_filter is True
        assert guardrail.enable_format_validation is True
        assert guardrail.enable_compliance_check is True
        assert len(guardrail.blocked_patterns) > 0
        assert len(guardrail.custom_validators) == 0

    def test_guardrail_initialization_custom(self):
        """Test Guardrail initialization with custom settings."""
        guardrail = Guardrail(
            level=ValidationLevel.STRICT,
            enable_content_filter=False,
            enable_format_validation=False,
            enable_compliance_check=False,
        )
        assert guardrail.level == ValidationLevel.STRICT
        assert guardrail.enable_content_filter is False
        assert guardrail.enable_format_validation is False
        assert guardrail.enable_compliance_check is False

    @pytest.mark.asyncio
    async def test_validate_success(self):
        """Test validate with valid output."""
        guardrail = Guardrail()
        result = await guardrail.validate("This is a valid output")
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.score > 0

    @pytest.mark.asyncio
    async def test_validate_with_blocked_pattern(self):
        """Test validate with blocked pattern."""
        guardrail = Guardrail()
        result = await guardrail.validate("password: secret123")
        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_empty_output(self):
        """Test validate with empty output."""
        guardrail = Guardrail()
        result = await guardrail.validate("")
        assert result.is_valid is False
        assert "empty" in result.errors[0].lower()

    @pytest.mark.asyncio
    async def test_validate_short_output(self):
        """Test validate with very short output."""
        guardrail = Guardrail()
        result = await guardrail.validate("short")
        assert len(result.warnings) > 0
        assert "short" in result.warnings[0].lower()

    @pytest.mark.asyncio
    async def test_validate_with_suspicious_content(self):
        """Test validate with suspicious content."""
        guardrail = Guardrail()
        result = await guardrail.validate("<script>alert('xss')</script>")
        assert result.is_valid is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_content_filter_disabled(self):
        """Test validate with content filter disabled."""
        guardrail = Guardrail(enable_content_filter=False)
        result = await guardrail.validate("password: secret123")
        # Should not catch blocked patterns when filter is disabled
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_format_json_valid(self):
        """Test validate with valid JSON format."""
        guardrail = Guardrail()
        result = await guardrail.validate('{"key": "value"}', output_type="json")
        assert result.is_valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_format_json_invalid(self):
        """Test validate with invalid JSON format."""
        guardrail = Guardrail()
        result = await guardrail.validate('{"key": "value"', output_type="json")
        assert result.is_valid is False
        assert "JSON" in result.errors[0]

    @pytest.mark.asyncio
    async def test_validate_format_incident(self):
        """Test validate with incident format."""
        guardrail = Guardrail()
        result = await guardrail.validate(
            "incident_id: INC-123, status: open, priority: high", output_type="incident"
        )
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_format_incident_missing_id(self):
        """Test validate with incident format missing ID."""
        guardrail = Guardrail()
        result = await guardrail.validate("status: open", output_type="incident")
        assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_validate_format_validation_disabled(self):
        """Test validate with format validation disabled."""
        guardrail = Guardrail(enable_format_validation=False)
        result = await guardrail.validate('{"invalid": json', output_type="json")
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_compliance_pii_detected(self):
        """Test validate with PII detection."""
        guardrail = Guardrail()
        context = {"allow_pii": False}
        result = await guardrail.validate("Email: test@example.com", context=context)
        assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_validate_compliance_pii_allowed(self):
        """Test validate with PII allowed."""
        guardrail = Guardrail()
        context = {"allow_pii": True}
        result = await guardrail.validate("Email: test@example.com", context=context)
        # Should not warn about PII when allowed
        pii_warnings = [w for w in result.warnings if "PII" in w]
        assert len(pii_warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_compliance_itil_required(self):
        """Test validate with ITIL compliance required."""
        guardrail = Guardrail()
        context = {"require_itil_compliance": True}
        result = await guardrail.validate("This is an incident", context=context)
        assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_validate_compliance_check_disabled(self):
        """Test validate with compliance check disabled."""
        guardrail = Guardrail(enable_compliance_check=False)
        context = {"require_itil_compliance": True}
        result = await guardrail.validate("This is an incident", context=context)
        # Should not check compliance when disabled
        itil_warnings = [w for w in result.warnings if "root cause" in w.lower() or "resolution" in w.lower()]
        assert len(itil_warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_strict_level(self):
        """Test validate with strict level."""
        guardrail = Guardrail(level=ValidationLevel.STRICT)
        result = await guardrail.validate("password: secret123")
        assert result.is_valid is False
        assert result.score < 1.0

    @pytest.mark.asyncio
    async def test_validate_lenient_level(self):
        """Test validate with lenient level."""
        guardrail = Guardrail(level=ValidationLevel.LENIENT)
        result = await guardrail.validate("password: secret123")
        # Lenient level may still mark as valid even with errors
        assert result.score >= 0.0

    @pytest.mark.asyncio
    async def test_validate_with_custom_validator_sync(self):
        """Test validate with custom sync validator."""
        guardrail = Guardrail()

        def custom_validator(output: str) -> tuple[bool, str]:
            return len(output) > 10, "Output too short"

        guardrail.add_validator(custom_validator)
        result = await guardrail.validate("short")
        assert len(result.warnings) > 0 or len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_with_custom_validator_async(self):
        """Test validate with custom async validator."""
        guardrail = Guardrail()

        async def custom_validator(output: str) -> tuple[bool, str]:
            await asyncio.sleep(0.01)
            return len(output) > 10, "Output too short"

        guardrail.add_validator(custom_validator)  # type: ignore[arg-type]
        result = await guardrail.validate("short")
        assert len(result.warnings) > 0 or len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_with_custom_validator_dict_result(self):
        """Test validate with custom validator returning dict."""
        guardrail = Guardrail()

        def custom_validator(output: str) -> dict:
            return {"is_valid": len(output) > 10, "message": "Output too short"}

        guardrail.add_validator(custom_validator)  # type: ignore[arg-type]
        result = await guardrail.validate("short")
        assert len(result.warnings) > 0 or len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_with_custom_validator_bool_result(self):
        """Test validate with custom validator returning bool."""
        guardrail = Guardrail()

        def custom_validator(output: str) -> bool:
            return len(output) > 10

        guardrail.add_validator(custom_validator)  # type: ignore[arg-type]
        result = await guardrail.validate("short")
        assert len(result.warnings) > 0 or len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_with_custom_validator_error(self):
        """Test validate with custom validator that raises error."""
        guardrail = Guardrail()

        def custom_validator(output: str):
            raise ValueError("Validator error")

        guardrail.add_validator(custom_validator)
        # Should not raise, but handle gracefully
        result = await guardrail.validate("test output")
        assert result is not None

    def test_add_validator(self):
        """Test add_validator method."""
        guardrail = Guardrail()
        assert len(guardrail.custom_validators) == 0

        def validator(output: str) -> tuple[bool, str]:
            return True, "OK"

        guardrail.add_validator(validator)
        assert len(guardrail.custom_validators) == 1

    def test_add_blocked_pattern(self):
        """Test add_blocked_pattern method."""
        guardrail = Guardrail()
        initial_count = len(guardrail.blocked_patterns)
        guardrail.add_blocked_pattern(r"test_pattern")
        assert len(guardrail.blocked_patterns) == initial_count + 1
        assert r"test_pattern" in guardrail.blocked_patterns

    @pytest.mark.asyncio
    async def test_apply_content_validation_disabled(self):
        """Test _apply_content_validation when disabled."""
        guardrail = Guardrail(enable_content_filter=False)
        errors = []
        warnings = []
        score = 1.0
        result_score = await guardrail._apply_content_validation("password: secret", errors, warnings, score)
        assert abs(result_score - 1.0) < 0.001
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_apply_format_validation_disabled(self):
        """Test _apply_format_validation when disabled."""
        guardrail = Guardrail(enable_format_validation=False)
        errors = []
        warnings = []
        score = 1.0
        result_score = await guardrail._apply_format_validation("test", None, errors, warnings, score)
        assert abs(result_score - 1.0) < 0.001

    @pytest.mark.asyncio
    async def test_apply_format_validation_no_output_type(self):
        """Test _apply_format_validation with no output_type."""
        guardrail = Guardrail()
        errors = []
        warnings = []
        score = 1.0
        result_score = await guardrail._apply_format_validation("test", None, errors, warnings, score)
        assert abs(result_score - 1.0) < 0.001

    @pytest.mark.asyncio
    async def test_apply_compliance_validation_disabled(self):
        """Test _apply_compliance_validation when disabled."""
        guardrail = Guardrail(enable_compliance_check=False)
        errors = []
        warnings = []
        score = 1.0
        result_score = await guardrail._apply_compliance_validation("test", None, errors, warnings, score)
        assert abs(result_score - 1.0) < 0.001

    @pytest.mark.asyncio
    async def test_execute_validator_sync(self):
        """Test _execute_validator with sync validator."""
        guardrail = Guardrail()

        def sync_validator(output: str) -> str:
            return "result"

        result = await guardrail._execute_validator(sync_validator, "test")
        assert result == "result"

    @pytest.mark.asyncio
    async def test_execute_validator_async(self):
        """Test _execute_validator with async validator."""
        guardrail = Guardrail()

        async def async_validator(output: str) -> str:
            await asyncio.sleep(0.01)
            return "result"

        result = await guardrail._execute_validator(async_validator, "test")
        assert result == "result"

    def test_parse_validator_result_tuple(self):
        """Test _parse_validator_result with tuple."""
        guardrail = Guardrail()
        is_valid, message = guardrail._parse_validator_result((True, "OK"))
        assert is_valid is True
        assert message == "OK"

    def test_parse_validator_result_dict(self):
        """Test _parse_validator_result with dict."""
        guardrail = Guardrail()
        is_valid, message = guardrail._parse_validator_result({"is_valid": False, "message": "Error"})
        assert is_valid is False
        assert message == "Error"

    def test_parse_validator_result_bool(self):
        """Test _parse_validator_result with bool."""
        guardrail = Guardrail()
        is_valid, message = guardrail._parse_validator_result(True)
        assert is_valid is True
        assert "passed" in message.lower()

    def test_apply_validation_result_strict(self):
        """Test _apply_validation_result with strict level."""
        guardrail = Guardrail(level=ValidationLevel.STRICT)
        errors = []
        warnings = []
        score = 1.0
        result_score = guardrail._apply_validation_result("Error message", errors, warnings, score)
        assert len(errors) == 1
        assert result_score < 1.0

    def test_apply_validation_result_moderate(self):
        """Test _apply_validation_result with moderate level."""
        guardrail = Guardrail(level=ValidationLevel.MODERATE)
        errors = []
        warnings = []
        score = 1.0
        result_score = guardrail._apply_validation_result("Warning message", errors, warnings, score)
        assert len(warnings) == 1
        assert abs(result_score - 1.0) < 0.001

    def test_adjust_score_by_level_lenient(self):
        """Test _adjust_score_by_level with lenient level."""
        guardrail = Guardrail(level=ValidationLevel.LENIENT)
        score = guardrail._adjust_score_by_level(0.5, [])
        assert score >= 0.5

    def test_adjust_score_by_level_strict_with_errors(self):
        """Test _adjust_score_by_level with strict level and errors."""
        guardrail = Guardrail(level=ValidationLevel.STRICT)
        score = guardrail._adjust_score_by_level(0.5, ["Error 1"])
        assert score < 0.5

    def test_adjust_score_by_level_strict_no_errors(self):
        """Test _adjust_score_by_level with strict level and no errors."""
        guardrail = Guardrail(level=ValidationLevel.STRICT)
        score = guardrail._adjust_score_by_level(0.5, [])
        assert abs(score - 0.5) < 0.001

    @pytest.mark.asyncio
    async def test_check_pii_patterns_ssn(self):
        """Test _check_pii_patterns with SSN."""
        guardrail = Guardrail()
        warnings = await guardrail._check_pii_patterns("SSN: 123-45-6789")
        assert len(warnings) > 0

    @pytest.mark.asyncio
    async def test_check_pii_patterns_email(self):
        """Test _check_pii_patterns with email."""
        guardrail = Guardrail()
        warnings = await guardrail._check_pii_patterns("Contact: user@example.com")
        assert len(warnings) > 0

    @pytest.mark.asyncio
    async def test_check_pii_patterns_credit_card(self):
        """Test _check_pii_patterns with credit card."""
        guardrail = Guardrail()
        warnings = await guardrail._check_pii_patterns("Card: 1234 5678 9012 3456")
        assert len(warnings) > 0

    def test_check_itil_compliance_missing_info(self):
        """Test _check_itil_compliance with missing information."""
        guardrail = Guardrail()
        warnings = guardrail._check_itil_compliance("This is an incident")
        assert len(warnings) > 0

    def test_check_itil_compliance_with_resolution(self):
        """Test _check_itil_compliance with resolution."""
        guardrail = Guardrail()
        warnings = guardrail._check_itil_compliance("This is an incident. Resolution: fixed")
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_result_metadata(self):
        """Test validate result includes metadata."""
        guardrail = Guardrail()
        result = await guardrail.validate("Test output", output_type="text")
        assert "output_length" in result.metadata
        assert "output_type" in result.metadata
        assert "validation_timestamp" in result.metadata
        assert result.metadata["output_type"] == "text"


class TestValidationManager:
    """Test ValidationManager class."""

    def test_validation_manager_initialization(self):
        """Test ValidationManager initialization."""
        manager = ValidationManager()
        assert manager.default_level == ValidationLevel.MODERATE
        assert len(manager.guardrails) == 0
        assert manager.default_guardrail is not None

    def test_validation_manager_custom_level(self):
        """Test ValidationManager with custom level."""
        manager = ValidationManager(default_level=ValidationLevel.STRICT)
        assert manager.default_level == ValidationLevel.STRICT

    def test_get_guardrail_default(self):
        """Test get_guardrail with default."""
        manager = ValidationManager()
        guardrail = manager.get_guardrail()
        assert guardrail.level == ValidationLevel.MODERATE

    def test_get_guardrail_by_name(self):
        """Test get_guardrail by name."""
        manager = ValidationManager()
        custom_guardrail = Guardrail(level=ValidationLevel.STRICT)
        manager.register_guardrail("strict", custom_guardrail)
        guardrail = manager.get_guardrail(name="strict")
        assert guardrail.level == ValidationLevel.STRICT

    def test_get_guardrail_by_level(self):
        """Test get_guardrail by level."""
        manager = ValidationManager()
        guardrail = manager.get_guardrail(level=ValidationLevel.LENIENT)
        assert guardrail.level == ValidationLevel.LENIENT

    def test_register_guardrail(self):
        """Test register_guardrail."""
        manager = ValidationManager()
        custom_guardrail = Guardrail(level=ValidationLevel.STRICT)
        manager.register_guardrail("custom", custom_guardrail)
        assert "custom" in manager.guardrails
        assert manager.guardrails["custom"] == custom_guardrail

    @pytest.mark.asyncio
    async def test_validate_output_default(self):
        """Test validate_output with default guardrail."""
        manager = ValidationManager()
        result = await manager.validate_output("Test output")
        assert result.is_valid is True
        assert result.level == ValidationLevel.MODERATE

    @pytest.mark.asyncio
    async def test_validate_output_with_guardrail_name(self):
        """Test validate_output with guardrail name."""
        manager = ValidationManager()
        custom_guardrail = Guardrail(level=ValidationLevel.STRICT)
        manager.register_guardrail("strict", custom_guardrail)
        result = await manager.validate_output("Test output", guardrail_name="strict")
        assert result.level == ValidationLevel.STRICT

    @pytest.mark.asyncio
    async def test_validate_output_with_context(self):
        """Test validate_output with context."""
        manager = ValidationManager()
        context = {"allow_pii": False}
        result = await manager.validate_output("Email: test@example.com", context=context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_validate_output_with_output_type(self):
        """Test validate_output with output_type."""
        manager = ValidationManager()
        result = await manager.validate_output('{"key": "value"}', output_type="json")
        assert result.is_valid is True

