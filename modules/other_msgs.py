# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.decorators import prep_function

# end conversation
END = ConversationHandler.END


async def other_messages_template(message: Message):
    """# template for unknown messages"""
    return await message.reply_text(
        "متوجه نشدم. اگه کمک میخوای از /help استفاده کن",
        reply_parameters=ReplyParameters(message.message_id),
    )


@prep_function
async def other_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """# for unkown messages"""
    await other_messages_template(message)


other_messages_handler = MessageHandler(filters.ALL, other_messages)
