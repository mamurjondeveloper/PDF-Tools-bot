import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

# App configurations
from app.config import config
from app.database.db import init_db
from app.middlewares.db_middleware import DbMiddleware
from app.services.cleanup_service import start_cleanup_loop

# Import Routers
from app.handlers import common, merge, split, jpg2pdf, doc2pdf, admin

# Setup Logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(sys.path[0] + "/logs/bot.log" if sys.path else "logs/bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

async def set_commands(bot: Bot) -> None:
    """Sets standard menu commands for the bot."""
    commands = [
        BotCommand(command="start", description="🚀 Start the bot & open menu"),
        BotCommand(command="help", description="ℹ️ How to use the bot"),
        BotCommand(command="admin", description="🛡 Admin panel (authorized admins only)")
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands set successfully.")

async def on_startup(bot: Bot) -> None:
    """Routines to execute on bot startup."""
    logger.info("Initializing database...")
    await init_db()
    
    # Set default commands
    await set_commands(bot)
    
    # Start the background temporary folder cleaner (every 30 minutes, files > 1 hour)
    asyncio.create_task(start_cleanup_loop(interval_seconds=1800, max_age_seconds=3600))
    logger.info("Bot startup routines complete.")

async def main() -> None:
    """Main execution entrypoint."""
    logger.info("Starting PDF Tools Bot...")
    
    # Initialize bot and dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register global outer middleware for database registration
    dp.update.outer_middleware(DbMiddleware())
    
    # Register routers in logical order
    dp.include_router(admin.router)
    dp.include_router(common.router)
    dp.include_router(merge.router)
    dp.include_router(split.router)
    dp.include_router(jpg2pdf.router)
    dp.include_router(doc2pdf.router)
    
    # Register startup callback
    dp.startup.register(on_startup)
    
    try:
        # Start polling, dropping pending updates to prevent backlog processing on reboot
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Critical failure in bot execution loop: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Bot execution finished.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot execution stopped by user (Ctrl+C).")
