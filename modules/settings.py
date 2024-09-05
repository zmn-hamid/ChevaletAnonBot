# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import VALIDATION_TEXT, MAX_NAME_LENGTH
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
        f"اسم نمایشی‌ات:\n{dbh.get_name(uid=userid)}\n"
        f"این اسمیه که بقیه موقع فرستادن پیام بهت میبینن.\n"
        "اسم جدید رو بفرست یا کنسل کن: /cancel:"
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
    if len(message.text) > MAX_NAME_LENGTH:
        await message.reply_text(
            f"اسم جدید نباید بیشتر از {MAX_NAME_LENGTH}تا حرف باشه. دوباره امتحان کن"
        )
        return 0
    dbh.cur.execute(
        f'UPDATE {dbh.users_table} SET name=%s WHERE uid="{userid}"', (message.text,)
    )
    dbh.db.commit()
    await message.reply_text(f"انجام شد. اسم جدیدت:\n{dbh.get_name(userid)}")

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
        await message.reply_text("همه با موفقیت آنبلاک شدن.")
    else:
        await message.reply_text(
            "اگه مطمئنی این متن رو بفرس: "
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
    await message.reply_text(
        "این پیام رو بفرس به یکی که میخوای آنبلاکت کنه و ازش بخواه تا بزنه رو لینک:"
    )
    await message.reply_text(f"t.me/{bot.username}?start=UNBLOCK-{userid}")


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
    await message.reply_text("کنسل شد.")
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
unblock_all_handler = CommandHandler("unblock_all", unblock_all_cmd)
unblock_me_handler = CommandHandler("unblock_me", unblock_me_cmd)
