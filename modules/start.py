# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM
from telegram.warnings import PTBUserWarning

# project imports
from config import REPORT_CHAT_ID, SUPPORT_ADMIN
from modules.Global.database import dbh
from modules.Global.get_user import get_link_username
from modules.Global.decorators import verify_user, handle_errors
from modules.Global.fetch_texts import fetch_text

# global imports
from warnings import filterwarnings
from shortuuid import uuid


# ignore the per_message error
filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)
# end conversation
END = ConversationHandler.END


@handle_errors
@verify_user(initialize_user=True)
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
        await message.reply_text(
            fetch_text("start_help") % (SUPPORT_ADMIN),
            parse_mode=PM.HTML,
            disable_web_page_preview=True,
        )

    else:
        if split_text[1].startswith("UNBLOCK-"):
            # unblocking user
            try:
                target_uid = split_text[1].split("-", 1)[-1]
                int(target_uid)
            except:
                await message.reply_text(
                    "لینکت اشتباهه?", reply_to_message_id=message.message_id
                )
                return
            dbh.remove_block(blocker_uid=userid, blocked_uid=target_uid)
            await message.reply_text(
                "آنبلاک شد.", reply_to_message_id=message.message_id
            )
            return END
        else:
            # sending message
            target_cid = split_text[1]
            target_uid = dbh.get_uid(target_cid)

            # check if target_cid exists
            if target_uid == None:
                await message.reply_text("این لینک اشتباهه و کار نمیکنه")
                return END

            # check is blocked by user
            if dbh.is_blocked(blocker_uid=target_uid, blocked_uid=userid):
                await message.reply_text(
                    "این کاربر بلاکت کرده خخ",
                    reply_to_message_id=message.message_id,
                )
                return END

            # save target to context
            context.user_data["target_cid"] = target_cid
            context.user_data["is_answer"] = False

            if target_uid == userid:
                await message.reply_text(
                    "میخوای با خودت صحبت کنی؟ :) عب نداره راحت باش"
                )
            await message.reply_text(
                f"در حال ارسال پیام به {dbh.get_name(target_uid)} هستی.\n"
                "کنسل کردن: /cancel",
                reply_to_message_id=message.message_id,
            )
            return 0  # state 0


@handle_errors
@verify_user()
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
    target_mid = context.user_data.get("reply_to")
    is_answer = context.user_data.get("is_answer")

    # get uid from cid for target
    target_uid = dbh.get_uid(target_cid)

    # check is blocked by user
    if dbh.is_blocked(blocker_uid=target_uid, blocked_uid=userid):
        await message.reply_text(
            "این کاربر بلاکت کرده خخ", reply_to_message_id=message.message_id
        )
        return END

    # get cid from uid for sender
    # so the reply markup won't have the uid inside it, for extra privacy
    sender_cid = dbh.get_cids(userid)[0]

    # sending message to target
    ## notify target
    if not is_answer and len(dbh.get_cids(target_uid)) > 1:
        await bot.send_message(target_uid, f"پیام جدید ({target_cid}):")
    ## send the message
    await message.copy(
        target_uid,
        parse_mode=PM.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "answer",
                        callback_data=f"answer|{sender_cid}|{message.message_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "report",
                        callback_data=f"report|{sender_cid}|{message.message_id}",
                    ),
                    InlineKeyboardButton("block", callback_data=f"block|{sender_cid}"),
                ],
            ]
        ),
        reply_to_message_id=target_mid,
    )
    await message.reply_text(
        "فرستادم بهش",
        reply_to_message_id=message.message_id,
    )
    context.user_data.clear()
    return END


@handle_errors
@verify_user()
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
            await message.reply_text(
                "این کاربر بلاکت کرده خخ", reply_to_message_id=message.message_id
            )
            return END

        context.user_data["target_cid"] = target_cid
        context.user_data["reply_to"] = target_mid
        context.user_data["is_answer"] = True

        await message.reply_text(
            f"در حال ارسال جواب هستی. کنسل کردن: /cancel",
            reply_to_message_id=message.message_id,
        )
        return 0  # state 0


@handle_errors
@verify_user()
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

        if dbh.add_block(userid, dbh.get_uid(target_cid)):
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
                                    "unblock",
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
            await clbk.answer("با موفقیت بلاک شد.")
            return END

        else:
            await clbk.answer("بلاک هستش.")
            return END


@handle_errors
@verify_user()
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

        if dbh.remove_block(userid, dbh.get_uid(target_cid)):
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
                                    "block",
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
            await clbk.answer("با موفقیت آنبلاک شد.")
            return END

        else:
            await clbk.answer("آنبلاک هستش.")
            return END


@handle_errors
@verify_user()
async def report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """
    # reports the message to report channel
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
            reply_to_message_id=first_message.message_id,
        )
        await message.reply_text(
            f"ریپورت شد.\nکد پیگیری: <code>{report_id}</code>",
            reply_to_message_id=message.message_id,
            parse_mode=PM.HTML,
        )

    return END


@handle_errors
@verify_user()
async def command_while_sending(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    context.user_data.clear()
    await message.reply_text("وسط ارسال پیام بودی. کنسلش کردم. دوباره دستور رو بفرست")
    return END


@handle_errors
@verify_user()
async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """# cancel"""
    context.user_data.clear()
    await message.reply_text("کنسل شد.")
    return END


start_cmd_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start_cmd),
        CallbackQueryHandler(answer, r"^answer\|"),
        CallbackQueryHandler(report, r"^report\|"),
        CallbackQueryHandler(block, r"^block\|"),
        CallbackQueryHandler(unblock, r"^unblock\|"),
    ],
    states={
        0: [
            CommandHandler("start", start_cmd),
            MessageHandler(filters.ALL & (~filters.COMMAND), send_msg),
            MessageHandler(
                filters.COMMAND & (~filters.Regex("/cancel")), command_while_sending
            ),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
    ],
    per_user=True,
)
