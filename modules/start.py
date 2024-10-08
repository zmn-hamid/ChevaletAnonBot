# telegram imports
from telegram import *
from telegram import Update
from telegram.ext import *
from telegram.constants import ParseMode as PM
from telegram.ext._utils.types import FilterDataDict
from telegram.warnings import PTBUserWarning

# project imports
from config import REPORT_CHAT_ID, SUPPORT_ADMIN, DELETION_TIMEOUT, DELETION_TEXT
from modules.Global.log import logger
from modules.Global.database import DBHandler
from modules.Global.get_user import get_username, href_user, get_link_username
from modules.Global.decorators import (
    prep_function,
    delete_notify_on_END,
    handle_target_send,
)
from modules.Global.fetch_texts import fetch_text
from modules.Global.jobs import delete_warning, delete_message
from modules.Global.reply_markups import CANCEL_BUTTON
from modules.Global.handler_templates import other_messages_template, _warning_handle

# global imports
from shortuuid import uuid
from warnings import filterwarnings
from typing import Optional, Union
import time


# reply markup buttons
class BTN:
    REPLIED_TO = "ریپلای شده به این پیام"
    REPLY = "⌨️ ارسال جواب"
    SEEN = "✅ سین بزن"
    SEEN_DONE = "☑️ سین زدم"
    BLOCK = "🔒 بلاک"
    UNBLOCK = "🔓 آنبلاک"
    REPORT = "⚠️ ریپورت"


# ignore the per_message error
filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)


