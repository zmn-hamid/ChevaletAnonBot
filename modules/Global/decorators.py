# telegram imports
from telegram import *
from telegram.ext import *
from telegram.error import Forbidden

# project imports
from modules.Global.log import logger
from modules.Global.database import dbh
from modules.Global.user_init import init_user

# global imports
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

            output = await func(update, context, message, userid, bot)
            # clear userdata
            if output == ConversationHandler.END:
                context.user_data.clear()
            return output
        except Forbidden as e:
            # bot is blocked by the user
            logger.debug(str(e))
            return ConversationHandler.END

    return wrapper


def delete_notify_on_END(func) -> Callable:
    """deletes the notify user message that is sent before private messages"""

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # making a list so whatever added to it in the function
        # will be accessible from here (inside the wrapper)
        # reason: lists are linked to their instances by default
        wrapper_list = []
        context.user_data["wrapper_list"] = wrapper_list
        output = await func(update, context)

        # main
        if output in ["del+0", "del+e"]:
            try:
                await wrapper_list[0].delete()
            except:
                pass

        # output
        if output == "del+0":
            return 0
        elif output == "del+e":
            return ConversationHandler.END
        else:
            return output

    return wrapper
