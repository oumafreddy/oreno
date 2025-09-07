# AI Governance Technical Implementation Guide
## Oreno GRC Platform - AI Governance Module

**Version:** 2.0  
**Last Updated:** January 2025  

---

## 🏗️ Architecture Overview

### System Components
- **Django App**: `ai_governance` - Core business logic
- **Celery Tasks**: Asynchronous test execution
- **PostgreSQL**: Structured data storage
- **Redis**: Caching and task queue
- **Object Storage**: Model files and artifacts

### Key Technologies
- **Django 5.1+**: Web framework
- **Django REST Framework**: API layer
- **Celery**: Task queue
- **PostgreSQL**: Database
- **Redis**: Cache and message broker

---

## 🔧 Installation & Setup

### Prerequisites
```bash
# Python 3.11+
python --version

# PostgreSQL 14+
psql --version

# Redis 6+
redis-server --version
```

### Environment Variables
```bash
# AI Governance Settings
AI_GOVERNANCE_ENABLED=true
AI_GOVERNANCE_QUEUE_PREFIX=ai_gov
AI_GOVERNANCE_CACHE_TTL=3600

# Security Settings
AI_GOVERNANCE_ENCRYPTION_KEY_ID=key-123
AI_GOVERNANCE_PII_MASKING_ENABLED=true

# Performance Settings
AI_GOVERNANCE_MAX_CONCURRENT_TESTS=5
AI_GOVERNANCE_TEST_TIMEOUT=1800
```

### Database Setup
```bash
# Create migrations
python manage.py makemigrations ai_governance

# Apply migrations
python manage.py migrate

# Seed frameworks
python manage.py seed_frameworks --organization=1
```

---

## 🗄️ Database Schema

### Core Models
```python
# Model Asset
class ModelAsset(OrganizationOwnedModel):
    name = CharField(max_length=255)
    model_type = CharField(choices=MODEL_TYPE_CHOICES)
    uri = CharField(max_length=1024)
    version = CharField(max_length=128)
    contains_pii = BooleanField(default=False)
    data_classification = CharField(choices=CLASSIFICATION_CHOICES)

# Test Run
class TestRun(OrganizationOwnedModel):
    model_asset = ForeignKey(ModelAsset)
    dataset_asset = ForeignKey(DatasetAsset, null=True)
    test_plan = ForeignKey(TestPlan, null=True)
    status = CharField(choices=STATUS_CHOICES)
    parameters = JSONField(default=dict)
```

### Indexes
```sql
-- Performance indexes
CREATE INDEX idx_model_asset_org_type ON ai_governance_modelasset(organization_id, model_type);
CREATE INDEX idx_test_run_status ON ai_governance_testrun(status);
CREATE INDEX idx_test_result_run ON ai_governance_testresult(test_run_id);
```

---

## 🔄 API Endpoints

### Model Management
```python
# List models
GET /ai-governance/api/models/
POST /ai-governance/api/models/
GET /ai-governance/api/models/{id}/
PUT /ai-governance/api/models/{id}/
DELETE /ai-governance/api/models/{id}/

# Test execution
POST /ai-governance/api/test-runs/
GET /ai-governance/api/test-runs/{id}/
GET /ai-governance/api/test-runs/{id}/results/
```

### Webhook Integration
```python
# Test webhook
POST /ai-governance/api/webhooks/{id}/test/

# Webhook payload
{
  "event": "test_run.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "test_run_id": 123,
    "status": "completed",
    "results": {...}
  }
}
```

---

## ⚙️ Configuration

### Django Settings
```python
# settings.py
INSTALLED_APPS = [
    'ai_governance.apps.AIGovernanceConfig',
    # ... other apps
]

# Celery configuration
CELERY_TASK_ROUTES = {
    'ai_governance.tasks.execute_test_run': {'queue': 'ai_governance_high'},
    'ai_governance.tasks.cleanup_old_test_runs': {'queue': 'ai_governance_bulk'},
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### Security Settings
```python
# Encryption
AI_GOVERNANCE_ENCRYPTION_KEY = 'your-encryption-key'

# PII Masking
AI_GOVERNANCE_PII_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
}

# Data Retention
AI_GOVERNANCE_RETENTION_PERIODS = {
    'test_runs': 2555,  # 7 years
    'test_results': 2555,
    'model_metadata': 3650,  # 10 years
}
```

---

## 🚀 Deployment

### Production Checklist
- [ ] Configure environment variables
- [ ] Set up database connections
- [ ] Configure Redis cache
- [ ] Set up Celery workers
- [ ] Configure object storage
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Test webhook endpoints

### Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["gunicorn", "config.wsgi:application"]
```

