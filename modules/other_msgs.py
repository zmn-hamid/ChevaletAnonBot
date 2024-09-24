# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.start import send_msg_template
from modules.Global.decorators import prep_function
from modules.Global.database import dbh

# global imports
import re

# end conversation
END = ConversationHandler.END


async def other_messages_template(message: Message):
    """# template for unknown messages"""
    return await message.reply_text(
        "متوجه نشدم. اگه کمک میخوای از /help استفاده کن",
        reply_parameters=ReplyParameters(message.message_id),
    )


@prep_function
async def other_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """# for unkown messages + send without link"""
    # send answer if it's replied to a sent message
    reply = message.reply_to_message
    if reply and reply.from_user.id == bot.id:
        # check the message has "answer" in callback datas
        for row in reply.reply_markup.inline_keyboard:
            for button in row:
                if (data := button.callback_data) and data.startswith("answer|"):
                    _, target_cid, target_mid = data.split("|")

                    context.user_data["target_cid"] = target_cid
                    context.user_data["reply_to"] = target_mid

                    await send_msg_template(update, context, message, userid, bot)
                    return END

    # send to channel if replied to
    external_reply = message.external_reply
    if external_reply:
        try:
            channel = await bot.get_chat(external_reply.chat.id)
            if description := channel.description:
                # check if link is in description and if yes, check what's the cid
                if match := re.search(
                    r"t.me/Chevalet_bot\?start=([A-Za-z0-9_-]+)", description
                ):
                    context.user_data["target_cid"] = match.group(1)
                    context.user_data["reply_to"] = None

                    await send_msg_template(update, context, message, userid, bot)
                    return END
                else:
                    return await message.reply_text(
                        "چنل مد نظرت لینک ناشناسشو تو بایو نذاشته",
                        reply_parameters=ReplyParameters(message.message_id),
                    )
            else:
                return await message.reply_text(
                    "چنل مد نظرت بایو نداره",
                    reply_parameters=ReplyParameters(message.message_id),
                )
        except:
            return await message.reply_text(
                "چنل مد نظرت پرایوته",
                reply_parameters=ReplyParameters(message.message_id),
            )

    # other messages
    if message.text and "/cancel" in message.text.split():
        await message.reply_text(
            "چیزی واسه کنسل کردن وجود نداره",
            reply_parameters=ReplyParameters(message.message_id),
        )
    else:
        await other_messages_template(message)


other_messages_handler = MessageHandler(filters.ALL, other_messages)
