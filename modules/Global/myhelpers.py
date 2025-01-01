# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import ALLOWED_CID_CHARS, KEY_MAX_INT, ERROR_CHAT_ID
from modules.Global.cid_gen import generate_cid
from modules.Global.database import DBHandler
from modules.Global.log import logger

# global imports
import time
import html
import string
import random
import traceback


END = ConversationHandler.END


def get_trace(e: Exception, html_escape: bool = True):
    tb_list = traceback.format_exception(None, e, e.__traceback__)
    tb_string = "".join(tb_list)
    return html.escape(tb_string) if html_escape else tb_string


def generate_chevaletid():
    return generate_cid() + str(time.time()).replace(".", "")


def encode_chevaletid(chevaletid: str):
    key = random.randint(0, KEY_MAX_INT)
    output = ""
    for letter in chevaletid:
        add = (ALLOWED_CID_CHARS.index(letter) + key) % len(ALLOWED_CID_CHARS)
        output += ALLOWED_CID_CHARS[add]
    key_patch_letter = random.choice(
        list(string.ascii_lowercase + string.ascii_uppercase)
    )
    key_patch = key_patch_letter + str(ord(key_patch_letter) + key)
    return output + key_patch


def decode_chevaletid(encoded_chevaletid: str):
    logger.debug(encoded_chevaletid, type(encoded_chevaletid))
    if not encoded_chevaletid:
        return False
    chevaletid, key_patch, key_patch_letter = None, None, None
    for letter in encoded_chevaletid[::-1]:
        if not letter.isnumeric():
            key_patch_letter = letter
            break
    if key_patch_letter is None:
        return False
    chevaletid, key_patch = encoded_chevaletid.rsplit(key_patch_letter, 1)
    if not key_patch.isnumeric():
        return False
    key = int(key_patch) - ord(key_patch_letter)
    if key > KEY_MAX_INT or key < 0:
        return False

    return "".join(
        [
            ALLOWED_CID_CHARS[
                (ALLOWED_CID_CHARS.index(letter) - key) % len(ALLOWED_CID_CHARS)
            ]
            for letter in chevaletid
        ]
    )


async def handle_cid_or_chid(
    target_cid_or_chid: str, dbh: DBHandler, message: Message, bot: Bot
):
    """
    for older messages

    > returns encoded target_chid or `END`
    """
    # it may be old and be cid instead of chid
    if (target_chid := decode_chevaletid(target_cid_or_chid)) and (
        dbh.get_uid_by_chevaletid(target_chid)
    ):
        # it's a chevaletid
        target_chid = target_cid_or_chid  # already encoded
    else:
        # it's a cid
        target_uid = dbh.get_uid_by_cid(target_cid_or_chid)
        # if not target_uid, then the link is changed and has no match
        if target_uid == None:
            await message.reply_text(
                "مخاطبت این لینک رو پاک یا عوض کرده. با لینک جدید بهش پیام بده",
                reply_parameters=ReplyParameters(message.message_id),
            )
            return END

        # add chevaletid for user if not made already
        if not (_target_chid := dbh.get_chevaletid_by_uid(target_uid)):
            _target_chid = generate_chevaletid()
            if not dbh.set_chevaletid(target_uid, target_chid):
                await message.reply_html(
                    "به مشکلی در خصوص مخاطب برخوردم. به ادمین خبر دادم ولی دوباره امتحان کن، به امتحانش میارزه :)",
                    reply_parameters=ReplyParameters(message.message_id),
                )
                await bot.send_message(
                    ERROR_CHAT_ID,
                    f"COULDNT SET chevaletid FOR USER: {target_uid} REPLY",
                    parse_mode=PM.HTML,
                )
                return END
        target_chid = encode_chevaletid(_target_chid)
    return target_chid
