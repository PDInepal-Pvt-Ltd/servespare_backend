"""
Token utility functions for password recovery and authentication.
"""
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken


def create_recovery_token(user, purpose='password_reset', expires_in=15):
    """
    Generate a JWT token for password recovery/reset purposes.
    
    Args:
        user: User instance for whom to generate the token
        purpose: Purpose of the token (e.g., 'password_reset')
        expires_in: Token expiry time in minutes (default: 15 minutes)
    
    Returns:
        dict: Dictionary containing:
            - access: JWT access token
            - expires_at: ISO format expiry timestamp
            - expires_in: Expiry time in seconds
    """
    # Generate refresh token (we'll use its access token)
    refresh = RefreshToken.for_user(user)
    
    # Add custom claims
    refresh['purpose'] = purpose
    
    # Set custom expiry time
    refresh.access_token.set_exp(lifetime=timedelta(minutes=expires_in))
    
    # Calculate expiry details
    expires_at = timezone.now() + timedelta(minutes=expires_in)
    
    return {
        'access': str(refresh.access_token),
        'expires_at': expires_at.isoformat(),
        'expires_in': expires_in * 60,  # Convert to seconds
    }


def verify_recovery_token(token, purpose='password_reset'):
    """
    Verify a recovery token and return the user if valid.
    
    Args:
        token: JWT token to verify
        purpose: Expected purpose of the token
    
    Returns:
        User instance if token is valid, None otherwise
    """
    from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
    from rest_framework_simplejwt.tokens import AccessToken
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        # Decode and verify token
        access_token = AccessToken(token)
        
        # Check if purpose matches
        if access_token.get('purpose') != purpose:
            return None
        
        # Get user from token
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
        
        return user
        
    except (TokenError, InvalidToken, User.DoesNotExist):
        return None
