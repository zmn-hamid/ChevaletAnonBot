# telegram imports
from telegram import *
from telegram.ext import *

from config import DELETION_TIMEOUT, DELETION_TEXT
from modules.Global.jobs import delete_warning
from modules.Global.database import DBHandler
from modules.Global.log import logger


async def other_messages_template(message: Message):
    """# template for unknown messages"""
    return await message.reply_text(
        "متوجه نشدم. اگه کمک میخوای از /help استفاده کن",
        reply_parameters=ReplyParameters(message.message_id),
    )


async def _warning_handle(
    was_channel_reply: bool,
    dbh: DBHandler,
    target_uid: str,
    userid: str,
    message: Message,
    deletion_callback_data: str,
    context: ContextTypes.DEFAULT_TYPE,
):
    # handle warning and deletion of it
    if was_channel_reply:
        sent_text = f"فرستادم به {dbh.get_name(target_uid)}."
    else:
        sent_text = f"فرستادم بهش."
    if dbh.get_warning(userid):
        warning_message = await message.reply_html(
            (f"{sent_text}\n" f"{DELETION_TEXT}"),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "پاکش کننن",
                            callback_data=f"delete|{deletion_callback_data}",
                        ),
                    ],
                ]
            ),
            reply_parameters=ReplyParameters(message.message_id),
        )
        context.application.job_queue.run_once(
            delete_warning, DELETION_TIMEOUT, {"warning_message": warning_message}
        )
    else:
        await message.reply_text(
            sent_text,
            reply_parameters=ReplyParameters(message.message_id),
        )
    return warning_message
