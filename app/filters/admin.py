import logging
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from app.config.config import ADMIN_IDS

logger = logging.getLogger(__name__)

class IsAdmin(Filter):
    """Filter that checks if a user is in the configured ADMIN_IDS."""
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id if event.from_user else 0
        is_admin = user_id in ADMIN_IDS
        if not is_admin:
            logger.warning(f"Unauthorized admin command attempt by user_id={user_id}")
        return is_admin
