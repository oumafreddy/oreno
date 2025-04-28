from datetime import datetime, date
from django.db import models
from django.core.exceptions import ValidationError
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import make_aware
from django.utils import timezone
from django.urls import reverse
from django.utils.functional import cached_property
from django.core.validators import MinValueValidator, MaxValueValidator

# File type validation
def validate_file_extension(value):
    """Validate file extensions to prevent security risks."""
    valid_extensions = ['pdf', 'doc', 'docx', 'xlsx', 'jpg', 'jpeg', 'png']
    excluded_extensions = ['exe', 'bat', 'sh', 'py']
    
    ext = value.name.split('.')[-1].lower()
    
    if ext in excluded_extensions:
        raise ValidationError(f'The file type {ext} is not allowed.')
    elif ext not in valid_extensions:
        raise ValidationError(f'Unsupported file extension. Valid extensions are: {", ".join(valid_extensions)}.')

# File size validation 
def validate_file_size(value):
    """Validate file size to prevent excessive storage usage."""
    filesize = value.size
    limit_mb = 50
    if filesize > limit_mb * 1024 * 1024:  # 50MB limit
        raise ValidationError(f'The maximum file size that can be uploaded is {limit_mb}MB')


def default_datetime():
    """Provide a default datetime that is timezone-aware."""
    dt = datetime(2024, 8, 1, 0, 0)
    return make_aware(dt)    

# Abstract base classes for common functionality
class TimeStampedModel(models.Model):
    """Abstract base class with created and modified timestamps."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class OrganizationOwnedModel(TimeStampedModel):
    """Abstract base class for models owned by an organization."""
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    
    class Meta:
        abstract = True

class AuditableModel(TimeStampedModel):
    """Abstract base class for models that track who created and updated them."""
    created_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_created')
    updated_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, related_name='%(class)s_updated')
    
    class Meta:
        abstract = True

# Users
class CustomUser(AbstractUser):
    """Extended user model with organization relationship and role."""
    email = models.EmailField(unique=True, verbose_name="Email Address")
    organization = models.ForeignKey(
        'Organization', 
        on_delete=models.CASCADE, 
        related_name='users', 
        null=True, 
        blank=True
    )
    role = models.CharField(max_length=128, default='staff', verbose_name="User Role")
    registration_date = models.DateTimeField(default=default_datetime, verbose_name="Registration Date")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        verbose_name="Groups",
        help_text="The groups this user belongs to."
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True,
        verbose_name="User Permissions",
        help_text="Specific permissions for this user."
    )
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['organization']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username

# Model for Organization
class Organization(AuditableModel):
    """Organization model representing a customer entity."""
    customer_code = models.CharField(max_length=8, unique=True, db_index=True, verbose_name="Customer Code")
    customer_name = models.CharField(max_length=512, db_index=True, verbose_name="Customer Name")
    financial_year_end_date = models.DateField(verbose_name="Financial Year End Date")
    logo = models.ImageField(
        upload_to='organization_logos/', 
        null=True, 
        blank=True, 
        verbose_name="Organization Logo"
    )
    customer_industry = models.CharField(
        max_length=32, 
        blank=True, 
        null=True, 
        db_index=True,
        verbose_name="Industry"
    )

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ['customer_name']
        indexes = [
            models.Index(fields=['customer_code']),
            models.Index(fields=['customer_name']),
            models.Index(fields=['customer_industry']),
        ]

    def __str__(self):
        return f"{self.customer_name} ({self.customer_industry or 'N/A'})"
    
    def get_absolute_url(self):
        """Return the URL to access a particular organization instance."""
        return reverse('organization_detail', args=[str(self.id)])
    
    def get_employees(self):
        """Return all users associated with this organization."""
        return self.users.all().select_related('profile')


class Profile(models.Model):
    """User profile with additional information."""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', default='default-avatar.png', verbose_name="Profile Picture")
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"Profile for {self.user.email}"


# Role choices as constants
ADMIN = 'admin'
MANAGER = 'manager'
STAFF = 'staff'
ROLE_CHOICES = [
    (ADMIN, 'Admin'),
    (MANAGER, 'Manager'),
    (STAFF, 'Staff'),
]

# User roles and permissions
class OrganizationRole(TimeStampedModel):
    """Model for managing user roles within an organization."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='roles')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_roles')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default=STAFF, db_index=True)
    
    class Meta:
        verbose_name = "Organization Role"
        verbose_name_plural = "Organization Roles"
        unique_together = ['organization', 'user']
        indexes = [
            models.Index(fields=['organization', 'role']),
            models.Index(fields=['user', 'role']),
        ]
    
    def __str__(self):
        return f"{self.user.email} as {self.get_role_display()} in {self.organization.customer_name}"

