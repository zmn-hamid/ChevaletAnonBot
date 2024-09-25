# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from modules.Global.database import DBHandler
from modules.Global.decorators import prep_function
from modules.Global.fetch_texts import fetch_text

# end conversation
END = ConversationHandler.END


@prep_function
async def privacy_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# sends priacy and security help text"""
    await message.reply_html(
        fetch_text("privacy_safety"),
        reply_parameters=ReplyParameters(message.message_id),
    )


privacy_handler = CommandHandler("privacy", privacy_cmd)
