import os
import shutil
import time
import asyncio
import logging
from app.config.config import TEMP_DIR

logger = logging.getLogger(__name__)

def delete_path(path: str) -> None:
    """Safely deletes a file or directory if it exists."""
    try:
        if os.path.isfile(path) or os.path.islink(path):
            os.unlink(path)
            logger.debug(f"Deleted file: {path}")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            logger.debug(f"Deleted directory: {path}")
    except Exception as e:
        logger.error(f"Error deleting path {path}: {e}")

def run_temp_cleanup(max_age_seconds: int = 3600) -> None:
    """Scans the temp directory and deletes files/directories older than max_age_seconds."""
    now = time.time()
    logger.info("Running temporary file cleanup scan...")
    
    if not os.path.exists(TEMP_DIR):
        return
        
    for item in os.listdir(TEMP_DIR):
        item_path = os.path.join(TEMP_DIR, item)
        try:
            # Check modification time
            mtime = os.path.getmtime(item_path)
            if now - mtime > max_age_seconds:
                delete_path(item_path)
        except Exception as e:
            logger.error(f"Error checking temporary item {item_path}: {e}")

async def start_cleanup_loop(interval_seconds: int = 1800, max_age_seconds: int = 3600) -> None:
    """Background loop that periodically runs the temporary cleanup service."""
    logger.info("Starting background temporary file cleanup service.")
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            await asyncio.to_thread(run_temp_cleanup, max_age_seconds)
        except asyncio.CancelledError:
            logger.info("Background cleanup service stopped.")
            break
        except Exception as e:
            logger.error(f"Error in background cleanup loop: {e}", exc_info=True)
            # Sleep a bit to prevent tight loop if something errors
            await asyncio.sleep(60)
