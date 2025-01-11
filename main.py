"""main file"""

# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from config import BOT_TOKEN

from modules.start import start_cmd_handler, delete_message_handler, media_group_handler
from modules.my_links import mylinks_handler
from modules.admin import admin_handler
from modules.myuid import myuid_handler
from modules.settings import settings_handler
from modules.privacy import privacy_handler
from modules.help import help_handler, more_links_clbk_handler
from modules.warn_bug import warn_bug_handler
from modules.other_msgs import other_messages_handler

from modules.Global.jobs import (
    set_commands,
    log_bot_started,
    check_connection,
    health_check_app,
)
from modules.Global.error_handler import error_handler
from modules.Global.log import logger

# global imports
import os


appbuilder = ApplicationBuilder().token(BOT_TOKEN)
if proxy := os.environ.get("PROXY"):
    logger.debug("Set proxy: %s" % proxy)
    appbuilder.proxy(proxy)
application = appbuilder.build()
job_queue = application.job_queue

# adding handlers
for handler in [
    # start help
    start_cmd_handler,
    media_group_handler,
    delete_message_handler,
    help_handler,
    more_links_clbk_handler,
    # mylinks
    mylinks_handler,
    # settings
    settings_handler,
    # privacy
    privacy_handler,
    # admin
    admin_handler,
    # myuid
    myuid_handler,
    # warn bugs
    warn_bug_handler,
    # other messages
    other_messages_handler,
]:
    application.add_handler(handler)

# adding error handler
application.add_error_handler(error_handler)

# updating the bot's command menu
job_queue.run_once(set_commands, 3)

# check if db connection is lost every 1 hour
# job_queue.run_once(health_check_app, 5)

# starting the bot
job_queue.run_once(log_bot_started, 2)
try:
    application.run_polling(timeout=5)
except error.TelegramError as e:
    logger.critical(f"closing the bot because: {e} | {e.__class__.__name__}")
