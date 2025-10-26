# Risk-Based Audit Architecture Enhancement

## Executive Summary 27/09/2025

This document outlines a critical architectural improvement needed to transform the Oreno GRC system from "risk-aware" auditing to truly "risk-based" auditing. Currently, the system maintains separate risk management systems that prevent true integration between audit activities and organizational risk management.

## Current State Analysis

### The Problem: Dual Risk Systems

**Audit App Risks:**
- `audit.models.risk.Risk` - Audit-specific risk model
- Linked to audit objectives only
- Isolated from main organizational risk management
- No connection to risk registers

**Risk App Risks:**
- `risk.models.risk.Risk` - Main organizational risk model
- Organized in risk registers (`risk.models.risk_register.RiskRegister`)
- Comprehensive risk management framework
- Proper categorization, scoring, and tracking

**Issue Model Gap:**
- `Issue.risks` field is a `CKEditor5Field` (free text)
- No actual references to risk objects
- Creates disconnect between audit findings and risk management

## Proposed Solution: True Risk-Based Auditing

### Architectural Changes Required

#### 1. Issue Model Enhancement
```python
# Current (Fragmented)
class Issue(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    risks = CKEditor5Field(_('Risks'), config_name='extends', blank=True, null=True)

# Proposed (Integrated)
class Issue(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    risks = models.ManyToManyField(
        'risk.Risk',
        related_name='audit_issues',
        blank=True,
        verbose_name=_('Related Risks'),
        help_text=_('Select risks from the organization\'s risk register that are relevant to this audit finding')
    )
```

#### 2. Form Updates
- Replace text input with multi-select widget
- Organization-scoped risk queryset
- Risk register filtering options
- Search and filter capabilities

#### 3. View Updates
- Risk selection interface
- Organization-aware risk filtering
- Integration with existing audit workflow

### Implementation Benefits

#### 1. Single Source of Truth
- All risks managed in one centralized system
- Eliminates duplication and inconsistencies
- Ensures audit activities reference actual organizational risks

#### 2. True Risk-Audit Alignment
- Clear linkage between audit findings and specific risks
- Audit recommendations directly address identified risks
- Risk mitigation efforts tracked through audit follow-up

#### 3. Enhanced Reporting
- Risk-based audit planning reports
- Audit coverage of organizational risks
- Risk mitigation effectiveness through audit findings
- Compliance with risk-based auditing standards

#### 4. Improved Workflow
- Auditors can select from actual risk registers
- Risk owners receive notifications about audit findings
- Risk management and audit teams work from same data

## Technical Implementation Plan

### Phase 1: Model Changes
1. Add ManyToManyField to Issue model
2. Create migration to preserve existing text data
3. Update serializers and admin interfaces

### Phase 2: Form and View Updates
1. Update IssueForm with risk selection widget
2. Modify views to handle risk selection
3. Add organization-scoped risk filtering

### Phase 3: Integration and Testing
1. Update templates and JavaScript
2. Comprehensive testing of risk selection workflow
3. Data migration and validation

### Phase 4: Reporting and Analytics
1. Update reports to show risk-audit relationships
2. Add risk-based audit planning features
3. Enhanced dashboard analytics

## Risk Considerations

### Data Migration
- Existing text-based risk references need careful handling
- Consider creating "legacy risk" entries for existing data
- Gradual migration approach recommended

### User Training
- Auditors need training on new risk selection process
- Risk managers need to understand audit integration
- Documentation and training materials required

### Performance
- ManyToManyField queries need optimization
- Consider caching for frequently accessed risk data
- Database indexing for efficient risk lookups

## Success Metrics

### Quantitative
- Percentage of issues linked to actual risks
- Reduction in duplicate risk entries
- Improved audit planning accuracy

### Qualitative
- User satisfaction with integrated workflow
- Improved risk-audit alignment
- Enhanced compliance reporting capabilities

## Future Enhancements

### Advanced Features
- Risk-based audit planning algorithms
- Automated risk assessment updates from audit findings
- Integration with risk appetite frameworks
- Advanced analytics and reporting

### Integration Opportunities
- Link audit procedures to specific risk controls
- Connect audit findings to risk treatment plans
- Integrate with compliance management systems

## Conclusion

This architectural enhancement represents a fundamental improvement to the Oreno GRC system, transforming it from a collection of separate modules to a truly integrated risk-based auditing platform. The implementation will require careful planning and execution but will result in significant improvements in audit effectiveness and risk management alignment.

---

**Document Version:** 1.0  
**Created:** December 2024  
**Status:** Planning Phase  
**Priority:** High - Critical Architectural Improvement
