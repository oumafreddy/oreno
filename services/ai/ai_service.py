import os
import logging
import json
from typing import Optional, Dict, Any, List
from django.apps import apps
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .ollama_adapter import ask_ollama
from .llm_adapter import ask_llm

logger = logging.getLogger('services.ai.ai_service')

# Enhanced FAQ knowledge base with categories and metadata
FAQ_KB = [
    {
        'question': 'what is your role',
        'answer': 'I am Oreno GRC\'s AI assistant, designed to help you with Governance, Risk, and Compliance (GRC) questions. I can assist with audit processes, risk management, compliance requirements, and general GRC best practices. I\'m here to provide guidance and answer questions about the Oreno GRC platform and GRC concepts.',
        'category': 'general',
        'keywords': ['role', 'what', 'assistant', 'ai', 'help']
    },
    {
        'question': 'how do i use the legal app',
        'answer': 'The Legal app in Oreno GRC helps you manage contracts and legal documents. You can create, review, and store legal documents securely. To get started, go to the Legal app from the dashboard and follow the on-screen instructions.',
        'category': 'legal',
        'keywords': ['legal', 'contracts', 'documents']
    },
    {
        'question': 'what does the risk app do',
        'answer': 'The Risk app allows you to identify, assess, and monitor risks within your organization. You can create risk registers, assign owners, and track mitigation actions.',
        'category': 'risk',
        'keywords': ['risk', 'assessment', 'mitigation']
    },
    {
        'question': 'how do i get started',
        'answer': 'Welcome to Oreno GRC! Start by exploring the dashboard. Each app (Audit, Risk, Legal, Compliance, etc.) is accessible from the main menu. Click on any app to see its features and guides.',
        'category': 'general',
        'keywords': ['start', 'begin', 'dashboard']
    },
    {
        'question': 'what is grc',
        'answer': 'GRC stands for Governance, Risk, and Compliance. Governance refers to management and leadership structures. Risk management involves identifying and mitigating risks. Compliance ensures adherence to laws and regulations. Oreno GRC provides tools to manage all three areas effectively.',
        'category': 'general',
        'keywords': ['grc', 'governance', 'compliance']
    },
    {
        'question': 'how do i create a workplan',
        'answer': 'To create a workplan in the Audit app: 1) Go to the Audit dashboard, 2) Click "Create Workplan", 3) Fill in the required fields including objectives and description, 4) Save the workplan. You can then add engagements to your workplan.',
        'category': 'audit',
        'keywords': ['workplan', 'audit', 'create']
    },
    {
        'question': 'how do i add an engagement',
        'answer': 'To add an engagement: 1) Go to your workplan detail page, 2) Click "Add Engagement", 3) Fill in the engagement details including scope and objectives, 4) Save the engagement. You can then add objectives to your engagement.',
        'category': 'audit',
        'keywords': ['engagement', 'audit', 'add']
    },
    {
        'question': 'how many workplans do i have',
        'answer': 'I can check your current workplans. Let me look at your organization data to give you the exact count and details.',
        'category': 'audit',
        'keywords': ['workplans', 'count', 'how many', 'audit']
    },
    {
        'question': 'what are my current risks',
        'answer': 'I can analyze your current risk profile. Let me check your organization data to show you your active risks, their severity levels, and any high-priority items that need attention.',
        'category': 'risk',
        'keywords': ['risks', 'current', 'risk profile', 'severity']
    },
    {
        'question': 'show me my compliance status',
        'answer': 'I can provide you with a comprehensive compliance overview. Let me check your organization data to show you your obligations, overdue items, and compliance metrics.',
        'category': 'compliance',
        'keywords': ['compliance', 'status', 'obligations', 'overdue']
    },
    {
        'question': 'what contracts are expiring soon',
        'answer': 'I can check your contract portfolio for upcoming expirations. Let me analyze your organization data to identify contracts that need renewal attention.',
        'category': 'contracts',
        'keywords': ['contracts', 'expiring', 'renewal', 'expiration']
    }
]

