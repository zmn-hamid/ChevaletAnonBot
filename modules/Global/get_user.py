# telegram imports
from telegram import Message

# project imports
from config import SELLER_ADMIN
from modules.Global.database import dbh


def href_user(userid) -> str:
    """returns hyperlinked user"""
    return f'<a href="tg://user?id={userid}">u{userid}</a>'


def get_user_links(userid, bot_username) -> str:
    """returns formatted user cid's"""
    cids = dbh.get_cids(userid)
    text = []
    for idx, cid in enumerate(cids):
        text.append(
            f"<b>{idx+1}. t.me/{bot_username}?start={cid}</b>\nحذف کردن لینک: /rm_{cid}\n"
        )
    cid_limit = dbh.get_cid_limit(userid)
    return "------\n".join(text) + (
        "\n\n"
        "<b>اضافه کردن لینک جدید</b>: /add_link\n"
        f"{len(cids)} از {cid_limit} لینک مجاز استفاده شده.\n"
        f"برای لینک های بیشتر به ادمین پیام بدید: @{SELLER_ADMIN}\n"
        f"توضیحات قابلیت لینک های بیشتر: /more_links"
    )
