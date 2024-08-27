# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from modules.Global.database import dbh
from modules.Global.decorators import verify_user, handle_errors
from modules.Global.fetch_texts import fetch_text

# end conversation
END = ConversationHandler.END


@handle_errors
@verify_user()
async def privacy_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """sends priacy and security help text"""
    await message.reply_text(fetch_text("privacy_safety"),
                             parse_mode=PM.HTML)


privacy_handler = CommandHandler("privacy", privacy_cmd)