class OrganizationDataProvider:
    """Provides organization-specific data for AI context"""
    
    def __init__(self, user, org):
        self.user = user
        self.org = org
        self.cache = {}
    
    def get_audit_data(self) -> Dict[str, Any]:
        """Get audit-related data for the organization"""
        if 'audit' in self.cache:
            return self.cache['audit']
        
        try:
            AuditWorkplan = apps.get_model('audit', 'AuditWorkplan')
            Engagement = apps.get_model('audit', 'Engagement')
            Issue = apps.get_model('audit', 'Issue')
            
            # Get workplans
            workplans = AuditWorkplan.objects.filter(organization=self.org).order_by('-created_at')[:5]
            workplan_data = []
            for wp in workplans:
                workplan_data.append({
                    'code': wp.code,
                    'name': wp.name,
                    'fiscal_year': wp.fiscal_year,
                    'status': wp.approval_status,
                    'engagements_count': wp.engagements.count()
                })
            
            # Get engagements
            engagements = Engagement.objects.filter(organization=self.org).order_by('-created_at')[:10]
            engagement_data = []
            for eng in engagements:
                engagement_data.append({
                    'code': eng.code,
                    'title': eng.title,
                    'status': eng.project_status,
                    'type': eng.engagement_type,
                    'workplan': eng.annual_workplan.name if eng.annual_workplan else None
                })
            
            # Get issues
            issues = Issue.objects.filter(organization=self.org).order_by('-created_at')[:10]
            issue_data = []
            for issue in issues:
                issue_data.append({
                    'title': issue.title,
                    'severity': issue.severity,
                    'status': issue.status,
                    'engagement': issue.procedure.risk.objective.engagement.title if issue.procedure else None
                })
            
            audit_data = {
                'workplans': workplan_data,
                'engagements': engagement_data,
                'issues': issue_data,
                'total_workplans': AuditWorkplan.objects.filter(organization=self.org).count(),
                'total_engagements': Engagement.objects.filter(organization=self.org).count(),
                'total_issues': Issue.objects.filter(organization=self.org).count(),
                'active_engagements': Engagement.objects.filter(organization=self.org, project_status__in=['planning', 'fieldwork']).count()
            }
            
            self.cache['audit'] = audit_data
            return audit_data
            
        except Exception as e:
            logger.error(f"Error getting audit data: {e}")
            return {}
    
    def get_risk_data(self) -> Dict[str, Any]:
        """Get risk-related data for the organization"""
        if 'risk' in self.cache:
            return self.cache['risk']
        
        try:
            Risk = apps.get_model('risk', 'Risk')
            
            risks = Risk.objects.filter(organization=self.org).order_by('-created_at')[:10]
            risk_data = []
            for risk in risks:
                risk_data.append({
                    'code': risk.code,
                    'name': risk.risk_name,
                    'owner': risk.risk_owner,
                    'likelihood': risk.likelihood,
                    'impact': risk.impact,
                    'status': risk.status
                })
            
            risk_summary = {
                'risks': risk_data,
                'total_risks': Risk.objects.filter(organization=self.org).count(),
                'high_risks': Risk.objects.filter(organization=self.org, likelihood__gte=4, impact__gte=4).count(),
                'medium_risks': Risk.objects.filter(organization=self.org, likelihood__in=[3, 4], impact__in=[3, 4]).count(),
                'low_risks': Risk.objects.filter(organization=self.org, likelihood__lte=2, impact__lte=2).count()
            }
            
            self.cache['risk'] = risk_summary
            return risk_summary
            
        except Exception as e:
            logger.error(f"Error getting risk data: {e}")
            return {}
    
    def get_compliance_data(self) -> Dict[str, Any]:
        """Get compliance-related data for the organization"""
        if 'compliance' in self.cache:
            return self.cache['compliance']
        
        try:
            ComplianceObligation = apps.get_model('compliance', 'ComplianceObligation')
            
            obligations = ComplianceObligation.objects.filter(organization=self.org).order_by('due_date')[:10]
            obligation_data = []
            for obl in obligations:
                obligation_data.append({
                    'id': obl.obligation_id,
                    'description': obl.description[:100] + '...' if len(obl.description) > 100 else obl.description,
                    'due_date': obl.due_date.strftime('%Y-%m-%d'),
                    'status': obl.status,
                    'priority': obl.priority
                })
            
            compliance_summary = {
                'obligations': obligation_data,
                'total_obligations': ComplianceObligation.objects.filter(organization=self.org).count(),
                'overdue_obligations': ComplianceObligation.objects.filter(organization=self.org, due_date__lt=timezone.now().date(), status__in=['open', 'in_progress']).count(),
                'completed_obligations': ComplianceObligation.objects.filter(organization=self.org, status='completed').count()
            }
            
            self.cache['compliance'] = compliance_summary
            return compliance_summary
            
        except Exception as e:
            logger.error(f"Error getting compliance data: {e}")
            return {}
    
    def get_contracts_data(self) -> Dict[str, Any]:
        """Get contracts-related data for the organization"""
        if 'contracts' in self.cache:
            return self.cache['contracts']
        
        try:
            Contract = apps.get_model('contracts', 'Contract')
            
            contracts = Contract.objects.filter(organization=self.org).order_by('-created_at')[:10]
            contract_data = []
            for contract in contracts:
                contract_data.append({
                    'code': contract.code,
                    'title': contract.title,
                    'status': contract.status,
                    'start_date': contract.start_date.strftime('%Y-%m-%d'),
                    'end_date': contract.end_date.strftime('%Y-%m-%d'),
                    'value': str(contract.value) if contract.value else 'N/A'
                })
            
            contracts_summary = {
                'contracts': contract_data,
                'total_contracts': Contract.objects.filter(organization=self.org).count(),
                'active_contracts': Contract.objects.filter(organization=self.org, status='active').count(),
                'expiring_soon': Contract.objects.filter(
                    organization=self.org, 
                    status='active',
                    end_date__lte=timezone.now().date() + timedelta(days=30)
                ).count()
            }
            
            self.cache['contracts'] = contracts_summary
            return contracts_summary
            
        except Exception as e:
            logger.error(f"Error getting contracts data: {e}")
            return {}
    
    def get_organization_summary(self) -> Dict[str, Any]:
        """Get overall organization summary"""
        return {
            'name': self.org.name,
            'id': self.org.id,
            'audit': self.get_audit_data(),
            'risk': self.get_risk_data(),
            'compliance': self.get_compliance_data(),
            'contracts': self.get_contracts_data()
        }

