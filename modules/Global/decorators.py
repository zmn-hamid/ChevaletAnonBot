# telegram imports
from telegram import *
from telegram.ext import *
from telegram.error import Forbidden

# project imports
from modules.Global.database import dbh
from modules.Global.user_init import init_user

# global imports
from functools import wraps


def verify_user(initialize_user: bool = False):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            message: Message = update.effective_message
            userid = str(update.effective_user.id)
            bot = update.get_bot()
            if initialize_user:
                await init_user(userid, bot)

            if dbh.user_is_banned(userid):
                await message.reply_text(
                    "you're banned bro. " "contact the admins if that's a mistake"
                )
                context.user_data.clear()
                return ConversationHandler.END

            return await func(update, context, message, userid, bot)

        return wrapper

    return decorator


def handle_errors(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Forbidden:
            # bot is blocked by the user
            return ConversationHandler.END
    return wrapper