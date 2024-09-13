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


def prep_function(func) -> Callable:
    """prepare user and handle forbidden error"""

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # only handle updates from private chats
            if update.effective_chat.type in ["channel", "group"]:
                return ConversationHandler.END

            message: Message = update.effective_message
            userid = str(update.effective_user.id)
            bot = update.get_bot()

            # initialize user
            output = await init_user(userid, bot)
            if output == False:
                await message.reply_text(
                    "مشکلی در ساخت لینک ناشناس بوجود اومد. دوباره تلاش کن و اگه موفق نشدی، قبل از استفاده از بات با پشتیبانی تماس بگیر"
                )
                return ConversationHandler.END

            if dbh.is_banned(userid):
                await message.reply_text(
                    "از بات بن شدی. اگه فک میکنی این یه اشتباهه با ادمین صحبت کن"
                )
                context.user_data.clear()
                return ConversationHandler.END

            return await func(update, context, message, userid, bot)
        except Forbidden:
            # bot is blocked by the user
            return ConversationHandler.END

    return wrapper
