import time
from typing import List
from warnings import filterwarnings

from shortuuid import uuid
from telegram import *
from telegram import Update
from telegram.constants import MessageType
from telegram.constants import ParseMode as PM
from telegram.error import TelegramError
from telegram.ext import *
from telegram.helpers import effective_message_type
from telegram.warnings import PTBUserWarning

from config import ERROR_CHAT_ID, EXPIRE_AFTER, REPORT_CHAT_ID, SUPPORT_ADMIN
from modules.Global.database import DBHandler
from modules.Global.decorators import (
    delete_notify_on_END,
    handle_target_send,
    prep_function,
)
from modules.Global.fetch_texts import fetch_text
from modules.Global.get_user import get_link_username, get_username, href_user
from modules.Global.handler_templates import (
    FilterMediaGroups,
    _warning_handle,
    add_tag,
    check_if_autoreply,
    other_messages_template,
    send_msg_template,
)
from modules.Global.jobs import delete_message
from modules.Global.myhelpers import (
    decode_chevaletid,
    encode_chevaletid,
    generate_chevaletid,
    handle_cid_or_chid,
)
from modules.Global.reply_markups import CANCEL_BUTTON
from modules.Global.reply_markups import MSG_BTN as BTN

# ignore the per_message error
filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)

# end conversation
END = ConversationHandler.END


