import os, logging, string

BOT_TOKEN = os.environ.get("BOT_TOKEN")
REPORT_CHAT_ID = os.environ.get("REPORT_CHAT_ID")
ERROR_CHAT_ID = os.environ.get("ERROR_CHAT_ID")
ADMINS = os.environ.get("ADMINS").split("|")
SELLER_ADMIN = os.environ.get("SELLER_ADMIN")  # username
SUPPORT_ADMIN = os.environ.get("SUPPORT_ADMIN")  # username
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
LOG_LEVEL = logging._nameToLevel[os.environ.get("LOG_LEVEL").upper()]
DEFAULT_CID_LIMIT = int(os.environ.get("DEFAULT_CID_LIMIT"))
MAX_NAME_LENGTH = int(os.environ.get("MAX_NAME_LENGTH"))
MAX_CID_LENGTH = int(os.environ.get("MAX_CID_LENGTH"))
MIN_CID_LENGTH = int(os.environ.get("MIN_CID_LENGTH"))
HEALTH_PORT = int(os.environ.get("HEALTH_PORT"))
HEALTH_ADDRESS = int(os.environ.get("HEALTH_ADDRESS"))

MAX_TRY_ADD_CID = 5
DELETION_TIMEOUT = 10
DEFAULT_AUDIO_TAG = "[ناشناس]"
ALLOWED_CID_CHARS = string.ascii_letters + string.digits + "_-"  # must NEVER contain |
DELETION_TEXT = (
    "%s ثانیه فرصت داری با دکمه ی زیر پاکش کنی.\n"
    "<blockquote>غیرفعال‌سازیِ اخطار توی منوی تنظیماته</blockquote>"
)
EXPIRE_AFTER = 0.3  # seconds
KEY_MAX_INT = 100
