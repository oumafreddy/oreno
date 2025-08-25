# apps/risk/models/nist.py
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django.contrib.auth import get_user_model

class NISTFunction(OrganizationOwnedModel, AuditableModel):
    """
    NIST CSF Core Functions (Identify, Protect, Detect, Respond, Recover)
    """
    FUNCTION_CHOICES = [
        ('ID', 'Identify'),
        ('PR', 'Protect'),
        ('DE', 'Detect'),
        ('RS', 'Respond'),
        ('RC', 'Recover'),
    ]
    
    function_code = models.CharField(max_length=2, choices=FUNCTION_CHOICES, unique=True)
    function_name = models.CharField(max_length=255)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    objectives = CKEditor5Field('Objectives', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "NIST Function"
        verbose_name_plural = "NIST Functions"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_nistfunction'
            )
        ]

class NISTCategory(OrganizationOwnedModel, AuditableModel):
    """
    NIST CSF Categories (e.g., ID.AM, PR.AC, etc.)
    """
    function = models.ForeignKey(NISTFunction, on_delete=models.CASCADE)
    category_code = models.CharField(max_length=10, db_index=True)  # e.g., ID.AM
    category_name = models.CharField(max_length=255, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    outcomes = CKEditor5Field('Outcomes', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "NIST Category"
        verbose_name_plural = "NIST Categories"
        unique_together = ['organization', 'category_code']
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_nistcategory'
            )
        ]

class NISTSubcategory(OrganizationOwnedModel, AuditableModel):
    """
    NIST CSF Subcategories (e.g., ID.AM-1, PR.AC-1, etc.)
    """
    category = models.ForeignKey(NISTCategory, on_delete=models.CASCADE)
    subcategory_code = models.CharField(max_length=15, db_index=True)  # e.g., ID.AM-1
    subcategory_name = models.CharField(max_length=255, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    outcomes = CKEditor5Field('Outcomes', config_name='extends', blank=True, null=True)
    informative_references = CKEditor5Field('Informative References', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "NIST Subcategory"
        verbose_name_plural = "NIST Subcategories"
        unique_together = ['organization', 'subcategory_code']
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_nistsubcategory'
            )
        ]

class NISTImplementation(OrganizationOwnedModel, AuditableModel):
    """
    NIST CSF Implementation Status and Maturity
    """
    MATURITY_LEVEL_CHOICES = [
        (1, 'Partial'),
        (2, 'Risk Informed'),
        (3, 'Repeatable'),
        (4, 'Adaptive'),
    ]
    
    subcategory = models.ForeignKey(NISTSubcategory, on_delete=models.CASCADE)
    current_maturity = models.IntegerField(choices=MATURITY_LEVEL_CHOICES, default=1)
    target_maturity = models.IntegerField(choices=MATURITY_LEVEL_CHOICES, default=3)
    implementation_status = models.CharField(
        max_length=25,
        choices=[
            ('not_implemented', 'Not Implemented'),
            ('partially_implemented', 'Partially Implemented'),
            ('fully_implemented', 'Fully Implemented'),
        ],
        default='not_implemented'
    )
    assessment_date = models.DateField(auto_now_add=True)
    assessed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    assessment_notes = CKEditor5Field('Assessment Notes', config_name='extends', blank=True, null=True)
    implementation_plan = CKEditor5Field('Implementation Plan', config_name='extends', blank=True, null=True)
    next_assessment_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "NIST Implementation"
        verbose_name_plural = "NIST Implementations"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_nistimplementation'
            )
        ]

class NISTThreat(OrganizationOwnedModel, AuditableModel):
    """
    NIST CSF Threat Intelligence and Modeling
    """
    THREAT_TYPE_CHOICES = [
        ('adversarial', 'Adversarial'),
        ('accidental', 'Accidental'),
        ('structural', 'Structural'),
        ('environmental', 'Environmental'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    threat_name = models.CharField(max_length=255, db_index=True)
    threat_type = models.CharField(max_length=20, choices=THREAT_TYPE_CHOICES)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    likelihood = models.CharField(
        max_length=20,
        choices=[
            ('rare', 'Rare'),
            ('unlikely', 'Unlikely'),
            ('possible', 'Possible'),
            ('likely', 'Likely'),
            ('certain', 'Certain'),
        ]
    )
    impact_analysis = CKEditor5Field('Impact Analysis', config_name='extends', blank=True, null=True)
    affected_assets = CKEditor5Field('Affected Assets', config_name='extends', blank=True, null=True)
    mitigation_strategies = CKEditor5Field('Mitigation Strategies', config_name='extends', blank=True, null=True)
    related_subcategories = models.ManyToManyField(NISTSubcategory, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "NIST Threat"
        verbose_name_plural = "NIST Threats"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_nistthreat'
            )
        ]

class NISTIncident(OrganizationOwnedModel, AuditableModel):
    """
    NIST CSF Incident Response Framework
    """
    INCIDENT_TYPE_CHOICES = [
        ('data_breach', 'Data Breach'),
        ('malware', 'Malware'),
        ('phishing', 'Phishing'),
        ('ddos', 'DDoS Attack'),
        ('insider_threat', 'Insider Threat'),
        ('physical', 'Physical Security'),
        ('other', 'Other'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('detected', 'Detected'),
        ('analyzing', 'Analyzing'),
        ('contained', 'Contained'),
        ('eradicated', 'Eradicated'),
        ('recovered', 'Recovered'),
        ('lessons_learned', 'Lessons Learned'),
        ('closed', 'Closed'),
    ]
    
    incident_id = models.CharField(max_length=50, unique=True, db_index=True)
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPE_CHOICES)
    title = models.CharField(max_length=255, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='detected')
    detected_date = models.DateTimeField(auto_now_add=True)
    reported_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='reported_nist_incidents')
    incident_team = models.ManyToManyField(get_user_model(), related_name='assigned_nist_incidents', blank=True)
    affected_systems = CKEditor5Field('Affected Systems', config_name='extends', blank=True, null=True)
    containment_actions = CKEditor5Field('Containment Actions', config_name='extends', blank=True, null=True)
    eradication_actions = CKEditor5Field('Eradication Actions', config_name='extends', blank=True, null=True)
    recovery_actions = CKEditor5Field('Recovery Actions', config_name='extends', blank=True, null=True)
    lessons_learned = CKEditor5Field('Lessons Learned', config_name='extends', blank=True, null=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "NIST Incident"
        verbose_name_plural = "NIST Incidents"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_nistincident'
            )
        ]
