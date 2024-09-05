"""main file"""

# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.log import logger
from modules.start import start_cmd_handler
from modules.my_links import my_cids_handler, rm_cid_handler, add_cid_handler
from modules.admin import admin_handler
from modules.myuid import myuid_handler
from modules.settings import (
    settings_handler,
    settings_name_handler,
    unblock_all_handler,
    unblock_me_handler,
)
from modules.privacy import privacy_handler
from modules.help import help_handler, more_links_help_handler
from modules.other_msgs import other_messages_handler, other_cancels_handler

from modules.app_handlers import application, job_queue, error_handler, job_set_commands


# adding handlers
for handler in [
    # start help
    start_cmd_handler,
    help_handler,
    more_links_help_handler,
    # mylinks
    my_cids_handler,
    rm_cid_handler,
    add_cid_handler,
    # settings
    settings_handler,
    settings_name_handler,
    unblock_all_handler,
    unblock_me_handler,
    # privacy
    privacy_handler,
    # admin
    admin_handler,
    # myuid
    myuid_handler,
    # other messages
    other_cancels_handler,
    other_messages_handler,
]:
    application.add_handler(handler)

# adding error handler
application.add_error_handler(error_handler)

# updating the bot's command menu
job_queue.run_once(job_set_commands, 3)

# starting the bot
logger.info(f"starting bot...")
application.run_polling()