@prep_function
async def handle_media(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None | int:
    """handles sent medias"""
    # check if it's reply to channel or message (auto reply)
    if (context.user_data.get("group_msgs") in [None, []]) or (
        message.media_group_id != context.user_data.get("media_group_id")
    ):
        context.user_data.clear()
        output = await check_if_autoreply(update, context, message, userid, bot, dbh)
        if type(output) is int:
            return output
        else:
            return await other_messages_template(message)

    # check if the media is handled ok
    if (expiration := context.user_data.get("group_expiration")) in [
        None,
        [],
    ] or context.user_data.get("group_msgs") in [None, []]:
        return await other_messages_template(message)

    # check if expired
    if time.time() - expiration >= EXPIRE_AFTER:
        context.user_data.clear()
        return await message.reply_text(
            "دیر شد. توی یه پیام جدید بفرست",
            reply_parameters=ReplyParameters(message.message_id, userid),
        )

    # add new media
    context.user_data["group_msgs"].append(message)

    # vars
    encoded_target_chid = context.user_data["group_target_chid"]
    target_chid = decode_chevaletid(encoded_target_chid)
    target_uid = dbh.get_uid_by_chevaletid(target_chid)
    msgs: List[Message] = context.user_data["group_msgs"]  # it's >2 now so we can go on
    reply_markup = context.user_data["group_reply_markup"]

    # delete the previously sent
    if context.user_data["sent_medias"]:
        await bot.delete_messages(target_uid, context.user_data["sent_medias"])
        context.user_data["sent_medias"] = []
    # send new ones
    sent_messages = await bot.copy_messages(
        target_uid, userid, [msg.message_id for msg in msgs]
    )
    # add for future deletion
    context.user_data["sent_medias"] += [
        str(sent_msg.message_id) for sent_msg in sent_messages
    ]

    # send tags
    ## calculate which message(s) to tag
    message_idxs_for_tags = []
    media_type = effective_message_type(msgs[0])
    tag = (
        dbh.get_audio_tag(target_uid)
        if media_type == MessageType.AUDIO
        else dbh.get_custom_tag(target_uid)
    )

    def _mark_all():
        """marks all of the messages to add tags to them"""
        return [{"idx": idx, "msg": msg} for idx, msg in enumerate(msgs)]

    if media_type in [MessageType.PHOTO, MessageType.VIDEO]:
        for idx, msg in enumerate(msgs):
            if msg.caption_html:
                if message_idxs_for_tags:
                    # there's already one message marked to get tag
                    # so just give all of them tags
                    message_idxs_for_tags = _mark_all()
                    break
                message_idxs_for_tags.append({"idx": idx, "msg": msg})
        if not message_idxs_for_tags:
            # means there's only one message marked to get tag
            message_idxs_for_tags.append({"idx": 0, "msg": msgs[0]})
    else:
        message_idxs_for_tags = _mark_all()
    ## send
    for msg_idx in message_idxs_for_tags:
        msg: Message = msg_idx["msg"]
        await add_tag(
            tag,
            "caption",
            bot,
            msg,
            target_uid,
            context.user_data["sent_medias"][msg_idx["idx"]],
            reply_markup,
            show_caption_above_media=msg.show_caption_above_media,
        )

    # send reply markups
    markup_msg = await bot.send_message(
        target_uid,
        "<blockquote>برای جواب دادن و اینجور چیزا، ازین پیام استفاده کن</blockquote>",
        parse_mode=PM.HTML,
        reply_parameters=ReplyParameters(sent_messages[0].message_id, target_uid),
        reply_markup=reply_markup,
    )
    context.user_data["sent_medias"].append(str(markup_msg.message_id))

    # delete previous warning message sent to sender
    if prev_warning_id := context.user_data.get("group_warning_msg_id"):
        try:
            await bot.delete_message(userid, prev_warning_id)
        except:
            pass

    # handle warning and deletion of it
    tbd_msgs = list(map(str, context.user_data["sent_medias"]))
    notify_msg: Message = context.user_data["group_notify_msg"]
    if notify_msg:
        tbd_msgs.append(str(notify_msg.message_id))
    _tbd_msgs = []
    for _tbd in tbd_msgs:
        if _tbd not in _tbd_msgs:
            _tbd_msgs.append(_tbd)
    tbd_msgs = _tbd_msgs
    if warning_message := await _warning_handle(
        context.user_data["group_was_channel_reply"],
        dbh,
        target_uid,
        userid,
        message,
        f"{encoded_target_chid}|{'|'.join(tbd_msgs)}",
        context,
    ):
        context.user_data["group_warning_msg_id"] = str(warning_message.message_id)
    context.user_data["group_expiration"] = time.time() + EXPIRE_AFTER


@prep_function
async def start_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None | int:
    """
    # Start command
    handles:\n
    - /start   -> sends start text
    - /start [CID]   -> connects to target for sending message
    - /start UNBLOCK-[UID]   -> unblocks the UID for the current user


    CID: Custom ID\n
    UID: User ID
    """
    split_text = message.text.split()

    if len(split_text) == 1:
        # send start/help text
        await message.reply_html(
            fetch_text("start_help") % (SUPPORT_ADMIN),
            disable_web_page_preview=True,
            reply_parameters=ReplyParameters(message.message_id),
        )
        return END

    else:
        if split_text[1].startswith("UNBLOCK-"):
            # unblocking user
            try:
                target_uid = split_text[1].split("-", 1)[-1]
                int(target_uid)
            except:
                await message.reply_text(
                    "لینکت اشتباهه?",
                    reply_parameters=ReplyParameters(message.message_id),
                )
                return END
            if dbh.is_blocked(blocker_uid=userid, blocked_uid=target_uid):
                dbh.remove_block(blocker_uid=userid, blocked_uid=target_uid)
                await message.reply_html(
                    f"این یوزر برات آنبلاک شد:\n{await get_username(target_uid, bot)} | {href_user(target_uid, '')}",
                    reply_parameters=ReplyParameters(message.message_id),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "پشیمون شدم دوباره بلاکش کن خخ",
                                    callback_data=f"block|{encode_chevaletid(dbh.get_chevaletid_by_uid(target_uid))}",
                                )
                            ]
                        ]
                    ),
                )
            else:
                await message.reply_text(
                    "این یوزر اصن برات بلاک نبود",
                    reply_parameters=ReplyParameters(message.message_id),
                )
            return END
        else:
            # sending message
            target_cid = split_text[1]
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

            # check is blocked by user
            if dbh.is_blocked(blocker_uid=target_uid, blocked_uid=userid):
                await message.reply_text(
                    "این کاربر بلاکت کرده خخ",
                    reply_parameters=ReplyParameters(message.message_id),
                )
                return END

            # check is blocked by user
            if dbh.is_banned(target_uid):
                await message.reply_text(
                    "این کاربر از بات بن شده اصن",
                    reply_parameters=ReplyParameters(message.message_id),
                )
                return END

            # save target to context
            context.user_data["target_cid"] = target_cid
            context.user_data["target_chid"] = target_chid  # already encoded
            context.user_data["reply_to"] = None

            await message.reply_html(
                (
                    f"{'میخوای با خودت صحبت کنی؟ :) عب نداره راحت باش.' if target_uid == userid else ''}\n"
                    f"به {dbh.get_name(target_uid)} وصل شدی. پیامتو بفرست\n\n"
                    f"<blockquote>میدونستی میتونی بدون استفاده از لینک، فقط با ریپلای کردن به کانال پیام بدی؟ منوی قابلیت ها و تنظیمات رو چک کن ؛)</blockquote>"
                ),
                reply_parameters=ReplyParameters(message.message_id),
                reply_markup=InlineKeyboardMarkup([[CANCEL_BUTTON]]),
            )
            return 0


