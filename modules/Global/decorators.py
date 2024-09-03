# telegram imports
from telegram import *
from telegram.ext import *
from telegram.error import Forbidden

# project imports
from modules.Global.database import dbh
from modules.Global.user_init import init_user

# global imports
from functools import wraps
from typing import Callable
import html, json


def verify_user(initialize_user: bool = False) -> Callable:
    """decorator for checking whether user is banned or initialized"""

    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # only handle updates from private chats
            if update.effective_chat.type in ["channel", "group"]:
                return ConversationHandler.END

            message: Message = update.effective_message
            userid = str(update.effective_user.id)
            bot = update.get_bot()
            if initialize_user:
                output = await init_user(userid, bot)
                if output == False:
                    await message.reply_text('مشکلی در ساخت لینک ناشناس بوجود اومد. دوباره تلاش کن و اگه موفق نشدی، قبل از استفاده از بات با پشتیبانی تماس بگیر')

            if dbh.user_is_banned(userid):
                await message.reply_text(
                    "از بات بن شدی. " "اگه فک میکنی این یه اشتباهه با ادمین صحبت کن"
                )
                context.user_data.clear()
                return ConversationHandler.END

            return await func(update, context, message, userid, bot)

        return wrapper

    return decorator


def handle_errors(func) -> Callable:
    """to handle if the user blocked the bot"""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Forbidden:
            # bot is blocked by the user
            return ConversationHandler.END

    return wrapper
