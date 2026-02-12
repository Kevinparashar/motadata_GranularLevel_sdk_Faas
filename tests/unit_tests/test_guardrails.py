"""
Unit Tests for Validation and Guardrails Framework

Tests guardrails, validation levels, and validation manager.
"""

import asyncio

import pytest

from src.core.validation.guardrails import (
    Guardrail,
    ValidationLevel,
    ValidationResult,
    ValidationManager,
)


class TestValidationLevel:
    """Test ValidationLevel enum."""

    def test_validation_level_values(self):
        """Test ValidationLevel enum values."""
        assert ValidationLevel.STRICT == "strict"
        assert ValidationLevel.MODERATE == "moderate"
        assert ValidationLevel.LENIENT == "lenient"


class TestValidationResult:
    """Test ValidationResult class."""

    def test_validation_result_defaults(self):
        """Test ValidationResult with default values."""
        result = ValidationResult(is_valid=True, level=ValidationLevel.MODERATE)
        assert result.is_valid is True
        assert result.level == ValidationLevel.MODERATE
        assert result.errors == []
        assert result.warnings == []
        assert abs(result.score - 1.0) < 0.001
        assert result.metadata == {}

    def test_validation_result_custom(self):
        """Test ValidationResult with custom values."""
        result = ValidationResult(
            is_valid=False,
            level=ValidationLevel.STRICT,
            errors=["Error 1"],
            warnings=["Warning 1"],
            score=0.5,
            metadata={"key": "value"},
        )
        assert result.is_valid is False
        assert result.level == ValidationLevel.STRICT
        assert result.errors == ["Error 1"]
        assert result.warnings == ["Warning 1"]
        assert abs(result.score - 0.5) < 0.001
        assert result.metadata == {"key": "value"}

    def test_validation_result_score_bounds(self):
        """Test ValidationResult score bounds."""
        # Score should be between 0.0 and 1.0
        result = ValidationResult(is_valid=True, level=ValidationLevel.MODERATE, score=0.0)
        assert abs(result.score - 0.0) < 0.001

        result = ValidationResult(is_valid=True, level=ValidationLevel.MODERATE, score=1.0)
        assert abs(result.score - 1.0) < 0.001