### Kubernetes Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-governance
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-governance
  template:
    metadata:
      labels:
        app: ai-governance
    spec:
      containers:
      - name: ai-governance
        image: oreno/ai-governance:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ai-governance-secrets
              key: database-url
```

---

## 📊 Monitoring

### Health Checks
```python
# Health check endpoint
@api_view(['GET'])
def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'database': check_database(),
        'redis': check_redis(),
        'celery': check_celery(),
    })
```

### Metrics Collection
```python
# Performance metrics
from ai_governance.performance import performance_monitor

@performance_monitor.monitor_query_performance('dashboard_metrics')
def get_dashboard_metrics():
    # Dashboard logic
    pass
```

### Logging Configuration
```python
# logging.conf
[loggers]
keys=root,ai_governance

[handlers]
keys=console,file

[formatters]
keys=standard

[logger_ai_governance]
level=INFO
handlers=console,file
qualname=ai_governance

[handler_file]
class=FileHandler
level=INFO
formatter=standard
args=('/var/log/ai_governance/app.log',)
```

---

## 🔒 Security Implementation

### Authentication
```python
# JWT Authentication
from rest_framework_simplejwt.authentication import JWTAuthentication

class AIGovernanceViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsOrgStaffOrReadOnly]
```

### Data Encryption
```python
# Encryption service
from ai_governance.security import encryption_service

# Encrypt sensitive data
encrypted_data = encryption_service.encrypt_data(sensitive_data)

# Decrypt data
decrypted_data = encryption_service.decrypt_data(encrypted_data)
```

### PII Masking
```python
# PII masking service
from ai_governance.security import pii_masking_service

# Detect PII
pii_detected = pii_masking_service.detect_pii(text)

# Mask PII
masked_text, mask_counts = pii_masking_service.mask_pii(text)
```

---

## 🧪 Testing

### Unit Tests
```python
# test_models.py
from django.test import TestCase
from ai_governance.models import ModelAsset

class ModelAssetTestCase(TestCase):
    def test_model_creation(self):
        model = ModelAsset.objects.create(
            name="Test Model",
            model_type="tabular",
            uri="test://model.pkl"
        )
        self.assertEqual(model.name, "Test Model")
```

### Integration Tests
```python
# test_api.py
from rest_framework.test import APITestCase

class ModelAssetAPITestCase(APITestCase):
    def test_create_model(self):
        data = {
            'name': 'Test Model',
            'model_type': 'tabular',
            'uri': 'test://model.pkl'
        }
        response = self.client.post('/ai-governance/api/models/', data)
        self.assertEqual(response.status_code, 201)
```

### Performance Tests
```python
# test_performance.py
import time
from django.test import TestCase

class PerformanceTestCase(TestCase):
    def test_dashboard_load_time(self):
        start_time = time.time()
        response = self.client.get('/ai-governance/dashboard/')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 2.0)  # < 2 seconds
```

---

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
python manage.py dbshell
>>> SELECT 1;

# Check database indexes
python manage.py sqlmigrate ai_governance 0001
```

#### Celery Worker Issues
```bash
# Check worker status
celery -A oreno status

# Restart workers
celery -A oreno restart

# Check task queue
celery -A oreno inspect active
```

#### Cache Issues
```bash
# Clear cache
python manage.py clear_cache

# Check Redis connection
redis-cli ping
```

### Performance Optimization

#### Database Optimization
```python
# Use select_related for foreign keys
models = ModelAsset.objects.select_related('organization', 'created_by')

# Use prefetch_related for many-to-many
test_runs = TestRun.objects.prefetch_related('results__metrics')
```

#### Query Optimization
```python
# Add database indexes
class ModelAsset(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['organization', 'model_type']),
            models.Index(fields=['created_at']),
        ]
```

---

## 📚 Additional Resources

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.org/)

### Community
- [Django Community](https://www.djangoproject.com/community/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/django)
- [Reddit r/django](https://www.reddit.com/r/django/)

### Support
- **Technical Support**: ai-governance-support@oreno.com
- **Documentation**: https://docs.oreno.com/ai-governance
- **GitHub Issues**: https://github.com/oreno/ai-governance/issues

---

**Technical Guide Version**: 2.0  
**Last Updated**: January 2025  
**Next Review**: April 2025

---

*This guide provides technical implementation details for developers and system administrators. For user-facing documentation, refer to the operational manual.*
