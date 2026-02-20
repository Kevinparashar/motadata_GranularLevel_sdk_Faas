"""
PII Masking Utilities

Functions to mask personally identifiable information (PII) before sending
data to OpenTelemetry or other observability systems.

IMPORTANT: PII masking must occur in application code BEFORE sending data
to the OpenTelemetry SDK. This ensures no sensitive data reaches observability backends.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def mask_email(email: str) -> str:
    """
    Mask email address to protect PII.
    
    Masks the local part (before @) while preserving the domain.
    Format: first_char***@domain.com
    
    Args:
        email: Email address to mask
        
    Returns:
        Masked email address
        
    Examples:
        >>> mask_email("john.doe@example.com")
        'j***@example.com'
        >>> mask_email("user@test.co.uk")
        'u***@test.co.uk'
        >>> mask_email("invalid")
        'invalid'
    """
    if not email or not isinstance(email, str):
        return email if email else "invalid"
    
    try:
        # Split email into local and domain parts
        parts = email.split("@", 1)
        if len(parts) != 2:
            # Invalid email format
            return "invalid"
        
        local_part, domain = parts
        
        if not local_part or not domain:
            return "invalid"
        
        # Mask local part: keep first character, mask the rest
        if len(local_part) == 1:
            masked_local = local_part + "***"
        else:
            masked_local = local_part[0] + "***"
        
        return f"{masked_local}@{domain}"
    except Exception as e:
        logger.debug(f"Failed to mask email '{email}': {e}")
        return "invalid"


def mask_phone(phone: str) -> str:
    """
    Mask phone number to protect PII.
    
    Masks all digits except the last 4.
    Format: ***-***-XXXX
    
    Args:
        phone: Phone number to mask (can include formatting)
        
    Returns:
        Masked phone number
        
    Examples:
        >>> mask_phone("+1-555-123-4567")
        '***-***-4567'
        >>> mask_phone("5551234567")
        '***-***-4567'
        >>> mask_phone("123")
        '***'
    """
    if not phone or not isinstance(phone, str):
        return phone if phone else "***"
    
    try:
        # Extract all digits
        digits = re.sub(r"\D", "", phone)
        
        if len(digits) < 4:
            # Too short, mask everything
            return "***"
        
        # Keep last 4 digits, mask the rest
        last_four = digits[-4:]
        return f"***-***-{last_four}"
    except Exception as e:
        logger.debug(f"Failed to mask phone '{phone}': {e}")
        return "***"


def mask_ssn(ssn: str) -> str:
    """
    Mask Social Security Number (SSN) to protect PII.
    
    Masks all digits except the last 4.
    Format: ***-**-XXXX
    
    Args:
        ssn: SSN to mask (can include formatting)
        
    Returns:
        Masked SSN
        
    Examples:
        >>> mask_ssn("123-45-6789")
        '***-**-6789'
        >>> mask_ssn("123456789")
        '***-**-6789'
    """
    if not ssn or not isinstance(ssn, str):
        return "***-**-****"
    
    try:
        # Extract all digits
        digits = re.sub(r"\D", "", ssn)
        
        if len(digits) < 4:
            # Too short, mask everything
            return "***-**-****"
        
        # Keep last 4 digits, mask the rest
        last_four = digits[-4:]
        return f"***-**-{last_four}"
    except Exception as e:
        logger.debug(f"Failed to mask SSN '{ssn}': {e}")
        return "***-**-****"


def mask_credit_card(card_number: str) -> str:
    """
    Mask credit card number to protect PII.
    
    Masks all digits except the last 4.
    Format: ****-****-****-XXXX
    
    Args:
        card_number: Credit card number to mask (can include formatting)
        
    Returns:
        Masked credit card number
        
    Examples:
        >>> mask_credit_card("4111-1111-1111-1111")
        '****-****-****-1111'
        >>> mask_credit_card("4111111111111111")
        '****-****-****-1111'
    """
    if not card_number or not isinstance(card_number, str):
        return "****-****-****-****"
    
    try:
        # Extract all digits
        digits = re.sub(r"\D", "", card_number)
        
        if len(digits) < 4:
            # Too short, mask everything
            return "****-****-****-****"
        
        # Keep last 4 digits, mask the rest
        last_four = digits[-4:]
        return f"****-****-****-{last_four}"
    except Exception as e:
        logger.debug(f"Failed to mask credit card '{card_number}': {e}")
        return "****-****-****-****"


def mask_ip_address(ip_address: str) -> str:
    """
    Mask IP address to protect PII.
    
    Masks the last octet for IPv4, last segment for IPv6.
    
    Args:
        ip_address: IP address to mask
        
    Returns:
        Masked IP address
        
    Examples:
        >>> mask_ip_address("192.168.1.100")
        '192.168.1.***'
        >>> mask_ip_address("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        '2001:0db8:85a3:0000:0000:8a2e:0370:***'
    """
    if not ip_address or not isinstance(ip_address, str):
        return "***"
    
    try:
        # IPv4 address
        if "." in ip_address:
            parts = ip_address.split(".")
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
        
        # IPv6 address
        if ":" in ip_address:
            parts = ip_address.split(":")
            if len(parts) > 0:
                parts[-1] = "***"
                return ":".join(parts)
        
        # Unknown format
        return "***"
    except Exception as e:
        logger.debug(f"Failed to mask IP address '{ip_address}': {e}")
        return "***"


def mask_string(value: str, keep_start: int = 2, keep_end: int = 2, mask_char: str = "*") -> str:
    """
    Generic string masking function.
    
    Masks the middle portion of a string while keeping some characters
    at the start and end visible.
    
    Args:
        value: String to mask
        keep_start: Number of characters to keep at the start
        keep_end: Number of characters to keep at the end
        mask_char: Character to use for masking
        
    Returns:
        Masked string
        
    Examples:
        >>> mask_string("sensitive_data", keep_start=3, keep_end=4)
        'sen*****data'
        >>> mask_string("short", keep_start=2, keep_end=2)
        'sh***'
    """
    if not value or not isinstance(value, str):
        return value if value else ""
    
    if len(value) <= keep_start + keep_end:
        # Too short, mask everything except first and last
        if len(value) <= 1:
            return mask_char * len(value)
        return value[0] + mask_char * (len(value) - 1)
    
    start = value[:keep_start]
    end = value[-keep_end:] if keep_end > 0 else ""
    masked_length = len(value) - keep_start - keep_end
    
    return f"{start}{mask_char * masked_length}{end}"


def should_mask_attribute(key: str) -> bool:
    """
    Check if an attribute key should be masked based on naming patterns.
    
    This is a helper function to identify attributes that likely contain PII.
    
    Args:
        key: Attribute key to check
        
    Returns:
        True if the attribute should be masked, False otherwise
        
    Examples:
        >>> should_mask_attribute("user.email")
        True
        >>> should_mask_attribute("user.phone")
        True
        >>> should_mask_attribute("user.id")
        False
    """
    if not key or not isinstance(key, str):
        return False
    
    key_lower = key.lower()
    
    # Patterns that indicate PII
    pii_patterns = [
        "email",
        "phone",
        "ssn",
        "social_security",
        "credit_card",
        "card_number",
        "password",
        "secret",
        "token",
        "api_key",
        "ip_address",
        "ip_addr",
    ]
    
    return any(pattern in key_lower for pattern in pii_patterns)


def mask_attribute_value(key: str, value: Optional[str]) -> Optional[str]:
    """
    Mask an attribute value based on its key.
    
    Automatically selects the appropriate masking function based on the
    attribute key name.
    
    Args:
        key: Attribute key name
        value: Attribute value to mask
        
    Returns:
        Masked value or original value if masking not needed
        
    Examples:
        >>> mask_attribute_value("user.email", "john@example.com")
        'j***@example.com'
        >>> mask_attribute_value("user.phone", "+1-555-123-4567")
        '***-***-4567'
        >>> mask_attribute_value("user.id", "user123")
        'user123'
    """
    if value is None or not isinstance(value, str):
        return value
    
    if not should_mask_attribute(key):
        return value
    
    key_lower = key.lower()
    
    # Apply appropriate masking based on key
    if "email" in key_lower:
        return mask_email(value)
    elif "phone" in key_lower or "tel" in key_lower:
        return mask_phone(value)
    elif "ssn" in key_lower or "social" in key_lower:
        return mask_ssn(value)
    elif "card" in key_lower or "credit" in key_lower:
        return mask_credit_card(value)
    elif "ip" in key_lower:
        return mask_ip_address(value)
    else:
        # Generic masking for other PII
        return mask_string(value, keep_start=2, keep_end=2)

