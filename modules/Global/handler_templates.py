# telegram imports
from telegram import *
from telegram.ext import *
from telegram.ext._utils.types import FilterDataDict
from telegram.constants import ParseMode as PM
from telegram.error import Forbidden
from telegram.constants import MessageEntityType as MET

# project imports
from config import DELETION_TIMEOUT, DELETION_TEXT, EXPIRE_AFTER
from modules.Global.jobs import delete_warning
from modules.Global.database import DBHandler
from modules.Global.log import logger
from modules.Global.decorators import (
    delete_notify_on_END,
    handle_target_send,
)
from modules.Global.reply_markups import MSG_BTN as BTN

# global imports
import re
import time
from typing import Optional, Union, List

# vars
END = ConversationHandler.END


class FilterMediaGroups(filters.MessageFilter):
    def check_update(self, update: Update) -> Optional[Union[bool, FilterDataDict]]:
        return bool(update.message and update.message.media_group_id)


async def other_messages_template(message: Message):
    """# template for unknown messages"""
    return await message.reply_text(
        "متوجه نشدم. اگه کمک میخوای از /help استفاده کن",
        reply_parameters=ReplyParameters(message.message_id),
    )


@delete_notify_on_END
async def send_msg_template(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    target_cid = context.user_data.get("target_cid")
    target_mid = context.user_data.get("reply_to")  # None when not answer
    was_channel_reply = context.user_data.get("channel_reply")
    external_reply = message.external_reply
    context.user_data.clear()

    # get target uid
    target_uid = dbh.get_uid(target_cid)

    # check if target_cid was indeed valid
    if target_uid == None:
        await message.reply_html(
            "مخاطبت لینکش رو عوض کرده. باید از نو پیام بفرستی",
            reply_parameters=ReplyParameters(message.message_id),
        )
        return END

    # check is blocked by user
    if dbh.is_blocked(blocker_uid=target_uid, blocked_uid=userid):
        await message.reply_text(
            "این کاربر بلاکت کرده خخ",
            reply_parameters=ReplyParameters(message.message_id),
        )
        return END

    # get cid from uid for sender (current user that is sending message)
    # so the reply markup won't have the uid inside it, for extra privacy
    sender_cid = dbh.get_cids(userid)[0]

    ## calculate reply and quote
    reply_to_chat, reply_to_mid, quote_text, quote_position = None, None, None, None
    if external_reply:
        reply_to_chat = str(external_reply.chat.id)
        reply_to_mid = str(external_reply.message_id)
    elif target_mid:
        reply_to_chat = target_uid
        reply_to_mid = target_mid
    if quote := message.quote:
        quote_text = quote.text
        quote_position = quote.position

    ## check if bot is not added then just use inline button
    replied_to_link = ""
    if external_reply:
        try:
            await bot.get_chat_administrators(reply_to_chat)
        except:
            if username := external_reply.chat.username:
                replied_to_link = f"https://t.me/{username}/{reply_to_mid}"
            else:
                replied_to_link = f"https://t.me/c/{reply_to_chat[4:]}/{reply_to_mid}"

            ### no reply, no quote
            reply_to_chat, reply_to_mid, quote_text, quote_position = (
                None,
                None,
                None,
                None,
            )

    ## calculate reply_markup
    reply_markup_keyboard = [
        [
            InlineKeyboardButton(
                BTN.REPLY,
                callback_data=f"answer|{sender_cid}|{message.message_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                BTN.REPORT,
                callback_data=f"report|{sender_cid}|{message.message_id}",
            ),
            InlineKeyboardButton(BTN.BLOCK, callback_data=f"block|{sender_cid}"),
        ],
    ]
    ## if seen option is activated
    if dbh.get_seen_status(userid):
        reply_markup_keyboard[0].insert(
            0,
            InlineKeyboardButton(
                BTN.SEEN,
                callback_data=f"seen|{sender_cid}|{message.message_id}",
            ),
        )

    # sending notif to target
    target_cids = dbh.get_cids(target_uid)

    @handle_target_send(message=message, external_reply=external_reply)
    async def send_notif() -> Message | None:
        # no target mid means not an answer
        return await bot.send_message(
            target_uid,
            "جواب جدید:",
            reply_parameters=(ReplyParameters(target_mid) if target_mid else None),
        )

    notify_msg: Message = None
    if len(target_cids) > 1 and not target_mid:
        # means it's not an answer, is a new message
        # also the user has more than one cid
        reply_markup_keyboard.append(
            [
                InlineKeyboardButton(
                    f"ارسال شده با لینک {target_cids.index(target_cid) + 1} ({target_cid})",
                    callback_data="no-callback",
                )
            ]
        )
    elif target_mid and (
        message.external_reply
        or (message.media_group_id and not message.external_reply)
    ):
        # means its in the middle answering and replied to external
        notify_msg = await send_notif()
        reply_to_chat, reply_to_mid, quote_text, quote_position = (
            None,
            notify_msg.message_id,
            None,
            None,
        )
        context.user_data.get("wrapper_list", []).append(notify_msg)

    # making reply_markup and parameters
    reply_markup = InlineKeyboardMarkup(reply_markup_keyboard)

    # handle group medias
    if media_group_id := message.media_group_id:
        # if context.user_data.get("media_group_id") != media_group_id:
        context.user_data["media_group_id"] = media_group_id
        context.user_data["group_msgs"] = [message]
        context.user_data["group_expiration"] = (
            time.time() + EXPIRE_AFTER
        )  # expire after EXPIRE_AFTER seconds
        # clear on end
        context.user_data["target_cid"] = None
        context.user_data["reply_to"] = None
        context.user_data["channel_reply"] = None
        # specify parameters for media sending
        context.user_data["group_target_cid"] = target_cid
        context.user_data["group_was_channel_reply"] = was_channel_reply
        context.user_data["group_notify_msg"] = notify_msg
        context.user_data["group_reply_markup"] = reply_markup
        return END

    # send message to target
    @handle_target_send(message=message, external_reply=external_reply)
    async def copy_msg_to_target():
        return await message.copy(
            target_uid,
            parse_mode=PM.HTML,
            reply_markup=reply_markup,
            reply_parameters=ReplyParameters(
                reply_to_mid,
                reply_to_chat,
                quote=quote_text,
                quote_position=quote_position,
            ),
        )

    output: MessageId | str = await copy_msg_to_target()
    if type(output) == MessageId:
        copied_message_id: MessageId = output.message_id
    else:
        return output

    # removing the link preview if needed
    if not dbh.get_wpp(target_uid):
        try:
            if message.text:
                await bot.edit_message_text(
                    message.text_html,
                    chat_id=target_uid,
                    message_id=copied_message_id,
                    parse_mode=PM.HTML,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True,
                )
        except:
            pass

    await _warning_handle(
        was_channel_reply,
        dbh,
        target_uid,
        userid,
        message,
        f"{target_cid}|{copied_message_id}|{notify_msg.message_id if notify_msg else None}",
        context,
    )

    # add reply's tag, custom tag and audio tag
    custom_tag = dbh.get_custom_tag(target_uid)
    if replied_to_link:
        replied_to_link = f'<blockquote><a href="{replied_to_link}">ریپلای به این پیام</a></blockquote>'
    add_tag_defaults = dict(
        bot=bot,
        message=message,
        target_uid=target_uid,
        copied_message_id=copied_message_id,
        reply_markup=reply_markup,
    )
    if message.audio and not custom_tag:
        await add_tag(
            dbh.get_audio_tag(target_uid) + "\n" + replied_to_link,
            "caption",
            **add_tag_defaults,
            show_caption_above_media=message.show_caption_above_media,
        )
    elif custom_tag:
        # edit text
        if not await add_tag(
            custom_tag + "\n" + replied_to_link,
            "text",
            **add_tag_defaults,
            link_preview_options=message.link_preview_options,
        ):
            await add_tag(
                custom_tag + "\n" + replied_to_link,
                "caption",
                **add_tag_defaults,
                show_caption_above_media=message.show_caption_above_media,
            )
    elif replied_to_link:
        if not await add_tag(
            replied_to_link,
            "text",
            **add_tag_defaults,
            link_preview_options=message.link_preview_options,
        ):
            await add_tag(
                replied_to_link,
                "caption",
                **add_tag_defaults,
                show_caption_above_media=message.show_caption_above_media,
            )

    context.user_data.clear()
    return END


async def is_answer(
    message: Message,
    bot: Bot,
):
    reply = message.reply_to_message
    if reply:
        if reply.reply_markup and reply.from_user.id == bot.id:
            # check the message has "answer" in callback datas
            for row in reply.reply_markup.inline_keyboard:
                for button in row:
                    if (data := button.callback_data) and data.startswith("answer|"):
                        _, target_cid, target_mid = data.split("|")
                        return target_cid, target_mid
        await message.reply_text(
            "اگه میخوای جواب بدی، باید خود پیام ناشناس رو ریپلای کنی. اونی که زیرش دکمه های شیشه ای هست",
            reply_parameters=ReplyParameters(message.message_id),
        )
        return END
    return False


async def is_reply_to_channel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
):
    external_reply = message.external_reply
    if external_reply:
        try:
            channel = await bot.get_chat(external_reply.chat.id)
        except Forbidden as e:
            await message.reply_text(
                "چنل مد نظرت پرایوته و بات بهش اضافه نشده",
                reply_parameters=ReplyParameters(message.message_id),
            )
            return False
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
            await message.reply_text(
                "چنل مدنظرت لینک ناشناسی توی بایو یا پیام پین شده ش نذاشته",
                reply_parameters=ReplyParameters(message.message_id),
            )
            return False

        if not target_cid:
            await message.reply_text(
                "لینک ناشناسی توی بایو (یا پیامِ پین شده) ی چنل مدنظرت پیدا نکردم",
                reply_parameters=ReplyParameters(message.message_id),
            )
            return False

        return target_cid, None

    return False


