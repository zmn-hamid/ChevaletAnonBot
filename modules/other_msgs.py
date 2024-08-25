# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.decorators import verify_user, handle_errors


@handle_errors
@verify_user()
async def other_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    await message.reply_text("what?")


other_messages_handler = MessageHandler(filters.ALL, other_messages)
