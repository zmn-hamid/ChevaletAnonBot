# project imports
from config import CHEVALETID_MP, ALLOWED_CID_CHARS, KEY_MAX_INT
from modules.Global.cid_gen import generate_cid
from modules.Global.database import DBHandler

# global imports
import time
import html
import string
import random
import traceback


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
