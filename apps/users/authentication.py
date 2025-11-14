"""
Custom JWT Authentication with Access Token Blacklisting
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from django.core.cache import cache
import logging

logger = logging.getLogger('users.authentication')


class BlacklistedJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that checks if access tokens are blacklisted.
    
    This prevents using access tokens after logout by checking a blacklist
    stored in Redis (or cache) with the token's jti (JWT ID) as the key.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and check if token is blacklisted.
        """
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        
        # Check if token is blacklisted
        if self.is_token_blacklisted(validated_token):
            logger.warning(f"Blacklisted access token attempted: jti={validated_token.get('jti')}")
            raise InvalidToken("Token has been blacklisted (user logged out)")
        
        return self.get_user(validated_token), validated_token
    
    def is_token_blacklisted(self, token):
        """
        Check if the access token's jti is in the blacklist.
        
        Args:
            token: Validated token object with jti claim
        
        Returns:
            bool: True if token is blacklisted, False otherwise
        """
        jti = token.get('jti')
        if not jti:
            # Token doesn't have jti claim - can't blacklist it
            # This shouldn't happen with proper token generation, but handle gracefully
            return False
        
        # Check Redis/cache for blacklisted token
        # Key format: "jwt_blacklist:{jti}"
        cache_key = f"jwt_blacklist:{jti}"
        is_blacklisted = cache.get(cache_key)
        
        if is_blacklisted:
            logger.debug(f"Token jti={jti} found in blacklist")
            return True
        
        return False


def blacklist_access_token(token_string):
    """
    Blacklist an access token by storing its jti in cache.
    
    Args:
        token_string: The raw JWT token string
    
    Returns:
        str: The jti (JWT ID) that was blacklisted, or None if failed
    """
    try:
        # Decode token to get jti without verification (we just need the jti)
        # Note: We use UntypedToken which doesn't verify signature, but we only need jti
        untyped_token = UntypedToken(token_string)
        jti = untyped_token.get('jti')
        
        if not jti:
            logger.warning("Token does not have jti claim, cannot blacklist")
            return None
        
        # Get token expiration time to set TTL
        exp = untyped_token.get('exp')
        if exp:
            from datetime import datetime
            from django.utils import timezone
            # Calculate TTL: expiration time - current time
            exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
            ttl = int((exp_datetime - timezone.now()).total_seconds())
            # Ensure TTL is positive and not too large (max 1 hour for access tokens)
            ttl = max(0, min(ttl, 3600))
        else:
            # Default to 1 hour if no expiration
            ttl = 3600
        
        # Store in cache with TTL matching token expiration
        cache_key = f"jwt_blacklist:{jti}"
        cache.set(cache_key, True, ttl)
        
        logger.info(f"Access token blacklisted: jti={jti}, ttl={ttl}s")
        return jti
        
    except Exception as e:
        logger.error(f"Failed to blacklist access token: {e}")
        return None


def blacklist_user_access_tokens(user):
    """
    Attempt to blacklist access tokens for a user.
    
    Note: OutstandingToken only tracks refresh tokens, not access tokens.
    Access tokens are stateless and not tracked. This function is a placeholder
    for potential future enhancement if we decide to track access token jti.
    
    The main protection comes from blacklisting the specific access token
    used during logout (handled in the logout view).
    
    Args:
        user: User object
    
    Returns:
        int: Number of tokens blacklisted (currently always 0)
    """
    # Note: We cannot blacklist all access tokens for a user because:
    # 1. Access tokens are stateless and not tracked in OutstandingToken
    # 2. OutstandingToken only stores refresh tokens
    # 3. The main protection is blacklisting the specific token used during logout
    
    # Future enhancement: If we want to track access tokens, we could:
    # - Store access token jti in a separate model when tokens are issued
    # - Or use a token version/sequence number that increments on logout
    
    logger.debug(f"blacklist_user_access_tokens called for user {user.id} (access tokens are stateless and not tracked)")
    return 0