# Onboarding invitation
def send_invitation(email, organization):
    """Send an invitation email to a new user."""
    send_mail(
        'You are invited!',
        f'Click here to join {organization.customer_name}.',
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )

class OTP(TimeStampedModel):
    """One-Time Password for user verification."""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=6, verbose_name="One-Time Password")
    is_verified = models.BooleanField(default=False, verbose_name="Verification Status")
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default=STAFF)
    
    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        indexes = [
            models.Index(fields=['user', 'is_verified']),
            models.Index(fields=['otp']),
        ]

    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp} (Verified: {self.is_verified})"


# Risk Register Model
class RiskRegister(OrganizationOwnedModel, AuditableModel):
    """Container for risks within an organization."""
    code = models.CharField(max_length=16, db_index=True, verbose_name="Register Code")
    register_name = models.CharField(max_length=255, db_index=True, verbose_name="Register Name")
    register_creation_date = models.DateField(auto_now_add=True, verbose_name="Creation Date")
    register_period = models.CharField(max_length=4, verbose_name="Period")
    register_description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "Risk Register"
        verbose_name_plural = "Risk Registers"
        ordering = ['-register_creation_date', 'register_name']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['register_name']),
            models.Index(fields=['register_period']),
        ]

    def __str__(self):
        return f"{self.register_name} ({self.register_period})"
    
    def get_absolute_url(self):
        """Return the URL to access a particular risk register instance."""
        return reverse('risk_register_detail', args=[str(self.id)])
    
    def get_risk_count(self):
        """Return the count of risks in this register."""
        return self.risks.count()
    
