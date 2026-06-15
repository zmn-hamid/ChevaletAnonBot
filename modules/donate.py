from telegram import Bot, Message, ReplyParameters, Update
from telegram.ext import CommandHandler, ContextTypes

from config import DONATION_LINK
from modules.Global.database import DBHandler
from modules.Global.decorators import prep_function
from modules.Global.fetch_texts import fetch_text


@prep_function
async def privacy_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# sends the donation command text"""
    await message.reply_html(
        fetch_text("donate") % DONATION_LINK,
        reply_parameters=ReplyParameters(message.message_id),
    )


donate_cmd_handler = CommandHandler("donate", privacy_cmd)
