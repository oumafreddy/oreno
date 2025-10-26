# AI Governance Quick Reference Guide
## Oreno GRC Platform - AI Governance Module

**Version:** 2.0  
**Last Updated:** January 2025  

---

## 🚀 Quick Start Checklist

### First-Time Setup
- [ ] Access AI Governance from main navigation
- [ ] Review user permissions and role
- [ ] Explore the dashboard components
- [ ] Register your first model
- [ ] Create a test plan
- [ ] Execute your first test run
- [ ] Review test results and metrics
- [ ] Set up compliance frameworks
- [ ] Generate a compliance report

---

## 📋 Daily Operations

### Core AI Components
| Action | Navigation Path | Key Fields |
|--------|----------------|------------|
| **Register Model** | Core AI → Models → Add Model | Name, Type, URI, Version |
| **View Models** | Core AI → Models → List | Filter by type, PII status |
| **Update Model** | Core AI → Models → [Model] → Edit | Security classifications |
| **Add Dataset** | Core AI → Datasets → Add Dataset | Name, Role, Format, Schema |
| **Create Test Plan** | Core AI → Test Plans → Add Test Plan | Name, Tests, Parameters |
| **Run Test** | Core AI → Test Runs → Create | Model, Dataset, Test Plan |
| **View Test Results** | Core AI → Test Results → List | Test Run, Status, Metrics |
| **Add Metrics** | Core AI → Metrics → Add Metric | Name, Value, Threshold |

### Compliance & Governance
| Action | Navigation Path | Key Fields |
|--------|----------------|------------|
| **Add Framework** | Compliance → Frameworks → Add Framework | Name, Version, Requirements |
| **Add Clause** | Compliance → Clauses → Add Clause | Framework, Number, Title |
| **Create Mapping** | Compliance → Mappings → Add Mapping | Framework, Clause, Test Plan |
| **Add Artifact** | Compliance → Artifacts → Add Artifact | Type, File Path, Classification |
| **Risk Assessment** | Compliance → Risk Assessments → New Assessment | Model, Risk Level, Assessor, Status |

### Integration & Configuration
| Action | Navigation Path | Key Fields |
|--------|----------------|------------|
| **Add Connector** | Integration → Connectors → Add Connector | Name, Type, Configuration |
| **Add Webhook** | Integration → Webhooks → Add Webhook | Name, URL, Events |

### Reports & Analytics
| Action | Navigation Path | Key Fields |
|--------|----------------|------------|
| **Generate Report** | Reports → Dashboard Report | Format, Date Range |
| **View Compliance** | Dashboard → Compliance Scores | Framework Status |
| **Export Data** | Reports → Export | Format, Filters |

---

## 🔧 Common Tasks

### Register a New Model
1. Go to **Core AI Components** → **Models** → **Add Model**
2. Fill in:
   - **Name**: Descriptive model name
   - **Type**: Tabular/Image/Generative
   - **URI**: Model location (MLflow/S3/Azure)
   - **Version**: Model version
3. Set security classifications
4. Click **Save**

### Execute a Test
1. Go to **Core AI Components** → **Test Runs** → **Create Test Run**
2. Select:
   - **Model**: Choose from dropdown
   - **Dataset**: Optional dataset
   - **Test Plan**: Select test configuration
3. Configure parameters
4. Click **Save & Run Test**

### Review Test Results
1. Go to **Core AI Components** → **Test Results** → **List**
2. Click on a test result to view details
3. Review metrics and artifacts
4. Check compliance status

### Set Up Compliance Framework
1. Go to **Compliance & Governance** → **Frameworks** → **Add Framework**
2. Fill in:
   - **Name**: Framework name (e.g., "EU AI Act")
   - **Version**: Framework version
   - **Description**: Detailed description
3. Add clauses and requirements
4. Click **Save**

### Generate Compliance Report
1. Go to **Reports** → **Dashboard Report**
2. Select:
   - **Format**: PDF/Word/Excel
   - **Date Range**: Last 30 days
   - **Frameworks**: EU AI Act, OECD, NIST