def find_faq_answer(question: str, user_context: Dict[str, Any] = None) -> Optional[str]:
    """Find a matching FAQ answer for the given question using improved matching with organization awareness."""
    if not question:
        return None
    
    q = question.lower().strip()
    
    # Filter FAQ entries based on organization context
    available_faqs = FAQ_KB
    
    # If we have organization context, we could filter organization-specific FAQs here
    # For now, we'll use the general FAQ but log the organization context
    if user_context:
        org_name = user_context.get('organization_name', 'Unknown')
        logger.info(f"Searching FAQ for organization: {org_name}")
    
    # First, try exact keyword matching
    for entry in available_faqs:
        if entry['question'] in q or q in entry['question']:
            logger.info(f"FAQ match found: {entry['question']}")
            return entry['answer']
    
    # Then try keyword-based matching with more flexible scoring
    question_words = set(q.split())
    best_match = None
    best_score = 0
    
    for entry in available_faqs:
        entry_keywords = set(entry['keywords'])
        score = len(question_words.intersection(entry_keywords))
        
        # Bonus points for exact word matches
        for word in question_words:
            if word in entry['question'].lower():
                score += 1
        
        if score > best_score:
            best_score = score
            best_match = entry
    
    # Return best match if score is reasonable (at least 1 keyword match)
    if best_match and best_score >= 1:
        logger.info(f"FAQ keyword match found: {best_match['question']} (score: {best_score})")
        return best_match['answer']
    
    return None

