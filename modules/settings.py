# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import VALIDATION_TEXT
from modules.Global.database import dbh
from modules.Global.decorators import verify_user, handle_errors
from modules.Global.fetch_texts import fetch_text


# end conversation
END = ConversationHandler.END


@handle_errors
@verify_user()
async def settings_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """sends settings help text"""
    await message.reply_text(fetch_text("settings"), parse_mode=PM.HTML)


@handle_errors
@verify_user()
async def change_name_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """sends changing name help text"""
    await message.reply_text(
        f"your name is {dbh.get_name(uid=userid)}\n" "send the updated name or /cancel:"
    )
    return 0


@handle_errors
@verify_user()
async def update_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """updates user's preview name"""
    dbh.cur.execute(
        f'UPDATE {dbh.users_table} SET name="{message.text}" ' f'WHERE uid="{userid}"'
    )
    dbh.db.commit()
    await message.reply_text(f"done. current name: {dbh.get_name(userid)}")

    return ConversationHandler.END


@handle_errors
@verify_user()
async def unblock_all_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """unblocks every one (with approval)"""
    if message.text == f"/unblock_all {VALIDATION_TEXT}":
        dbh.cur.execute(f'DELETE FROM {dbh.blocks_table} WHERE blocker_uid="{userid}"')
        dbh.db.commit()
        await message.reply_text("unblocked everyone.")
    else:
        await message.reply_text(
            "if youre sure, you gotta send "
            f"<code>/unblock_all {VALIDATION_TEXT}</code>",
            parse_mode=PM.HTML,
        )


@handle_errors
@verify_user()
async def unblock_me_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """sends unblock link of the user"""
    await message.reply_text("send this to someone who has to unblock you:")
    await message.reply_text(f"t.me/{bot.username}?start=UNBLOCK-{userid}")


@handle_errors
@verify_user()
async def notify_src_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """
    # notify source help text
    notify srouce is the "new message (*source*)" text which user can enable
    or diable. it shows user where did that message come from (link-wise)
    """
    await message.reply_text(
        "/notify_link_enable\n/notify_link_disable",
        parse_mode=PM.HTML,
    )


@handle_errors
@verify_user()
async def notify_src_enable_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """enable notify source"""
    dbh.notify_cid_action(userid, True)
    await message.reply_text(
        "enabled notification.",
        parse_mode=PM.HTML,
    )


@handle_errors
@verify_user()
async def notify_src_disable_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """disable notify source"""
    dbh.notify_cid_action(userid, False)
    await message.reply_text(
        "disabled notification.",
        parse_mode=PM.HTML,
    )


@handle_errors
@verify_user()
async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """cancel"""
    await message.reply_text("canceled.")
    return ConversationHandler.END


settings_handler = CommandHandler("settings", settings_cmd)
settings_name_handler = ConversationHandler(
    entry_points=[
        CommandHandler("change_name", change_name_cmd),
    ],
    states={
        0: [
            MessageHandler(filters.TEXT & (~filters.COMMAND), update_name),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
    ],
    per_user=True,
)
notify_link_handler = CommandHandler("notify_src", notify_src_cmd)
notify_link_enable_handler = CommandHandler("notify_src_enable", notify_src_enable_cmd)
notify_link_disable_handler = CommandHandler(
    "notify_src_disable", notify_src_disable_cmd
)
unblock_all_handler = CommandHandler("unblock_all", unblock_all_cmd)
unblock_me_handler = CommandHandler("unblock_me", unblock_me_cmd)
