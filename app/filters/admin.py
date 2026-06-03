import logging
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from app.config.config import ADMIN_USERNAMES

logger = logging.getLogger(__name__)

class IsAdmin(Filter):
    """Filter that checks if a user's username is in the configured ADMIN_USERNAMES."""
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        if not user or not user.username:
            return False
            
        username = user.username.lower()
        is_admin = username in ADMIN_USERNAMES
        if not is_admin:
            logger.warning(f"Ruxsat etilmagan admin buyrug'i: username=@{username}")
        return is_admin

