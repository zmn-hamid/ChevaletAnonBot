# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.database import dbh
from modules.Global.decorators import verify_user, handle_errors


@handle_errors
@verify_user()
async def mylinks_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    text = ""
    for cid in dbh.get_cids(userid):
        text += f"- t.me/{bot.username}?start={cid}\n"
    await message.reply_text(text)


mylinks_handler = CommandHandler("mylinks", mylinks_cmd)