def get_user_context(user, org) -> Dict[str, Any]:
    """Get user-specific context for AI responses with enhanced organization scoping."""
    context = {
        'user_role': getattr(user, 'role', 'user'),
        'organization_id': getattr(org, 'id', None) if org else None,
        'organization_name': getattr(org, 'name', 'Unknown') if org else 'Unknown',
        'is_authenticated': user.is_authenticated,
        'user_id': user.id if user.is_authenticated else None,
        'username': user.username if user.is_authenticated else None,
    }
    
    # Add user permissions if available
    if hasattr(user, 'get_all_permissions'):
        context['permissions'] = list(user.get_all_permissions())
    
    # Add organization-specific restrictions
    if org:
        context['organization_restrictions'] = {
            'can_only_access_own_data': True,
            'organization_scope': f"Organization: {org.name} (ID: {org.id})",
            'data_boundary': f"All responses must be scoped to organization '{org.name}' only"
        }
    
    return context

def create_data_aware_prompt(question: str, user_context: Dict[str, Any], org_data: Dict[str, Any]) -> str:
    """Create a prompt that includes organization data for context-aware responses."""
    org_name = user_context.get('organization_name', 'Unknown')
    org_id = user_context.get('organization_id')
    
    # Build data context
    data_context = f"""
ORGANIZATION: {org_name} (ID: {org_id})

CURRENT DATA SUMMARY:
- Audit: {org_data.get('audit', {}).get('total_workplans', 0)} workplans, {org_data.get('audit', {}).get('total_engagements', 0)} engagements, {org_data.get('audit', {}).get('total_issues', 0)} issues
- Risk: {org_data.get('risk', {}).get('total_risks', 0)} risks ({org_data.get('risk', {}).get('high_risks', 0)} high, {org_data.get('risk', {}).get('medium_risks', 0)} medium)
- Compliance: {org_data.get('compliance', {}).get('total_obligations', 0)} obligations ({org_data.get('compliance', {}).get('overdue_obligations', 0)} overdue)
- Contracts: {org_data.get('contracts', {}).get('total_contracts', 0)} contracts ({org_data.get('contracts', {}).get('active_contracts', 0)} active)

USER QUESTION: {question}

INSTRUCTIONS:
1. Use the organization data above to provide specific, relevant answers
2. Reference actual data when possible (e.g., "You have 5 active engagements")
3. Provide actionable insights based on the current state
4. Focus on {org_name}'s specific context
5. If asked about data, use the provided summary rather than making assumptions
"""
    return data_context.strip()

def validate_ai_response(response: str, user_context: Dict[str, Any] = None) -> bool:
    """Validate AI response for safety and quality with organization scoping."""
    if not response or not isinstance(response, str):
        return False
    
    response_lower = response.lower()
    
    # Check for potentially harmful content - more specific patterns
    harmful_patterns = [
        'password:',
        'api key:',
        'secret:',
        'private data:',
        'other users:',
        'other organizations:',
        'database password',
        'admin password',
        'root password',
    ]
    
    for pattern in harmful_patterns:
        if pattern in response_lower:
            logger.warning(f"AI response contains potentially harmful content: {pattern}")
            return False
    
    # Organization-specific validation - only check for specific data leaks
    if user_context:
        org_name = user_context.get('organization_name', 'Unknown')
        org_id = user_context.get('organization_id')
        
        # Only block responses that explicitly mention other organizations by name
        if org_name != 'Unknown':
            # Look for specific organization names that don't match the user's organization
            # This is a more targeted approach
            if 'organization' in response_lower and org_name.lower() not in response_lower:
                # Only block if it's clearly about other organizations
                if any(word in response_lower for word in ['other org', 'different org', 'another org']):
                    logger.warning(f"AI response may contain references to other organizations")
                    return False
    
    # Check for reasonable response length
    if len(response) < 5 or len(response) > 10000:  # More lenient length limits
        logger.warning(f"AI response length outside acceptable range: {len(response)}")
        return False
    
    return True

