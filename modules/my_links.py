# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import VALIDATION_TEXT
from modules.Global.database import dbh
from modules.Global.decorators import verify_user, handle_errors
from modules.Global.get_user import get_user_links
from modules.Global.cid_gen import generate_cid


@handle_errors
@verify_user()
async def my_cids_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """returns users cids"""
    await message.reply_text(get_user_links(userid, bot))


@handle_errors
@verify_user()
async def rm_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """removes a cid"""
    text_split = message.text.split(" ", 1)
    cid = text_split[0].split("rm_", 1)[-1]
    if text_split[-1] == VALIDATION_TEXT:
        dbh.cur.execute(f'DELETE FROM {dbh.cids_table} WHERE cid="{cid}"')
        dbh.db.commit()
        await message.reply_text(get_user_links(userid, bot))
    else:
        # check if there's only one left
        if len(dbh.get_cids(userid)) == 1:
            await message.reply_text(
                "only one link is left. make a new one "
                "if you want to delete this one."
            )
        else:
            await message.reply_text(
                f"if you're sure, send: <code>{text_split[0]} {VALIDATION_TEXT}</code>",
                parse_mode=PM.HTML,
            )


@handle_errors
@verify_user()
async def add_link_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
):
    """adds a new cid if not reached the limit"""
    # check if user has reached limit
    limit = dbh.get_cid_limit(userid)
    current_cid_count = len(dbh.get_cids(userid))
    if current_cid_count >= limit:
        return await message.reply_text("you have reached the limit.")

    # add cid and return links
    dbh.add_cid(userid, generate_cid())
    await message.reply_text(get_user_links(userid, bot))


@handle_errors
@verify_user()
async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
):
    """cancel"""
    context.user_data.clear()
    await message.reply_text("canceled.")
    return ConversationHandler.END


my_cids_handler = CommandHandler("my_links", my_cids_cmd)
rm_cid_handler = MessageHandler(filters.Regex(r"^/rm_"), rm_cmd)
add_cid_handler = CommandHandler("add_link", add_link_cmd)
