import os
import src.config
       
from urllib.parse import urlparse

TT_COOKIES = os.getenv("TT_COOKIES")
YT_COOKIES = os.getenv("YT_COOKIES")
IG_COOKIES = os.getenv("IG_COOKIES")

def get_cookies_path(url: str):
    if not url:
        return

    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        yt_domains = {
            "youtube.com",
            "youtu.be",
        }

        if any(hostname == domain or hostname.endswith(f".{domain}") for domain in yt_domains):
            return YT_COOKIES
    
        tt_domains = {
            "tiktok.com",
        }
        
        if any(hostname == domain or hostname.endswith(f".{domain}") for domain in tt_domains):
            return TT_COOKIES
        
        ig_domains = {
            "instagram.com",
        }

        if any(hostname == domain or hostname.endswith(f".{domain}") for domain in ig_domains):
            return IG_COOKIES
        
    except Exception:
        return False