class TestGuardrail:
    """Test Guardrail class."""

    def test_guardrail_init_default(self):
        """Test Guardrail initialization with defaults."""
        guardrail = Guardrail()
        assert guardrail.level == ValidationLevel.MODERATE
        assert guardrail.enable_content_filter is True
        assert guardrail.enable_format_validation is True
        assert guardrail.enable_compliance_check is True
        assert len(guardrail.blocked_patterns) > 0
        assert guardrail.custom_validators == []

    def test_guardrail_init_custom(self):
        """Test Guardrail initialization with custom values."""
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
        result = await guardrail.validate("This is a valid output message.")
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert abs(result.score - 1.0) < 0.001

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
        result = await guardrail.validate("Short")
        assert result.is_valid is True  # Short output is a warning, not error
        assert len(result.warnings) > 0
        assert "short" in result.warnings[0].lower()

    @pytest.mark.asyncio
    async def test_validate_blocked_pattern_password(self):
        """Test validate with blocked password pattern."""
        guardrail = Guardrail()
        result = await guardrail.validate("password: secret123")
        assert result.is_valid is False
        assert any("password" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_blocked_pattern_api_key(self):
        """Test validate with blocked API key pattern."""
        guardrail = Guardrail()
        result = await guardrail.validate("api_key: abc123xyz")
        assert result.is_valid is False
        assert any("api" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_blocked_pattern_token(self):
        """Test validate with blocked token pattern."""
        guardrail = Guardrail()
        result = await guardrail.validate("token: abcdefghijklmnopqrstuvwxyz123456")
        assert result.is_valid is False
        assert any("token" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_suspicious_script(self):
        """Test validate with suspicious script pattern."""
        guardrail = Guardrail()
        result = await guardrail.validate("Here is some <script>alert('xss')</script> content")
        assert result.is_valid is False
        assert any("suspicious" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_suspicious_javascript(self):
        """Test validate with suspicious javascript pattern."""
        guardrail = Guardrail()
        result = await guardrail.validate("Link: javascript:alert('xss')")
        assert result.is_valid is False
        assert any("suspicious" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_with_output_type_incident(self):
        """Test validate with incident output type."""
        guardrail = Guardrail()
        result = await guardrail.validate(
            "Incident ID: INC-001, Status: open, Priority: high", output_type="incident"
        )
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_with_output_type_incident_missing_id(self):
        """Test validate with incident output type missing ID."""
        guardrail = Guardrail()
        result = await guardrail.validate("Status: open, Priority: high", output_type="incident")
        # Missing ID is a warning, not an error
        assert any("missing" in warning.lower() for warning in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_with_output_type_json_valid(self):
        """Test validate with valid JSON output type."""
        guardrail = Guardrail()
        result = await guardrail.validate('{"key": "value"}', output_type="json")
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_with_output_type_json_invalid(self):
        """Test validate with invalid JSON output type."""
        guardrail = Guardrail()
        result = await guardrail.validate('{"key": "value"', output_type="json")
        assert result.is_valid is False
        assert any("json" in error.lower() for error in result.errors)

    @pytest.mark.asyncio
    async def test_validate_with_context_pii_not_allowed(self):
        """Test validate with PII not allowed in context."""
        guardrail = Guardrail()
        result = await guardrail.validate(
            "Contact: user@example.com", context={"allow_pii": False}
        )
        # PII detection is a warning, not an error
        assert any("pii" in warning.lower() for warning in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_with_context_pii_allowed(self):
        """Test validate with PII allowed in context."""
        guardrail = Guardrail()
        result = await guardrail.validate(
            "Contact: user@example.com", context={"allow_pii": True}
        )
        # Should not have PII warnings when allowed
        assert not any("pii" in warning.lower() for warning in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_with_context_itil_compliance_required(self):
        """Test validate with ITIL compliance required."""
        guardrail = Guardrail()
        result = await guardrail.validate(
            "This is an incident report.", context={"require_itil_compliance": True}
        )
        # Should have ITIL compliance warnings
        assert any("root cause" in warning.lower() or "resolution" in warning.lower() for warning in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_with_context_itil_compliance_not_required(self):
        """Test validate with ITIL compliance not required."""
        guardrail = Guardrail()
        result = await guardrail.validate(
            "This is an incident report.", context={"require_itil_compliance": False}
        )
        # Should not have ITIL compliance warnings when not required
        assert not any("root cause" in warning.lower() or "resolution" in warning.lower() for warning in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_level_strict(self):
        """Test validate with strict level."""
        guardrail = Guardrail(level=ValidationLevel.STRICT)
        result = await guardrail.validate("password: secret")
        assert result.is_valid is False
        assert result.level == ValidationLevel.STRICT
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_validate_level_lenient(self):
        """Test validate with lenient level."""
        guardrail = Guardrail(level=ValidationLevel.LENIENT)
        result = await guardrail.validate("password: secret")
        # Lenient level may allow some errors
        assert result.level == ValidationLevel.LENIENT

    @pytest.mark.asyncio
    async def test_validate_content_filter_disabled(self):
        """Test validate with content filter disabled."""
        guardrail = Guardrail(enable_content_filter=False)
        result = await guardrail.validate("password: secret")
        # Should not detect blocked patterns when filter is disabled
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_format_validation_disabled(self):
        """Test validate with format validation disabled."""
        guardrail = Guardrail(enable_format_validation=False)
        result = await guardrail.validate('{"invalid": json', output_type="json")
        # Should not validate format when disabled
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_compliance_check_disabled(self):
        """Test validate with compliance check disabled."""
        guardrail = Guardrail(enable_compliance_check=False)
        result = await guardrail.validate(
            "Incident report", context={"require_itil_compliance": True}
        )
        # Should not check compliance when disabled
        assert not any("root cause" in warning.lower() for warning in result.warnings)

    @pytest.mark.asyncio
    async def test_validate_with_custom_validator_sync(self):
        """Test validate with custom sync validator."""
        guardrail = Guardrail()

        def custom_validator(output: str) -> tuple[bool, str]:
            if "custom_check" in output:
                return True, "Validation passed"
            return False, "Custom validation failed"

        guardrail.add_validator(custom_validator)
        result = await guardrail.validate("This has custom_check in it")
        # Custom validator should pass
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_with_custom_validator_async(self):
        """Test validate with custom async validator."""
        guardrail = Guardrail()

        async def custom_validator(output: str) -> tuple[bool, str]:
            await asyncio.sleep(0)
            if "async_check" in output:
                return True, "Validation passed"
            return False, "Custom validation failed"

        # Type ignore: add_validator accepts any callable, not just Tuple return type
        guardrail.add_validator(custom_validator)  # type: ignore[arg-type]
        result = await guardrail.validate("This has async_check in it")
        # Custom validator should pass
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_with_custom_validator_dict_result(self):
        """Test validate with custom validator returning dict."""
        guardrail = Guardrail()

        def custom_validator(output: str) -> dict:
            return {"is_valid": True, "message": "Valid"}

        # Type ignore: add_validator accepts any callable, not just Tuple return type
        guardrail.add_validator(custom_validator)  # type: ignore[arg-type]
        result = await guardrail.validate("Test output")
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_with_custom_validator_bool_result(self):
        """Test validate with custom validator returning bool."""
        guardrail = Guardrail()

        def custom_validator(output: str) -> bool:
            return "valid" in output

        # Type ignore: add_validator accepts any callable, not just Tuple return type
        guardrail.add_validator(custom_validator)  # type: ignore[arg-type]
        result = await guardrail.validate("This is valid")
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_with_custom_validator_error(self):
        """Test validate with custom validator that raises error."""
        guardrail = Guardrail()

        def custom_validator(output: str):
            raise ValueError("Validator error")

        guardrail.add_validator(custom_validator)
        # Should not raise, but log and continue
        result = await guardrail.validate("Test output")
        assert isinstance(result, ValidationResult)

    @pytest.mark.asyncio
    async def test_validate_metadata(self):
        """Test validate includes metadata."""
        guardrail = Guardrail()
        result = await guardrail.validate("Test output", output_type="test")
        assert "output_length" in result.metadata
        assert result.metadata["output_type"] == "test"
        assert "validation_timestamp" in result.metadata

    def test_add_validator(self):
        """Test add_validator method."""
        guardrail = Guardrail()
        assert len(guardrail.custom_validators) == 0

        def validator(output: str) -> tuple[bool, str]:
            return True, "Valid"

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
        score = await guardrail._apply_content_validation("password: secret", errors, warnings, 1.0)
        assert abs(score - 1.0) < 0.001
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_apply_format_validation_disabled(self):
        """Test _apply_format_validation when disabled."""
        guardrail = Guardrail(enable_format_validation=False)
        errors = []
        warnings = []
        score = await guardrail._apply_format_validation("invalid json", "json", errors, warnings, 1.0)
        assert abs(score - 1.0) < 0.001
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_apply_format_validation_no_output_type(self):
        """Test _apply_format_validation when no output_type."""
        guardrail = Guardrail()
        errors = []
        warnings = []
        score = await guardrail._apply_format_validation("output", None, errors, warnings, 1.0)
        assert abs(score - 1.0) < 0.001

    @pytest.mark.asyncio
    async def test_apply_compliance_validation_disabled(self):
        """Test _apply_compliance_validation when disabled."""
        guardrail = Guardrail(enable_compliance_check=False)
        errors = []
        warnings = []
        score = await guardrail._apply_compliance_validation("output", {}, errors, warnings, 1.0)
        assert abs(score - 1.0) < 0.001

    @pytest.mark.asyncio
    async def test_apply_custom_validators_empty(self):
        """Test _apply_custom_validators with no validators."""
        guardrail = Guardrail()
        errors = []
        warnings = []
        score = await guardrail._apply_custom_validators("output", errors, warnings, 1.0)
        assert abs(score - 1.0) < 0.001

    @pytest.mark.asyncio
    async def test_apply_custom_validators_strict_level(self):
        """Test _apply_custom_validators with strict level."""
        guardrail = Guardrail(level=ValidationLevel.STRICT)

        def validator(output: str) -> tuple[bool, str]:
            return False, "Custom error"

        guardrail.add_validator(validator)
        errors = []
        warnings = []
        await guardrail._apply_custom_validators("output", errors, warnings, 1.0)
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_apply_custom_validators_moderate_level(self):
        """Test _apply_custom_validators with moderate level."""
        guardrail = Guardrail(level=ValidationLevel.MODERATE)

        def validator(output: str) -> tuple[bool, str]:
            return False, "Custom warning"

        guardrail.add_validator(validator)
        errors = []
        warnings = []
        await guardrail._apply_custom_validators("output", errors, warnings, 1.0)
        assert len(warnings) > 0
        assert len(errors) == 0

    def test_parse_validator_result_tuple(self):
        """Test _parse_validator_result with tuple."""
        guardrail = Guardrail()
        is_valid, message = guardrail._parse_validator_result((True, "Success"))
        assert is_valid is True
        assert message == "Success"

    def test_parse_validator_result_dict(self):
        """Test _parse_validator_result with dict."""
        guardrail = Guardrail()
        is_valid, message = guardrail._parse_validator_result({"is_valid": False, "message": "Failed"})
        assert is_valid is False
        assert message == "Failed"

    def test_parse_validator_result_bool(self):
        """Test _parse_validator_result with bool."""
        guardrail = Guardrail()
        is_valid, message = guardrail._parse_validator_result(True)
        assert is_valid is True
        assert "passed" in message.lower()

    def test_parse_validator_result_false_bool(self):
        """Test _parse_validator_result with False bool."""
        guardrail = Guardrail()
        is_valid, message = guardrail._parse_validator_result(False)
        assert is_valid is False
        assert "failed" in message.lower()

    def test_adjust_score_by_level_lenient(self):
        """Test _adjust_score_by_level with lenient level."""
        guardrail = Guardrail(level=ValidationLevel.LENIENT)
        score = guardrail._adjust_score_by_level(0.5, [])
        assert abs(score - 0.7) < 0.001

    def test_adjust_score_by_level_strict_with_errors(self):
        """Test _adjust_score_by_level with strict level and errors."""
        guardrail = Guardrail(level=ValidationLevel.STRICT)
        score = guardrail._adjust_score_by_level(0.5, ["Error 1"])
        assert abs(score - 0.15) < 0.001

    def test_adjust_score_by_level_strict_no_errors(self):
        """Test _adjust_score_by_level with strict level and no errors."""
        guardrail = Guardrail(level=ValidationLevel.STRICT)
        score = guardrail._adjust_score_by_level(0.5, [])
        assert abs(score - 0.5) < 0.001  # No adjustment

    def test_adjust_score_by_level_moderate(self):
        """Test _adjust_score_by_level with moderate level."""
        guardrail = Guardrail(level=ValidationLevel.MODERATE)
        score = guardrail._adjust_score_by_level(0.5, ["Error 1"])
        assert abs(score - 0.5) < 0.001  # No adjustment for moderate

    @pytest.mark.asyncio
    async def test_validate_lenient_with_errors(self):
        """Test validate with lenient level allows errors."""
        guardrail = Guardrail(level=ValidationLevel.LENIENT)
        result = await guardrail.validate("password: secret")
        # Lenient level should still mark as valid even with errors
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_check_pii_patterns_email(self):
        """Test _check_pii_patterns detects email."""
        guardrail = Guardrail()
        warnings = await guardrail._check_pii_patterns("Contact: user@example.com")
        assert len(warnings) > 0
        assert any("pii" in warning.lower() for warning in warnings)

    @pytest.mark.asyncio
    async def test_check_pii_patterns_ssn(self):
        """Test _check_pii_patterns detects SSN."""
        guardrail = Guardrail()
        warnings = await guardrail._check_pii_patterns("SSN: 123-45-6789")
        assert len(warnings) > 0

    @pytest.mark.asyncio
    async def test_check_pii_patterns_credit_card(self):
        """Test _check_pii_patterns detects credit card."""
        guardrail = Guardrail()
        warnings = await guardrail._check_pii_patterns("Card: 1234 5678 9012 3456")
        assert len(warnings) > 0

    def test_check_itil_compliance_missing_root_cause(self):
        """Test _check_itil_compliance detects missing root cause."""
        guardrail = Guardrail()
        warnings = guardrail._check_itil_compliance("This is an incident report.")
        assert len(warnings) > 0
        assert any("root cause" in warning.lower() or "resolution" in warning.lower() for warning in warnings)

    def test_check_itil_compliance_with_root_cause(self):
        """Test _check_itil_compliance with root cause present."""
        guardrail = Guardrail()
        warnings = guardrail._check_itil_compliance("Incident report. Root cause: Network issue.")
        assert len(warnings) == 0

    def test_check_itil_compliance_with_resolution(self):
        """Test _check_itil_compliance with resolution present."""
        guardrail = Guardrail()
        warnings = guardrail._check_itil_compliance("Incident report. Resolution: Fixed network.")
        assert len(warnings) == 0

    def test_check_itil_compliance_no_incident(self):
        """Test _check_itil_compliance with no incident/problem."""
        guardrail = Guardrail()
        warnings = guardrail._check_itil_compliance("Regular text without any issues.")
        assert len(warnings) == 0


class TestValidationManager:
    """Test ValidationManager class."""

    def test_validation_manager_init(self):
        """Test ValidationManager initialization."""
        manager = ValidationManager()
        assert manager.default_level == ValidationLevel.MODERATE
        assert manager.guardrails == {}
        assert isinstance(manager.default_guardrail, Guardrail)

    def test_validation_manager_init_custom_level(self):
        """Test ValidationManager initialization with custom level."""
        manager = ValidationManager(default_level=ValidationLevel.STRICT)
        assert manager.default_level == ValidationLevel.STRICT

    def test_get_guardrail_default(self):
        """Test get_guardrail returns default."""
        manager = ValidationManager()
        guardrail = manager.get_guardrail()
        assert guardrail is manager.default_guardrail

    def test_get_guardrail_by_name(self):
        """Test get_guardrail by name."""
        manager = ValidationManager()
        custom_guardrail = Guardrail(level=ValidationLevel.STRICT)
        manager.register_guardrail("strict", custom_guardrail)
        guardrail = manager.get_guardrail(name="strict")
        assert guardrail is custom_guardrail

    def test_get_guardrail_by_level(self):
        """Test get_guardrail by level."""
        manager = ValidationManager()
        guardrail = manager.get_guardrail(level=ValidationLevel.LENIENT)
        assert guardrail.level == ValidationLevel.LENIENT
        assert guardrail is not manager.default_guardrail

    def test_get_guardrail_name_not_found(self):
        """Test get_guardrail with name not found."""
        manager = ValidationManager()
        guardrail = manager.get_guardrail(name="nonexistent")
        # Should return default when name not found
        assert guardrail is manager.default_guardrail

    def test_register_guardrail(self):
        """Test register_guardrail method."""
        manager = ValidationManager()
        custom_guardrail = Guardrail(level=ValidationLevel.STRICT)
        manager.register_guardrail("custom", custom_guardrail)
        assert "custom" in manager.guardrails
        assert manager.guardrails["custom"] is custom_guardrail

    @pytest.mark.asyncio
    async def test_validate_output_default(self):
        """Test validate_output with default guardrail."""
        manager = ValidationManager()
        result = await manager.validate_output("Valid output")
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_output_with_guardrail_name(self):
        """Test validate_output with guardrail name."""
        manager = ValidationManager()
        custom_guardrail = Guardrail(level=ValidationLevel.STRICT)
        manager.register_guardrail("strict", custom_guardrail)
        result = await manager.validate_output("Valid output", guardrail_name="strict")
        assert result.level == ValidationLevel.STRICT

    @pytest.mark.asyncio
    async def test_validate_output_with_context(self):
        """Test validate_output with context."""
        manager = ValidationManager()
        result = await manager.validate_output(
            "Output", context={"allow_pii": False, "require_itil_compliance": True}
        )
        assert isinstance(result, ValidationResult)

    @pytest.mark.asyncio
    async def test_validate_output_with_output_type(self):
        """Test validate_output with output type."""
        manager = ValidationManager()
        result = await manager.validate_output('{"key": "value"}', output_type="json")
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True