class RiskMatrixConfig(OrganizationOwnedModel, AuditableModel):
    """Configuration for risk scoring matrix."""
    name = models.CharField(max_length=100, default="Default Risk Matrix", verbose_name="Matrix Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    # Matrix dimensions
    impact_levels = models.IntegerField(
        default=5, 
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Number of impact levels (e.g., 5)",
        verbose_name="Impact Levels"
    )
    likelihood_levels = models.IntegerField(
        default=5, 
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Number of likelihood levels (e.g., 5)",
        verbose_name="Likelihood Levels"
    )
    
    # Risk level thresholds
    low_threshold = models.IntegerField(
        default=5, 
        help_text="Maximum score for low risk",
        verbose_name="Low Risk Threshold"
    )
    medium_threshold = models.IntegerField(
        default=10, 
        help_text="Maximum score for medium risk",
        verbose_name="Medium Risk Threshold"
    )
    high_threshold = models.IntegerField(
        default=15, 
        help_text="Maximum score for high risk",
        verbose_name="High Risk Threshold"
    )
    very_high_threshold = models.IntegerField(
        default=20, 
        help_text="Maximum score for very high risk",
        verbose_name="Very High Risk Threshold"
    )
    
    # Risk level colors (for visualization)
    low_color = models.CharField(
        max_length=7, 
        default="#00FF00", 
        help_text="Color code for low risk (e.g., #00FF00)",
        verbose_name="Low Risk Color"
    )
    medium_color = models.CharField(
        max_length=7, 
        default="#FFFF00", 
        help_text="Color code for medium risk (e.g., #FFFF00)",
        verbose_name="Medium Risk Color"
    )
    high_color = models.CharField(
        max_length=7, 
        default="#FFA500", 
        help_text="Color code for high risk (e.g., #FFA500)",
        verbose_name="High Risk Color"
    )
    very_high_color = models.CharField(
        max_length=7, 
        default="#FF0000", 
        help_text="Color code for very high risk (e.g., #FF0000)",
        verbose_name="Very High Risk Color"
    )
    critical_color = models.CharField(
        max_length=7, 
        default="#800000", 
        help_text="Color code for critical risk (e.g., #800000)",
        verbose_name="Critical Risk Color"
    )
    
    # Is this the active matrix for the organization?
    is_active = models.BooleanField(default=True, verbose_name="Active Matrix")
    
    class Meta:
        verbose_name = "Risk Matrix Configuration"
        verbose_name_plural = "Risk Matrix Configurations"
        indexes = [
            models.Index(fields=['organization', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} for {self.organization.customer_name}"
    
    def get_risk_level(self, risk_score):
        """Determine risk level based on score thresholds."""
        if risk_score <= self.low_threshold:
            return 'low'
        elif risk_score <= self.medium_threshold:
            return 'medium'
        elif risk_score <= self.high_threshold:
            return 'high'
        elif risk_score <= self.very_high_threshold:
            return 'very_high'
        else:
            return 'critical'
    
    def get_risk_level_color(self, risk_score):
        """Get the color code for a risk score."""
        risk_level = self.get_risk_level(risk_score)
        if risk_level == 'low':
            return self.low_color
        elif risk_level == 'medium':
            return self.medium_color
        elif risk_level == 'high':
            return self.high_color
        elif risk_level == 'very_high':
            return self.very_high_color
        else:  # critical
            return self.critical_color
    
    def save(self, *args, **kwargs):
        # Ensure only one active matrix per organization
        if self.is_active:
            RiskMatrixConfig.objects.filter(
                organization=self.organization, 
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        
        super().save(*args, **kwargs)

# Dropdown Choices for Risk Model
CONTROL_STATUS_CHOICES = [
    ('implemented', 'Implemented'),
    ('in-progress', 'In Progress'),
    ('not-implemented', 'Not Implemented'),
    ('planned', 'Planned'),
]

ACTION_PLAN_STATUS_CHOICES = [
    ('not-started', 'Not Started'),
    ('in-progress', 'In Progress'),
    ('completed', 'Completed'),
    ('overdue', 'Overdue'),
    ('cancelled', 'Cancelled'),
]

CONTROL_RATING_CHOICES = [
    ('effective', 'Effective'),
    ('partially-effective', 'Partially Effective'),
    ('ineffective', 'Ineffective'),
    ('not-assessed', 'Not Assessed'),
]

RISK_RESPONSE_CHOICES = [
    ('mitigate', 'Mitigate/Reduce'),
    ('accept', 'Accept'),
    ('transfer', 'Transfer/Share'),
    ('avoid', 'Avoid/Terminate'),
    ('exploit', 'Exploit/Enhance'),  # For positive risks/opportunities
]

RISK_CATEGORY_CHOICES = [
    ('strategic', 'Strategic'),
    ('operational', 'Operational'),
    ('financial', 'Financial'),
    ('compliance', 'Compliance'),
    ('reputational', 'Reputational'),
    ('technological', 'Technological'),
    ('environmental', 'Environmental'),
    ('social', 'Social'),
    ('governance', 'Governance'),
    ('other', 'Other'),
]

STATUS_CHOICES = [
    ('open', 'Open'),
    ('in-progress', 'In Progress'),
    ('closed', 'Closed'),
    ('archived', 'Archived'),
]

class Risk(OrganizationOwnedModel, AuditableModel):
    """Model for managing risks according to ISO 31000 and COSO ERM frameworks."""
    risk_register = models.ForeignKey(
        'RiskRegister', 
        on_delete=models.CASCADE, 
        related_name='risks',
        verbose_name="Risk Register"
    )

    # Risk Overview
    code = models.CharField(max_length=16, db_index=True, verbose_name="Risk Code")
    risk_name = models.CharField(max_length=512, db_index=True, verbose_name="Risk Name")
    
    # Risk Context (ISO 31000 emphasizes understanding context)
    external_context = CKEditor5Field(
        'External Context', 
        config_name='extends', 
        blank=True, 
        null=True, 
        help_text="External factors affecting this risk (market, regulatory, etc.)"
    )
    internal_context = CKEditor5Field(
        'Internal Context', 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text="Internal factors affecting this risk (processes, capabilities, etc.)"
    )
    risk_description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    
    # Risk Identification
    date_identified = models.DateField(default=timezone.now, verbose_name="Date Identified")
    identified_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Identified By")
    
    # Risk Ownership (COSO emphasizes governance)
    risk_owner = models.CharField(max_length=70, db_index=True, verbose_name="Risk Owner")
    department = models.CharField(max_length=100, blank=True, null=True, db_index=True, verbose_name="Department")
    
    # Risk Classification
    category = models.CharField(
        max_length=20, 
        choices=RISK_CATEGORY_CHOICES, 
        default='other', 
        db_index=True,
        verbose_name="Risk Category"
    )
    
    # Risk Assessment (both frameworks emphasize assessment)
    # Inherent Risk (before controls)
    inherent_impact_score = models.IntegerField(
        default=3, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Score from 1 (Low) to 5 (High)",
        verbose_name="Inherent Impact Score"
    )
    inherent_likelihood_score = models.IntegerField(
        default=3, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Score from 1 (Low) to 5 (High)",
        verbose_name="Inherent Likelihood Score"
    )
    inherent_risk_score = models.IntegerField(
        editable=False, 
        help_text="Calculated field: Impact × Likelihood",
        verbose_name="Inherent Risk Score"
    )
    
    # Residual Risk (after controls)
    residual_impact_score = models.IntegerField(
        default=3, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Score from 1 (Low) to 5 (High)",
        verbose_name="Residual Impact Score"
    )
    residual_likelihood_score = models.IntegerField(
        default=3, 
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Score from 1 (Low) to 5 (High)",
        verbose_name="Residual Likelihood Score"
    )
    residual_risk_score = models.IntegerField(
        editable=False, 
        help_text="Calculated field: Impact × Likelihood",
        verbose_name="Residual Risk Score"
    )
    
    # Risk Treatment (ISO 31000 terminology)
    risk_response_strategy = models.CharField(
        max_length=20, 
        choices=RISK_RESPONSE_CHOICES, 
        default='mitigate',
        verbose_name="Risk Response Strategy"
    )
    risk_appetite = models.IntegerField(
        default=15, 
        help_text="The maximum acceptable risk score",
        verbose_name="Risk Appetite"
    )
    
    # Controls (COSO emphasizes control activities)
    controls_description = CKEditor5Field('Controls', config_name='extends', blank=True, null=True)
    control_status = models.CharField(
        max_length=20, 
        choices=CONTROL_STATUS_CHOICES, 
        default='not-implemented',
        verbose_name="Control Status"
    )
    control_rating = models.CharField(
        max_length=20, 
        choices=CONTROL_RATING_CHOICES, 
        default='not-assessed',
        verbose_name="Control Rating"
    )
    control_owner = models.CharField(max_length=70, blank=True, null=True, verbose_name="Control Owner")
    control_last_review_date = models.DateField(null=True, blank=True, verbose_name="Last Control Review Date")
    control_next_review_date = models.DateField(null=True, blank=True, verbose_name="Next Control Review Date")
    
    # Action Plan (Treatment implementation)
    action_plan = CKEditor5Field('Action Plan', config_name='extends', blank=True, null=True)
    action_plan_status = models.CharField(
        max_length=20, 
        choices=ACTION_PLAN_STATUS_CHOICES, 
        default='not-started',
        verbose_name="Action Plan Status"
    )
    action_owner = models.CharField(max_length=70, blank=True, null=True, verbose_name="Action Owner")
    action_due_date = models.DateField(null=True, blank=True, verbose_name="Action Due Date")
    
    # Monitoring and Review (both frameworks emphasize this)
    # Key Risk Indicators (KRIs)
    kri_description = CKEditor5Field('KRI Description', config_name='extends', blank=True, null=True)
    kri_threshold = models.IntegerField(
        default=70, 
        help_text="Threshold for triggering alerts",
        verbose_name="KRI Threshold"
    )
    
    # Review Dates
    next_review_date = models.DateField(null=True, blank=True, verbose_name="Next Review Date")
    last_reviewed_date = models.DateField(null=True, blank=True, verbose_name="Last Reviewed Date")
    last_reviewed_by = models.CharField(max_length=70, blank=True, null=True, verbose_name="Last Reviewed By")
    
    # Status Tracking
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='open', 
        db_index=True,
        verbose_name="Risk Status"
    )
    closure_date = models.DateField(null=True, blank=True, verbose_name="Closure Date")
    closure_justification = CKEditor5Field('Closure Justification', config_name='extends', blank=True, null=True)
    
    # Additional Information
    additional_notes = CKEditor5Field('Additional Notes', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "Risk"
        verbose_name_plural = "Risks"
        ordering = ['-updated_at', 'risk_name']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['risk_register']),
            models.Index(fields=['code']),
            models.Index(fields=['risk_name']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['risk_owner']),
            models.Index(fields=['date_identified']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate risk scores before saving
        self.inherent_risk_score = self.calculate_inherent_risk()
        self.residual_risk_score = self.calculate_residual_risk()
        
        # Check if action is overdue
        self.check_action_due()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.code}: {self.risk_name} ({self.get_category_display()})"
    
    def get_absolute_url(self):
        """Return the URL to access a particular risk instance."""
        return reverse('risk_detail', args=[str(self.id)])
    
    def clean(self):
        if self.date_identified and self.date_identified > timezone.now().date():
            raise ValidationError('Date identified cannot be in the future.')
    
    def check_action_due(self):
        """Check if the action plan is overdue and update status."""
        if (self.action_due_date and 
            self.action_due_date < timezone.now().date() and 
            self.action_plan_status != 'completed'):
            self.action_plan_status = 'overdue'
    
    def calculate_inherent_risk(self):
        """Calculate inherent risk score."""
        return self.inherent_impact_score * self.inherent_likelihood_score
    
    def calculate_residual_risk(self):
        """Calculate residual risk score."""
        return self.residual_impact_score * self.residual_likelihood_score
    
    def get_risk_level(self):
        """Determine the risk level based on the residual risk score."""
        risk_score = self.residual_risk_score
        
        # Use cached_property to avoid repeated DB queries
        matrix_config = self.get_matrix_config()
        return matrix_config.get_risk_level(risk_score)
    
    @cached_property
    def get_matrix_config(self):
        """Get the risk matrix configuration for this organization."""
        return RiskMatrixConfig.objects.filter(
            organization=self.organization, 
            is_active=True
        ).first()
    
    def is_within_appetite(self):
        """Check if the residual risk is within the defined risk appetite."""
        return self.residual_risk_score <= self.risk_appetite
    
    def get_current_kri_value(self):
        """Get the most recent Key Risk Indicator (KRI) value."""
        # Use select_related to optimize query
        latest_kri = self.kris.order_by('-timestamp').first()
        return latest_kri.value if latest_kri else 0
    
    def is_kri_violated(self):
        """Check if the KRI threshold is violated."""
        current_value = self.get_current_kri_value()
        if current_value > self.kri_threshold:
            self.send_kri_alert()
            return True
        return False
    
    def send_kri_alert(self):
        """Send an alert for KRI violations."""
        # Implementation for sending alerts
        pass
    
    def get_control_effectiveness(self):
        """Calculate control effectiveness based on inherent vs residual risk."""
        if self.inherent_risk_score == 0:
            return 0
        
        reduction = self.inherent_risk_score - self.residual_risk_score
        effectiveness = (reduction / self.inherent_risk_score) * 100
        return round(effectiveness, 2)


class Control(AuditableModel, OrganizationOwnedModel):
    """Model for risk controls aligned with COSO's emphasis on control activities."""
    code = models.CharField(max_length=16, db_index=True, verbose_name="Control Code")
    name = models.CharField(max_length=255, db_index=True, verbose_name="Control Name")
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    
    # Control classification
    CONTROL_TYPE_CHOICES = [
        ('preventive', 'Preventive'),
        ('detective', 'Detective'),
        ('corrective', 'Corrective'),
        ('directive', 'Directive'),
    ]
    control_type = models.CharField(
        max_length=20, 
        choices=CONTROL_TYPE_CHOICES,
        verbose_name="Control Type"
    )
    
    CONTROL_NATURE_CHOICES = [
        ('manual', 'Manual'),
        ('automated', 'Automated'),
        ('semi-automated', 'Semi-Automated'),
    ]
    control_nature = models.CharField(
        max_length=20, 
        choices=CONTROL_NATURE_CHOICES,
        verbose_name="Control Nature"
    )
    
    CONTROL_FREQUENCY_CHOICES = [
        ('continuous', 'Continuous'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
        ('ad-hoc', 'Ad-hoc'),
    ]
    control_frequency = models.CharField(
        max_length=20, 
        choices=CONTROL_FREQUENCY_CHOICES,
        verbose_name="Control Frequency"
    )
    
    # Control status and effectiveness
    status = models.CharField(
        max_length=20, 
        choices=CONTROL_STATUS_CHOICES, 
        default='not-implemented',
        db_index=True,
        verbose_name="Control Status"
    )
    
    effectiveness_rating = models.CharField(
        max_length=20, 
        choices=CONTROL_RATING_CHOICES, 
        default='not-assessed',
        verbose_name="Effectiveness Rating"
    )
    
    # Control ownership and review
    control_owner = models.CharField(max_length=100, db_index=True, verbose_name="Control Owner")
    owner_department = models.CharField(max_length=100, blank=True, null=True, verbose_name="Owner Department")
    last_review_date = models.DateField(null=True, blank=True, verbose_name="Last Review Date")
    next_review_date = models.DateField(null=True, blank=True, verbose_name="Next Review Date")
    
    # Documentation
    documentation = models.FileField(
        upload_to='control_docs/', 
        blank=True, 
        null=True, 
        validators=[validate_file_extension, validate_file_size],
        verbose_name="Documentation"
    )
    
    # Many-to-many relationship with risks
    risks = models.ManyToManyField(Risk, related_name='controls', through='RiskControl')
    
    class Meta:
        verbose_name = "Control"
        verbose_name_plural = "Controls"
        ordering = ['code']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['code']),
            models.Index(fields=['control_owner']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.code}: {self.name}"
    
    def get_absolute_url(self):
        """Return the URL to access a particular control instance."""
        return reverse('control_detail', args=[str(self.id)])


class RiskControl(models.Model):
    """Junction model for the many-to-many relationship between Risk and Control."""
    risk = models.ForeignKey(Risk, on_delete=models.CASCADE, verbose_name="Risk")
    control = models.ForeignKey(Control, on_delete=models.CASCADE, verbose_name="Control")
    
    # Specific details about how this control applies to this risk
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    
    # Effectiveness specifically for this risk-control combination
    effectiveness_rating = models.CharField(
        max_length=20, 
        choices=CONTROL_RATING_CHOICES, 
        default='not-assessed',
        verbose_name="Effectiveness Rating"
    )
    
    class Meta:
        verbose_name = "Risk Control"
        verbose_name_plural = "Risk Controls"
        unique_together = ('risk', 'control')
        indexes = [
            models.Index(fields=['risk']),
            models.Index(fields=['control']),
        ]
    
    def __str__(self):
        return f"{self.control.code} applied to {self.risk.code}"


class KRI(TimeStampedModel):
    """Key Risk Indicator model for monitoring risks."""
    risk = models.ForeignKey(Risk, on_delete=models.CASCADE, related_name='kris', verbose_name="Risk")
    name = models.CharField(max_length=255, verbose_name="KRI Name")
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    
    # KRI measurement
    value = models.FloatField(verbose_name="Value")
    unit = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Unit of measurement (%, $, count, etc.)",
        verbose_name="Unit"
    )
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Timestamp")
    
    # Thresholds
    threshold_warning = models.FloatField(help_text="Warning level threshold", verbose_name="Warning Threshold")
    threshold_critical = models.FloatField(help_text="Critical level threshold", verbose_name="Critical Threshold")
    
    # Direction
    DIRECTION_CHOICES = [
        ('increasing', 'Increasing values indicate higher risk'),
        ('decreasing', 'Decreasing values indicate higher risk'),
    ]
    direction = models.CharField(
        max_length=20, 
        choices=DIRECTION_CHOICES, 
        default='increasing',
        verbose_name="Direction"
    )
    
    # Metadata
    data_source = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="Source of the KRI data",
        verbose_name="Data Source"
    )
    collection_frequency = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="How often this KRI is collected",
        verbose_name="Collection Frequency"
    )
    
    class Meta:
        verbose_name = "Key Risk Indicator"
        verbose_name_plural = "Key Risk Indicators"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['risk']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.name} for {self.risk.risk_name} - Value: {self.value} {self.unit or ''}"
    
    def get_status(self):
        """Get the status of this KRI based on thresholds."""
        if self.direction == 'increasing':
            if self.value >= self.threshold_critical:
                return 'critical'
            elif self.value >= self.threshold_warning:
                return 'warning'
            return 'normal'
        else:  # decreasing
            if self.value <= self.threshold_critical:
                return 'critical'
            elif self.value <= self.threshold_warning:
                return 'warning'
            return 'normal'


