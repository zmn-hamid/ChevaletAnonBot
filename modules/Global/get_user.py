from telegram import Message
from modules.Global.database import dbh


def href_user(userid):
    return f'<a href="tg://user?id={userid}">u{userid}</a>'
