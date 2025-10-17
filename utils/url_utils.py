"""
URL utility functions for DOCZAP
Handles URL sanitization and construction
"""

import re
from urllib.parse import urljoin

def clean_string(s: str) -> str:
    """Clean string by removing non-printable ASCII characters and zero-width spaces"""
    if not s:
        return ""

    # Remove zero-width spaces and other problematic Unicode characters
    s = s.replace("\u200b", "")  # Zero-width space
    s = s.replace("\ufeff", "")  # Byte order mark
    s = s.replace("\u2060", "")  # Word joiner

    # Remove all control characters except newline and tab
    s = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", s)

    return s.strip()

def build_graph_api_url(api_version: str, phone_number_id: str, endpoint: str = "messages") -> str:
    """Build clean Facebook Graph API URL"""
    base_url = "https://graph.facebook.com/"

    # Clean all components
    api_version = clean_string(api_version)
    phone_number_id = clean_string(phone_number_id)
    endpoint = clean_string(endpoint).lstrip("/")

    # Ensure api_version starts with 'v'
    if not api_version.startswith('v'):
        api_version = f"v{api_version}"

    # Build URL step by step
    version_url = urljoin(base_url, f"{api_version}/")
    final_url = urljoin(version_url, f"{phone_number_id}/{endpoint}")

    return final_url

def clean_phone_number(phone: str) -> str:
    """Clean phone number string"""
    return clean_string(phone)

def clean_message_id(message_id: str) -> str:
    """Clean message ID string"""
    return clean_string(message_id)