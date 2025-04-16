"""
Common Constants for the GRC Application

This module defines a collection of constants used across the project,
including default configuration values, role definitions, status codes,
and other reusable constants.

Update this file as needed to reflect any changes in business logic or defaults.
"""

# -----------------------------------
# GENERAL DEFAULTS & SETTINGS
# -----------------------------------
DEFAULT_PAGINATION_PAGE_SIZE = 25
MAX_UPLOAD_SIZE_MB = 10  # Default maximum file upload size (in MB)
DEFAULT_CHAR_FIELD_MAX_LENGTH = 255

# Environment/Connection Defaults
DEFAULT_TIMEOUT_SECONDS = 30

# -----------------------------------
# FILE UPLOAD CONSTANTS
# -----------------------------------
ALLOWED_FILE_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt',
    'jpg', 'jpeg', 'png', 'gif'
}
DISALLOWED_FILE_EXTENSIONS = {
    'exe', 'bat', 'sh', 'py', 'js', 'msi', 'dll', 'jar', 'php', 'pl', 'cgi'
}

# -----------------------------------
# USER ROLE CHOICES
# -----------------------------------
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
ROLE_STAFF = 'staff'
ROLE_CHOICES = [
    (ROLE_ADMIN, "Admin"),
    (ROLE_MANAGER, "Manager"),
    (ROLE_STAFF, "Staff"),
]

# -----------------------------------
# SUBSCRIPTION & BILLING CONSTANTS
# -----------------------------------
SUBSCRIPTION_STATUS_ACTIVE = 'active'
SUBSCRIPTION_STATUS_CANCELLED = 'cancelled'
SUBSCRIPTION_STATUS_PAUSED = 'paused'
SUBSCRIPTION_STATUS_CHOICES = [
    (SUBSCRIPTION_STATUS_ACTIVE, "Active"),
    (SUBSCRIPTION_STATUS_CANCELLED, "Cancelled"),
    (SUBSCRIPTION_STATUS_PAUSED, "Paused"),
]

BILLING_CYCLE_MONTHLY = 'monthly'
BILLING_CYCLE_YEARLY = 'yearly'
BILLING_CYCLE_CHOICES = [
    (BILLING_CYCLE_MONTHLY, "Monthly"),
    (BILLING_CYCLE_YEARLY, "Yearly"),
]

# -----------------------------------
# RISK MANAGEMENT CONSTANTS
# -----------------------------------
RISK_CATEGORY_STRATEGIC = 'strategic'
RISK_CATEGORY_OPERATIONAL = 'operational'
RISK_CATEGORY_FINANCIAL = 'financial'
RISK_CATEGORY_COMPLIANCE = 'compliance'
RISK_CATEGORY_REPUTATIONAL = 'reputational'
RISK_CATEGORY_TECHNOLOGICAL = 'technological'
RISK_CATEGORY_OTHER = 'other'

RISK_CATEGORY_CHOICES = [
    (RISK_CATEGORY_STRATEGIC, "Strategic"),
    (RISK_CATEGORY_OPERATIONAL, "Operational"),
    (RISK_CATEGORY_FINANCIAL, "Financial"),
    (RISK_CATEGORY_COMPLIANCE, "Compliance"),
    (RISK_CATEGORY_REPUTATIONAL, "Reputational"),
    (RISK_CATEGORY_TECHNOLOGICAL, "Technological"),
    (RISK_CATEGORY_OTHER, "Other"),
]

# -----------------------------------
# EMAIL & NOTIFICATION SETTINGS
# -----------------------------------
DEFAULT_FROM_EMAIL = "noreply@example.com"
EMAIL_SUBJECT_PREFIX = "[GRC Application] "

# -----------------------------------
# MISCELLANEOUS CONSTANTS
# -----------------------------------
# Example: Default language and timezone settings
DEFAULT_LANGUAGE_CODE = "en-us"
DEFAULT_TIME_ZONE = "UTC"

# For any additional default values, add them below.
