# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.decorators import verify_user, handle_errors

# end conversation
END = ConversationHandler.END


async def other_messages_template(message: Message):
    return await message.reply_text("متوجه نشدم. اگه کمک میخوای از /help استفاده کن")

@handle_errors
@verify_user()
async def other_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """other messages that are sent"""
    await other_messages_template(message)


@handle_errors
@verify_user()
async def other_cancels(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """in case a random /cancel is called"""
    await message.reply_text("چیزی واسه کنسل کردن وجود نداره")


other_cancels_handler = CommandHandler(f"cancel", other_cancels)
other_messages_handler = MessageHandler(filters.ALL, other_messages)
