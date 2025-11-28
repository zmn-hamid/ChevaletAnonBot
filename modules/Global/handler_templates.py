import html
import re
import time
from typing import Optional, Union

from telegram import *
from telegram.constants import MessageEntityType as MET
from telegram.constants import ParseMode as PM
from telegram.error import Forbidden
from telegram.ext import *
from telegram.ext._utils.types import FilterDataDict

from config import (
    DELETION_TEXT,
    DELETION_TIMEOUT,
    DELETION_TIMEOUT_EXTENDED,
    ERROR_CHAT_ID,
    EXPIRE_AFTER,
)
from modules.Global.database import DBHandler
from modules.Global.decorators import (
    delete_notify_on_END,
    handle_target_send,
)
from modules.Global.jobs import delete_warning
from modules.Global.log import logger
from modules.Global.myhelpers import (
    decode_chevaletid,
    encode_chevaletid,
    generate_chevaletid,
    handle_cid_or_chid,
)
from modules.Global.reply_markups import MSG_BTN as BTN

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
    target_chid = decode_chevaletid(context.user_data.get("target_chid"))
    target_cid = context.user_data.get("target_cid")
    target_mid = context.user_data.get("reply_to")  # None when not answer
    was_channel_reply = context.user_data.get("channel_reply")
    external_reply = message.external_reply
    context.user_data.clear()

    # target uid
    target_uid = dbh.get_uid_by_chevaletid(target_chid)
    if not target_uid:
        await message.reply_html(
            "نشست شما منقضی شده. لطفاً دوباره از لینک ناشناس استفاده کنید.",
            reply_parameters=ReplyParameters(message.message_id),
        )
        return END

    # check if target cid is valid in case of existence
    if target_cid and dbh.get_uid_by_cid(target_cid) is None:
        await message.reply_html(
            "مخاطبت لینکش رو عوض کرده. باید از نو پیام بفرستی",
            reply_parameters=ReplyParameters(message.message_id),
        )
        return END

    # check if replied to another new message to cancel sending to the previous
    # -> is used for when pressed the answer button but replied to another one
    if (
        target_mid
        and (_output := await is_answer(message, bot, dbh, False))
        and (_output != END)
        and (
            not (
                (decode_chevaletid(_output[1]) == target_chid)
                and (_output[2] == target_mid)
            )
        )
    ):
        await message.reply_html(
            "در حال ارسال پیام به یکی دیگه بودی. کنسلش کردم. "
            "دوباره ریپلای بزن به فردی که میخواستی",
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

    # get chevaletid from uid for sender (current user that is sending message)
    # and encode it
    # so the reply markup won't have the uid or original chevaletid inside it, for extra privacy
    sender_enc_chid = encode_chevaletid(dbh.get_chevaletid_by_uid(userid))

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
                callback_data=f"answer|{sender_enc_chid}|{message.message_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                BTN.REPORT,
                callback_data=f"report|{sender_enc_chid}|{message.message_id}",
            ),
            InlineKeyboardButton(BTN.BLOCK, callback_data=f"block|{sender_enc_chid}"),
        ],
    ]
    ## if seen option is activated
    if dbh.get_seen_status(userid):
        reply_markup_keyboard[0].insert(
            0,
            InlineKeyboardButton(
                BTN.SEEN,
                callback_data=f"seen|{sender_enc_chid}|{message.message_id}",
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
        context.user_data["media_group_id"] = media_group_id
        context.user_data["group_msgs"] = [message]
        context.user_data["group_expiration"] = (
            time.time() + EXPIRE_AFTER
        )  # expire after EXPIRE_AFTER seconds
        # clear on end
        context.user_data["target_chid"] = None
        context.user_data["reply_to"] = None
        context.user_data["channel_reply"] = None
        # specify parameters for media sending
        context.user_data["group_target_chid"] = encode_chevaletid(target_chid)
        context.user_data["group_was_channel_reply"] = was_channel_reply
        context.user_data["group_notify_msg"] = notify_msg
        context.user_data["group_reply_markup"] = reply_markup
        context.user_data["group_warning_msg_id"] = None
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
    if type(output) == MessageId:  # noqa: E721
        copied_message_id: MessageId = output.message_id
    else:
        context.user_data.clear()
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
        f"{encode_chevaletid(target_chid)}|{copied_message_id}|{notify_msg.message_id if notify_msg else None}",
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
    dbh: DBHandler,
    _warn_wrong_reply: bool = True,
):
    reply = message.reply_to_message
    if reply:
        if reply.reply_markup and reply.from_user.id == bot.id:
            # check the message has "answer" in callback datas
            for row in reply.reply_markup.inline_keyboard:
                for button in row:
                    if (data := button.callback_data) and data.startswith("answer|"):
                        _, target_cid_or_chid, target_mid = data.split("|")
                        target_chid = await handle_cid_or_chid(
                            target_cid_or_chid, dbh, message, bot
                        )
                        if target_chid == END:
                            return END
                        return (
                            None,  # target_cid which is not none only for /start
                            target_chid,  # target_chid
                            target_mid,
                        )

        if _warn_wrong_reply:
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
        except Forbidden:
            await message.reply_text(
                "چنل مد نظرت پرایوته و بات بهش اضافه نشده",
                reply_parameters=ReplyParameters(message.message_id),
            )
            return False
        bio = channel.description
        pin = channel.pinned_message
        pattern = rf"t\.me/{bot.username.lower()}\?start=([A-Za-z0-9_-]+)"
        target_cid: str = None

        # check for author_signature to find specific admin's link
        author_signature = None
        if external_reply.origin:
            author_signature = external_reply.origin.to_dict().get(
                "author_signature", None
            )

        # helper function to find author-specific link
        def find_author_link(text: str, signature: str) -> str | None:
            """Find the link associated with a specific author signature in text."""
            if not text or not signature:
                return None
            # pattern: "Name: t.me/..." or "Name: https://t.me/..."
            author_pattern = rf"{re.escape(signature)}\s*:\s*(?:https?://)?t\.me/{bot.username.lower()}\?start=([A-Za-z0-9_-]+)"
            if match := re.search(author_pattern, text, re.IGNORECASE):
                # get the cid with original case from text
                offset, end = match.span(1)
                return text[offset:end]
            return None

        # if author_signature exists, try to find their specific link first
        if author_signature:
            # check bio for author-specific link
            if bio and (cid := find_author_link(bio, author_signature)):
                target_cid = cid
            # check pin text for author-specific link
            elif (
                pin
                and pin.text
                and (cid := find_author_link(pin.text, author_signature))
            ):
                target_cid = cid
            # check pin caption for author-specific link
            elif (
                pin
                and pin.caption
                and (cid := find_author_link(pin.caption, author_signature))
            ):
                target_cid = cid

        # fallback to original behavior if no author_signature or no match found
        if not target_cid:
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
                                url := pin.caption[
                                    entt.offset : entt.offset + entt.length
                                ]
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
                return END

        if not target_cid:
            await message.reply_text(
                "لینک ناشناسی توی بایو (یا پیامِ پین شده) ی چنل مدنظرت پیدا نکردم",
                reply_parameters=ReplyParameters(message.message_id),
            )
            return END

        target_uid = dbh.get_uid_by_cid(target_cid)
        # if not target_uid, then the link is changed and has no match
        if target_uid is None:
            await message.reply_text(
                "مخاطبت این لینک رو پاک یا عوض کرده. با لینک جدید بهش پیام بده",
                reply_parameters=ReplyParameters(message.message_id),
            )
            return END

        # add chevaletid for user if not made already
        target_chid = dbh.get_chevaletid_by_uid(target_uid)
        if not target_chid:
            target_chid = generate_chevaletid()
            if not dbh.set_chevaletid(target_uid, target_chid):
                await message.reply_html(
                    "به مشکلی در خصوص مخاطب برخوردم. به ادمین خبر دادم. لطفا صبر کن",
                    reply_parameters=ReplyParameters(message.message_id),
                )
                await bot.send_message(
                    ERROR_CHAT_ID,
                    f"COULDNT SET chevaletid FOR USER: {target_uid} ON SEND FROM {userid}",
                    parse_mode=PM.HTML,
                )
                return END
        target_chid = encode_chevaletid(target_chid)

        return (
            target_cid,
            target_chid,
            None,
        )  # last one is target_mid (used for private replies)

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
    output = await is_answer(message, bot, dbh)
    if output == END:
        return END
    if output:
        (
            context.user_data["target_cid"],
            context.user_data["target_chid"],
            context.user_data["reply_to"],
        ) = output
        context.user_data["channel_reply"] = None
        await send_msg_template(update, context, message, userid, bot, dbh)
        return END

    # send to channel if replied to
    output = await is_reply_to_channel(update, context, message, userid, bot, dbh)
    if output == END:
        return END
    if output:
        (
            context.user_data["target_cid"],
            context.user_data["target_chid"],
            context.user_data["reply_to"],
        ) = output
        context.user_data["channel_reply"] = True
        await send_msg_template(update, context, message, userid, bot, dbh)
        context.user_data["channel_reply"] = None
        return END

    return False


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
    deletion_timeout = DELETION_TIMEOUT
    if was_channel_reply:
        # undo timeout addition when bug fixed
        deletion_timeout = DELETION_TIMEOUT_EXTENDED
        sent_text = (
            f"فرستادم به {dbh.get_name(target_uid)}.\n"
            # undo text when bug fixed
            f"<blockquote><b>{html.escape('⚠️به هیچ پیام فوروارد شده ای ریپلای نزن. چرایی: /bug⚠️')}</b></blockquote>\n"
        )
    else:
        sent_text = "فرستادم بهش."
    # undo condition when bug fixed -> if dbh.get_warning(userid):
    if was_channel_reply or dbh.get_warning(userid):

        def _is_valid(rm):
            """checks validity of reply markup button limit"""
            return len("|".join(rm).encode()) <= 64

        def _kb_template():
            return ["delete", target_chid]

        target_chid, *mids = deletion_callback_data.split("|")
        reply_markup_kb = []
        _temp_kb = _kb_template()
        for mid in mids:
            if _is_valid(_temp_kb + [mid]):
                _temp_kb.append(mid)
            else:
                reply_markup_kb.append(
                    InlineKeyboardButton(
                        "پاکش کننن",
                        callback_data="|".join(_temp_kb),
                    )
                )
                _temp_kb = _kb_template() + [mid]
        if _temp_kb != _kb_template():
            reply_markup_kb.append(
                InlineKeyboardButton(
                    "پاکش کننن",
                    callback_data="|".join(_temp_kb),
                )
            )
        reply_markup_kb = [
            reply_markup_kb[idx : idx + 2] for idx in range(0, len(reply_markup_kb), 2)
        ]

        warning_message = await message.reply_html(
            (f"{sent_text}\n{DELETION_TEXT}" % deletion_timeout),
            reply_markup=InlineKeyboardMarkup(reply_markup_kb),
            reply_parameters=ReplyParameters(message.message_id),
        )
        context.application.job_queue.run_once(
            delete_warning,
            deletion_timeout,
            {"warning_message": warning_message},
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
