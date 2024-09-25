# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import SUPPORT_ADMIN
from modules.Global.database import DBHandler
from modules.Global.decorators import prep_function
from modules.Global.fetch_texts import fetch_text


@prep_function
async def help_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# sends priacy and security help text"""
    await message.reply_html(
        fetch_text("start_help") % (SUPPORT_ADMIN),
        disable_web_page_preview=True,
        reply_parameters=ReplyParameters(message.message_id),
    )


@prep_function
async def more_links_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """sends more links help text"""
    if (clbk := update.callback_query) and (data := clbk.data):
        await message.reply_html(
            fetch_text("more_links"),
            reply_parameters=ReplyParameters(message.message_id),
        )


help_handler = CommandHandler("help", help_cmd)
more_links_clbk_handler = CallbackQueryHandler(more_links_clbk, r"more-links")
