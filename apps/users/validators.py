from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.password_validation import validate_password
from .models import PasswordHistory


class PasswordHistoryValidator:
    """
    Custom password validator that prevents reuse of recent passwords.
    """
    
    def __init__(self, history_count=5):
        self.history_count = history_count
    
    def validate(self, password, user=None):
        if user is None:
            return
        
        if PasswordHistory.is_password_reused(user, password, self.history_count):
            raise ValidationError(
                _("This password has been used recently. Please choose a different password."),
                code='password_reused'
            )
    
    def get_help_text(self):
        return _(
            "Your password cannot be the same as any of your last %(history_count)d passwords."
        ) % {'history_count': self.history_count}


class FirstTimeSetupPasswordValidator:
    """
    Special validator for first-time setup that prevents reuse of the initial password.
    """
    
    def validate(self, password, user=None):
        if user is None:
            return
        
        # For first-time setup, we need to check against the current password
        # which is typically a temporary password set by admin
        if user.check_password(password):
            raise ValidationError(
                _("You cannot reuse the same password. Please choose a different password for security."),
                code='password_reused_first_time'
            )
    
    def get_help_text(self):
        return _("You cannot reuse the same password. Please choose a different password for security.")


def validate_password_strength(password):
    """
    Enhanced password strength validation.
    """
    errors = []
    
    if len(password) < 8:
        errors.append(_("Password must be at least 8 characters long."))
    
    if not any(c.isupper() for c in password):
        errors.append(_("Password must contain at least one uppercase letter."))
    
    if not any(c.islower() for c in password):
        errors.append(_("Password must contain at least one lowercase letter."))
    
    if not any(c.isdigit() for c in password):
        errors.append(_("Password must contain at least one digit."))
    
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        errors.append(_("Password must contain at least one special character."))
    
    if errors:
        raise ValidationError(errors)
