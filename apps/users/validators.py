from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.core.cache import cache
import re
import hashlib
import requests
from typing import List, Dict, Any
import logging

from .models import PasswordHistory

logger = logging.getLogger(__name__)

class EnhancedPasswordStrengthValidator:
    """
    Enhanced password strength validator based on NIST guidelines and global best practices.
    """
    
    def __init__(self, min_length=12, max_length=128):
        self.min_length = min_length
        self.max_length = max_length
        
        # Common weak passwords and patterns
        self.common_passwords = {
            'password', '123456', '123456789', 'qwerty', 'abc123', 
            'password123', 'admin', 'letmein', 'welcome', 'monkey',
            'dragon', 'master', 'hello', 'freedom', 'whatever',
            'qazwsx', 'trustno1', 'jordan', 'harley', 'ranger',
            'iwantu', 'jennifer', 'hunter', 'buster', 'soccer',
            'baseball', 'tequiero', 'princess', 'merlin', 'cookie',
            'summer', 'internet', 'service', 'canada', 'cooper'
        }
        
        # Common keyboard patterns
        self.keyboard_patterns = [
            r'qwerty', r'asdfgh', r'zxcvbn', r'123456', r'654321',
            r'qazwsx', r'edcrfv', r'tgbnhy', r'yhnujm', r'ikm',
            r'olp', r'qsc', r'wsx', r'edc', r'rfv', r'tgb', r'yhn',
            r'ujm', r'ik', r'ol', r'p;', r'asd', r'sdf', r'dfg',
            r'fgh', r'ghj', r'hjk', r'jkl', r'kl;', r'zxc', r'xcv',
            r'cvb', r'vbn', r'bnm', r'nm,', r'm,.', r',./', r'./',
            r'qwe', r'wer', r'ert', r'rty', r'tyu', r'yui', r'uio',
            r'iop', r'asd', r'sdf', r'dfg', r'fgh', r'ghj', r'hjk',
            r'jkl', r'zxc', r'xcv', r'cvb', r'vbn', r'bnm'
        ]
    
    def validate(self, password: str, user=None) -> None:
        """
        Validate password strength according to enhanced security requirements.
        """
        errors = []
        
        # Basic length validation
        if len(password) < self.min_length:
            errors.append(_(f"Password must be at least {self.min_length} characters long."))
        
        if len(password) > self.max_length:
            errors.append(_(f"Password must not exceed {self.max_length} characters."))
        
        # Character variety requirements (NIST guidelines)
        has_uppercase = any(c.isupper() for c in password)
        has_lowercase = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        # Require at least 3 character types
        char_types = sum([has_uppercase, has_lowercase, has_digit, has_special])
        if char_types < 3:
            errors.append(_("Password must contain at least 3 of the following: uppercase letters, lowercase letters, numbers, and special characters."))
        
        # Check for common weak passwords
        if password.lower() in self.common_passwords:
            errors.append(_("This password is too common. Please choose a more unique password."))
        
        # Check for keyboard patterns
        password_lower = password.lower()
        for pattern in self.keyboard_patterns:
            if pattern in password_lower:
                errors.append(_("Password contains common keyboard patterns. Please choose a more random password."))
                break
        
        # Check for repeated characters
        if re.search(r'(.)\1{2,}', password):
            errors.append(_("Password contains too many repeated characters."))
        
        # Check for sequential characters
        if re.search(r'(?:abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789)', password.lower()):
            errors.append(_("Password contains sequential characters."))
        
        # Check for user-specific information
        if user:
            user_info = [
                user.username.lower(),
                user.email.lower().split('@')[0],
                user.first_name.lower(),
                user.last_name.lower()
            ]
            
            for info in user_info:
                if info and len(info) > 2 and info in password.lower():
                    errors.append(_("Password should not contain your personal information."))
                    break
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self) -> str:
        return _(
            f"Your password must be at least {self.min_length} characters long and contain "
            "at least 3 of the following: uppercase letters, lowercase letters, numbers, "
            "and special characters. Avoid common passwords and personal information."
        )


class PasswordBreachValidator:
    """
    Validator that checks if a password has been compromised in known data breaches.
    Uses HaveIBeenPwned API (k-anonymity approach for privacy).
    """
    
    def __init__(self, min_breach_count=1):
        self.min_breach_count = min_breach_count
        self.api_url = "https://api.pwnedpasswords.com/range/"
        self.cache_timeout = 3600  # 1 hour cache
    
    def validate(self, password: str, user=None) -> None:
        """
        Check if password has been compromised using k-anonymity approach.
        """
        try:
            # Create SHA-1 hash of password
            password_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
            prefix = password_hash[:5]
            suffix = password_hash[5:]
            
            # Check cache first
            cache_key = f"pwned_password_{prefix}"
            cached_results = cache.get(cache_key)
            
            if cached_results is None:
                # Make API request
                response = requests.get(f"{self.api_url}{prefix}", timeout=5)
                if response.status_code == 200:
                    cached_results = response.text
                    cache.set(cache_key, cached_results, self.cache_timeout)
                else:
                    # If API is unavailable, skip validation
                    logger.warning(f"HaveIBeenPwned API unavailable: {response.status_code}")
                    return
            
            # Check if our password hash suffix is in the results
            for line in cached_results.split('\n'):
                if line.startswith(suffix):
                    count = int(line.split(':')[1])
                    if count >= self.min_breach_count:
                        raise ValidationError(
                            _("This password has been found in {count} data breaches. Please choose a different password.").format(count=count)
                        )
                    break
                    
        except requests.RequestException as e:
            logger.warning(f"Password breach check failed: {e}")
            # Don't fail validation if API is unavailable
            return
        except Exception as e:
            logger.error(f"Password breach validation error: {e}")
            return
    
    def get_help_text(self) -> str:
        return _("Your password will be checked against known data breaches to ensure it hasn't been compromised.")


