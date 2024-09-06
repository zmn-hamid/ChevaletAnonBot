# telegram imports
from telegram import Bot

# Global imports
from typing import List


def href_user(userid: str) -> str:
    """returns hyperlinked user"""
    return f'<a href="tg://user?id={userid}">u{userid}</a>'


def get_user_links(cids: List[str], bot_username: str, flag_cid: int = -1) -> str:
    text = []
    for idx, cid in enumerate(cids):
        text.append(
            "<b>%sلینک %s:</b> t.me/%s?start=%s\n"
            % ("* " if flag_cid == cid else "", idx + 1, bot_username, cid)
        )
    return "------------\n".join(text)


def user_links_text(cids: List[str], cid_limit: int, bot_username: str) -> str:
    """returns formatted user cid's"""
    return (
        f"{get_user_links(cids, bot_username)}\n\n"
        f"{len(cids)} از {cid_limit} لینک مجاز استفاده شده.\n"
        f"چرا چندتا لینک داشته باشی؟ اینو بزن تا بفهمی: /more_links"
    )


async def get_link_username(userid: str, bot: Bot) -> str:
    try:
        uname_part = f" | @{(await bot.get_chat(userid)).username}"
    except:
        uname_part = ""
    return f"{href_user(userid)}{uname_part}"