class RiskAssessment(AuditableModel, OrganizationOwnedModel):
    """Model for tracking risk assessments over time."""
    risk = models.ForeignKey(Risk, on_delete=models.CASCADE, related_name='assessments', verbose_name="Risk")
    assessment_date = models.DateField(default=timezone.now, verbose_name="Assessment Date")
    assessor = models.CharField(max_length=100, verbose_name="Assessor")
    
    # Assessment scores
    impact_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Impact Score"
    )
    likelihood_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Likelihood Score"
    )
    risk_score = models.IntegerField(editable=False, verbose_name="Risk Score")  # Calculated field
    
    # Assessment type
    ASSESSMENT_TYPE_CHOICES = [
        ('inherent', 'Inherent Risk (before controls)'),
        ('residual', 'Residual Risk (after controls)'),
        ('target', 'Target Risk (desired state)'),
    ]
    assessment_type = models.CharField(
        max_length=20, 
        choices=ASSESSMENT_TYPE_CHOICES,
        verbose_name="Assessment Type"
    )
    
    # Assessment notes
    notes = CKEditor5Field('Assessment Notes', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "Risk Assessment"
        verbose_name_plural = "Risk Assessments"
        ordering = ['-assessment_date']
        indexes = [
            models.Index(fields=['risk']),
            models.Index(fields=['assessment_date']),
            models.Index(fields=['assessment_type']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate risk score
        self.risk_score = self.impact_score * self.likelihood_score
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_assessment_type_display()} Assessment for {self.risk.risk_name} on {self.assessment_date}"
    
    def get_absolute_url(self):
        """Return the URL to access a particular risk assessment instance."""
        return reverse('risk_assessment_detail', args=[str(self.id)])


# Model for Audit Workplan
class AuditWorkplan(OrganizationOwnedModel, AuditableModel):
    """Model for audit workplans."""
    code = models.CharField(max_length=8, db_index=True, verbose_name="Workplan Code")
    name = models.CharField(max_length=512, db_index=True, verbose_name="Workplan Name")
    creation_date = models.DateField(auto_now_add=True, verbose_name="Creation Date")
    description = CKEditor5Field('Description', config_name='extends', max_length=512, blank=True, null=True)
    
    class Meta:
        verbose_name = "Audit Workplan"
        verbose_name_plural = "Audit Workplans"
        ordering = ['-creation_date', 'name']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_absolute_url(self):
        """Return the URL to access a particular audit workplan instance."""
        return reverse('audit_workplan_detail', args=[str(self.id)])
   

# Model for Engagement
class Engagement(OrganizationOwnedModel, AuditableModel):
    """Model for audit engagements."""
    code = models.CharField(max_length=16, db_index=True, verbose_name="Engagement Code")
    project_name = models.CharField(max_length=512, db_index=True, verbose_name="Project Name")
    engagement_type = models.CharField(
        max_length=80, 
        blank=True, 
        null=True, 
        default='Compliance Audit',
        verbose_name="Engagement Type"
    )
    project_start_date = models.DateField(verbose_name="Start Date")
    target_end_date = models.DateField(blank=True, null=True, verbose_name="Target End Date")
    assigned_to = models.CharField(max_length=80, blank=True, null=True, verbose_name="Assigned To")
    assigned_by = models.CharField(max_length=80, blank=True, null=True, verbose_name="Assigned By")
    executive_summary = CKEditor5Field('Executive Summary', config_name='extends', blank=True, null=True)
    purpose = CKEditor5Field('Purpose', config_name='extends', blank=True, null=True)
    background = CKEditor5Field('Background', config_name='extends', blank=True, null=True)
    scope = CKEditor5Field('Scope', config_name='extends', blank=True, null=True)
    project_objectives = CKEditor5Field('Project Objectives', config_name='extends', blank=True, null=True)
    conclusion_description = CKEditor5Field('Conclusion Description', config_name='extends', blank=True, null=True)

    CONCLUSION_CHOICES = [
        ('satisfactory', 'Satisfactory'),
        ('needs improvement', 'Needs Improvement'),
        ('unsatisfactory', 'Unsatisfactory'),
    ]
    conclusion = models.CharField(
        max_length=32,
        choices=CONCLUSION_CHOICES,
        default='satisfactory',
        verbose_name="Conclusion"
    )
    
    PROJECT_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    project_status = models.CharField(
        max_length=32,
        choices=PROJECT_STATUS_CHOICES,
        default='draft',
        db_index=True,
        verbose_name="Project Status"
    )

    # Link Engagement to Audit Workplan
    auditworkplan = models.ForeignKey(
        AuditWorkplan,
        on_delete=models.CASCADE,
        related_name='engagements',
        verbose_name="Audit Workplan"
    )
    
    class Meta:
        verbose_name = "Engagement"
        verbose_name_plural = "Engagements"
        ordering = ['-project_start_date', 'project_name']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['code']),
            models.Index(fields=['project_name']),
            models.Index(fields=['project_status']),
            models.Index(fields=['auditworkplan']),
        ]

    def __str__(self):
        return f"{self.project_name} ({self.code})"
    
    def get_absolute_url(self):
        """Return the URL to access a particular engagement instance."""
        return reverse('engagement_detail', args=[str(self.id)])

    def clean(self):
        if self.project_start_date and self.target_end_date and self.project_start_date > self.target_end_date:
            raise ValidationError('Target end date cannot be before the project start date.')


