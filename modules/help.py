# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import SUPPORT_ADMIN
from modules.Global.database import dbh
from modules.Global.decorators import verify_user, handle_errors
from modules.Global.fetch_texts import fetch_text


@handle_errors
@verify_user()
async def help_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """sends priacy and security help text"""
    await message.reply_text(fetch_text("start_help") % (SUPPORT_ADMIN),
                             parse_mode=PM.HTML,
                             disable_web_page_preview=True)


@handle_errors
@verify_user()
async def more_links_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """sends more links help text"""
    await message.reply_text(fetch_text("more_links"), parse_mode=PM.HTML)


more_links_help_handler = CommandHandler("more_links", more_links_cmd)
help_handler = CommandHandler("help", help_cmd)
