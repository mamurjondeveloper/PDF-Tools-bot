import logging
from datetime import datetime, UTC
import aiosqlite
from app.config.config import DB_PATH

logger = logging.getLogger(__name__)

async def init_db() -> None:
    """Initializes the database by creating tables if they do not exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                registration_date TEXT NOT NULL,
                conversion_count INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                conversion_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        await db.commit()
    logger.info("Database initialized successfully.")

async def register_user(user_id: int, username: str | None, first_name: str | None) -> None:
    """Registers a user or updates their profile details if already registered."""
    now_str = datetime.now(UTC).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            
        if row is None:
            await db.execute(
                "INSERT INTO users (user_id, username, first_name, registration_date) VALUES (?, ?, ?, ?)",
                (user_id, username, first_name, now_str)
            )
            logger.info(f"Registered new user: {user_id}")
        else:
            await db.execute(
                "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
                (username, first_name, user_id)
            )
        await db.commit()

async def log_conversion(user_id: int, conversion_type: str) -> None:
    """Logs a conversion event and increments the user's conversion counter."""
    now_str = datetime.now(UTC).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        # Increment user's conversion count
        await db.execute(
            "UPDATE users SET conversion_count = conversion_count + 1 WHERE user_id = ?",
            (user_id,)
        )
        # Log details in conversions table
        await db.execute(
            "INSERT INTO conversions (user_id, conversion_type, timestamp) VALUES (?, ?, ?)",
            (user_id, conversion_type, now_str)
        )
        await db.commit()
    logger.info(f"Logged conversion: user={user_id}, type={conversion_type}")

async def get_user_stats() -> dict:
    """Returns general user registration statistics."""
    stats = {}
    now = datetime.now(UTC)
    today_start = datetime(now.year, now.month, now.day, tzinfo=UTC).isoformat()
    last_24h = datetime.fromtimestamp(now.timestamp() - 86400, tzinfo=UTC).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        # Total Users
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            stats["total_users"] = row[0] if row else 0

        # Registered today
        async with db.execute("SELECT COUNT(*) FROM users WHERE registration_date >= ?", (today_start,)) as cursor:
            row = await cursor.fetchone()
            stats["new_users_today"] = row[0] if row else 0

        # Active users in the last 24h (users who made a conversion)
        async with db.execute("SELECT COUNT(DISTINCT user_id) FROM conversions WHERE timestamp >= ?", (last_24h,)) as cursor:
            row = await cursor.fetchone()
            stats["active_users_24h"] = row[0] if row else 0

    return stats

async def get_conversion_stats() -> dict:
    """Returns statistics regarding file conversions."""
    stats = {}
    now = datetime.now(UTC)
    last_24h = datetime.fromtimestamp(now.timestamp() - 86400, tzinfo=UTC).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        # Total conversions
        async with db.execute("SELECT COUNT(*) FROM conversions") as cursor:
            row = await cursor.fetchone()
            stats["total_conversions"] = row[0] if row else 0

        # Conversions in the last 24h
        async with db.execute("SELECT COUNT(*) FROM conversions WHERE timestamp >= ?", (last_24h,)) as cursor:
            row = await cursor.fetchone()
            stats["conversions_24h"] = row[0] if row else 0

        # Conversions by type
        stats["by_type"] = {}
        async with db.execute("SELECT conversion_type, COUNT(*) FROM conversions GROUP BY conversion_type") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                stats["by_type"][row[0]] = row[1]

    return stats

async def get_daily_activity() -> dict:
    """Returns total activity in the last 24h."""
    user_stats = await get_user_stats()
    conv_stats = await get_conversion_stats()
    return {
        "active_users": user_stats.get("active_users_24h", 0),
        "total_conversions": conv_stats.get("conversions_24h", 0)
    }

async def get_all_user_ids() -> list[int]:
    """Returns a list of all registered user IDs."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