class PasswordHistoryValidator:
    """
    Enhanced password history validator that prevents reuse of recent passwords.
    """
    
    def __init__(self, history_count=8, min_age_days=1):
        self.history_count = history_count
        self.min_age_days = min_age_days
    
    def validate(self, password: str, user=None) -> None:
        if user is None:
            return
        
        if PasswordHistory.is_password_reused(user, password, self.history_count):
            raise ValidationError(
                _("This password has been used recently. Please choose a different password."),
                code='password_reused'
            )
    
    def get_help_text(self) -> str:
        return _(
            "Your password cannot be the same as any of your last %(history_count)d passwords."
        ) % {'history_count': self.history_count}


class FirstTimeSetupPasswordValidator:
    """
    Special validator for first-time setup that prevents reuse of the initial password.
    """
    
    def validate(self, password: str, user=None) -> None:
        if user is None:
            return
        
        # For first-time setup, we need to check against the current password
        # which is typically a temporary password set by admin
        if user.check_password(password):
            raise ValidationError(
                _("You cannot reuse the same password. Please choose a different password for security."),
                code='password_reused_first_time'
            )
    
    def get_help_text(self) -> str:
        return _("You cannot reuse the same password. Please choose a different password for security.")


class PasswordComplexityValidator:
    """
    Validator that enforces password complexity requirements.
    """
    
    def __init__(self, require_uppercase=True, require_lowercase=True, 
                 require_digits=True, require_special=True, min_length=12):
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.min_length = min_length
    
    def validate(self, password: str, user=None) -> None:
        errors = []
        
        if len(password) < self.min_length:
            errors.append(_(f"Password must be at least {self.min_length} characters long."))
        
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append(_("Password must contain at least one uppercase letter."))
        
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append(_("Password must contain at least one lowercase letter."))
        
        if self.require_digits and not any(c.isdigit() for c in password):
            errors.append(_("Password must contain at least one digit."))
        
        if self.require_special and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            errors.append(_("Password must contain at least one special character."))
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self) -> str:
        requirements = []
        if self.require_uppercase:
            requirements.append("uppercase letter")
        if self.require_lowercase:
            requirements.append("lowercase letter")
        if self.require_digits:
            requirements.append("digit")
        if self.require_special:
            requirements.append("special character")
        
        return _(
            f"Password must be at least {self.min_length} characters long and contain "
            f"at least one {', '.join(requirements)}."
        )


def validate_password_strength(password: str) -> None:
    """
    Enhanced password strength validation using multiple validators.
    """
    validators = [
        EnhancedPasswordStrengthValidator(),
        PasswordComplexityValidator(),
    ]
    
    for validator in validators:
        validator.validate(password)


def get_password_strength_score(password: str) -> Dict[str, Any]:
    """
    Calculate password strength score and provide feedback.
    Returns a dictionary with score (0-100) and feedback.
    """
    score = 0
    feedback = []
    
    # Length contribution (up to 25 points)
    if len(password) >= 12:
        score += 25
    elif len(password) >= 8:
        score += 15
    elif len(password) >= 6:
        score += 10
    else:
        feedback.append("Password is too short")
    
    # Character variety contribution (up to 25 points)
    char_types = 0
    if any(c.isupper() for c in password):
        char_types += 1
    if any(c.islower() for c in password):
        char_types += 1
    if any(c.isdigit() for c in password):
        char_types += 1
    if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        char_types += 1
    
    score += char_types * 6.25  # 25 points / 4 types
    
    # Complexity contribution (up to 25 points)
    if not re.search(r'(.)\1{2,}', password):  # No repeated characters
        score += 10
    else:
        feedback.append("Avoid repeated characters")
    
    if not re.search(r'(?:abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789)', password.lower()):
        score += 10
    else:
        feedback.append("Avoid sequential characters")
    
    # Entropy contribution (up to 25 points)
    unique_chars = len(set(password))
    if unique_chars >= 10:
        score += 25
    elif unique_chars >= 8:
        score += 20
    elif unique_chars >= 6:
        score += 15
    else:
        feedback.append("Use more unique characters")
    
    # Determine strength level
    if score >= 80:
        strength = "Very Strong"
    elif score >= 60:
        strength = "Strong"
    elif score >= 40:
        strength = "Moderate"
    elif score >= 20:
        strength = "Weak"
    else:
        strength = "Very Weak"
    
    return {
        'score': min(100, int(score)),
        'strength': strength,
        'feedback': feedback,
        'char_types': char_types,
        'length': len(password),
        'unique_chars': unique_chars
    }
