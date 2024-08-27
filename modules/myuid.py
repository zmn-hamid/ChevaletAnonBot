# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.database import dbh
from modules.Global.decorators import verify_user, handle_errors

# end conversation
END = ConversationHandler.END


@handle_errors
@verify_user()
async def myuid_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """returns user id | is gonna be used for education"""
    await message.reply_text(userid)


myuid_handler = CommandHandler("myuid", myuid_cmd)