def ai_assistant_answer(question: str, user, org, system_prompt: str = None, return_meta: bool = False):
    """
    Main AI assistant function that handles user questions.
    Uses FAQ first, then data-aware LLM responses with organization context.
    
    Args:
        question: User's question
        user: User object
        org: Organization object
        system_prompt: Optional custom system prompt
        return_meta: If True, returns tuple (response, metadata), else just response string
    
    Returns:
        str if return_meta=False, tuple (str, dict) if return_meta=True
    """
    if not question or not question.strip():
        error_response = "Please provide a question to get help."
        if return_meta:
            return error_response, {'error': 'Empty question', 'provider': None}
        return error_response
    
    question = question.strip()
    logger.info(f"AI Assistant query: {question} | User: {user} | Org: {org}")
    
    # 1. Check FAQ first for quick answers (skip if custom system_prompt provided)
    if not system_prompt:
        faq_answer = find_faq_answer(question, get_user_context(user, org))
        if faq_answer:
            logger.info("FAQ answer found")
            if return_meta:
                return faq_answer, {'provider': 'faq', 'source': 'faq'}
            return faq_answer
    
    # 2. Get user context and organization data
    user_context = get_user_context(user, org)
    data_provider = OrganizationDataProvider(user, org)
    org_data = data_provider.get_organization_summary()
    
    # 3. Create data-aware prompt (unless custom system prompt provided)
    if system_prompt:
        data_aware_prompt = question  # Use question as-is with custom system prompt
    else:
        data_aware_prompt = create_data_aware_prompt(question, user_context, org_data)
    
    # 4. Use Ollama for AI responses with OpenAI fallback
    try:
        logger.info("Attempting Ollama response with organization data")
        if return_meta:
            response, meta = ask_ollama(data_aware_prompt, user, org, system_prompt=system_prompt, return_meta=True)
        else:
            response = ask_ollama(data_aware_prompt, user, org, system_prompt=system_prompt, return_meta=False)
            meta = {'provider': 'ollama'}
        
        if response and response.strip():
            # Validate the response
            if validate_ai_response(response, user_context):
                logger.info("Ollama response successful and validated")
                if return_meta:
                    return response.strip(), meta
                return response.strip()
            else:
                logger.warning("Ollama response failed validation")
                raise Exception("Invalid response from Ollama")
        else:
            logger.warning("Ollama returned empty response")
            raise Exception("Empty response from Ollama")
            
    except Exception as e:
        logger.error(f"Ollama error: {e}, falling back to OpenAI")
        try:
            if return_meta:
                response, meta = ask_llm(data_aware_prompt, user, org, system_prompt=system_prompt, return_meta=True)
            else:
                response = ask_llm(data_aware_prompt, user, org, system_prompt=system_prompt, return_meta=False)
                meta = {'provider': 'openai'}
            
            if response and response.strip():
                # Validate the response
                if validate_ai_response(response, user_context):
                    logger.info("OpenAI fallback successful and validated")
                    if return_meta:
                        return response.strip(), meta
                    return response.strip()
                else:
                    logger.warning("OpenAI response failed validation")
                    error_response = "I'm sorry, I'm having trouble providing a safe response to your question. Please try rephrasing your question."
                    if return_meta:
                        return error_response, {'error': 'Validation failed', 'provider': 'openai'}
                    return error_response
            else:
                logger.error("OpenAI also returned empty response")
                error_response = "I'm sorry, I'm having trouble processing your request right now. Please try again later."
                if return_meta:
                    return error_response, {'error': 'Empty response', 'provider': 'openai'}
                return error_response
        except Exception as fallback_error:
            logger.error(f"OpenAI fallback also failed: {fallback_error}")
            error_response = "I'm sorry, I'm unable to process your request at the moment. Please try again later or contact support if the problem persists."
            if return_meta:
                return error_response, {'error': str(fallback_error), 'provider': None}
            return error_response