3. Click **Generate Report**

---

## 🎯 Model Types & Use Cases

| Model Type | Best For | Example URIs |
|------------|----------|--------------|
| **Tabular** | Classification, Regression | `mlflow://models/Model/1` |
| **Image** | Computer Vision | `s3://bucket/cv-model.pkl` |
| **Generative** | LLMs, Chatbots | `https://api.openai.com/v1/models` |

---

## 🔒 Security Classifications

| Level | Description | Access |
|-------|-------------|--------|
| **Public** | No restrictions | Anyone |
| **Internal** | Company use | Authenticated users |
| **Confidential** | Restricted | Authorized personnel |
| **Restricted** | Highly sensitive | Limited access |

---

## 📊 Test Categories

| Category | Purpose | Key Metrics |
|----------|---------|-------------|
| **Fairness** | Bias detection | Demographic parity, Equalized odds |
| **Explainability** | Model interpretability | SHAP values, Feature importance |
| **Robustness** | Attack resistance | Adversarial accuracy |
| **Privacy** | Data protection | PII detection, Differential privacy |

---

## 🚨 Common Issues & Solutions

### Test Execution Fails
**Problem**: Tests timeout or fail to start
**Solution**: 
- Check model URI accessibility
- Verify dataset format
- Increase timeout settings
- Check Celery worker status

### Permission Denied
**Problem**: Cannot access features
**Solution**:
- Verify user role and permissions
- Contact administrator
- Check organization membership

### Slow Performance
**Problem**: Dashboard or tests are slow
**Solution**:
- Clear browser cache
- Reduce dataset size
- Check system resources
- Contact support

---

## 📞 Support Contacts

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| **Technical Issues** | ai-governance-support@oreno.com | 4 hours |
| **Feature Requests** | product@oreno.com | 24 hours |
| **Security Issues** | security@oreno.com | 1 hour |
| **Training** | training@oreno.com | 48 hours |

---

## 🔗 Useful Links

- **Full Manual**: [AI_GOVERNANCE_OPERATIONAL_MANUAL.md](./AI_GOVERNANCE_OPERATIONAL_MANUAL.md)
- **API Documentation**: `/ai-governance/api/`
- **Training Videos**: https://training.oreno.com/ai-governance
- **Community Forum**: https://community.oreno.com
- **Knowledge Base**: https://kb.oreno.com/ai-governance

---

## ⚡ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + M` | Go to Models |
| `Ctrl + T` | Go to Test Runs |
| `Ctrl + R` | Go to Reports |
| `Ctrl + D` | Go to Dashboard |
| `F5` | Refresh current page |

---

## 📈 Key Metrics to Monitor

### Dashboard KPIs
- **Total Models**: Number of registered models
- **Test Success Rate**: Percentage of passed tests
- **Compliance Score**: Overall compliance percentage
- **Recent Tests**: Latest test execution status

### Performance Indicators
- **Test Execution Time**: Average time per test
- **System Uptime**: Platform availability
- **User Activity**: Active users and sessions
- **Data Volume**: Models and datasets processed

---

## 🎓 Best Practices

### Model Registration
- Use descriptive names
- Include version information
- Set appropriate security classifications
- Document model purpose and limitations

### Test Planning
- Create comprehensive test plans
- Set realistic thresholds
- Include multiple test categories
- Regular test execution

### Compliance Management
- Regular compliance assessments
- Maintain audit trails
- Update frameworks as needed
- Generate regular reports

---

## 🔄 Regular Maintenance

### Daily
- [ ] Check test execution status
- [ ] Review failed tests
- [ ] Monitor system performance

### Weekly
- [ ] Generate compliance reports
- [ ] Review security classifications
- [ ] Update test plans if needed

### Monthly
- [ ] Full compliance assessment
- [ ] Security audit
- [ ] Performance review
- [ ] User access review

---

**Quick Reference Version**: 2.0  
**Last Updated**: January 2025  
**Next Review**: April 2025

---

*Keep this guide handy for quick access to common tasks and troubleshooting steps. For detailed information, refer to the full operational manual.*
