import random
import string

from urllib.parse import urlparse

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

        social_domains = {
            "youtube.com",
            "youtu.be",
            "instagram.com",
            "tiktok.com",
        }

        return any(hostname == domain or hostname.endswith(f".{domain}") for domain in social_domains)

    except Exception:
        return False