@delete_notify_on_END
@prep_function
async def send_msg(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """
    # message sending fallback
    forwards the given message to the user (without sender)
    """
    return await send_msg_template(update, context, message, userid, bot, dbh)


@prep_function
async def answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """
    # asnwer callback
    callback for the answer button under each message
    """
    if (clbk := update.callback_query) and (data := clbk.data):
        await clbk.answer()
        _, target_cid_or_chid, target_mid = data.split("|")
        target_chid = await handle_cid_or_chid(target_cid_or_chid, dbh, message, bot)
        if target_chid == END:
            return END

        # check is blocked by user
        if dbh.is_blocked(
            blocker_uid=dbh.get_uid_by_chevaletid(decode_chevaletid(target_chid)),
            blocked_uid=userid,
        ):
            await clbk.answer("این کاربر بلاکت کرده خخ", show_alert=True)
            return END

        context.user_data["target_chid"] = target_chid
        context.user_data["reply_to"] = target_mid

        await message.reply_html(
            "جوابت به این پیام رو بفرست\n\n"
            "<blockquote>میدونستی ازین به بعد نیاز نیست حتما از دکمه ی ارسال جواب استفاده کنی. فقط کافیه پیام رو ریپلای کنی و جوابتو بهش بنویسی، مث یه چت معمولی :)</blockquote>",
            reply_parameters=ReplyParameters(message.message_id),
            reply_markup=InlineKeyboardMarkup([[CANCEL_BUTTON]]),
        )
        return 0


@prep_function
async def seen(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """tells the target that they saw their message (mark as seen)"""
    if (clbk := update.callback_query) and (data := clbk.data):
        _, target_cid_or_chid, target_mid = data.split("|")
        target_chid = await handle_cid_or_chid(target_cid_or_chid, dbh, message, bot)
        if target_chid == END:
            return END
        target_uid = dbh.get_uid_by_chevaletid(decode_chevaletid(target_chid))

        # check is blocked by user
        if dbh.is_blocked(blocker_uid=target_uid, blocked_uid=userid):
            await clbk.answer("این کاربر بلاکت کرده خخ", show_alert=True)
            return END

        # send seen message
        @handle_target_send(message=message, external_reply=message.external_reply)
        async def seen_message():
            await bot.send_message(
                target_uid,
                "این پیامت سین شد",
                parse_mode=PM.HTML,
                reply_parameters=ReplyParameters(target_mid),
            )

        await seen_message()

        # tell it was sent
        await clbk.answer("بهش گفتم سین زدی")

        # edit message so they can't seen the message again
        try:
            await message.edit_reply_markup(
                InlineKeyboardMarkup(
                    [
                        [
                            (
                                InlineKeyboardButton(
                                    button.text, callback_data=button.callback_data
                                )
                                if not button.callback_data.startswith("seen")
                                else InlineKeyboardButton(
                                    BTN.SEEN_DONE,
                                    callback_data="alread-seen",
                                )
                            )
                            for button in line
                        ]
                        for line in message.reply_markup.inline_keyboard
                    ]
                )
            )
        except:
            pass

        return END


@prep_function
async def block(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """
    # block using message button
    """
    if (clbk := update.callback_query) and (data := clbk.data):
        _, target_cid_or_chid = data.split("|")
        target_chid = await handle_cid_or_chid(target_cid_or_chid, dbh, message, bot)
        if target_chid == END:
            return END
        target_uid = dbh.get_uid_by_chevaletid(decode_chevaletid(target_chid))

        async def _add_block():
            try:
                await message.edit_reply_markup(
                    InlineKeyboardMarkup(
                        [
                            [
                                (
                                    InlineKeyboardButton(
                                        button.text, callback_data=button.callback_data
                                    )
                                    if not button.callback_data.startswith("block")
                                    else InlineKeyboardButton(
                                        BTN.UNBLOCK,
                                        callback_data=button.callback_data.replace(
                                            "block", "unblock"
                                        ),
                                    )
                                )
                                for button in line
                            ]
                            for line in message.reply_markup.inline_keyboard
                        ]
                    )
                )
            except:
                pass

        if dbh.add_block(userid, target_uid):
            await _add_block()
            if userid == target_uid:
                await clbk.answer("یه تراپی برو💀👍")
            else:
                await clbk.answer("با موفقیت بلاک شد.")
        else:
            await clbk.answer("همین الانش بلاک هست")
            await _add_block()


@prep_function
async def alread_seen(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """tell user the message is already seen so avoid doing it again"""
    await update.callback_query.answer("یبار سین زدم")


@prep_function
async def unblock(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """
    # unblock using message button
    """
    if (clbk := update.callback_query) and (data := clbk.data):
        _, target_cid_or_chid = data.split("|")
        target_chid = await handle_cid_or_chid(target_cid_or_chid, dbh, message, bot)
        if target_chid == END:
            return END
        target_uid = dbh.get_uid_by_chevaletid(decode_chevaletid(target_chid))

        async def _remove_block():
            try:
                await message.edit_reply_markup(
                    InlineKeyboardMarkup(
                        [
                            [
                                (
                                    InlineKeyboardButton(
                                        button.text, callback_data=button.callback_data
                                    )
                                    if not button.callback_data.startswith("unblock")
                                    else InlineKeyboardButton(
                                        BTN.BLOCK,
                                        callback_data=button.callback_data.replace(
                                            "unblock", "block"
                                        ),
                                    )
                                )
                                for button in line
                            ]
                            for line in message.reply_markup.inline_keyboard
                        ]
                    )
                )
            except:
                pass

        if dbh.remove_block(userid, target_uid):
            await _remove_block()
            if userid == target_uid:
                await clbk.answer("خوبه پس تراپی جواب داد🥹")
            else:
                await clbk.answer("با موفقیت آنبلاک شد.")
        else:
            await clbk.answer("همین الانش بلاک نیس")
            await _remove_block()


@prep_function
async def report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """
    # reports the message to admins
    """
    if (clbk := update.callback_query) and (data := clbk.data):
        _, target_cid_or_chid, target_mid = data.split("|")
        target_chid = await handle_cid_or_chid(target_cid_or_chid, dbh, message, bot)
        if target_chid == END:
            return END
        target_uid = dbh.get_uid_by_chevaletid(decode_chevaletid(target_chid))

        # report id
        report_id = uuid()

        # report to REPORT CHANNEL
        first_message = await bot.send_message(
            REPORT_CHAT_ID,
            f"id: <code>{report_id}</code>\n"
            f"reporter: {await get_link_username(userid, bot)}\n"
            f"reported: {await get_link_username(target_uid, bot)}\n"
            f"\n----------------\n❇️ COPY: <code>{target_uid}</code>\n------------\n"
            f"message:",
            parse_mode=PM.HTML,
        )
        try:
            await bot.copy_message(
                REPORT_CHAT_ID,
                target_uid,
                target_mid,
                reply_parameters=ReplyParameters(first_message.message_id, None, True),
            )
        except TelegramError:
            second_message = await message.copy(
                REPORT_CHAT_ID,
                reply_parameters=ReplyParameters(first_message.message_id),
            )
            await bot.send_message(
                REPORT_CHAT_ID,
                "این پیام از چت گیرنده کپی شد. ممکنه تهش تگ دلخواه داشته باشه",
                reply_parameters=ReplyParameters(second_message.message_id),
            )
        await message.reply_html(
            f"ریپورت شد.\nکد پیگیری: <code>{report_id}</code>",
            reply_parameters=ReplyParameters(message.message_id),
        )


@prep_function
async def cancel_all(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# cancel if other messages sent"""
    context.user_data.clear()
    await message.reply_text(
        "وسط ارسال پیام بودی. کنسلش کردم. دوباره بفرست",
        reply_parameters=ReplyParameters(message.message_id),
    )
    return END


@prep_function
async def cancel_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# cancel if other messages sent"""
    context.user_data.clear()
    await message.reply_text(
        "هرچی که بود کنسل شد",
        reply_parameters=ReplyParameters(message.message_id),
    )
    return END


@prep_function
async def delete_msg_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# delete the sent message on undo"""
    if (clbk := update.callback_query) and (data := clbk.data):
        _, target_cid_or_chid = data.split("|")[:2]
        target_chid = await handle_cid_or_chid(target_cid_or_chid, dbh, message, bot)
        if target_chid == END:
            return END
        target_uid = dbh.get_uid_by_chevaletid(decode_chevaletid(target_chid))
        assert target_uid

        to_be_deleted = []
        for row in update.effective_message.reply_markup.inline_keyboard:
            for btn in row:
                to_be_deleted += str(btn.callback_data).split("|")[2:]

        # delete the sent message
        for tbd in set(to_be_deleted):
            try:
                await bot.delete_message(target_uid, tbd)
            except:
                pass

        # delete the message so it won't fuck up
        try:
            await message.delete()
        except:
            pass

        try:
            await message.reply_text(
                "پاکش کردم براش😮‍💨",
                reply_parameters=ReplyParameters(
                    message.reply_to_message.message_id, None, True
                ),
            )
        except:
            pass
        return END


@prep_function
async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# cancel"""
    context.user_data.clear()
    await message.edit_text("چشم بهم بزنی این پیام نیس👋")
    context.application.job_queue.run_once(delete_message, 2, {"message": message})
    return END


delete_message_handler = CallbackQueryHandler(delete_msg_clbk, r"^delete\|")
start_clbk = CommandHandler("start", start_cmd)
answer_clbk = CallbackQueryHandler(answer, r"^answer\|")
seen_clbk = CallbackQueryHandler(seen, r"^seen\|")
already_seen_clbk = CallbackQueryHandler(alread_seen, r"alread-seen")
report_clbk = CallbackQueryHandler(report, r"^report\|")
block_clbk = CallbackQueryHandler(block, r"^block\|")
unblock_clbk = CallbackQueryHandler(unblock, r"^unblock\|")
cancel_clbk = CallbackQueryHandler(cancel, r"cancel")
media_group_handler = MessageHandler(FilterMediaGroups(), handle_media)
start_cmd_handler = ConversationHandler(
    entry_points=[
        start_clbk,
        answer_clbk,
        seen_clbk,
        already_seen_clbk,
        report_clbk,
        block_clbk,
        unblock_clbk,
    ],
    states={
        0: [
            start_clbk,
            answer_clbk,
            seen_clbk,
            already_seen_clbk,
            report_clbk,
            block_clbk,
            unblock_clbk,
            MessageHandler(filters.ALL & (~filters.COMMAND), send_msg),
        ]
    },
    fallbacks=[
        delete_message_handler,
        cancel_clbk,
        CommandHandler("cancel", cancel_cmd),
        MessageHandler(filters.ALL, cancel_all),
    ],
    per_user=True,
)
