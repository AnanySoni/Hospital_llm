"""
Comprehensive input validation utilities for onboarding and security.
"""
import re
from typing import Optional, Tuple, Dict
import os

# Try to import optional dependencies gracefully
try:
    from email_validator import validate_email, EmailNotValidError
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False
    EmailNotValidError = Exception

try:
    import dns.resolver
    DNS_RESOLVER_AVAILABLE = True
except ImportError:
    DNS_RESOLVER_AVAILABLE = False


class CompanyNameValidator:
    """Validates company names with comprehensive rules."""
    MIN_LENGTH = 2
    MAX_LENGTH = 100
    PATTERN = re.compile(r'^[a-zA-Z0-9\s-]+$')
    
    @staticmethod
    def validate(name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate company name.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not name:
            return False, "Company name is required"
        
        name = name.strip()
        
        if len(name) < CompanyNameValidator.MIN_LENGTH:
            return False, f"Company name must be at least {CompanyNameValidator.MIN_LENGTH} characters"
        
        if len(name) > CompanyNameValidator.MAX_LENGTH:
            return False, f"Company name must be at most {CompanyNameValidator.MAX_LENGTH} characters"
        
        if not CompanyNameValidator.PATTERN.match(name):
            return False, "Company name can only contain letters, numbers, spaces, and hyphens"
        
        # Prevent only spaces/hyphens
        if not re.search(r'[a-zA-Z0-9]', name):
            return False, "Company name must contain at least one letter or number"
        
        # Prevent consecutive hyphens
        if '--' in name:
            return False, "Company name cannot contain consecutive hyphens"
        
        return True, None


class EmailValidator:
    """Enhanced email validation with domain checks."""
    DISALLOWED_DOMAINS = [
        'tempmail.com', '10minutemail.com', 'guerrillamail.com',
        'mailinator.com', 'throwaway.email', 'temp-mail.org',
        'mohmal.com', 'fakeinbox.com', 'trashmail.com'
    ]
    
    @staticmethod
    def validate(email: str, check_deliverability: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Enhanced email validation with domain checks.
        
        Args:
            email: Email address to validate
            check_deliverability: Whether to perform DNS check (slower)
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        email = email.strip().lower()
        
        # Basic format check
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "Invalid email format"
        
        # Use email-validator if available for RFC 5322 compliance
        if EMAIL_VALIDATOR_AVAILABLE:
            try:
                validation = validate_email(
                    email,
                    check_deliverability=check_deliverability
                )
                normalized_email = validation.email.lower()
            except EmailNotValidError as e:
                return False, str(e)
        else:
            normalized_email = email
        
        # Check against disallowed domains
        domain = normalized_email.split('@')[1]
        if domain in EmailValidator.DISALLOWED_DOMAINS:
            return False, "Temporary email addresses are not allowed"
        
        return True, None


class SlugValidator:
    """Validates URL slugs with format and reserved word checks."""
    MIN_LENGTH = 3
    MAX_LENGTH = 50
    PATTERN = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    RESERVED_SLUGS = [
        'admin', 'api', 'www', 'mail', 'ftp', 'localhost', 'test',
        'dev', 'staging', 'prod', 'production', 'app', 'dashboard',
        'login', 'logout', 'register', 'signup', 'signin', 'signout',
        'oauth', 'auth', 'account', 'profile', 'settings', 'config',
        'system', 'root', 'support', 'help', 'docs', 'documentation'
    ]
    
    @staticmethod
    def validate(slug: str, check_reserved: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate slug format and reserved words.
        
        Args:
            slug: Slug to validate
            check_reserved: Whether to check against reserved words
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not slug:
            return False, "Slug is required"
        
        slug = slug.lower().strip()
        
        if len(slug) < SlugValidator.MIN_LENGTH:
            return False, f"Slug must be at least {SlugValidator.MIN_LENGTH} characters"
        
        if len(slug) > SlugValidator.MAX_LENGTH:
            return False, f"Slug must be at most {SlugValidator.MAX_LENGTH} characters"
        
        if not SlugValidator.PATTERN.match(slug):
            return False, "Slug can only contain lowercase letters, numbers, and hyphens"
        
        # No consecutive hyphens
        if '--' in slug:
            return False, "Slug cannot contain consecutive hyphens"
        
        # No leading/trailing hyphens
        if slug.startswith('-') or slug.endswith('-'):
            return False, "Slug cannot start or end with a hyphen"
        
        # Check reserved words
        if check_reserved and slug in SlugValidator.RESERVED_SLUGS:
            return False, f"'{slug}' is a reserved word and cannot be used"
        
        return True, None


class PasswordValidator:
    """Comprehensive password validation with strength calculation."""
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBER = True
    REQUIRE_SPECIAL = False  # Optional for now
    
    # Common passwords list (expandable)
    COMMON_PASSWORDS = [
        'password', '12345678', 'password123', 'admin123',
        'qwerty123', 'welcome123', 'letmein123', '123456789',
        'password1', 'admin', 'root', 'toor', 'pass1234',
        'welcome', 'monkey', '1234567', '1234567890', 'abc123'
    ]
    
    @staticmethod
    def validate(password: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Validate password with complexity checks and strength calculation.
        
        Returns:
            Tuple[bool, Optional[str], Optional[Dict]]: 
            (is_valid, error_message, strength_info)
            strength_info: {score: 0-4, level: 'weak'|'fair'|'good'|'strong'}
        """
        if not password:
            return False, "Password is required", None
        
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MIN_LENGTH} characters", None
        
        if len(password) > PasswordValidator.MAX_LENGTH:
            return False, f"Password must be at most {PasswordValidator.MAX_LENGTH} characters", None
        
        # Check common passwords
        if password.lower() in [p.lower() for p in PasswordValidator.COMMON_PASSWORDS]:
            return False, "This password is too common. Please choose a more unique password", None
        
        # Complexity checks
        errors = []
        if PasswordValidator.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("uppercase letter")
        if PasswordValidator.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("lowercase letter")
        if PasswordValidator.REQUIRE_NUMBER and not re.search(r'\d', password):
            errors.append("number")
        if PasswordValidator.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("special character")
        
        if errors:
            return False, f"Password must contain at least one: {', '.join(errors)}", None
        
        # Calculate strength
        strength = PasswordValidator._calculate_strength(password)
        
        return True, None, strength
    
    @staticmethod
    def _calculate_strength(password: str) -> Dict:
        """Calculate password strength score (0-4)."""
        score = 0
        
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if re.search(r'[A-Z]', password) and re.search(r'[a-z]', password):
            score += 1
        if re.search(r'\d', password) and re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        
        levels = {0: 'weak', 1: 'weak', 2: 'fair', 3: 'good', 4: 'strong'}
        return {'score': score, 'level': levels.get(score, 'weak')}

