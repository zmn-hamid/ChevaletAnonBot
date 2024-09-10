# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import MAX_NAME_LENGTH
from modules.Global.database import dbh
from modules.Global.decorators import verify_user, handle_errors
from modules.Global.fetch_texts import fetch_text
from modules.Global.reply_markups import SETTINGS_MARKUP


# end conversation
END = ConversationHandler.END


@handle_errors
@verify_user()
async def settings_cmd_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """sends settings help text"""
    if update.callback_query:
        method = message.edit_text
    else:
        method = message.reply_text
    await method(
        fetch_text("settings/main"),
        reply_markup=InlineKeyboardMarkup(SETTINGS_MARKUP["main-menu-set"]),
        parse_mode=PM.HTML,
    )
    return END


@handle_errors
@verify_user()
async def change_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """sends changing name help text"""
    if (clbk := update.callback_query) and (data := clbk.data):
        msg = await clbk.edit_message_text(
            fetch_text("settings/change_name") % (dbh.get_name(userid)),
            parse_mode=PM.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [SETTINGS_MARKUP["formatting"]],
                    [SETTINGS_MARKUP["nvm-back-to-menu"]],
                ]
            ),
        )
        context.user_data["og_mid"] = msg.message_id
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
            f"نکته: قالب بندی یه مقدار به تعداد حروفت اضافه میکنه"
        )
        return 0
    dbh.cur.execute(
        f'UPDATE {dbh.users_table} SET name=%s WHERE uid="{userid}"', (new_name,)
    )
    dbh.db.commit()
    try:
        await bot.delete_message(userid, context.user_data["og_mid"])
    except:
        pass
    await message.reply_text(
        f"انجام شد. اسم جدیدت:\n{dbh.get_name(userid)}\n\n"
        f"میتونی لینک خودتو تست کنی تا ببینی چجوری شده :)",
        parse_mode=PM.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [SETTINGS_MARKUP["back-to-menu"]],
            ]
        ),
    )
    return ConversationHandler.END


@handle_errors
@verify_user()
async def warning_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """warning settings for user"""
    if (clbk := update.callback_query) and (data := clbk.data):

        async def _warning_text():
            current = dbh.get_warning(userid)
            await clbk.edit_message_text(
                fetch_text("settings/warning") % ("فعال" if current else "غیرفعال"),
                parse_mode=PM.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            SETTINGS_MARKUP["warning-deactivate"]
                            if current
                            else SETTINGS_MARKUP["warning-activate"],
                        ],
                        [SETTINGS_MARKUP["back-to-menu"]],
                    ]
                ),
            )

        _, activation_text = data.split("|", 1)
        if activation_text:
            if activation_text == "activate":
                dbh.cur.execute(
                    f'UPDATE {dbh.users_table} SET warning=%s WHERE uid="{userid}"',
                    (True,),
                )
                dbh.db.commit()
                await clbk.answer("اخطار فعال شد")
                await _warning_text()
            else:
                dbh.cur.execute(
                    f'UPDATE {dbh.users_table} SET warning=%s WHERE uid="{userid}"',
                    (False,),
                )
                dbh.db.commit()
                await clbk.answer("اخطار غیرفعال شد")
                await _warning_text()
        else:
            await _warning_text()
        return END


@handle_errors
@verify_user()
async def custom_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """custom tag"""
    if (clbk := update.callback_query) and (data := clbk.data):
        user_custom_tag = dbh.get_custom_tag(userid)
        msg = await clbk.edit_message_text(
            fetch_text("settings/custom_tag")
            % (user_custom_tag if user_custom_tag else "[تگی ثبت نکردی]"),
            parse_mode=PM.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [SETTINGS_MARKUP["remove-custom-tag"]],
                    [SETTINGS_MARKUP["formatting"]],
                    [SETTINGS_MARKUP["nvm-back-to-menu"]],
                ],
            ),
        )
        context.user_data["og_mid"] = msg.message_id
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
    try:
        await bot.delete_message(userid, context.user_data["og_mid"])
    except:
        pass
    await message.reply_text(
        f"انجام شد. تگ جدیدت:\n{dbh.get_custom_tag(userid)}\n\n"
        f"میتونی لینک خودتو تست کنی تا ببینی چجوری شده :)",
        parse_mode=PM.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [SETTINGS_MARKUP["back-to-menu"]],
            ]
        ),
    )
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
    try:
        await bot.delete_message(userid, context.user_data["og_mid"])
    except:
        pass
    await message.reply_text(
        "تگ دلخواهت با موفقیت پاک شد.",
        reply_markup=InlineKeyboardMarkup(
            [
                [SETTINGS_MARKUP["back-to-menu"]],
            ]
        ),
    )
    return ConversationHandler.END


