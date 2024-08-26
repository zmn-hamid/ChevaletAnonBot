from telegram import Message
from modules.Global.database import dbh


def href_user(userid) -> str:
    """returns hyperlinked user"""
    return f'<a href="tg://user?id={userid}">u{userid}</a>'


def get_user_links(userid, bot) -> str:
    """returns formatted user cid's"""
    text = []
    for cid in dbh.get_cids(userid):
        text.append(f"• t.me/{bot.username}?start={cid}\ndelete: /rm_{cid}\n")
    return "------\n".join(text) + "\n\n/add_link"
