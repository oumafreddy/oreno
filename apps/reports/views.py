from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from risk.models import Risk, RiskRegister, Control, KRI, RiskAssessment
from django.db.models import Count, Q
import tempfile
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
from django.db.models.functions import TruncMonth
from audit.models import AuditWorkplan, Engagement, Issue, Approval
from django.db.models.functions import TruncYear
from legal.models import LegalCase
from compliance.models import ComplianceRequirement, ComplianceFramework, PolicyDocument, ComplianceObligation, ComplianceEvidence
from contracts.models import Contract, Party, ContractMilestone

def risk_report_pdf(request):
    org = request.tenant
    risks = Risk.objects.filter(organization=org)
    # Apply filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')
    if start_date:
        risks = risks.filter(date_identified__gte=start_date)
    if end_date:
        risks = risks.filter(date_identified__lte=end_date)
    if status:
        risks = risks.filter(status=status)
    html_string = render_to_string('reports/risk_report.html', {
        'organization': org,
        'risks': risks,
        'title': 'Risk Register Report',
        'description': f'This report summarizes all risks for your organization. Filters: {start_date or "Any"} to {end_date or "Any"}, Status: {status or "All"}.',
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_risk_report.pdf"'
    return response

def risk_register_summary_pdf(request):
    org = request.tenant
    risks = Risk.objects.filter(organization=org)
    category = request.GET.get('category')
    owner = request.GET.get('owner')
    status = request.GET.get('status')
    register = request.GET.get('register')
    if category:
        risks = risks.filter(category=category)
    if owner:
        risks = risks.filter(risk_owner__icontains=owner)
    if status:
        risks = risks.filter(status=status)
    if register:
        risks = risks.filter(risk_register_id=register)
    summary = {
        'by_status': risks.values('status').annotate(count=Count('id')),
        'by_category': risks.values('category').annotate(count=Count('id')),
        'by_owner': risks.values('risk_owner').annotate(count=Count('id')),
        'by_register': risks.values('risk_register__register_name').annotate(count=Count('id')),
    }
    html_string = render_to_string('reports/risk_register_summary.html', {
        'organization': org,
        'summary': summary,
        'filters': {'category': category, 'owner': owner, 'status': status, 'register': register},
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_risk_register_summary.pdf"'
    return response

def risk_heatmap_pdf(request):
    org = request.tenant
    risks = Risk.objects.filter(organization=org)
    # Prepare heatmap data (impact vs likelihood)
    impact_range = range(1, 6)
    likelihood_range = range(1, 6)
    heatmap = [[risks.filter(residual_impact_score=i, residual_likelihood_score=j).count() for i in impact_range] for j in likelihood_range]
    # Generate heatmap image
    fig, ax = plt.subplots(figsize=(8, 6))
    cax = ax.imshow(heatmap, cmap='YlOrRd', origin='lower')
    ax.set_xticks(range(len(impact_range)))
    ax.set_yticks(range(len(likelihood_range)))
    ax.set_xticklabels(impact_range)
    ax.set_yticklabels(likelihood_range)
    ax.set_xlabel('Impact')
    ax.set_ylabel('Likelihood')
    ax.set_title('Risk Heatmap')
    fig.colorbar(cax)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    html_string = render_to_string('reports/risk_heatmap.html', {
        'organization': org,
        'image_base64': image_base64,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_risk_heatmap.pdf"'
    return response

def risk_trends_pdf(request):
    org = request.tenant
    risks = Risk.objects.filter(organization=org)
    # Group by month using TruncMonth for DB compatibility
    risks_by_month = (
        risks.annotate(month=TruncMonth('date_identified'))
             .values('month')
             .annotate(count=Count('id'))
             .order_by('month')
    )
    months = [r['month'].strftime('%Y-%m') if r['month'] else '' for r in risks_by_month]
    counts = [r['count'] for r in risks_by_month]
    # Generate trend chart
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(months, counts, marker='o')
    ax.set_xlabel('Month')
    ax.set_ylabel('Number of Risks Identified')
    ax.set_title('Risk Identification Trend')
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    html_string = render_to_string('reports/risk_trends.html', {
        'organization': org,
        'image_base64': image_base64,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_risk_trends.pdf"'
    return response

def control_effectiveness_pdf(request):
    org = request.tenant
    controls = Control.objects.filter(organization=org)
    effectiveness = controls.values('effectiveness_rating').annotate(count=Count('id'))
    labels = [e['effectiveness_rating'] for e in effectiveness]
    counts = [e['count'] for e in effectiveness]
    # Pie chart
    fig, ax = plt.subplots()
    ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.set_title('Control Effectiveness Distribution')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    html_string = render_to_string('reports/control_effectiveness.html', {
        'organization': org,
        'image_base64': image_base64,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_control_effectiveness.pdf"'
    return response

def kri_status_pdf(request):
    org = request.tenant
    kris = KRI.objects.filter(risk__organization=org)
    status_counts = {'normal': 0, 'warning': 0, 'critical': 0}
    for kri in kris:
        status = kri.get_status()
        if status in status_counts:
            status_counts[status] += 1
    html_string = render_to_string('reports/kri_status.html', {
        'organization': org,
        'status_counts': status_counts,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_kri_status.pdf"'
    return response

def assessment_timeline_pdf(request):
    org = request.tenant
    assessments = RiskAssessment.objects.filter(organization=org)
    # Group by date
    timeline = assessments.values('assessment_date').annotate(avg_score=Count('risk_score')).order_by('assessment_date')
    dates = [t['assessment_date'] for t in timeline]
    scores = [t['avg_score'] for t in timeline]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(dates, scores, marker='o')
    ax.set_xlabel('Date')
    ax.set_ylabel('Avg Risk Score')
    ax.set_title('Assessment Timeline')
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    html_string = render_to_string('reports/assessment_timeline.html', {
        'organization': org,
        'image_base64': image_base64,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_assessment_timeline.pdf"'
    return response

def risk_register_detailed_pdf(request):
    org = request.tenant
    risks = Risk.objects.filter(organization=org)
    category = request.GET.get('category')
    owner = request.GET.get('owner')
    status = request.GET.get('status')
    register = request.GET.get('register')
    if category:
        risks = risks.filter(category=category)
    if owner:
        risks = risks.filter(risk_owner__icontains=owner)
    if status:
        risks = risks.filter(status=status)
    if register:
        risks = risks.filter(risk_register_id=register)
    html_string = render_to_string('reports/risk_register_detailed.html', {
        'organization': org,
        'risks': risks,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_risk_register_detailed.pdf"'
    return response

def risk_assessment_details_pdf(request):
    org = request.tenant
    assessments = RiskAssessment.objects.filter(organization=org)
    risk_id = request.GET.get('risk')
    assessment_type = request.GET.get('assessment_type')
    assessor = request.GET.get('assessor')
    min_score = request.GET.get('min_score')
    max_score = request.GET.get('max_score')
    if risk_id:
        assessments = assessments.filter(risk_id=risk_id)
    if assessment_type:
        assessments = assessments.filter(assessment_type=assessment_type)
    if assessor:
        assessments = assessments.filter(assessor__icontains=assessor)
    if min_score:
        assessments = assessments.filter(risk_score__gte=min_score)
    if max_score:
        assessments = assessments.filter(risk_score__lte=max_score)
    html_string = render_to_string('reports/risk_assessment_details.html', {
        'organization': org,
        'assessments': assessments,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_risk_assessment_details.pdf"'
    return response

def control_details_pdf(request):
    org = request.tenant
    controls = Control.objects.filter(organization=org)
    html_string = render_to_string('reports/control_details.html', {
        'organization': org,
        'controls': controls,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_control_details.pdf"'
    return response

def kri_details_pdf(request):
    org = request.tenant
    kris = KRI.objects.filter(risk__organization=org)
    html_string = render_to_string('reports/kri_details.html', {
        'organization': org,
        'kris': kris,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_kri_details.pdf"'
    return response

def workplan_summary_pdf(request):
    org = request.tenant
    year = request.GET.get('year')
    status = request.GET.get('status')
    workplans = AuditWorkplan.objects.filter(organization=org)
    if year:
        workplans = workplans.filter(fiscal_year=year)
    if status:
        workplans = workplans.filter(state=status)
    summary = workplans.values('fiscal_year', 'state').annotate(count=Count('id')).order_by('-fiscal_year')
    html_string = render_to_string('reports/audit_workplan_summary.html', {
        'organization': org,
        'summary': summary,
        'filters': {'year': year, 'status': status},
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_audit_workplan_summary.pdf"'
    return response

def get_engagement_names(org):
    return list(Engagement.objects.filter(organization=org).values_list('title', flat=True).distinct().order_by('title'))

def engagement_summary_pdf(request):
    org = request.tenant
    status = request.GET.get('status')
    assigned_to = request.GET.get('assigned_to')
    engagement_name = request.GET.get('engagement_name')
    engagements = Engagement.objects.filter(organization=org)
    if status:
        engagements = engagements.filter(project_status=status)
    if assigned_to:
        engagements = engagements.filter(assigned_to__email__icontains=assigned_to)
    if engagement_name:
        # Try exact match first, then icontains
        if engagements.filter(title=engagement_name).exists():
            engagements = engagements.filter(title=engagement_name)
        else:
            engagements = engagements.filter(title__icontains=engagement_name)
    summary = engagements.values('project_status', 'assigned_to__email').annotate(count=Count('id')).order_by('project_status')
    engagement_names = get_engagement_names(org)
    html_string = render_to_string('reports/audit_engagement_summary.html', {
        'organization': org,
        'summary': summary,
        'filters': {'status': status, 'assigned_to': assigned_to, 'engagement_name': engagement_name},
        'engagement_names': engagement_names,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_audit_engagement_summary.pdf"'
    return response

def issue_register_pdf(request):
    org = request.tenant
    status = request.GET.get('status')
    severity = request.GET.get('severity')  # risk_level param
    engagement_name = request.GET.get('engagement_name')
    issues = Issue.objects.filter(organization=org)
    if status:
        issues = issues.filter(issue_status=status)
    if severity:
        issues = issues.filter(risk_level=severity)
    if engagement_name:
        # Filter issues by engagement through the relationship chain: Issue -> Procedure -> Risk -> Objective -> Engagement
        if Engagement.objects.filter(organization=org, title=engagement_name).exists():
            issues = issues.filter(procedure__risk__objective__engagement__title=engagement_name)
        else:
            issues = issues.filter(procedure__risk__objective__engagement__title__icontains=engagement_name)
    engagement_names = get_engagement_names(org)
    html_string = render_to_string('reports/audit_issue_register.html', {
        'organization': org,
        'issues': issues,
        'filters': {'status': status, 'severity': severity, 'engagement_name': engagement_name},
        'engagement_names': engagement_names,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_audit_issue_register.pdf"'
    return response

def issue_followup_pdf(request):
    org = request.tenant
    overdue = request.GET.get('overdue')
    issues = Issue.objects.filter(organization=org)
    if overdue == '1':
        from django.utils import timezone
        today = timezone.now().date()
        issues = issues.filter(target_date__lt=today, issue_status__in=['open', 'in_progress'])
    html_string = render_to_string('reports/audit_issue_followup.html', {
        'organization': org,
        'issues': issues,
        'filters': {'overdue': overdue},
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_audit_issue_followup.pdf"'
    return response

def approval_workflow_pdf(request):
    org = request.tenant
    status = request.GET.get('status')
    approvals = Approval.objects.filter(organization=org)
    if status:
        approvals = approvals.filter(status=status)
    html_string = render_to_string('reports/audit_approval_workflow.html', {
        'organization': org,
        'approvals': approvals,
        'filters': {'status': status},
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_audit_approval_workflow.pdf"'
    return response

def smart_engagement_progress_pdf(request):
    org = request.tenant
    # Example: % closed engagements, avg duration, etc.
    from django.db.models import Avg, Count, F, ExpressionWrapper, DurationField
    from django.db.models.functions import Now
    engagements = Engagement.objects.filter(organization=org)
    total = engagements.count()
    closed = engagements.filter(project_status='closed').count()
    avg_duration = engagements.annotate(
        duration=ExpressionWrapper(F('target_end_date') - F('project_start_date'), output_field=DurationField())
    ).aggregate(avg=Avg('duration'))['avg']
    html_string = render_to_string('reports/audit_engagement_progress.html', {
        'organization': org,
        'total': total,
        'closed': closed,
        'avg_duration': avg_duration,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_audit_engagement_progress.pdf"'
    return response

def get_engagement_by_name(org, engagement_name):
    if engagement_name:
        # Try exact match first
        engagement = Engagement.objects.filter(organization=org, title=engagement_name).first()
        if not engagement:
            # Fallback to icontains for partial/typed input
            engagement = Engagement.objects.filter(organization=org, title__icontains=engagement_name).first()
        return engagement
    return None

def engagement_details_pdf(request):
    org = request.tenant
    engagement_name = request.GET.get('engagement_name') or request.GET.get('q')
    engagement = None
    if engagement_name:
        # Try exact match first, then icontains
        engagement = Engagement.objects.filter(organization=org, title=engagement_name).first()
        if not engagement:
            engagement = Engagement.objects.filter(organization=org, title__icontains=engagement_name).first()
    else:
        # If no filter, show the most recent engagement
        engagement = Engagement.objects.filter(organization=org).order_by('-project_start_date').first()
    engagement_names = get_engagement_names(org)
    html_string = render_to_string('reports/audit_engagement_details.html', {
        'organization': org,
        'engagement': engagement,
        'engagement_names': engagement_names,
        'filters': {'engagement_name': engagement_name},
        'for_pdf': True,  # Always set for PDF context
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_audit_engagement_details.pdf"'
    return response

def engagement_with_issues_pdf(request):
    org = request.tenant
    engagement_name = request.GET.get('engagement_name') or request.GET.get('q')
    engagement = None
    if engagement_name:
        engagement = Engagement.objects.filter(organization=org, title=engagement_name).first()
        if not engagement:
            engagement = Engagement.objects.filter(organization=org, title__icontains=engagement_name).first()
    else:
        engagement = Engagement.objects.filter(organization=org).order_by('-project_start_date').first()
    issues = engagement.all_issues if engagement else []
    engagement_names = get_engagement_names(org)
    html_string = render_to_string('reports/audit_engagement_with_issues.html', {
        'organization': org,
        'engagement': engagement,
        'issues': issues,
        'engagement_names': engagement_names,
        'filters': {'engagement_name': engagement_name},
        'for_pdf': True,  # Always set for PDF context
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_audit_engagement_with_issues.pdf"'
    return response

def legal_case_summary_pdf(request):
    org = request.tenant
    status = request.GET.get('status')
    case_type = request.GET.get('case_type')
    priority = request.GET.get('priority')
    lead_attorney = request.GET.get('lead_attorney')
    case_name = request.GET.get('case_name')
    cases = LegalCase.objects.filter(organization=org)
    if status:
        cases = cases.filter(status=status)
    if case_type:
        cases = cases.filter(case_type__name__icontains=case_type)
    if priority:
        cases = cases.filter(priority=priority)
    if lead_attorney:
        cases = cases.filter(lead_attorney__email__icontains=lead_attorney)
    if case_name:
        cases = cases.filter(title__icontains=case_name)
    html_string = render_to_string('reports/legal_case_summary.html', {
        'organization': org,
        'cases': cases,
        'filters': {'status': status, 'case_type': case_type, 'priority': priority, 'lead_attorney': lead_attorney, 'case_name': case_name},
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_legal_case_summary.pdf"'
    return response

def legal_case_details_pdf(request):
    org = request.tenant
    case_name = request.GET.get('case_name')
    case = None
    parties = []
    tasks = []
    documents = []
    if case_name:
        case = LegalCase.objects.filter(organization=org, title__icontains=case_name).first()
        if case:
            parties = case.parties.all()
            tasks = case.tasks.all()
            documents = case.documents.all()
    html_string = render_to_string('reports/legal_case_details.html', {
        'organization': org,
        'case': case,
        'parties': parties,
        'tasks': tasks,
        'documents': documents,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_legal_case_details.pdf"'
    return response

def compliance_requirement_summary_pdf(request):
    org = request.tenant
    requirements = ComplianceRequirement.objects.filter(organization=org)
    framework = request.GET.get('framework')
    jurisdiction = request.GET.get('jurisdiction')
    mandatory = request.GET.get('mandatory')
    policy = request.GET.get('policy')
    title = request.GET.get('title')
    if framework:
        requirements = requirements.filter(regulatory_framework__name__icontains=framework)
    if jurisdiction:
        requirements = requirements.filter(jurisdiction__icontains=jurisdiction)
    if mandatory in ['0', '1']:
        requirements = requirements.filter(mandatory=(mandatory == '1'))
    if policy:
        requirements = requirements.filter(policy_document__title__icontains=policy)
    if title:
        requirements = requirements.filter(title__icontains=title)
    html_string = render_to_string('reports/compliance_requirement_summary.html', {
        'organization': org,
        'requirements': requirements,
        'filters': {'framework': framework, 'jurisdiction': jurisdiction, 'mandatory': mandatory, 'policy': policy, 'title': title},
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_compliance_requirement_summary.pdf"'
    return response

def compliance_obligation_register_pdf(request):
    org = request.tenant
    obligations = ComplianceObligation.objects.filter(organization=org)
    status = request.GET.get('status')
    owner = request.GET.get('owner')
    due_date = request.GET.get('due_date')
    priority = request.GET.get('priority')
    requirement = request.GET.get('requirement')
    obligation_id = request.GET.get('obligation_id')
    if status:
        obligations = obligations.filter(status=status)
    if owner:
        obligations = obligations.filter(owner__email__icontains=owner)
    if due_date:
        obligations = obligations.filter(due_date=due_date)
    if priority:
        obligations = obligations.filter(priority=priority)
    if requirement:
        obligations = obligations.filter(requirement__title__icontains=requirement)
    if obligation_id:
        obligations = obligations.filter(obligation_id__icontains=obligation_id)
    html_string = render_to_string('reports/compliance_obligation_register.html', {
        'organization': org,
        'obligations': obligations,
        'filters': {'status': status, 'owner': owner, 'due_date': due_date, 'priority': priority, 'requirement': requirement, 'obligation_id': obligation_id},
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_compliance_obligation_register.pdf"'
    return response

def compliance_evidence_register_pdf(request):
    org = request.tenant
    evidences = ComplianceEvidence.objects.filter(organization=org)
    obligation = request.GET.get('obligation')
    document = request.GET.get('document')
    validity_start = request.GET.get('validity_start')
    validity_end = request.GET.get('validity_end')
    if obligation:
        evidences = evidences.filter(obligation__obligation_id__icontains=obligation)
    if document:
        evidences = evidences.filter(document__title__icontains=document)
    if validity_start:
        evidences = evidences.filter(validity_start__gte=validity_start)
    if validity_end:
        evidences = evidences.filter(validity_end__lte=validity_end)
    html_string = render_to_string('reports/compliance_evidence_register.html', {
        'organization': org,
        'evidences': evidences,
        'filters': {'obligation': obligation, 'document': document, 'validity_start': validity_start, 'validity_end': validity_end},
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_compliance_evidence_register.pdf"'
    return response

def policy_document_register_pdf(request):
    org = request.tenant
    documents = PolicyDocument.objects.filter(organization=org)
    owner = request.GET.get('owner')
    effective_date = request.GET.get('effective_date')
    expiration_date = request.GET.get('expiration_date')
    title = request.GET.get('title')
    if owner:
        documents = documents.filter(owner__email__icontains=owner)
    if effective_date:
        documents = documents.filter(effective_date=effective_date)
    if expiration_date:
        documents = documents.filter(expiration_date=expiration_date)
    if title:
        documents = documents.filter(title__icontains=title)
    html_string = render_to_string('reports/policy_document_register.html', {
        'organization': org,
        'documents': documents,
        'filters': {'owner': owner, 'effective_date': effective_date, 'expiration_date': expiration_date, 'title': title},
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_policy_document_register.pdf"'
    return response

def compliance_requirement_details_pdf(request):
    org = request.tenant
    requirement = None
    obligations = []
    evidences = []
    title = request.GET.get('title')
    if title:
        requirement = ComplianceRequirement.objects.filter(organization=org, title__icontains=title).first()
        if requirement:
            obligations = ComplianceObligation.objects.filter(requirement=requirement)
            evidences = ComplianceEvidence.objects.filter(obligation__in=obligations)
    html_string = render_to_string('reports/compliance_requirement_details.html', {
        'organization': org,
        'requirement': requirement,
        'obligations': obligations,
        'evidences': evidences,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_compliance_requirement_details.pdf"'
    return response

def compliance_obligation_details_pdf(request):
    org = request.tenant
    obligation = None
    evidences = []
    obligation_id = request.GET.get('obligation_id')
    if obligation_id:
        obligation = ComplianceObligation.objects.filter(organization=org, obligation_id__icontains=obligation_id).first()
        if obligation:
            evidences = ComplianceEvidence.objects.filter(obligation=obligation)
    html_string = render_to_string('reports/compliance_obligation_details.html', {
        'organization': org,
        'obligation': obligation,
        'evidences': evidences,
    })
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{org.code}_compliance_obligation_details.pdf"'
    return response

def contract_register_summary_pdf(request):
    org = request.tenant
    contracts = Contract.objects.filter(organization=org)
    status = request.GET.get('status')
    type_ = request.GET.get('type')
    party = request.GET.get('party')
    title = request.GET.get('title')
    if status:
        contracts = contracts.filter(status=status)
    if type_:
        contracts = contracts.filter(contract_type__name__icontains=type_)
    if party:
        contracts = contracts.filter(parties__name__icontains=party)
    if title:
        contracts = contracts.filter(title__icontains=title)
    filters = {'status': status, 'type': type_, 'party': party, 'title': title}
    return render(request, 'reports/contract_register_summary.html', {
        'contracts': contracts,
        'organization': org,
        'filters': filters,
    })

def contract_register_detailed_pdf(request):
    org = request.tenant
    contracts = Contract.objects.filter(organization=org)
    status = request.GET.get('status')
    type_ = request.GET.get('type')
    party = request.GET.get('party')
    title = request.GET.get('title')
    if status:
        contracts = contracts.filter(status=status)
    if type_:
        contracts = contracts.filter(contract_type__name__icontains=type_)
    if party:
        contracts = contracts.filter(parties__name__icontains=party)
    if title:
        contracts = contracts.filter(title__icontains=title)
    filters = {'status': status, 'type': type_, 'party': party, 'title': title}
    return render(request, 'reports/contract_register_detailed.html', {
        'contracts': contracts,
        'organization': org,
        'filters': filters,
    })

def milestone_register_pdf(request):
    org = request.tenant
    milestones = ContractMilestone.objects.filter(organization=org)
    type_ = request.GET.get('type')
    due_date = request.GET.get('due_date')
    status = request.GET.get('status')
    if type_:
        milestones = milestones.filter(milestone_type__icontains=type_)
    if due_date:
        milestones = milestones.filter(due_date=due_date)
    if status:
        milestones = milestones.filter(status=status)
    filters = {'type': type_, 'due_date': due_date, 'status': status}
    return render(request, 'reports/milestone_register.html', {
        'milestones': milestones,
        'organization': org,
        'filters': filters,
    })

def party_register_pdf(request):
    org = request.tenant
    parties = Party.objects.filter(organization=org)
    party_name = request.GET.get('party_name')
    role = request.GET.get('role')
    if party_name:
        parties = parties.filter(name__icontains=party_name)
    if role:
        parties = parties.filter(role__icontains=role)
    filters = {'party_name': party_name, 'role': role}
    return render(request, 'reports/party_register.html', {
        'parties': parties,
        'organization': org,
        'filters': filters,
    })

def contract_expiry_pdf(request):
    org = request.tenant
    contracts = Contract.objects.filter(organization=org)
    # Optionally filter by expiry date range
    expiry_start = request.GET.get('expiry_start')
    expiry_end = request.GET.get('expiry_end')
    if expiry_start:
        contracts = contracts.filter(expiry_date__gte=expiry_start)
    if expiry_end:
        contracts = contracts.filter(expiry_date__lte=expiry_end)
    filters = {'expiry_start': expiry_start, 'expiry_end': expiry_end}
    return render(request, 'reports/contract_expiry.html', {
        'contracts': contracts,
        'organization': org,
        'filters': filters,
    })

def contract_details_pdf(request):
    org = request.tenant
    contracts = Contract.objects.filter(organization=org)
    return render(request, 'reports/contract_details.html', {
        'contracts': contracts,
        'organization': org
    })

def milestone_details_pdf(request):
    org = request.tenant
    milestones = ContractMilestone.objects.filter(organization=org)
    return render(request, 'reports/milestone_details.html', {
        'milestones': milestones,
        'organization': org
    })

def party_details_pdf(request):
    org = request.tenant
    parties = Party.objects.filter(organization=org)
    return render(request, 'reports/party_details.html', {
        'parties': parties,
        'organization': org
    }) 