from telegram import Bot
from modules.Global.database import dbh
from modules.Global.cid_gen import generate_cid


async def init_user(uid, bot: Bot) -> None:
    """
    # initializes user
    steps:
    1. adding user to users table
    2. adding cid to cids table if nothing is there
    """
    cht = await bot.get_chat(uid)
    dbh.add_user(uid, cht.full_name)
    if len(dbh.get_cids(uid)) == 0:
        dbh.add_cid(uid, generate_cid())
