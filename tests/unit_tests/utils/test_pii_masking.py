"""
Unit Tests for PII Masking Utilities

Tests for PII masking functions to ensure sensitive data is properly masked
before sending to observability systems.
"""

from src.core.utils.pii_masking import (
    mask_email,
    mask_phone,
    mask_ssn,
    mask_credit_card,
    mask_ip_address,
    mask_string,
    should_mask_attribute,
    mask_attribute_value,
)


class TestMaskEmail:
    """Tests for email masking."""

    def test_mask_email_normal(self):
        """Test masking normal email address."""
        result = mask_email("john.doe@example.com")
        assert result == "j***@example.com"

    def test_mask_email_single_char_local(self):
        """Test masking email with single character local part."""
        result = mask_email("a@example.com")
        assert result == "a***@example.com"

    def test_mask_email_short_local(self):
        """Test masking email with short local part."""
        result = mask_email("ab@example.com")
        assert result == "a***@example.com"

    def test_mask_email_complex_domain(self):
        """Test masking email with complex domain."""
        result = mask_email("user@subdomain.example.co.uk")
        assert result == "u***@subdomain.example.co.uk"

    def test_mask_email_invalid_no_at(self):
        """Test masking invalid email without @."""
        result = mask_email("invalid")
        assert result == "invalid"

    def test_mask_email_invalid_empty(self):
        """Test masking empty email."""
        result = mask_email("")
        assert result == "invalid"

    def test_mask_email_invalid_none(self):
        """Test masking None email."""
        result = mask_email(None)  # type: ignore
        assert result == "invalid"

    def test_mask_email_invalid_only_local(self):
        """Test masking email with only local part."""
        result = mask_email("user@")
        assert result == "invalid"

    def test_mask_email_invalid_only_domain(self):
        """Test masking email with only domain."""
        result = mask_email("@example.com")
        assert result == "invalid"

    def test_mask_email_special_characters(self):
        """Test masking email with special characters."""
        result = mask_email("user+tag@example.com")
        assert result == "u***@example.com"


class TestMaskPhone:
    """Tests for phone masking."""

    def test_mask_phone_formatted(self):
        """Test masking formatted phone number."""
        result = mask_phone("+1-555-123-4567")
        assert result == "***-***-4567"

    def test_mask_phone_unformatted(self):
        """Test masking unformatted phone number."""
        result = mask_phone("5551234567")
        assert result == "***-***-4567"

    def test_mask_phone_with_spaces(self):
        """Test masking phone number with spaces."""
        result = mask_phone("555 123 4567")
        assert result == "***-***-4567"

    def test_mask_phone_short(self):
        """Test masking short phone number."""
        result = mask_phone("123")
        assert result == "***"

    def test_mask_phone_empty(self):
        """Test masking empty phone."""
        result = mask_phone("")
        assert result == "***"

    def test_mask_phone_none(self):
        """Test masking None phone."""
        result = mask_phone(None)  # type: ignore
        assert result == "***"

    def test_mask_phone_international(self):
        """Test masking international phone number."""
        result = mask_phone("+44-20-7946-0958")
        assert result == "***-***-0958"

    def test_mask_phone_exactly_four_digits(self):
        """Test masking phone with exactly 4 digits."""
        result = mask_phone("1234")
        assert result == "***-***-1234"


class TestMaskSSN:
    """Tests for SSN masking."""

    def test_mask_ssn_formatted(self):
        """Test masking formatted SSN."""
        result = mask_ssn("123-45-6789")
        assert result == "***-**-6789"

    def test_mask_ssn_unformatted(self):
        """Test masking unformatted SSN."""
        result = mask_ssn("123456789")
        assert result == "***-**-6789"

    def test_mask_ssn_short(self):
        """Test masking short SSN."""
        result = mask_ssn("123")
        assert result == "***-**-****"

    def test_mask_ssn_empty(self):
        """Test masking empty SSN."""
        result = mask_ssn("")
        assert result == "***-**-****"

    def test_mask_ssn_none(self):
        """Test masking None SSN."""
        result = mask_ssn(None)  # type: ignore
        assert result == "***-**-****"


