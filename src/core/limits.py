import os
import src.config

from src.db.schema import User, UserTier
from src.db.repository import get_today_requests_count

REQUESTS_LIMITED = int(os.getenv("REQUESTS_LIMITED"))
REQUESTS_REGULAR = int(os.getenv("REQUESTS_REGULAR"))
REQUESTS_ADVANCED = int(os.getenv("REQUESTS_ADVANCED"))

def ensure_user_limits(user: User):
    requests_today = get_today_requests_count(user.id)

    return (user.tier != UserTier.LIMITED or requests_today < REQUESTS_LIMITED) and \
            (user.tier != UserTier.REGULAR or requests_today < REQUESTS_REGULAR) and \
            (user.tier != UserTier.ADVANCED or requests_today < REQUESTS_ADVANCED)
        

