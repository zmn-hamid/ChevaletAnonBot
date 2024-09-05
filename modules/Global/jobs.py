# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.log import logger


async def set_commands(context: CallbackContext) -> None:
    """updates the bot's command menu"""
    await context.application.bot.set_my_commands(
        [
            ("help", "🆘 کمک!"),
            ("my_links", "🔗 لینک های من"),
            ("settings", "⚙️ تنظیمات پیام ناشناس"),
        ]
    )
    logger.info("successfully set the commands")


async def delete_warning(context: CallbackContext) -> None:
    """deletes the warning message"""
    msg: Message = context.job.data.get("warning_message")
    try:
        await msg.edit_text("فرستادم بهش.")
    except:
        pass
