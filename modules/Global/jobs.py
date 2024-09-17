# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.log import logger
from modules.Global.database import dbh


async def log_bot_started(context: CallbackContext) -> None:
    """updates the bot's command menu"""
    if context.application.bot._initialized:
        logger.info(f"started @{context.application.bot.username}...")
    else:
        context.application.job_queue.run_once(log_bot_started, 0.5)


async def renew_connection(context: CallbackContext) -> None:
    """updates the bot's command menu"""
    dbh.connect_db()
    logger.debug("renewed sql connection")


async def set_commands(context: CallbackContext) -> None:
    """updates the bot's command menu"""
    await context.application.bot.set_my_commands(
        [
            ("help", "🆘 کمک!"),
            ("my_links", "🔗 لینک های من"),
            ("settings", "⚙️ تنظیمات و قابلیت ها"),
            ("cancel", "❌ کنسل کردن هرکاری که داری انجام میدی"),
        ]
    )
    logger.info("successfully set the commands")


async def delete_warning(context: CallbackContext) -> None:
    """deletes the warning message"""
    try:
        msg: Message = context.job.data.get("warning_message")
        await msg.edit_text("فرستادم بهش")
    except:
        pass


async def delete_message(context: CallbackContext) -> None:
    """deletes the warning message"""
    try:
        await context.job.data.get("message").delete()
    except:
        pass
