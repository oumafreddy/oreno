"""
Redis caching utilities for AI responses
"""
import hashlib
import logging
from django.core.cache import cache

logger = logging.getLogger('services.ai.cache_utils')

def ai_cached_response(prompt, org_id, fetch_fn, ttl=86400, context_hash=None):
    """
    Cache AI responses with organization and context awareness
    
    Args:
        prompt: User prompt
        org_id: Organization ID
        fetch_fn: Function to call if cache miss (should return response)
        ttl: Time to live in seconds (default: 24 hours)
        context_hash: Optional hash of additional context (e.g., data snapshot)
    
    Returns:
        tuple: (response, was_cached)
    """
    # Create cache key from prompt, org, and optional context
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    if context_hash:
        cache_key = f"oreno:ai:{org_id}:{prompt_hash}:{context_hash}"
    else:
        cache_key = f"oreno:ai:{org_id}:{prompt_hash}"
    
    # Try to get from cache
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"Cache hit for key: {cache_key}")
        return cached, True
    
    # Cache miss - fetch and store
    logger.debug(f"Cache miss for key: {cache_key}")
    result = fetch_fn()
    cache.set(cache_key, result, ttl)
    return result, False


def invalidate_ai_cache(org_id, pattern=None):
    """
    Invalidate AI cache for an organization
    
    Args:
        org_id: Organization ID
        pattern: Optional pattern to match (e.g., specific model IDs)
    """
    if pattern:
        cache_key_pattern = f"oreno:ai:{org_id}:*:{pattern}*"
    else:
        cache_key_pattern = f"oreno:ai:{org_id}:*"
    
    # Note: django-redis doesn't support pattern deletion directly
    # You may need to use Redis directly or iterate through keys
    # For now, this is a placeholder - implement based on your Redis setup
    logger.info(f"Cache invalidation requested for pattern: {cache_key_pattern}")
    # TODO: Implement actual cache invalidation using Redis client if needed

