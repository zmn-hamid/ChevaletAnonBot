# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.log import logger


async def log_bot_started(context: CallbackContext) -> None:
    """updates the bot's command menu"""
    application = context.application
    bot: Bot = application.bot
    if bot._initialized:
        logger.info(f"started @{bot.username}...")
    else:
        application.job_queue.run_once(log_bot_started, 0.5)
