# apps/risk/models/cobit.py
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django.contrib.auth import get_user_model

class COBITDomain(OrganizationOwnedModel, AuditableModel):
    """
    COBIT 2019 Domains (EDM, APO, BAI, DSS, MEA)
    """
    DOMAIN_CHOICES = [
        ('EDM', 'Evaluate, Direct and Monitor'),
        ('APO', 'Align, Plan and Organize'),
        ('BAI', 'Build, Acquire and Implement'),
        ('DSS', 'Deliver, Service and Support'),
        ('MEA', 'Monitor, Evaluate and Assess'),
    ]
    
    domain_code = models.CharField(max_length=3, choices=DOMAIN_CHOICES, unique=True)
    domain_name = models.CharField(max_length=255)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    objectives = CKEditor5Field('Objectives', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "COBIT Domain"
        verbose_name_plural = "COBIT Domains"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_cobitdomain'
            )
        ]

class COBITProcess(OrganizationOwnedModel, AuditableModel):
    """
    COBIT 2019 Processes
    """
    domain = models.ForeignKey(COBITDomain, on_delete=models.CASCADE)
    process_code = models.CharField(max_length=10, db_index=True)  # e.g., APO01
    process_name = models.CharField(max_length=255, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    purpose = CKEditor5Field('Purpose', config_name='extends', blank=True, null=True)
    goals = CKEditor5Field('Goals', config_name='extends', blank=True, null=True)
    practices = CKEditor5Field('Practices', config_name='extends', blank=True, null=True)
    inputs = CKEditor5Field('Inputs', config_name='extends', blank=True, null=True)
    outputs = CKEditor5Field('Outputs', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "COBIT Process"
        verbose_name_plural = "COBIT Processes"
        unique_together = ['organization', 'process_code']
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_cobitprocess'
            )
        ]

class COBITCapability(OrganizationOwnedModel, AuditableModel):
    """
    COBIT 2019 Capability Maturity Model
    """
    MATURITY_LEVEL_CHOICES = [
        (0, 'Incomplete'),
        (1, 'Performed'),
        (2, 'Managed'),
        (3, 'Established'),
        (4, 'Predictable'),
        (5, 'Optimizing'),
    ]
    
    process = models.ForeignKey(COBITProcess, on_delete=models.CASCADE)
    current_maturity = models.IntegerField(choices=MATURITY_LEVEL_CHOICES, default=0)
    target_maturity = models.IntegerField(choices=MATURITY_LEVEL_CHOICES, default=3)
    assessment_date = models.DateField(auto_now_add=True)
    assessed_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    assessment_notes = CKEditor5Field('Assessment Notes', config_name='extends', blank=True, null=True)
    improvement_plan = CKEditor5Field('Improvement Plan', config_name='extends', blank=True, null=True)
    next_assessment_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "COBIT Capability"
        verbose_name_plural = "COBIT Capabilities"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_cobitcapability'
            )
        ]

class COBITControl(OrganizationOwnedModel, AuditableModel):
    """
    COBIT 2019 Control Objectives
    """
    CONTROL_TYPE_CHOICES = [
        ('preventive', 'Preventive'),
        ('detective', 'Detective'),
        ('corrective', 'Corrective'),
        ('directive', 'Directive'),
    ]
    
    process = models.ForeignKey(COBITProcess, on_delete=models.CASCADE)
    control_code = models.CharField(max_length=20, db_index=True)
    control_name = models.CharField(max_length=255, db_index=True)
    control_type = models.CharField(max_length=20, choices=CONTROL_TYPE_CHOICES)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    control_owner = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    implementation_status = models.CharField(
        max_length=25,
        choices=[
            ('not_implemented', 'Not Implemented'),
            ('partially_implemented', 'Partially Implemented'),
            ('fully_implemented', 'Fully Implemented'),
        ],
        default='not_implemented'
    )
    effectiveness_rating = models.CharField(
        max_length=20,
        choices=[
            ('not_assessed', 'Not Assessed'),
            ('ineffective', 'Ineffective'),
            ('partially_effective', 'Partially Effective'),
            ('effective', 'Effective'),
            ('highly_effective', 'Highly Effective'),
        ],
        default='not_assessed'
    )
    last_assessment_date = models.DateField(null=True, blank=True)
    next_assessment_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "COBIT Control"
        verbose_name_plural = "COBIT Controls"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_cobitcontrol'
            )
        ]

class COBITGovernance(OrganizationOwnedModel, AuditableModel):
    """
    COBIT 2019 Governance and Management Objectives
    """
    OBJECTIVE_TYPE_CHOICES = [
        ('governance', 'Governance Objective'),
        ('management', 'Management Objective'),
    ]
    
    objective_type = models.CharField(max_length=20, choices=OBJECTIVE_TYPE_CHOICES)
    objective_code = models.CharField(max_length=10, db_index=True)
    objective_name = models.CharField(max_length=255, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    outcome_statements = CKEditor5Field('Outcome Statements', config_name='extends', blank=True, null=True)
    related_processes = models.ManyToManyField(COBITProcess, blank=True)
    stakeholder_responsibilities = CKEditor5Field('Stakeholder Responsibilities', config_name='extends', blank=True, null=True)
    
    class Meta:
        verbose_name = "COBIT Governance Objective"
        verbose_name_plural = "COBIT Governance Objectives"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_cobitgovernance'
            )
        ]
