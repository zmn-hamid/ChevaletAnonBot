from telegram import *
from telegram.ext import *

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
        reply_parameters=ReplyParameters(message.message_id),
        link_preview_options=LinkPreviewOptions(
            url="https://bugs.telegram.org/c/47222",
            prefer_small_media=True,
            prefer_large_media=False,
        ),
    )


warn_bug_handler = CommandHandler("bug", warn_bug_reply_to_channel)