async def check_if_autoreply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
):
    # send answer if it's replied to a sent message
    output = await is_answer(message, bot)
    if type(output) == int:
        return output
    if output:
        context.user_data["target_cid"], context.user_data["reply_to"] = output
        context.user_data["channel_reply"] = None
        await send_msg_template(update, context, message, userid, bot, dbh)
        return END

    # send to channel if replied to
    output = await is_reply_to_channel(update, context, message, userid, bot, dbh)
    if type(output) == int:
        return output
    if output:
        context.user_data["target_cid"], context.user_data["reply_to"] = output
        context.user_data["channel_reply"] = True
        await send_msg_template(update, context, message, userid, bot, dbh)
        context.user_data["channel_reply"] = None
        return END

    return None


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
        return warning_message
    else:
        await message.reply_text(
            sent_text,
            reply_parameters=ReplyParameters(message.message_id),
        )


async def add_tag(
    tag: str,
    edit_what: str,
    bot: Bot,
    message: Message,
    target_uid: str,
    copied_message_id: str | int,
    reply_markup: ReplyKeyboardMarkup,
    **kwargs,
) -> None:
    """
    # base function for adding tag to text or caption

    `edit_what` is either `caption` or `text`
    """
    try:
        if edit_what == "caption":
            edit_method = bot.edit_message_caption
            og_text_html = message.caption_html if message.caption_html else ""
        else:
            edit_method = bot.edit_message_text
            og_text_html = message.text_html if message.text_html else ""
        await edit_method(
            **{edit_what: og_text_html + "\n" + tag},
            chat_id=target_uid,
            message_id=copied_message_id,
            parse_mode=PM.HTML,
            reply_markup=reply_markup,
            **kwargs,
        )
        return True
    except Exception as e:
        logger.debug(f"add_tag failed: {e}")
