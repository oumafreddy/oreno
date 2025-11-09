"""
Agent registry for managing and routing to specialized agents
"""
from .agents import AuditAgent, DataAgent, ComplianceAgent, BaseGrcAgent
import logging

logger = logging.getLogger('services.agent.registry')

# Registry of available agents
AGENTS = {
    'audit': AuditAgent,
    'data': DataAgent,
    'compliance': ComplianceAgent,
}


def run_agent(agent_key, organization, user, context):
    """
    Run a specific agent with given context
    
    Args:
        agent_key: Key from AGENTS registry ('audit', 'data', 'compliance')
        organization: Organization object
        user: User object
        context: Context dict to pass to agent
    
    Returns:
        Agent result dict
    
    Raises:
        KeyError: If agent_key not found
    """
    AgentCls = AGENTS.get(agent_key)
    if not AgentCls:
        raise KeyError(f"Unknown agent: {agent_key}. Available: {list(AGENTS.keys())}")
    
    try:
        agent = AgentCls(organization, user)
        result = agent.act(context)
        logger.info(f"Agent {agent_key} executed successfully for org {organization.id}")
        return result
    except Exception as e:
        logger.error(f"Agent {agent_key} execution failed: {e}")
        raise


def list_agents():
    """Return list of available agent keys"""
    return list(AGENTS.keys())


def get_agent_info(agent_key):
    """Get information about a specific agent"""
    AgentCls = AGENTS.get(agent_key)
    if not AgentCls:
        return None
    
    return {
        'key': agent_key,
        'name': AgentCls.__name__,
        'description': AgentCls.__doc__ or 'No description available'
    }

