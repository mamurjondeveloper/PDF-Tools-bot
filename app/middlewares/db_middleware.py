import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from app.database.db import register_user

logger = logging.getLogger(__name__)

class DbMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Determine the user from the event
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if user:
            try:
                # Register or update user details in database
                await register_user(
                    user_id=user.id,
                    username=user.username,
                    first_name=user.first_name
                )
            except Exception as e:
                logger.error(f"Error in DbMiddleware registering user {user.id}: {e}", exc_info=True)

        return await handler(event, data)
