# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.database import dbh
from modules.Global.decorators import verify_user, handle_errors


@handle_errors
@verify_user()
async def myuid_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    await message.reply_text(update.effective_user.id)


myuid_handler = CommandHandler("myuid", myuid_cmd)
