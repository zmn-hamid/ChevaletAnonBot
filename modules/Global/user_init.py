from telegram import Bot
from modules.Global.database import dbh
from modules.Global.cid_gen import generate_cid


async def init_user(uid, bot: Bot):
    cht = await bot.get_chat(uid)
    dbh.add_user(uid, cht.full_name)
    if len(dbh.get_cids(uid)) == 0:
        dbh.add_cid(uid, generate_cid())