# end conversation
END = ConversationHandler.END
EXPIRE_AFTER = 1 # seconds


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
    # check if the media is handled ok
    if not (expiration:=context.user_data.get('group_expiration')):
        await other_messages_template(message)

    # check if expired
    if time.time() - expiration >= EXPIRE_AFTER:
        await message.reply_text('دیر شد. توی یه پیام جدید بفرست')
        context.user_data.clear()

    # add new media
    context.user_data["group_msgs"].append(message.message_id)
    context.user_data['group_expiration'] = time.time() + EXPIRE_AFTER

    # send and shit
    target_cid = context.user_data['group_target_cid']
    target_uid = dbh.get_uid(target_cid)
    if len(context.user_data["group_msgs"]) >= 2:
        # delete the previously sent
        if context.user_data["sent_medias"]:
            await bot.delete_messages(target_uid, context.user_data["sent_medias"])
            context.user_data["sent_medias"] = []
        # send new ones
        sent_messages = await bot.copy_messages(target_uid, userid, context.user_data["group_msgs"])
        # add for future deletion
        context.user_data["sent_medias"] += [sent_msg.message_id for sent_msg in sent_messages]

        # handle warning and deletion of it
        sent_medias = context.user_data["sent_medias"]
        notify_msg: Message = context.user_data["group_notify_msg"]
        warning_message = await _warning_handle(
            context.user_data["group_was_channel_reply"],
            dbh,
            target_uid,
            userid,
            message,
            f"{target_cid}|{'|'.join(list(map(str, sent_medias)))}|{notify_msg.message_id if notify_msg else None}",
            context,
        )
        context.user_data["sent_medias"].append(warning_message.message_id)


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
                                    callback_data=f"block|{dbh.get_cids(target_uid)[0]}",
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
            target_uid = dbh.get_uid(target_cid)

            # check if target_cid exists
            if target_uid == None:
                await message.reply_text(
                    "این لینک اشتباهه و کار نمیکنه",
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

            # check is blocked by user
            if dbh.is_banned(target_uid):
                await message.reply_text(
                    "این کاربر از بات بن شده اصن",
                    reply_parameters=ReplyParameters(message.message_id),
                )
                return END

            # save target to context
            context.user_data["target_cid"] = target_cid
            context.user_data["reply_to"] = None

            await message.reply_html(
                (
                    f'{"میخوای با خودت صحبت کنی؟ :) عب نداره راحت باش." if target_uid == userid else ''}\n'
                    f"به {dbh.get_name(target_uid)} وصل شدی. پیامتو بفرست\n\n"
                    f"<blockquote>میدونستی میتونی بدون استفاده از لینک، فقط با ریپلای کردن به کانال پیام بدی؟ منوی قابلیت ها و تنظیمات رو چک کن ؛)</blockquote>"
                ),
                reply_parameters=ReplyParameters(message.message_id),
                reply_markup=InlineKeyboardMarkup([[CANCEL_BUTTON]]),
            )
            return 0


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
    replied_to_link = ''
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
        # no target uid means not an answer
        if target_mid:
            return await bot.send_message(
                target_uid,
                "جواب جدید:",
                reply_parameters=(ReplyParameters(target_mid) if target_mid else None),
            )
        elif len(target_cids) > 1:
            ## notify user if target has >1 cid
            reply_markup_keyboard.append(
                [
                    InlineKeyboardButton(
                        f"ارسال شده با لینک {target_cids.index(target_cid) + 1} ({target_cid})",
                        callback_data='no-callback'
                    )
                ]
            )

    notify_msg: Message = None
    if (len(target_cids) > 1 and not target_mid) or (
        target_mid and message.external_reply
    ):
        if notify_msg := await send_notif():
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
        if context.user_data.get("media_group_id") != media_group_id:
            context.user_data["group_msgs"] = []
            context.user_data["media_group_id"] = media_group_id
        context.user_data["group_msgs"].append(message.message_id)
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

    async def add_tag(tag: str, edit_what: str, **kwargs) -> None:
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
            pass

    if replied_to_link:
        replied_to_link = f'<blockquote><a href="{replied_to_link}">ریپلای به این پیام</a></blockquote>'
    if message.audio and not custom_tag:
        await add_tag(
            dbh.get_audio_tag(target_uid) +'\n'+ replied_to_link,
            "caption",
            show_caption_above_media=message.show_caption_above_media,
        )
    elif custom_tag:
        # edit text
        if not await add_tag(
            custom_tag +'\n'+ replied_to_link,
            "text",
            link_preview_options=message.link_preview_options,
        ):
            await add_tag(
                custom_tag +'\n'+ replied_to_link,
                "caption",
                show_caption_above_media=message.show_caption_above_media,
            )
    elif replied_to_link:
        if not await add_tag(
            replied_to_link,
            "text",
            link_preview_options=message.link_preview_options,
        ):
            await add_tag(
                replied_to_link,
                "caption",
                show_caption_above_media=message.show_caption_above_media,
            )

    context.user_data.clear()
    return END


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
        _, target_cid, target_mid = data.split("|")

        # check is blocked by user
        if dbh.is_blocked(blocker_uid=dbh.get_uid(target_cid), blocked_uid=userid):
            await clbk.answer("این کاربر بلاکت کرده خخ", show_alert=True)
            return END

        context.user_data["target_cid"] = target_cid
        context.user_data["reply_to"] = target_mid

        await message.reply_html(
            f"جوابت به این پیام رو بفرست\n\n"
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
        _, target_cid, target_mid = data.split("|")

        # send seen message
        @handle_target_send(message=message, external_reply=message.external_reply)
        async def seen_message():
            await bot.send_message(
                dbh.get_uid(target_cid),
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
        _, target_cid = data.split("|")
        target_uid = dbh.get_uid(target_cid)

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
        _, target_cid = data.split("|")
        target_uid = dbh.get_uid(target_cid)

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
        _, target_cid, target_mid = data.split("|")

        # get uid from cid for sender
        target_uid = dbh.get_uid(target_cid)

        # report id
        report_id = uuid()

        # report to REPORT CHANNEL
        first_message = await context.bot.send_message(
            REPORT_CHAT_ID,
            f"id: <code>{report_id}</code>\n"
            f"reporter: {await get_link_username(userid, bot)}\n"
            f"reported: {await get_link_username(target_uid, bot)}\n"
            f"message:",
            parse_mode=PM.HTML,
        )
        await context.bot.copy_message(
            REPORT_CHAT_ID,
            target_uid,
            target_mid,
            reply_parameters=ReplyParameters(first_message.message_id, None, True),
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
        _, target_cid, *to_be_deleted = data.split("|")
        # delete the sent message
        for tbd in to_be_deleted:
            try:
                await bot.delete_message(
                    dbh.get_uid(target_cid),
                    tbd
                )
            except:
                pass
        # delete the message so it won't fuck up
        ## save reply_to
        reply_mid = message.reply_to_message.message_id
        ### delete
        try:
            await message.delete()
        except:
            pass
        # the true edit text
        try:
            await message.reply_text(
                "پاکش کردم براش😮‍💨",
                reply_parameters=ReplyParameters(reply_mid, None, True),
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


class FilterMediaGroups(filters.MessageFilter):
    def check_update(self, update: Update) -> Optional[Union[bool, FilterDataDict]]:
        return bool(update.message and update.message.media_group_id)


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
