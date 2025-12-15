from telegram import Bot, Message, ReplyParameters, Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from telegram.ext._handlers.callbackqueryhandler import CallbackQueryHandler

from modules.Global.database import DBHandler
from modules.Global.decorators import prep_function
from modules.Global.handler_templates import check_if_autoreply, other_messages_template

# vars
END = ConversationHandler.END


@prep_function
async def other_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# for unkown messages + send without link"""
    output = await check_if_autoreply(update, context, message, userid, bot, dbh)
    if output == END:
        return END

    # other messages
    if message.text and "/cancel" in message.text.split():
        await message.reply_text(
            "چیزی واسه کنسل کردن وجود نداره",
            reply_parameters=ReplyParameters(message.message_id),
        )
    else:
        await other_messages_template(message)


@prep_function
async def no_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    if update.callback_query:
        await update.callback_query.answer()


class IsDirectMessageFilter(filters.MessageFilter):
    __slots__ = ()

    def filter(self, message: Message) -> bool:  # noqa: ARG002
        if message.to_dict().get("chat", {}).get("is_direct_messages", False):
            return True
        return False


other_messages_handler = MessageHandler(
    filters.ALL & ~IsDirectMessageFilter(), other_messages
)
no_callback_handler = CallbackQueryHandler(no_callback, r"^no-callback")
