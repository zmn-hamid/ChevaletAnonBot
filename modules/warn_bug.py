# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.database import DBHandler
from modules.Global.decorators import prep_function
from modules.Global.fetch_texts import fetch_text

# end conversation
END = ConversationHandler.END


@prep_function
async def warn_bug_reply_to_channel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """
    when user replies to a forwarded message,
    """
    await message.reply_html(
        fetch_text("warn_reply_to_channel"),
        disable_web_page_preview=True,
        reply_parameters=ReplyParameters(message.message_id),
    )


warn_bug_handler = CommandHandler("bug", warn_bug_reply_to_channel)