# Model for Issue
class Issue(OrganizationOwnedModel, AuditableModel):
    """Model for audit issues."""
    code = models.CharField(max_length=16, db_index=True, verbose_name="Issue Code")
    issue_title = models.CharField(max_length=512, db_index=True, verbose_name="Issue Title")
    issue_description = CKEditor5Field('Issue Description', config_name='extends', blank=True, null=True)
    root_cause = CKEditor5Field('Root Cause', config_name='extends', blank=True, null=True)
    risks = CKEditor5Field('Risks', config_name='extends', blank=True, null=True)
    date_identified = models.DateField(verbose_name="Date Identified")
    issue_owner = models.CharField(max_length=100, blank=True, null=True, db_index=True, verbose_name="Issue Owner")
    issue_owner_title = models.CharField(max_length=100, blank=True, null=True, verbose_name="Issue Owner Title")
    audit_procedures = CKEditor5Field(
        'Audit Procedures', 
        config_name='extends', 
        default='Bank reconciliation reperformance',
        verbose_name="Audit Procedures"
    )
    recommendation = CKEditor5Field('Recommendation', config_name='extends', blank=True, null=True)
    
    # Link Issue to Engagement
    engagement = models.ForeignKey(
        Engagement,
        on_delete=models.CASCADE,
        related_name='issues',
        verbose_name="Engagement"
    )

    SEVERITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    severity_status = models.CharField(
        max_length=12,
        choices=SEVERITY_CHOICES,
        default='high',
        db_index=True,
        verbose_name="Severity"
    )
    
    ISSUE_CHOICES = [
        ('open', 'Open'),
        ('in progress', 'In Progress'),
        ('closed', 'Closed'),
    ]
    issue_status = models.CharField(
        max_length=56,
        choices=ISSUE_CHOICES,
        default='open',
        db_index=True,
        verbose_name="Issue Status"
    )
    
    REMEDIATION_CHOICES = [
        ('open', 'Open'),
        ('management remediating', 'Management Remediating'),
        ('remediated awaiting verification', 'Remediated Awaiting Verification'),
        ('closed', 'Closed'),
    ]
    remediation_status = models.CharField(
        max_length=56,
        choices=REMEDIATION_CHOICES,
        default='open',
        db_index=True,
        verbose_name="Remediation Status"
    )    
    remediation_deadline_date = models.DateField(blank=True, null=True, verbose_name="Remediation Deadline")
    actual_remediation_date = models.DateField(blank=True, null=True, verbose_name="Actual Remediation Date")
    management_action_plan = CKEditor5Field('Management Action Plan', config_name='extends', blank=True, null=True)
    
    # Working papers field with file type validation
    working_papers = models.FileField(
        upload_to='working_papers/', 
        blank=True, 
        null=True, 
        validators=[validate_file_extension, validate_file_size],
        verbose_name="Working Papers"
    )
    
    class Meta:
        verbose_name = "Issue"
        verbose_name_plural = "Issues"
        ordering = ['-date_identified', 'issue_title']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['code']),
            models.Index(fields=['issue_title']),
            models.Index(fields=['issue_status']),
            models.Index(fields=['severity_status']),
            models.Index(fields=['remediation_status']),
            models.Index(fields=['engagement']),
        ]
    
    def __str__(self):
        return f"{self.issue_title} ({self.issue_status})"
    
    def get_absolute_url(self):
        """Return the URL to access a particular issue instance."""
        return reverse('issue_detail', args=[str(self.id)])
    
    def clean(self):
        if self.date_identified and self.date_identified > timezone.now().date():
            raise ValidationError('Date identified cannot be in the future.')
        
        if (self.remediation_deadline_date and self.actual_remediation_date and 
            self.remediation_deadline_date > self.actual_remediation_date):
            raise ValidationError('Actual remediation date cannot be before the deadline date.')


