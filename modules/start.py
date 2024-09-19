# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM
from telegram.warnings import PTBUserWarning
from telegram.error import BadRequest, Forbidden

# project imports
from config import REPORT_CHAT_ID, SUPPORT_ADMIN, DELETION_TIMEOUT
from modules.Global.database import dbh
from modules.Global.get_user import get_username, href_user, get_link_username
from modules.Global.decorators import prep_function, delete_notify_on_END
from modules.Global.fetch_texts import fetch_text
from modules.Global.jobs import delete_warning, delete_message
from modules.Global.reply_markups import CANCEL_BUTTON

# global imports
from shortuuid import uuid
from warnings import filterwarnings


# reply markup buttons
class BTN:
    REPLY = "⌨️ ارسال جواب"
    BLOCK = "🔒 بلاک"
    UNBLOCK = "🔓 آنبلاک"
    REPORT = "⚠️ ریپورت"


# ignore the per_message error
filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)


# end conversation
END = ConversationHandler.END


@prep_function
async def start_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
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
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "❔چرا چندتا لینک داشته باشم",
                            callback_data=f"more-links",
                        )
                    ]
                ]
            ),
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

            if target_uid == userid:
                await message.reply_text(
                    "میخوای با خودت صحبت کنی؟ :) عب نداره راحت باش"
                )
            await message.reply_html(
                f"به {dbh.get_name(target_uid)} وصل شدی. پیامتو بفرست",
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
) -> int:
    """
    # message sending fallback
    forwards the given message to the user (without sender)
    """
    target_cid = context.user_data.get("target_cid")
    target_mid = context.user_data.get("reply_to")  # None when not answer

    # get target uid
    target_uid = dbh.get_uid(target_cid)

    # check is blocked by user
    if dbh.is_blocked(blocker_uid=target_uid, blocked_uid=userid):
        await message.reply_text(
            "این کاربر بلاکت کرده خخ",
            reply_parameters=ReplyParameters(message.message_id),
        )
        return END

    # get cid from uid for sender
    # so the reply markup won't have the uid inside it, for extra privacy
    sender_cid = dbh.get_cids(userid)[0]

    # sending message to target
    target_cids = dbh.get_cids(target_uid)
    cid_idx_text = ""
    msg_type_text = "پیامِ"
    ## no target uid means not an answer
    if target_mid:
        msg_type_text = "ریپلایِ"
    elif len(target_cids) > 1:
        ### notify user if target has >1 cid
        cid_idx_text = f" با لینک {target_cids.index(target_cid) + 1} ({target_cid})"
    announce_msg = await bot.send_message(
        target_uid,
        f"{msg_type_text} جدید{cid_idx_text}:",
        reply_parameters=ReplyParameters(target_mid) if target_mid else None,
    )
    context.user_data.get("wrapper_list", []).append(announce_msg)
    ## send the message
    reply_markup = InlineKeyboardMarkup(
        [
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
    )
    ## calculate reply and quote
    has_quote = message.quote
    reply_to_chat, reply_to_mid, quote_text, quote_position = None, None, None, None
    external_reply = message.external_reply
    if external_reply:
        reply_to_chat = external_reply.chat.id
        reply_to_mid = external_reply.message_id
    elif target_mid:
        reply_to_chat = target_uid
        reply_to_mid = target_mid
    if has_quote:
        quote_text = message.quote.text
        quote_position = message.quote.position
    try:
        copied_message_id: MessageId = await message.copy(
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
    except Forbidden as e:
        if str(e) == "Forbidden: bot is not a member of the channel chat":
            await message.reply_html(
                "چنلی که ازش ریپلای کردی بات رو به خودش اضافه نکرده. اول باید از ادمینش بخوای که اینکارو کنه."
                "\n\nدوباره پیامتو بفرست.",
                reply_parameters=ReplyParameters(message.message_id),
            )
            return "del+0"
        else:
            raise Forbidden(str(e)) from e
    except BadRequest as e:
        if str(e) == "Message to be replied not found":
            if external_reply:
                await message.reply_html(
                    "چنلی که ازش ریپلای کردی بات رو به خودش اضافه نکرده. اول باید از ادمینش بخوای که اینکارو کنه."
                    "\n\nدوباره پیامتو بفرست.",
                    reply_parameters=ReplyParameters(message.message_id),
                )
                return "del+0"
            else:
                await message.reply_text(
                    "پیامی که میخوای جوابشو بدی از چت مخاطبت پاک شده. باید از نو پیام بفرستی بهش\n"
                    "این پیام موقتا تعبیه شده. اگه فک میکنی اشتباه تشخیص دادیم، لطفا به ادمین خبر بده",
                    reply_parameters=ReplyParameters(message.message_id),
                )
                return "del+e"
        elif str(e) == "MESSAGE_ID_INVALID":
            return "del+e"
        elif str(e) == "Quote_text_invalid":
            await message.reply_text(
                "پیام اشتباهی رو ریپلای کردی. دوباره امتحان کن",
                reply_parameters=ReplyParameters(message.message_id),
            )
            return "del+0"
        else:
            raise BadRequest(str(e)) from e
    if dbh.get_warning(userid):
        warning_message = await message.reply_text(
            f"فرستادم بهش. {DELETION_TIMEOUT} ثانیه فرصت داری با دکمه ی زیر پاکش کنی.\n"
            "غیرفعال‌سازیِ اخطار توی ستینگه",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "پاکش کننن",
                            callback_data=f"delete|{target_cid}|{copied_message_id.message_id}|{announce_msg.message_id}",
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
            "فرستادم بهش",
            reply_parameters=ReplyParameters(message.message_id),
        )

    # add custom tag and audio tag
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
                message_id=copied_message_id.message_id,
                parse_mode=PM.HTML,
                reply_markup=reply_markup,
                **kwargs,
            )
            return True
        except:
            pass

    if message.audio and not custom_tag:
        await add_tag(
            dbh.get_audio_tag(target_uid),
            "caption",
            show_caption_above_media=message.show_caption_above_media,
        )
    elif custom_tag:
        # edit text
        if not await add_tag(
            custom_tag, "text", link_preview_options=message.link_preview_options
        ):
            await add_tag(
                custom_tag,
                "caption",
                link_preview_options=message.link_preview_options,
            )

    context.user_data.clear()
    return END


@prep_function
async def answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
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

        await message.reply_text(
            f"جوابت به این پیام رو بفرست",
            reply_parameters=ReplyParameters(message.message_id),
            reply_markup=InlineKeyboardMarkup([[CANCEL_BUTTON]]),
        )
        return 0


@prep_function
async def block(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """
    # block using message button
    """
    if (clbk := update.callback_query) and (data := clbk.data):
        _, target_cid = data.split("|")
        target_uid = dbh.get_uid(target_cid)

        if dbh.add_block(userid, target_uid):
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
            if userid == target_uid:
                await clbk.answer("یه تراپی برو💀👍")
            else:
                await clbk.answer("با موفقیت بلاک شد.")

        else:
            await clbk.answer("همین الانش بلاک هست")


@prep_function
async def unblock(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """
    # unblock using message button
    """
    if (clbk := update.callback_query) and (data := clbk.data):
        _, target_cid = data.split("|")
        target_uid = dbh.get_uid(target_cid)

        if dbh.remove_block(userid, target_uid):
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
            if userid == target_uid:
                await clbk.answer("خوبه پس تراپی جواب داد🥹")
            else:
                await clbk.answer("با موفقیت آنبلاک شد.")

        else:
            await clbk.answer("همین الانش بلاک نیس")


@prep_function
async def report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
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
) -> int:
    """# delete the sent message on undo"""
    if (clbk := update.callback_query) and (data := clbk.data):
        _, target_cid, copied_message_id, announce_mid = data.split("|")
        # delete the sent message
        try:
            await bot.delete_messages(
                dbh.get_uid(target_cid), [copied_message_id, announce_mid]
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
) -> int:
    """# cancel"""
    context.user_data.clear()
    await message.edit_text("چشم بهم بزنی این پیام نیس👋")
    context.application.job_queue.run_once(delete_message, 2, {"message": message})
    return END


delete_message_handler = CallbackQueryHandler(delete_msg_clbk, r"^delete\|")
start_clbk = CommandHandler("start", start_cmd)
answer_clbk = CallbackQueryHandler(answer, r"^answer\|")
report_clbk = CallbackQueryHandler(report, r"^report\|")
block_clbk = CallbackQueryHandler(block, r"^block\|")
unblock_clbk = CallbackQueryHandler(unblock, r"^unblock\|")
cancel_clbk = CallbackQueryHandler(cancel, r"cancel")
start_cmd_handler = ConversationHandler(
    entry_points=[
        start_clbk,
        answer_clbk,
        report_clbk,
        block_clbk,
        unblock_clbk,
    ],
    states={
        0: [
            start_clbk,
            answer_clbk,
            report_clbk,
            block_clbk,
            unblock_clbk,
            MessageHandler(filters.ALL & (~filters.COMMAND), send_msg),
        ],
    },
    fallbacks=[
        delete_message_handler,
        cancel_clbk,
        CommandHandler("cancel", cancel_cmd),
        MessageHandler(filters.ALL & filters.COMMAND, cancel_all),
    ],
    per_user=True,
)
