# telegram imports
from telegram import *
from telegram.ext import *
from telegram.error import Forbidden
from telegram.constants import MessageEntityType as MET

# project imports
from modules.start import send_msg_template
from modules.Global.decorators import prep_function
from modules.Global.database import DBHandler
from modules.Global.handler_templates import other_messages_template

# global imports
import re

# end conversation
END = ConversationHandler.END


@prep_function
async def other_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# for unkown messages + send without link"""
    # import json

    # print(json.dumps(update.to_dict(), indent=2, ensure_ascii=False))
    # print("0000000000")
    # send answer if it's replied to a sent message
    reply = message.reply_to_message
    if reply:
        if reply.reply_markup and reply.from_user.id == bot.id:
            # check the message has "answer" in callback datas
            for row in reply.reply_markup.inline_keyboard:
                for button in row:
                    if (data := button.callback_data) and data.startswith("answer|"):
                        _, target_cid, target_mid = data.split("|")

                        context.user_data["target_cid"] = target_cid
                        context.user_data["reply_to"] = target_mid

                        await send_msg_template(
                            update, context, message, userid, bot, dbh
                        )
                        return END
        return await message.reply_text(
            "اگه میخوای جواب بدی، باید خود پیام ناشناس رو ریپلای کنی. اونی که زیرش دکمه های شیشه ای هست",
            reply_parameters=ReplyParameters(message.message_id),
        )

    # send to channel if replied to
    external_reply = message.external_reply
    if external_reply:
        try:
            channel = await bot.get_chat(external_reply.chat.id)
        except Forbidden as e:
            print(e)
            return await message.reply_text(
                "چنل مد نظرت پرایوته و بات بهش اضافه نشده",
                reply_parameters=ReplyParameters(message.message_id),
            )
        bio = channel.description
        pin = channel.pinned_message
        pattern = rf"t.me/{bot.username.lower()}\?start=([A-Za-z0-9_-]+)"
        target_cid: str = None
        # check if link is in description and if yes, check what's the cid
        if bio and (match := re.search(pattern, bio.lower())):
            offset, end = match.span(1)
            target_cid = bio[offset:end]

        elif pin and (entities := pin.entities):
            for entt in entities:
                entt: MessageEntity
                if entt.type == MET.URL and (
                    match := re.search(
                        pattern,
                        (
                            url := pin.text[entt.offset : entt.offset + entt.length]
                        ).lower(),
                    )
                ):
                    offset, end = match.span(1)
                    target_cid = url[offset:end]

        elif pin and (entities := pin.caption_entities):
            for entt in entities:
                entt: MessageEntity
                if entt.type == MET.URL and (
                    match := re.search(
                        pattern,
                        (
                            url := pin.caption[entt.offset : entt.offset + entt.length]
                        ).lower(),
                    )
                ):
                    offset, end = match.span(1)
                    target_cid = url[offset:end]

        elif (
            pin
            and (reply_markup := pin.reply_markup)
            and (inline_keyboard := reply_markup.inline_keyboard)
        ):
            for row in inline_keyboard:
                for col in row:
                    if col.url and (match := re.search(pattern, col.url.lower())):
                        offset, end = match.span(1)
                        target_cid = col.url[offset:end]

        else:
            return await message.reply_text(
                "چنل مدنظرت لینک ناشناسی توی بایو یا پیام پین شده ش نذاشته",
                reply_parameters=ReplyParameters(message.message_id),
            )

        if not target_cid:
            return await message.reply_text(
                "لینک ناشناسی توی بایو (یا پیامِ پین شده) ی چنل مدنظرت پیدا نکردم",
                reply_parameters=ReplyParameters(message.message_id),
            )
        context.user_data["target_cid"] = target_cid
        context.user_data["reply_to"] = None
        context.user_data["channel_reply"] = True
        await send_msg_template(update, context, message, userid, bot, dbh)
        context.user_data["channel_reply"] = None
        return END

    # other messages
    if message.text and "/cancel" in message.text.split():
        await message.reply_text(
            "چیزی واسه کنسل کردن وجود نداره",
            reply_parameters=ReplyParameters(message.message_id),
        )
    else:
        await other_messages_template(message)


other_messages_handler = MessageHandler(filters.ALL, other_messages)
