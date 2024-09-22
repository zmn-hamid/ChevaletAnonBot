# telegram imports
from telegram import *
from telegram.ext import *
from telegram.error import Forbidden, BadRequest, TimedOut

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

            return await func(update, context, message, userid, bot)
        except TimedOut:
            return
        except Forbidden as e:
            # bot is blocked by the user
            logger.debug(str(e))
            return ConversationHandler.END

    return wrapper


def delete_notify_on_END(func) -> Callable:
    """deletes the notify user message that is sent before private messages"""

    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        # making a list so whatever added to it in the function
        # will be accessible from here (inside the wrapper)
        # reason: lists are linked to their instances by default
        wrapper_list = []
        context.user_data["wrapper_list"] = wrapper_list
        output = await func(update, context, *args, **kwargs)

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


def handle_target_send(message: Message, external_reply: Message):
    """decorator for handling sending message to target (in case errors happen)"""

    def tst(func) -> Callable:
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Forbidden as e:
                if str(e) == "Forbidden: bot is not a member of the channel chat":
                    await message.reply_html(
                        "چنلی که ازش ریپلای کردی بات رو به خودش اضافه نکرده. اول باید از ادمینش بخوای که اینکارو کنه."
                        "\n\nدوباره پیامتو بفرست.",
                        reply_parameters=ReplyParameters(message.message_id),
                    )
                    return "del+0"
                elif str(e) == "Forbidden: bot was blocked by the user":
                    await message.reply_html("مخاطبت بات رو بلاک کرده")
                    return "del+0"
                else:
                    raise Forbidden(str(e)) from e
            except BadRequest as e:
                if str(e) == "Message to be replied not found":
                    if external_reply:
                        await message.reply_html(
                            "چنلی که ازش ریپلای کردی بات رو به خودش اضافه نکرده. اول باید از ادمینش بخوای که اینکارو کنه."
                            "\n\nدوباره پیامتو بفرست.",
                            reply_parameters=ReplyParameters(message.message_id),
                        )
                        return "del+0"
                    else:
                        # this was previously recognized as "deleted target message"
                        # but now after testing, it's probabely caused by blocking the bot
                        await message.reply_html(
                            "مخاطبت احتمالا بات رو بلاک کرده. ممکنم هست بخاطر کلیر هیستوری، پیام مدنظرت پاک شده باشه. میتونی لینکشو تست کنی تا ببینی میشه پیام فرستاد یا نه.\n\n"
                            "<blockquote>بخاطر ویژگیِ تلگرام، تا پیام معمولی نفرستم بهش نمیتونم مطمئن شم بات رو بلاک کرده یا نه</blockquote>",
                            reply_parameters=ReplyParameters(message.message_id),
                        )
                        return "del+e"
                elif str(e) == "MESSAGE_ID_INVALID":
                    return "del+e"
                elif str(e) == "Quote_text_invalid":
                    await message.reply_text(
                        "پیام اشتباهی رو ریپلای کردی. دوباره امتحان کن",
                        reply_parameters=ReplyParameters(message.message_id),
                    )
                    return "del+0"
                else:
                    raise BadRequest(str(e)) from e

        return wrapper

    return tst
