# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from config import BOT_TOKEN
from modules.start import start_cmd_handler
from modules.mylinks import mylinks_handler
from modules.admin import admin_handler
from modules.myuid import myuid_handler
from modules.settings import settings_handler
from modules.settings import settings_name_handler
from modules.privacy import privacy_handler
from modules.other_msgs import other_messages_handler
from modules.app_handlers import error_handler, job_set_commands


if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    job_queue = application.job_queue

    for handler in [
        start_cmd_handler,
        mylinks_handler,
        settings_handler,
        settings_name_handler,
        privacy_handler,
        admin_handler,
        myuid_handler,
        other_messages_handler,
    ]:
        application.add_handler(handler)

    # application.add_error_handler(error_handler)
    job_queue.run_once(job_set_commands, 3)

    print("starting the bot...")
    application.run_polling()
