import logging
import os
import string

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
BOT_ID = BOT_TOKEN.split(":")[0]
REPORT_CHAT_ID = os.environ.get("REPORT_CHAT_ID")
ERROR_CHAT_ID = os.environ.get("ERROR_CHAT_ID")
ADMINS = admins.split("|") if (admins := os.environ.get("ADMINS")) else []
SELLER_ADMIN = os.environ.get("SELLER_ADMIN")  # username
SUPPORT_ADMIN = os.environ.get("SUPPORT_ADMIN")  # username
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_HOST = os.environ.get("DB_HOST", "localhost")
LOG_LEVEL = logging._nameToLevel[os.environ.get("LOG_LEVEL", "INFO").upper()]
DEFAULT_CID_LIMIT = int(os.environ.get("DEFAULT_CID_LIMIT"))
MAX_NAME_LENGTH = int(os.environ.get("MAX_NAME_LENGTH"))
MAX_CID_LENGTH = int(os.environ.get("MAX_CID_LENGTH"))
MIN_CID_LENGTH = int(os.environ.get("MIN_CID_LENGTH"))
HEALTH_PORT = int(os.environ["HEALTH_PORT"])
SEND_GM_GN = os.environ["SEND_GM_GN"].lower() == "true"
GM_TIME = [int(item.strip()) for item in os.environ["GM_TIME"].split(":")]
GN_TIME = [int(item.strip()) for item in os.environ["GN_TIME"].split(":")]
GM_GROUP_ID = os.environ["GM_GROUP_ID"]
GM_GROUP_TOPIC_ID = os.environ.get("GM_GROUP_TOPIC_ID")
AI_URL = os.environ.get("AI_URL", "")
AI_SESSION_ID = os.environ.get("AI_SESSION_ID", "")
AI_INTERVAL = os.environ.get("AI_INTERVAL", 5)
DONATION_LINK = os.environ.get("DONATION_LINK")
assert DONATION_LINK is not None

MAX_TRY_ADD_CID = 5
DELETION_TIMEOUT = 10
DELETION_TIMEOUT_EXTENDED = DELETION_TIMEOUT + 5
DEFAULT_AUDIO_TAG = "[ناشناس]"
ALLOWED_CID_CHARS = string.ascii_letters + string.digits + "_-"  # must NEVER contain |
DELETION_TEXT = (
    "%s ثانیه فرصت داری با دکمه ی زیر پاکش کنی.\n"
    "<blockquote>غیرفعال‌سازیِ اخطار توی منوی تنظیماته</blockquote>"
)
EXPIRE_AFTER = 0.3  # seconds
KEY_MAX_INT = 100
