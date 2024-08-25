# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.database import dbh
from modules.Global.decorators import verify_user, handle_errors


@handle_errors
@verify_user()
async def settings_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    # TODO correct settings help text
    text = message.text.split()[1:]
    await message.reply_text("this is settings help text.\n" "/settings_name")


@handle_errors
@verify_user()
async def settings_name_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
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
):
    dbh.cur.execute(
        f'UPDATE {dbh.users_table} SET name="{message.text}" ' f'WHERE uid="{userid}"'
    )
    dbh.db.commit()
    await message.reply_text(f"done. current name: {dbh.get_name(userid)}")

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
    await message.reply_text("canceled.")
    return ConversationHandler.END


settings_handler = CommandHandler("settings", settings_cmd)
settings_name_handler = ConversationHandler(
    entry_points=[
        CommandHandler("settings_name", settings_name_cmd),
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
