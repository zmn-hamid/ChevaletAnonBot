import os, logging, string

BOT_TOKEN = os.environ.get("BOT_TOKEN")
LOG_LEVEL = logging._nameToLevel[os.environ.get("LOG_LEVEL").upper()]
