import os
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure required directories exist
for directory in [DATA_DIR, TEMP_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Configurations
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables or .env file.")

# Parse Admin Usernames (comma-separated strings, stripped of '@' and forced lowercase)
admin_usernames_raw = os.getenv("ADMIN_USERNAMES", "")
ADMIN_USERNAMES = []
if admin_usernames_raw:
    for username in admin_usernames_raw.split(","):
        username = username.strip().lstrip("@").lower()
        if username:
            ADMIN_USERNAMES.append(username)


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DB_PATH = os.path.join(DATA_DIR, "pdf_tools_bot.db")
