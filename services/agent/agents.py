"""
Multi-agent pattern using smolagents for specialized GRC tasks
"""
from smolagents import Agent
import logging

logger = logging.getLogger('services.agent.agents')

class BaseGrcAgent(Agent):
    """Base agent class for GRC-specific agents"""
    
    def __init__(self, organization, user):
        super().__init__()
        self.organization = organization
        self.user = user
        self.name = self.__class__.__name__


class AuditAgent(BaseGrcAgent):
    """Agent specialized in audit-related tasks"""
    
    def act(self, context):
        """
        Process audit-related context and return suggestions
        
        Args:
            context: dict with keys like 'engagement', 'issue', 'workplan', etc.
        
        Returns:
            dict with summary and suggested_actions
        """
        from django.apps import apps
        
        try:
            Engagement = apps.get_model('audit', 'Engagement')
            Issue = apps.get_model('audit', 'Issue')
            AuditWorkplan = apps.get_model('audit', 'AuditWorkplan')
            
            result = {
                "summary": "",
                "suggested_actions": [],
                "insights": []
            }
            
            # Handle engagement context
            if 'engagement_id' in context:
                engagement = Engagement.objects.filter(
                    id=context['engagement_id'],
                    organization=self.organization
                ).first()
                if engagement:
                    issue_count = engagement.issues.count()
                    result["summary"] = f"Engagement {engagement.code} has {issue_count} issues"
                    if issue_count > 0:
                        result["suggested_actions"].append("Review and prioritize issues")
                        result["suggested_actions"].append("Assign issue owners if not set")
            
            # Handle issue context
            if 'issue_id' in context:
                issue = Issue.objects.filter(
                    id=context['issue_id'],
                    engagement__organization=self.organization
                ).first()
                if issue:
                    result["summary"] = f"Issue: {issue.title} (Priority: {issue.priority})"
                    if not issue.root_cause:
                        result["suggested_actions"].append("Document root cause")
                    if not issue.recommendation:
                        result["suggested_actions"].append("Add recommendation")
            
            # Handle workplan context
            if 'workplan_id' in context:
                workplan = AuditWorkplan.objects.filter(
                    id=context['workplan_id'],
                    organization=self.organization
                ).first()
                if workplan:
                    engagement_count = workplan.engagements.count()
                    result["summary"] = f"Workplan {workplan.name} has {engagement_count} engagements"
                    result["suggested_actions"].append("Review engagement status")
            
            return result
            
        except Exception as e:
            logger.error(f"AuditAgent error: {e}")
            return {
                "summary": "Error processing audit context",
                "suggested_actions": [],
                "error": str(e)
            }


class DataAgent(BaseGrcAgent):
    """Agent specialized in data analysis and trends"""
    
    def act(self, context):
        """
        Analyze data trends and provide insights
        
        Args:
            context: dict with keys like 'model', 'timeframe', 'filters', etc.
        
        Returns:
            dict with insights and recommendations
        """
        from django.apps import apps
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            result = {
                "insights": [],
                "trends": {},
                "recommendations": []
            }
            
            # Analyze risk trends if Risk model available
            if 'analyze_risks' in context:
                Risk = apps.get_model('risk', 'Risk')
                thirty_days_ago = timezone.now() - timedelta(days=30)
                
                recent_risks = Risk.objects.filter(
                    organization=self.organization,
                    created_at__gte=thirty_days_ago
                )
                
                high_risks = recent_risks.filter(risk_level='high').count()
                if high_risks > 5:
                    result["insights"].append(f"High risk spike: {high_risks} high-priority risks in last 30 days")
                    result["recommendations"].append("Review risk mitigation strategies")
                    result["recommendations"].append("Consider risk appetite review")
            
            # Analyze audit issues
            if 'analyze_issues' in context:
                Issue = apps.get_model('audit', 'Issue')
                open_issues = Issue.objects.filter(
                    engagement__organization=self.organization,
                    status__in=['open', 'in_progress']
                ).count()
                
                if open_issues > 10:
                    result["insights"].append(f"High number of open issues: {open_issues}")
                    result["recommendations"].append("Prioritize issue resolution")
            
            return result
            
        except Exception as e:
            logger.error(f"DataAgent error: {e}")
            return {
                "insights": ["Error analyzing data"],
                "error": str(e)
            }


class ComplianceAgent(BaseGrcAgent):
    """Agent specialized in compliance framework matching"""
    
    def act(self, context):
        """
        Match controls to compliance frameworks
        
        Args:
            context: dict with keys like 'control_id', 'framework', etc.
        
        Returns:
            dict with mappings and recommendations
        """
        from django.apps import apps
        
        try:
            result = {
                "mappings": [],
                "recommendations": []
            }
            
            # Example: Map controls to ISO 27001
            if 'control_id' in context:
                # This would integrate with your compliance mapping logic
                result["mappings"].append("ISO 27001 A.12.4.1 (Logging and monitoring)")
                result["recommendations"].append("Ensure logging is comprehensive")
            
            return result
            
        except Exception as e:
            logger.error(f"ComplianceAgent error: {e}")
            return {
                "mappings": [],
                "error": str(e)
            }

