"""
Security Policies and Audit Framework

Security policies, audit framework, and compliance checking.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class SecurityLevel(str, Enum):
    """Security level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityIssue(BaseModel):
    """Security issue found during audit."""
    level: SecurityLevel
    component: str
    description: str
    recommendation: str
    fixed: bool = False
    fixed_date: Optional[datetime] = None


class SecurityPolicy(BaseModel):
    """
    Security policy configuration.
    
    Defines security requirements and best practices for the SDK.
    """
    name: str
    version: str = "1.0.0"
    description: str = ""
    
    # API Key Management
    require_api_key_encryption: bool = True
    api_key_env_var_prefix: str = "MOTADATA_"
    disallow_hardcoded_keys: bool = True
    
    # Input Validation
    require_input_validation: bool = True
    max_input_length: int = 1000000
    sanitize_user_input: bool = True
    
    # Connection Security
    require_https: bool = True
    require_certificate_validation: bool = True
    connection_timeout: float = 30.0
    
    # Data Protection
    encrypt_sensitive_data: bool = True
    log_sensitive_data: bool = False
    redact_sensitive_data_in_logs: bool = True


class SecurityAudit:
    """
    Security audit framework.
    
    Performs security audits and checks compliance with security policies.
    """
    
    def __init__(self, policy: SecurityPolicy):
        """
        Initialize security audit.
        
        Args:
            policy: Security policy to enforce
        """
        self.policy = policy
        self.issues: List[SecurityIssue] = []
    
    def audit(self, code: str) -> List[SecurityIssue]:
        """
        Perform comprehensive security audit.
        
        Args:
            code: Code to audit
        
        Returns:
            List of all security issues found
        """
        issues = []
        
        # Check for hardcoded API keys
        if self.policy.disallow_hardcoded_keys:
            import re
            patterns = [
                r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
                r'apikey\s*=\s*["\'][^"\']+["\']',
                r'API[_-]?KEY\s*=\s*["\'][^"\']+["\']',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, code, re.IGNORECASE)
                for match in matches:
                    issues.append(SecurityIssue(
                        level=SecurityLevel.CRITICAL,
                        component="API Key Management",
                        description=f"Hardcoded API key found: {match.group()[:50]}...",
                        recommendation="Use environment variables or secure credential storage",
                    ))
        
        # Check for HTTP URLs (should use HTTPS)
        if self.policy.require_https:
            import re
            http_pattern = r'http://[^\s\'"]+'
            matches = re.finditer(http_pattern, code)
            for match in matches:
                issues.append(SecurityIssue(
                    level=SecurityLevel.MEDIUM,
                    component="Connection Security",
                    description=f"HTTP URL found (should use HTTPS): {match.group()}",
                    recommendation="Use HTTPS for all external connections",
                ))
        
        self.issues.extend(issues)
        return issues
    
    def get_summary(self) -> Dict[str, int]:
        """
        Get summary of security issues by level.
        
        Returns:
            Dictionary mapping security levels to issue counts
        """
        summary = {
            level.value: 0
            for level in SecurityLevel
        }
        
        for issue in self.issues:
            if not issue.fixed:
                summary[issue.level.value] += 1
        
        return summary

