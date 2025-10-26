# AI Governance Security Configuration

## Overview
This document provides configuration instructions for the enhanced AI Governance security features implemented in Phase 1, including Model Risk Assessment and Enhanced Key Management.

## Model Risk Assessment Configuration

### 1. Database Migration
Run the following command to create the new ModelRiskAssessment table:

```bash
python manage.py makemigrations ai_governance
python manage.py migrate
```

### 2. Permissions Setup
Add the following permissions to your user roles:

```python
# In your user management system
RISK_ASSESSMENT_PERMISSIONS = [
    'ai_governance.add_modelriskassessment',
    'ai_governance.change_modelriskassessment',
    'ai_governance.view_modelriskassessment',
    'ai_governance.delete_modelriskassessment',
]

# Role-based access control
RISK_ASSESSMENT_ROLES = {
    'risk_assessor': ['add_modelriskassessment', 'change_modelriskassessment', 'view_modelriskassessment'],
    'risk_approver': ['view_modelriskassessment', 'change_modelriskassessment'],
    'security_admin': ['add_modelriskassessment', 'change_modelriskassessment', 'view_modelriskassessment', 'delete_modelriskassessment'],
}
```

## Enhanced Key Management Configuration

### 1. Settings Configuration

Add the following settings to your Django settings file:

```python
# AI Governance Security Settings
AI_GOVERNANCE_USE_HSM = True  # Set to False for local key management
AI_GOVERNANCE_KMS_PROVIDER = 'aws'  # Options: 'local', 'aws', 'azure', 'gcp'
AI_GOVERNANCE_KEY_ROTATION_DAYS = 90  # Key rotation interval in days

# AWS KMS Configuration (if using AWS)
AWS_KMS_KEY_ID = 'arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012'
AWS_REGION = 'us-east-1'

# Azure Key Vault Configuration (if using Azure)
AZURE_KEY_VAULT_URL = 'https://your-keyvault.vault.azure.net/'
AZURE_KEY_NAME = 'ai-governance-key'

# Google Cloud KMS Configuration (if using GCP)
GCP_PROJECT_ID = 'your-project-id'
GCP_KMS_LOCATION = 'global'
GCP_KMS_KEY_RING = 'ai-governance'
GCP_KMS_KEY_NAME = 'ai-governance-key'
```

### 2. Required Dependencies

Install the required packages for KMS integration:

```bash
# For AWS KMS
pip install boto3

# For Azure Key Vault
pip install azure-keyvault-keys azure-identity

# For Google Cloud KMS
pip install google-cloud-kms
```

### 3. Key Rotation Setup

#### Automated Key Rotation (Recommended)
Add to your crontab or task scheduler:

```bash
# Rotate keys every 90 days
0 2 1 */3 * /path/to/your/venv/bin/python /path/to/your/project/manage.py rotate_encryption_keys --all-organizations
```

#### Manual Key Rotation
```bash
# Rotate keys for all organizations
python manage.py rotate_encryption_keys --all-organizations

# Rotate keys for specific organization
python manage.py rotate_encryption_keys --organization 1

# Dry run to see what would be rotated
python manage.py rotate_encryption_keys --all-organizations --dry-run

# Force rotation even if not due
python manage.py rotate_encryption_keys --all-organizations --force
```

## Security Best Practices

### 1. Model Risk Assessment Workflow

1. **Model Registration**: All models must be registered in the system
2. **Risk Assessment**: Conduct formal risk assessment before production deployment
3. **Approval Process**: Risk assessments must be approved by authorized personnel
4. **Production Gating**: Models cannot be deployed to production without approved risk assessment
5. **Regular Reviews**: Risk assessments must be reviewed periodically

### 2. Key Management Best Practices

1. **Separation of Duties**: Different roles for key creation, rotation, and audit
2. **Regular Rotation**: Rotate keys according to organizational policy (recommended: 90 days)
3. **Audit Trail**: All key operations are logged for compliance
4. **HSM Integration**: Use Hardware Security Modules for production environments
5. **Backup and Recovery**: Ensure key backup and recovery procedures are in place

### 3. Access Control

```python
# Example role definitions
KEY_MANAGEMENT_ROLES = {
    'key_administrator': ['rotate_keys', 'view_keys', 'audit_keys'],
    'key_operator': ['view_keys'],
    'security_admin': ['audit_keys', 'view_keys'],
    'security_analyst': ['view_keys'],
}
```

## Compliance Integration

### 1. GDPR Compliance
The enhanced key management system supports GDPR requirements:
- Data encryption at rest
- Key rotation for data minimization
- Audit trails for data processing activities

### 2. ISO 27001 Compliance
Key management controls align with ISO 27001:
- A.10.1.1: Cryptographic controls
- A.12.1.1: Documented operating procedures
- A.16.1.1: Management of information security incidents

### 3. SOC 2 Compliance
The system provides:
- Logical access controls
- Data encryption
- Audit logging
- Incident response capabilities

## Monitoring and Alerting

### 1. Key Rotation Monitoring
Set up alerts for:
- Failed key rotations
- Overdue key rotations
- Unauthorized key access attempts

### 2. Risk Assessment Monitoring
Monitor for:
- Models without risk assessments
- Overdue risk assessment reviews
- High-risk models in production

### 3. Security Event Monitoring
Track:
- Key usage patterns
- Risk assessment approvals/rejections
- Security policy violations

## Troubleshooting

### Common Issues

1. **KMS Connection Failures**
   - Verify credentials and permissions
   - Check network connectivity
   - Validate KMS configuration

2. **Key Rotation Failures**
   - Check KMS quotas and limits
   - Verify backup procedures
   - Review audit logs

3. **Risk Assessment Workflow Issues**
   - Verify user permissions
   - Check approval workflow configuration
   - Review model asset associations

### Support Commands

```bash
# Check key management status
python manage.py shell
>>> from ai_governance.security import key_management_service
>>> key_management_service.get_key_usage_audit_trail(organization_id=1)

# Validate risk assessment workflow
python manage.py shell
>>> from ai_governance.models import ModelRiskAssessment
>>> ModelRiskAssessment.objects.filter(approval_status='draft').count()
```

## Migration from Existing System

### 1. Data Migration
If migrating from an existing system:

1. Export existing model metadata
2. Create risk assessments for existing models
3. Migrate encryption keys (if applicable)
4. Update access controls

### 2. User Training
Provide training on:
- Risk assessment process
- Key management procedures
- Security best practices
- Incident response procedures

## Conclusion

The enhanced AI Governance security features provide enterprise-grade security controls for AI/ML model management. Proper configuration and adherence to security best practices ensure compliance with regulatory requirements and industry standards.

For additional support or questions, refer to the AI Governance documentation or contact your security team.
