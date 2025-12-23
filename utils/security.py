"""
Security utilities for API key management and validation
"""


def validate_api_key(api_key):
    """
    Validate Google Cloud TTS API key format

    Args:
        api_key: API key string

    Returns:
        bool: True if valid format, False otherwise
    """
    if not api_key:
        return False

    # Google Cloud API keys start with "AIzaSy" and are at least 39 characters
    if not api_key.startswith("AIzaSy"):
        return False

    if len(api_key) < 39:
        return False

    return True


def mask_api_key(api_key):
    """
    Mask API key for display (show first 6 chars + ...****)

    Args:
        api_key: API key string

    Returns:
        str: Masked API key
    """
    if not api_key:
        return ""

    if len(api_key) <= 10:
        return "***"

    return f"{api_key[:6]}...****"


def has_api_key(api_key):
    """
    Check if API key exists and is valid

    Args:
        api_key: API key string or None

    Returns:
        bool: True if API key exists and is valid
    """
    return api_key is not None and validate_api_key(api_key)
