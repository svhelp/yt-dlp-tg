import random
import string

from urllib.parse import urlparse

SOCIAL_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "instagram.com",
    "tiktok.com",
}

DISABLED_SOCIAL_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "instagram.com",
}

def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def verify_supported_url(url: str) -> bool:
    if not url:
        return False

    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        return any(hostname == domain or hostname.endswith(f".{domain}") for domain in SOCIAL_DOMAINS)

    except Exception:
        return False
    
def check_for_a_disabled_url(url: str) -> bool:
    if not url:
        return False

    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        return any(hostname == domain or hostname.endswith(f".{domain}") for domain in DISABLED_SOCIAL_DOMAINS)

    except Exception:
        return False