@handle_errors
@verify_user()
async def audio_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """audio tag"""
    if (clbk := update.callback_query) and (data := clbk.data):
        user_audio_tag = dbh.get_audio_tag(userid)
        msg = await clbk.edit_message_text(
            fetch_text("settings/audio_tag")
            % (user_audio_tag if user_audio_tag else "[تگی ثبت نکردی]"),
            parse_mode=PM.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [SETTINGS_MARKUP["remove-audio-tag"]],
                    [SETTINGS_MARKUP["formatting"]],
                    [SETTINGS_MARKUP["nvm-back-to-menu"]],
                ],
            ),
        )
        context.user_data["og_mid"] = msg.message_id
        return 1


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
    try:
        await bot.delete_message(userid, context.user_data["og_mid"])
    except:
        pass
    await message.reply_text(
        f"انجام شد. تگ جدیدت:\n{dbh.get_audio_tag(userid)}\n\n"
        f"میتونی لینک خودتو تست کنی تا ببینی چجوری شده :)",
        parse_mode=PM.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [SETTINGS_MARKUP["back-to-menu"]],
            ]
        ),
    )
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
    try:
        await bot.delete_message(userid, context.user_data["og_mid"])
    except:
        pass
    await message.reply_text(
        "تگ دلخواهت با موفقیت پاک شد.",
        reply_markup=InlineKeyboardMarkup(
            [
                [SETTINGS_MARKUP["back-to-menu"]],
            ]
        ),
    )
    return ConversationHandler.END


@handle_errors
@verify_user()
async def unblock_all_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """warning settings for user"""
    if (clbk := update.callback_query) and (data := clbk.data):
        _, activation_text = data.split("|", 1)
        if activation_text:
            dbh.cur.execute(
                f'DELETE FROM {dbh.blocks_table} WHERE blocker_uid="{userid}"'
            )
            dbh.db.commit()
            await clbk.edit_message_text(
                "همه با موفقیت آنبلاک شدن.",
                reply_markup=InlineKeyboardMarkup([[SETTINGS_MARKUP["back-to-menu"]]]),
            )
        else:
            await clbk.edit_message_text(
                "اگه میخوای همه رو آنبلاک کنی و مطمئنی، دکمه ی زیر رو بزن",
                parse_mode=PM.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "مطمئنم، بزن همه رو آنبلاک کن",
                                callback_data="unblock-all|yes",
                            ),
                        ],
                        [
                            SETTINGS_MARKUP["back-to-menu"],
                        ],
                    ]
                ),
            )
        return END


@handle_errors
@verify_user()
async def unblock_me_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """sends unblock link of the user"""
    await message.reply_text(
        "این لینک رو بفرس به یکی که بلاکت کرده. وقتی که بزنه روش آنبلاک میشی:"
    )
    await message.reply_text(f"t.me/{bot.username}?start=UNBLOCK-{userid}")


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
    await message.reply_text(
        "در حال تغییر تنظیماتت بودی پس کنسلش کردم. دوباره امتحان کن"
    )
    context.user_data.clear()
    return END


@handle_errors
@verify_user()
async def what_is_formatting(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """cancel all"""
    # await message.reply_text()
    await update.callback_query.answer(
        fetch_text("formatting_explanation"), show_alert=True
    )


_settings_clbk_handler = CallbackQueryHandler(settings_cmd_clbk, r"settings-menu")
_what_is_formatting = CallbackQueryHandler(what_is_formatting, r"what-is-formatting")
settings_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(change_name, r"^change-name\|"),
        CallbackQueryHandler(custom_tag, r"^custom-tag\|"),
        CallbackQueryHandler(audio_tag, r"^audio-tag\|"),
        # other handlers
        CallbackQueryHandler(warning_clbk, r"^warning\|"),
        CallbackQueryHandler(unblock_all_clbk, r"^unblock-all\|"),
        CallbackQueryHandler(unblock_me_clbk, r"^unblock-me\|"),
        CommandHandler("settings", settings_cmd_clbk),
        _settings_clbk_handler,
        _what_is_formatting,
    ],
    states={
        0: [
            MessageHandler(filters.TEXT & (~filters.COMMAND), update_name),
        ],
        1: [
            CallbackQueryHandler(remove_custom_tag, r"rm-custom-tag"),
            MessageHandler(filters.TEXT & (~filters.COMMAND), update_custom_tag),
        ],
        2: [
            CallbackQueryHandler(remove_audio_tag, r"rm-audio-tag"),
            MessageHandler(filters.TEXT & (~filters.COMMAND), update_audio_tag),
        ],
    },
    fallbacks=[
        _what_is_formatting,
        _settings_clbk_handler,
        CallbackQueryHandler(settings_cmd_clbk, r"nvm-back-to-menu"),
        MessageHandler(filters.ALL & filters.COMMAND, cancel_all),
    ],
    per_user=True,
)
