"""main file"""

# telegram imports
from telegram import *
from telegram.ext import *
from telegram.error import TimedOut

# project imports
from config import BOT_TOKEN
from modules.start import start_cmd_handler, delete_message_handler
from modules.my_links import mylinks_handler
from modules.admin import admin_handler
from modules.myuid import myuid_handler
from modules.settings import settings_handler
from modules.privacy import privacy_handler
from modules.help import help_handler, more_links_clbk_handler
from modules.other_msgs import other_messages_handler

from modules.Global.jobs import set_commands, renew_connection, log_bot_started
from modules.Global.error_handler import error_handler


application = ApplicationBuilder().token(BOT_TOKEN).build()
job_queue = application.job_queue

# adding handlers
for handler in [
    # start help
    start_cmd_handler,
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
    # other messages
    other_messages_handler,
]:
    application.add_handler(handler)

# adding error handler
application.add_error_handler(error_handler)

# updating the bot's command menu
job_queue.run_once(set_commands, 3)

# renew sql connection every 8 minutes
job_queue.run_repeating(renew_connection, 8 * 60)

# starting the bot
job_queue.run_once(log_bot_started, 2)
try:
    application.run_polling(timeout=5)
except TimedOut:
    print("connection timed out. closing the bot...")
