# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM
from telegram.warnings import PTBUserWarning

# project imports
from config import REPORT_CHAT_ID
from modules.Global.database import dbh
from modules.Global.user_init import init_user
from modules.Global.get_user import href_user
from modules.Global.decorators import verify_user, handle_errors

# global imports
from warnings import filterwarnings
from shortuuid import uuid


# ignore the per_message error
filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)


@handle_errors
@verify_user(initialize_user=True)
async def start_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
):
    # input texts:
    # /start
    # /start USER_CID
    split_text = message.text.split()

    if len(split_text) == 1:
        # send start/help text
        await message.reply_text("This is the start text")

    else:
        target_cid = split_text[1]

        # save target to context
        context.user_data["target_cid"] = target_cid

        await message.reply_text(
            f"sending message to {dbh.get_name(dbh.get_uid(target_cid))}" " | /cancel",
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
):
    target_cid = context.user_data.get("target_cid")
    target_mid = context.user_data.get("reply_to")

    # get uid from cid for target
    target_uid = dbh.get_uid(target_cid)
    if target_uid == None:
        await message.reply_text("target user has not started the bot yet")
        return ConversationHandler.END

    # get cid from uid for sender
    # so the reply markup won't have the uid inside it, for extra privacy
    sender_cid = dbh.get_cids(userid)[0]

    # send message to target
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
        reply_to_message_id=target_mid if target_mid else None,
    )
    await message.reply_text(
        "sent",
        reply_to_message_id=message.message_id,
    )
    context.user_data.clear()
    return ConversationHandler.END


@handle_errors
@verify_user()
async def answer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
):
    if (clbk := update.callback_query) and (data := clbk.data):
        _, target_cid, target_mid = data.split("|")

        context.user_data["target_cid"] = target_cid
        context.user_data["reply_to"] = target_mid

        await message.reply_text(
            f"sending your answer | /cancel", reply_to_message_id=message.message_id
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
):
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
            await clbk.answer("blocked successfully.")
            return ConversationHandler.END

        else:
            await clbk.answer("failed to block.")
            return ConversationHandler.END


@handle_errors
@verify_user()
async def unblock(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
):
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
            await clbk.answer("unblocked successfully.")
            return ConversationHandler.END

        else:
            await clbk.answer("failed to unblock.")
            return ConversationHandler.END


@handle_errors
@verify_user()
async def report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
):
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
            f"reporter: {href_user(update.effective_user.id)}\n"
            f"reported: {href_user(target_uid)}\n"
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
            f"done.\nreport id: <code>{report_id}</code>",
            reply_to_message_id=message.message_id,
            parse_mode=PM.HTML,
        )

    return ConversationHandler.END


@handle_errors
@verify_user()
async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
):
    context.user_data.clear()
    await message.reply_text("canceled.")
    return ConversationHandler.END


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
            MessageHandler(filters.ALL & (~filters.COMMAND), send_msg),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
    ],
    per_user=True,
)
