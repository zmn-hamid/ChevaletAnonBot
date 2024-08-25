# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.database import dbh
from modules.Global.decorators import verify_user, handle_errors


@handle_errors
@verify_user()
async def privacy_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    # TODO correct privacy text
    await message.reply_text("this is the privacy text.")


privacy_handler = CommandHandler("myuid", privacy_cmd)