# Document management
class DocumentRequest(OrganizationOwnedModel, AuditableModel):
    """Model for document requests."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]

    request_name = models.CharField(max_length=255, db_index=True, verbose_name="Request Name")
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending',
        db_index=True,
        verbose_name="Status"
    )
    file = models.FileField(
        upload_to='media/', 
        null=True, 
        blank=True,
        validators=[validate_file_extension, validate_file_size],
        verbose_name="File"
    )
    due_date = models.DateField(verbose_name="Due Date")
    date_of_request = models.DateField(default=timezone.now, verbose_name="Request Date")
    request_owner = models.ForeignKey(
        CustomUser, 
        related_name='requests_made', 
        on_delete=models.CASCADE,
        verbose_name="Request Owner"
    )
    
    requestee = models.ForeignKey(
        CustomUser, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='requests_received',
        verbose_name="Requestee"
    )
    requestee_email = models.EmailField(null=True, blank=True, verbose_name="Requestee Email")

    requestee_identifier = models.CharField(
        max_length=255, 
        help_text="Enter details about the requestee (team, department, etc.)",
        verbose_name="Requestee Identifier"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")
    
    class Meta:
        verbose_name = "Document Request"
        verbose_name_plural = "Document Requests"
        ordering = ['-date_of_request', 'request_name']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['request_name']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['request_owner']),
        ]

    def send_email_to_requestee(self):
        """Send an email notification to the requestee."""
        subject = f"New Document Request: {self.request_name}"
        message = f"""
        Hello,
        
        You have a new document request: {self.request_name}.
        Due date: {self.due_date}
        
        Please log in to the system to view the details and submit the requested document.
        
        Thank you,
        {self.request_owner.get_full_name()}
        """
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [self.requestee_email or self.requestee.email]
        
        # Use a task queue for sending emails asynchronously
        # For now, we'll use Django's send_mail directly
        send_mail(subject, message, from_email, recipient_list)

    def __str__(self):
        return self.request_name
    
    def get_absolute_url(self):
        """Return the URL to access a particular document request instance."""
        return reverse('document_request_detail', args=[str(self.id)])
 

class Document(OrganizationOwnedModel, AuditableModel):
    """Model for documents."""
    document_request = models.ForeignKey(
        DocumentRequest, 
        related_name='documents', 
        on_delete=models.CASCADE,
        verbose_name="Document Request"
    )
    file = models.FileField(
        upload_to='media/', 
        validators=[validate_file_extension, validate_file_size],
        verbose_name="File"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Upload Time")
    uploaded_by = models.ForeignKey(
        CustomUser, 
        related_name='documents_uploaded', 
        on_delete=models.CASCADE,
        verbose_name="Uploaded By"
    )
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['document_request']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return f'Document for {self.document_request.request_name}'
    
    def get_absolute_url(self):
        """Return the URL to access a particular document instance."""
        return reverse('document_detail', args=[str(self.id)])
