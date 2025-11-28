from telegram import *
from telegram.ext import *

from modules.Global.database import DBHandler
from modules.Global.decorators import prep_function

# end conversation
END = ConversationHandler.END


@prep_function
async def myuid_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """
    # returns user id

    is gonna be used for education
    """
    await message.reply_text(
        userid,
        reply_parameters=ReplyParameters(message.message_id),
    )


myuid_handler = CommandHandler("myuid", myuid_cmd)
