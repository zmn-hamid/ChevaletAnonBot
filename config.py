import os, logging

BOT_TOKEN = os.environ.get("BOT_TOKEN")
REPORT_CHAT_ID = os.environ.get("REPORT_CHAT_ID")
ERROR_CHAT_ID = os.environ.get("ERROR_CHAT_ID")
ADMINS = os.environ.get("ADMINS").split("|")
DB_NAME = os.environ.get("db_name")
DB_USER = os.environ.get("db_user")
DB_PASS = os.environ.get("db_pass")
LOG_LEVEL = logging._nameToLevel[os.environ.get("log_level").upper()]

VALIDATION_TEXT = "YES I AM SURE"
