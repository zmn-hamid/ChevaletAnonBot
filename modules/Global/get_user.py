# telegram imports
from telegram import Bot

# Global imports
from typing import List


def href_user(userid: str, pre_text: str='u') -> str:
    """returns hyperlinked user"""
    return f'<a href="tg://user?id={userid}">{pre_text}{userid}</a>'


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


async def get_username(userid: str, bot: Bot):
    try:
        return f"@{(await bot.get_chat(userid)).username}"
    except:
        return ""

async def get_link_username(userid: str, bot: Bot) -> str:
    return f"{href_user(userid)} | {await get_username(userid, bot)}"