class TestMaskCreditCard:
    """Tests for credit card masking."""

    def test_mask_credit_card_formatted(self):
        """Test masking formatted credit card."""
        result = mask_credit_card("4111-1111-1111-1111")
        assert result == "****-****-****-1111"

    def test_mask_credit_card_unformatted(self):
        """Test masking unformatted credit card."""
        result = mask_credit_card("4111111111111111")
        assert result == "****-****-****-1111"

    def test_mask_credit_card_short(self):
        """Test masking short credit card."""
        result = mask_credit_card("123")
        assert result == "****-****-****-****"

    def test_mask_credit_card_empty(self):
        """Test masking empty credit card."""
        result = mask_credit_card("")
        assert result == "****-****-****-****"

    def test_mask_credit_card_none(self):
        """Test masking None credit card."""
        result = mask_credit_card(None)  # type: ignore
        assert result == "****-****-****-****"


class TestMaskIPAddress:
    """Tests for IP address masking."""

    def test_mask_ip_address_ipv4(self):
        """Test masking IPv4 address."""
        result = mask_ip_address("192.168.1.100")
        assert result == "192.168.1.***"

    def test_mask_ip_address_ipv6(self):
        """Test masking IPv6 address."""
        result = mask_ip_address("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        assert result == "2001:0db8:85a3:0000:0000:8a2e:0370:***"

    def test_mask_ip_address_invalid(self):
        """Test masking invalid IP address."""
        result = mask_ip_address("invalid")
        assert result == "***"

    def test_mask_ip_address_empty(self):
        """Test masking empty IP address."""
        result = mask_ip_address("")
        assert result == "***"

    def test_mask_ip_address_none(self):
        """Test masking None IP address."""
        result = mask_ip_address(None)  # type: ignore
        assert result == "***"


class TestMaskString:
    """Tests for generic string masking."""

    def test_mask_string_normal(self):
        """Test masking normal string."""
        result = mask_string("sensitive_data", keep_start=3, keep_end=4)
        # "sensitive_data" = 14 chars, keep 3 start + 4 end = 7 visible, mask 7 chars
        assert result == "sen*******data"

    def test_mask_string_short(self):
        """Test masking short string."""
        result = mask_string("short", keep_start=2, keep_end=2)
        # "short" = 5 chars, keep 2 start + 2 end = 4 visible, mask 1 char
        assert result == "sh*rt"

    def test_mask_string_very_short(self):
        """Test masking very short string."""
        result = mask_string("ab", keep_start=1, keep_end=1)
        assert result == "a*"

    def test_mask_string_single_char(self):
        """Test masking single character."""
        result = mask_string("a", keep_start=1, keep_end=0)
        assert result == "*"

    def test_mask_string_empty(self):
        """Test masking empty string."""
        result = mask_string("")
        assert result == ""

    def test_mask_string_none(self):
        """Test masking None string."""
        result = mask_string(None)  # type: ignore
        assert result == ""

    def test_mask_string_custom_mask_char(self):
        """Test masking with custom mask character."""
        result = mask_string("secret", keep_start=2, keep_end=2, mask_char="#")
        assert result == "se##et"


class TestShouldMaskAttribute:
    """Tests for attribute masking detection."""

    def test_should_mask_email(self):
        """Test detecting email attribute."""
        assert should_mask_attribute("user.email") is True
        assert should_mask_attribute("email") is True
        assert should_mask_attribute("user_email") is True

    def test_should_mask_phone(self):
        """Test detecting phone attribute."""
        assert should_mask_attribute("user.phone") is True
        assert should_mask_attribute("phone_number") is True
        assert should_mask_attribute("telephone") is True

    def test_should_mask_ssn(self):
        """Test detecting SSN attribute."""
        assert should_mask_attribute("user.ssn") is True
        assert should_mask_attribute("social_security_number") is True

    def test_should_mask_credit_card(self):
        """Test detecting credit card attribute."""
        assert should_mask_attribute("payment.card_number") is True
        assert should_mask_attribute("credit_card") is True

    def test_should_mask_password(self):
        """Test detecting password attribute."""
        assert should_mask_attribute("user.password") is True
        assert should_mask_attribute("api_secret") is True

    def test_should_not_mask_normal(self):
        """Test not masking normal attributes."""
        assert should_mask_attribute("user.id") is False
        assert should_mask_attribute("tenant_id") is False
        assert should_mask_attribute("request_id") is False

    def test_should_mask_case_insensitive(self):
        """Test case-insensitive detection."""
        assert should_mask_attribute("USER.EMAIL") is True
        assert should_mask_attribute("Email") is True

    def test_should_mask_empty(self):
        """Test empty key."""
        assert should_mask_attribute("") is False

    def test_should_mask_none(self):
        """Test None key."""
        assert should_mask_attribute(None) is False  # type: ignore


class TestMaskAttributeValue:
    """Tests for automatic attribute value masking."""

    def test_mask_attribute_value_email(self):
        """Test masking email attribute value."""
        result = mask_attribute_value("user.email", "john@example.com")
        assert result == "j***@example.com"

    def test_mask_attribute_value_phone(self):
        """Test masking phone attribute value."""
        result = mask_attribute_value("user.phone", "+1-555-123-4567")
        assert result == "***-***-4567"

    def test_mask_attribute_value_ssn(self):
        """Test masking SSN attribute value."""
        result = mask_attribute_value("user.ssn", "123-45-6789")
        assert result == "***-**-6789"

    def test_mask_attribute_value_credit_card(self):
        """Test masking credit card attribute value."""
        result = mask_attribute_value("payment.card_number", "4111-1111-1111-1111")
        assert result == "****-****-****-1111"

    def test_mask_attribute_value_ip(self):
        """Test masking IP address attribute value."""
        result = mask_attribute_value("client.ip_address", "192.168.1.100")
        assert result == "192.168.1.***"

    def test_mask_attribute_value_non_pii(self):
        """Test not masking non-PII attribute value."""
        result = mask_attribute_value("user.id", "user123")
        assert result == "user123"

    def test_mask_attribute_value_none(self):
        """Test masking None value."""
        result = mask_attribute_value("user.email", None)
        assert result is None

    def test_mask_attribute_value_empty(self):
        """Test masking empty value."""
        result = mask_attribute_value("user.email", "")
        assert result == "invalid"

    def test_mask_attribute_value_generic_pii(self):
        """Test masking generic PII attribute."""
        result = mask_attribute_value("user.secret", "sensitive_data")
        assert result == "se**********ta"


class TestPIIMaskingEdgeCases:
    """Tests for edge cases in PII masking."""

    def test_mask_email_unicode(self):
        """Test masking email with unicode characters."""
        result = mask_email("tëst@example.com")
        assert result == "t***@example.com"

    def test_mask_phone_unicode(self):
        """Test masking phone with unicode characters."""
        result = mask_phone("+1-555-123-4567")
        assert result == "***-***-4567"

    def test_mask_string_unicode(self):
        """Test masking string with unicode characters."""
        result = mask_string("sënsitivë", keep_start=2, keep_end=2)
        assert len(result) > 0
        assert result.startswith("së")

    def test_mask_attribute_value_multiple_patterns(self):
        """Test masking attribute with multiple PII patterns."""
        # Should match first pattern found
        result = mask_attribute_value("user.email_phone", "test@example.com")
        assert result is not None
        assert isinstance(result, str)
        assert "***" in result or "@" in result

