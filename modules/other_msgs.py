# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.decorators import prep_function
from modules.Global.database import DBHandler
from modules.Global.handler_templates import other_messages_template, check_if_autoreply
from modules.Global.log import logger

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
    if output in [END, False]:
        return END

    # other messages
    if message.text and "/cancel" in message.text.split():
        await message.reply_text(
            "چیزی واسه کنسل کردن وجود نداره",
            reply_parameters=ReplyParameters(message.message_id),
        )
    else:
        await other_messages_template(message)


other_messages_handler = MessageHandler(filters.ALL, other_messages)
