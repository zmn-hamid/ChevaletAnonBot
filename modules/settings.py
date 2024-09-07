# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import MAX_NAME_LENGTH
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
        f"اسم نمایشی‌ات:\n{dbh.get_name(uid=userid)}\n\n"
        f"این اسمیه که بقیه موقع فرستادن پیام بهت میبینن.\n"
        "اسم جدید رو بفرست یا کنسل کن: /cancel:",
        parse_mode=PM.HTML,
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
    new_name = message.text_html
    if len(new_name) > MAX_NAME_LENGTH:
        await message.reply_text(
            f"اسم جدید نباید بیشتر از {MAX_NAME_LENGTH}تا حرف باشه. دوباره امتحان کن.\n"
            f"نکته: لینک و بولد و اینا یه مقدار به تعداد حرفات اضافه میکنن"
        )
        return 0
    dbh.cur.execute(
        f'UPDATE {dbh.users_table} SET name=%s WHERE uid="{userid}"', (new_name,)
    )
    dbh.db.commit()
    await message.reply_text(f"انجام شد. اسم جدیدت:\n{dbh.get_name(userid)}",
                             parse_mode=PM.HTML,)

    return ConversationHandler.END


@handle_errors
@verify_user()
async def custom_tag_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """sends changing name help text"""
    custom_tag = dbh.get_custom_tag(userid)
    if custom_tag:
        custom_tag_text = f"تگ دلخواهت:\n{custom_tag}\n"
    else:
        custom_tag_text = 'تگ دلخواهی ثبت نکردی\n'
    await message.reply_text(
        f"{custom_tag_text}"
        f"این تگیه که به انتهای پیام ناشناسات اضافه میشه.\n"
        "تگ جدید رو بفرست یا کنسل کن: /cancel\n"
        "اگه بجاش میخوای تگت رو حذف کنی این رو بزن: /remove_custom_tag",
        parse_mode=PM.HTML,
    )
    return 1


@handle_errors
@verify_user()
async def update_custom_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """updates user's preview name"""
    new_tag = message.text_html
    if len(new_tag) > MAX_NAME_LENGTH:
        await message.reply_text(
            f"تگ جدید نباید بیشتر از {MAX_NAME_LENGTH}تا حرف باشه. دوباره امتحان کن.\n"
            f"نکته: لینک و بولد و اینا یه مقدار به تعداد حرفات اضافه میکنن"
        )
        return 1
    dbh.set_custom_tag(userid, new_tag)
    await message.reply_text(f"انجام شد. تگ جدیدت:\n{dbh.get_custom_tag(userid)}\n\n"
                             f"میتونی لینک خودتو تست کنی تا ببینی چجوری شده :)",
                             parse_mode=PM.HTML)

    return ConversationHandler.END


@handle_errors
@verify_user()
async def remove_custom_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    dbh.set_custom_tag(userid, None)
    await message.reply_text('تگ دلخواهت با موفقیت حذف شد.')
    return ConversationHandler.END


@handle_errors
@verify_user()
async def audio_tag_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """sends changing name help text"""
    audio_tag = dbh.get_audio_tag(userid)
    if audio_tag:
        custom_tag_text = f"تگ آهنگات:\n{audio_tag}\n\n"
    else:
        custom_tag_text = 'تگ آهنگی ثبت نکردی\n'
    await message.reply_text(
        f"{custom_tag_text}"
        f"این تگیه که به انتهای آهنگایی که ناشناس میفرستن بهت اضافه میشه.\n"
        f'<b>اگه "تگ دلخواه" داشته باشی، اون بجای این تگ میاد زیر آهنگا</b>\n'
        "تگ جدید رو بفرست یا کنسل کن: /cancel\n"
        "اگه بجاش میخوای تگت رو حذف کنی این رو بزن: /remove_audio_tag",
        parse_mode=PM.HTML,
    )
    return 2


@handle_errors
@verify_user()
async def update_audio_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """updates user's preview name"""
    new_tag = message.text_html
    if len(new_tag) > MAX_NAME_LENGTH:
        await message.reply_text(
            f"تگ جدید نباید بیشتر از {MAX_NAME_LENGTH}تا حرف باشه. دوباره امتحان کن.\n"
            f"نکته: لینک و بولد و اینا یه مقدار به تعداد حرفات اضافه میکنن"
        )
        return 2
    dbh.set_audio_tag(userid, new_tag)
    await message.reply_text(f"انجام شد. تگ جدیدت:\n{dbh.get_audio_tag(userid)}\n\n"
                             f"میتونی لینک خودتو تست کنی تا ببینی چجوری شده :)",
                             parse_mode=PM.HTML)

    return ConversationHandler.END


@handle_errors
@verify_user()
async def remove_audio_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    dbh.set_audio_tag(userid, None)
    await message.reply_text('تگ آهنگت با موفقیت حذف شد. همچنان اگه تگ دلخواه داشته باشی، اون میاد زیر آهنگا')
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
async def disable_warning_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """disable warning for user"""
    dbh.cur.execute(
        f'UPDATE {dbh.users_table} SET warning=%s WHERE uid="{userid}"', (False,)
    )
    dbh.db.commit()
    return await message.reply_text(
        "اخطار غیرفعال شد. برای فعال سازی /enable_warning را بزنید"
    )


@handle_errors
@verify_user()
async def enable_warning_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """enable warning for user"""
    dbh.cur.execute(
        f'UPDATE {dbh.users_table} SET warning=%s WHERE uid="{userid}"', (True,)
    )
    dbh.db.commit()
    return await message.reply_text(
        "اخطار فعال شد. برای غیرفعال سازی /disable_warning را بزنید"
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
    await message.reply_text("کنسل شد.")
    return ConversationHandler.END


@handle_errors
@verify_user()
async def cancel_all(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """cancel all"""
    await message.reply_text("در حال تغییر تنظیماتت بودی پس کنسلش کردم. دوباره امتحان کن")
    return ConversationHandler.END



settings_handler = CommandHandler("settings", settings_cmd)
settings_name_handler = ConversationHandler(
    entry_points=[
        CommandHandler("change_name", change_name_cmd),
        CommandHandler("custom_tag", custom_tag_cmd),
        CommandHandler("audio_tag", audio_tag_cmd),
    ],
    states={
        0: [
            MessageHandler(filters.TEXT & (~filters.COMMAND), update_name),
            MessageHandler(filters.ALL & (~filters.Regex("/cancel")), cancel_all),
        ],
        1: [
            CommandHandler('remove_custom_tag', remove_custom_tag),
            MessageHandler(filters.TEXT & (~filters.COMMAND), update_custom_tag),
            MessageHandler(filters.ALL & (~filters.Regex("/cancel")), cancel_all),
        ],
        2: [
            CommandHandler('remove_audio_tag', remove_audio_tag),
            MessageHandler(filters.TEXT & (~filters.COMMAND), update_audio_tag),
            MessageHandler(filters.ALL & (~filters.Regex("/cancel")), cancel_all),
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
    ],
    per_user=True,
)
unblock_all_handler = CommandHandler("unblock_all", unblock_all_cmd)
unblock_me_handler = CommandHandler("unblock_me", unblock_me_cmd)
disable_warning_handler = CommandHandler("disable_warning", disable_warning_cmd)
enable_warning_handler = CommandHandler("enable_warning", enable_warning_cmd)
