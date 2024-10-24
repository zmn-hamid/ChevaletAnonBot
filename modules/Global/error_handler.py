# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import ERROR_CHAT_ID
from modules.Global.log import logger

# global imports
import html
import json
import traceback
from shortuuid import uuid


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developers."""

    async def inner():
        try:
            if update is None:
                return
            # error code
            code = uuid()

            # Log the error before we do anything else, so we can see it even if something breaks.
            logger.error("Exception while handling an update:", exc_info=context.error)

            # traceback.format_exception returns the usual python message about an exception, but as a
            # list of strings rather than a single string, so we have to join them together.
            tb_list = traceback.format_exception(
                None, context.error, context.error.__traceback__
            )
            tb_string = "".join(tb_list)

            # Build the message with some markup and additional information about what happened.
            # You might need to add some logic to deal with messages longer than the 4096 character limit.
            update_str = update.to_dict() if isinstance(update, Update) else str(update)

            # send the message to devs
            msg = await context.bot.send_message(
                chat_id=ERROR_CHAT_ID,
                text=(
                    "An exception was raised while handling an update\n"
                    f"Error code: <code>{code}</code>"
                    f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
                    "</pre>\n\n"
                    f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
                    f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
                ),
                parse_mode=PM.HTML,
            )
            await context.bot.send_message(
                chat_id=ERROR_CHAT_ID,
                text=f"<pre>{html.escape(tb_string)}</pre>",
                parse_mode=PM.HTML,
                reply_parameters=ReplyParameters(msg.message_id, None, True),
            )

            # send report back to user
            try:
                message = update.effective_message
                await message.reply_html(
                    f"خطایی رخ داد. کد پیگیری: <code>{code}</code>",
                    reply_parameters=ReplyParameters(message.message_id),
                )
            except:
                pass
        except Exception as e:
            logger.error(f"error handler error lol: {e}")
        return

    await inner()
    return ConversationHandler.END
