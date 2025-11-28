from telegram import *
from telegram.constants import ParseMode as PM
from telegram.ext import *

from config import MAX_NAME_LENGTH
from modules.Global.database import DBHandler
from modules.Global.decorators import prep_function
from modules.Global.fetch_texts import fetch_text
from modules.Global.reply_markups import SETTINGS_MARKUP

# end conversation
END = ConversationHandler.END


@prep_function
async def settings_cmd_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """sends settings help text"""
    if update.callback_query:
        await update.callback_query.answer()
        method = message.edit_text
    else:
        method = message.reply_text
    await method(
        fetch_text("settings/main"),
        reply_markup=InlineKeyboardMarkup(SETTINGS_MARKUP["main-menu-set"]),
        parse_mode=PM.HTML,
    )
    return END


@prep_function
async def media_settings_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# unblocks all the blocked users"""
    await update.callback_query.answer()
    if (clbk := update.callback_query) and (clbk.data):
        await clbk.edit_message_text(
            fetch_text("settings/media_settings"),
            parse_mode=PM.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        SETTINGS_MARKUP["formatting"],
                        SETTINGS_MARKUP["back-to-menu"],
                    ],
                ]
            ),
        )
        return END


@prep_function
async def reply_quote_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# unblocks all the blocked users"""
    await update.callback_query.answer()
    if (clbk := update.callback_query) and (clbk.data):
        await clbk.edit_message_text(
            fetch_text("settings/reply_quote"),
            parse_mode=PM.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        SETTINGS_MARKUP["back-to-menu"],
                    ],
                ]
            ),
        )
        return END


@prep_function
async def change_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# sends changing name help text"""
    await update.callback_query.answer()
    if (clbk := update.callback_query) and (clbk.data):
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


@prep_function
async def update_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# updates user's preview name"""
    new_name = message.text_html
    if len(new_name) > MAX_NAME_LENGTH:
        await message.reply_text(
            f"اسم جدید نباید بیشتر از {MAX_NAME_LENGTH}تا حرف باشه. دوباره امتحان کن.\n"
            f"نکته: قالب بندی یه مقدار به تعداد حروفت اضافه میکنه"
        )
        return 0
    dbh.set_name(userid, new_name)
    try:
        await bot.delete_message(userid, context.user_data["og_mid"])
    except:
        pass
    await message.reply_html(
        f"انجام شد. اسم جدیدت:\n{dbh.get_name(userid)}\n\n"
        f"میتونی لینک خودتو تست کنی تا ببینی چجوری شده :)",
        reply_markup=InlineKeyboardMarkup(
            [
                [SETTINGS_MARKUP["back-to-menu"]],
            ]
        ),
    )
    return ConversationHandler.END


@prep_function
async def wpp_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# warning settings for user"""
    await update.callback_query.answer()
    if (clbk := update.callback_query) and (data := clbk.data):

        async def _wpp_text():
            wpp = dbh.get_wpp(userid)
            await clbk.edit_message_text(
                fetch_text("settings/wpp") % ("حالت پیشفرض" if wpp else "غیرفعال"),
                parse_mode=PM.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            (
                                SETTINGS_MARKUP["wpp-deactivate"]
                                if wpp
                                else SETTINGS_MARKUP["wpp-activate"]
                            ),
                        ],
                        [SETTINGS_MARKUP["back-to-menu"]],
                    ]
                ),
            )

        _, activation_text = data.split("|", 1)
        if activation_text:
            if activation_text == "activate":
                dbh.set_wpp(userid, True)
                await clbk.answer("پیشنمایش به حالتِ پیشفرض تبدیل شد")
                await _wpp_text()
            else:
                dbh.set_wpp(userid, False)
                await clbk.answer("پیشنمایش غیرفعال شد")
                await _wpp_text()
        else:
            await _wpp_text()
        return END


@prep_function
async def warning_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# warning settings for user"""
    await update.callback_query.answer()
    if (clbk := update.callback_query) and (data := clbk.data):

        async def _warning_text():
            current = dbh.get_warning(userid)
            await clbk.edit_message_text(
                fetch_text("settings/warning") % ("فعال" if current else "غیرفعال"),
                parse_mode=PM.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            (
                                SETTINGS_MARKUP["warning-deactivate"]
                                if current
                                else SETTINGS_MARKUP["warning-activate"]
                            ),
                        ],
                        [SETTINGS_MARKUP["back-to-menu"]],
                    ]
                ),
            )

        _, activation_text = data.split("|", 1)
        if activation_text:
            if activation_text == "activate":
                dbh.set_warning(userid, True)
                await clbk.answer("اخطار فعال شد")
                await _warning_text()
            else:
                dbh.set_warning(userid, False)
                await clbk.answer("اخطار غیرفعال شد")
                await _warning_text()
        else:
            await _warning_text()
        return END


@prep_function
async def easier_answer_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# unblocks all the blocked users"""
    await update.callback_query.answer()
    if (clbk := update.callback_query) and (clbk.data):
        await clbk.edit_message_text(
            fetch_text("settings/easier_answer"),
            parse_mode=PM.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        SETTINGS_MARKUP["back-to-menu"],
                    ],
                ]
            ),
        )
        return END


@prep_function
async def channel_signature_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# channel signature feature explanation"""
    await update.callback_query.answer()
    if (clbk := update.callback_query) and (clbk.data):
        await clbk.edit_message_text(
            fetch_text("settings/channel_signature"),
            parse_mode=PM.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        SETTINGS_MARKUP["back-to-menu"],
                    ],
                ]
            ),
        )
        return END


@prep_function
async def seen_settings_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# warning settings for user"""
    await update.callback_query.answer()
    if (clbk := update.callback_query) and (data := clbk.data):

        async def _seen_text():
            current = dbh.get_seen_status(userid)
            await clbk.edit_message_text(
                fetch_text("settings/seen") % ("فعال" if current else "غیرفعال"),
                parse_mode=PM.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            (
                                SETTINGS_MARKUP["seen-deactivate"]
                                if current
                                else SETTINGS_MARKUP["seen-activate"]
                            ),
                        ],
                        [SETTINGS_MARKUP["back-to-menu"]],
                    ]
                ),
            )

        _, activation_text = data.split("|", 1)
        if activation_text:
            if activation_text == "activate":
                dbh.set_seen_option(userid, True)
                await clbk.answer("آپشن سین زدن فعال شد")
                await _seen_text()
            else:
                dbh.set_seen_option(userid, False)
                await clbk.answer("آپشن سین زدن غیرفعال شد")
                await _seen_text()
        else:
            await _seen_text()
        return END


@prep_function
async def custom_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """
    # custom tag help text
    """
    await update.callback_query.answer()
    if (clbk := update.callback_query) and (clbk.data):
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


@prep_function
async def update_custom_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# updates user's custom tag"""
    new_tag = message.text_html
    if len(new_tag) > MAX_NAME_LENGTH:
        await message.reply_text(
            f"تگ جدید نباید بیشتر از {MAX_NAME_LENGTH}تا حرف باشه. دوباره امتحان کن.\n"
            f"نکته: لینک و بولد و اینا یه مقدار به تعداد حرفات اضافه میکنن",
            reply_parameters=ReplyParameters(message.message_id),
        )
        return 1
    dbh.set_custom_tag(userid, new_tag)
    try:
        await bot.delete_message(userid, context.user_data["og_mid"])
    except:
        pass
    await message.reply_html(
        f"انجام شد. تگ جدیدت:\n{dbh.get_custom_tag(userid)}\n\n"
        f"میتونی لینک خودتو تست کنی تا ببینی چجوری شده :)",
        reply_parameters=ReplyParameters(message.message_id),
        reply_markup=InlineKeyboardMarkup(
            [
                [SETTINGS_MARKUP["back-to-menu"]],
            ]
        ),
    )
    return ConversationHandler.END


@prep_function
async def remove_custom_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# removes the custom tag of user"""
    dbh.set_custom_tag(userid, None)
    await message.edit_text(
        "تگ دلخواهت با موفقیت پاک شد",
        reply_markup=InlineKeyboardMarkup(
            [
                [SETTINGS_MARKUP["back-to-menu"]],
            ]
        ),
    )
    return ConversationHandler.END


@prep_function
async def audio_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# audio tag help text"""
    await update.callback_query.answer()
    if (clbk := update.callback_query) and (clbk.data):
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
        return 2


@prep_function
async def update_audio_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# updates user's audio tag"""
    new_tag = message.text_html
    if len(new_tag) > MAX_NAME_LENGTH:
        await message.reply_text(
            f"تگ جدید نباید بیشتر از {MAX_NAME_LENGTH}تا حرف باشه. دوباره امتحان کن.\n"
            f"نکته: لینک و بولد و اینا یه مقدار به تعداد حرفات اضافه میکنن",
            reply_parameters=ReplyParameters(message.message_id),
        )
        return 2
    dbh.set_audio_tag(userid, new_tag)
    try:
        await bot.delete_message(userid, context.user_data["og_mid"])
    except:
        pass
    await message.reply_html(
        f"انجام شد. تگ جدیدت:\n{dbh.get_audio_tag(userid)}\n\n"
        f"میتونی لینک خودتو تست کنی تا ببینی چجوری شده :)",
        reply_parameters=ReplyParameters(message.message_id),
        reply_markup=InlineKeyboardMarkup(
            [
                [SETTINGS_MARKUP["back-to-menu"]],
            ]
        ),
    )
    return ConversationHandler.END


@prep_function
async def remove_audio_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# removes user audio tag"""
    dbh.set_audio_tag(userid, None)
    await message.edit_text(
        "تگ دلخواهت با موفقیت پاک شد",
        reply_markup=InlineKeyboardMarkup(
            [
                [SETTINGS_MARKUP["back-to-menu"]],
            ]
        ),
    )
    return ConversationHandler.END


@prep_function
async def unblock_all_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# unblocks all the blocked users"""
    await update.callback_query.answer()
    if (clbk := update.callback_query) and (data := clbk.data):
        _, activation_text = data.split("|", 1)
        if activation_text:
            dbh.unblock_all(userid)
            await clbk.edit_message_text(
                "همه با موفقیت آنبلاک شدن",
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


@prep_function
async def unblock_me_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# unblock me help text"""
    msg: Message = await message.reply_text(
        "این لینک رو بفرس به یکی که بلاکت کرده. وقتی که بزنه روش آنبلاک میشی:"
    )
    await message.reply_text(
        f"t.me/{bot.username}?start=UNBLOCK-{userid}",
        reply_parameters=ReplyParameters(msg.message_id, None, True),
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
    """# cancel other messages sent while in convo"""
    await message.reply_text(
        "در حال تغییر تنظیماتت بودی پس کنسلش کردم. دوباره امتحان کن",
        reply_parameters=ReplyParameters(message.message_id),
    )
    context.user_data.clear()
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
async def what_is_formatting(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# sends help text for what is text formatting"""
    await update.callback_query.answer(
        fetch_text("formatting_explanation"), show_alert=True
    )


_settings_clbk = CallbackQueryHandler(settings_cmd_clbk, r"settings-menu")
_formatting_clbk = CallbackQueryHandler(what_is_formatting, r"what-is-formatting")
settings_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(reply_quote_clbk, r"^reply-quote\|"),
        CallbackQueryHandler(media_settings_clbk, r"^media-settings\|"),
        CallbackQueryHandler(change_name, r"^change-name\|"),
        CallbackQueryHandler(custom_tag, r"^custom-tag\|"),
        CallbackQueryHandler(audio_tag, r"^audio-tag\|"),
        # other handlers
        CallbackQueryHandler(wpp_clbk, r"^wpp\|"),
        CallbackQueryHandler(warning_clbk, r"^warning\|"),
        CallbackQueryHandler(easier_answer_clbk, r"^easier-answer\|"),
        CallbackQueryHandler(channel_signature_clbk, r"^channel-signature\|"),
        CallbackQueryHandler(seen_settings_clbk, r"^seen-settings\|"),
        CallbackQueryHandler(unblock_all_clbk, r"^unblock-all\|"),
        CallbackQueryHandler(unblock_me_clbk, r"^unblock-me\|"),
        CommandHandler("settings", settings_cmd_clbk),
        _settings_clbk,
        _formatting_clbk,
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
        _formatting_clbk,
        _settings_clbk,
        CallbackQueryHandler(settings_cmd_clbk, r"nvm-back-to-menu"),
        CommandHandler("cancel", cancel_cmd),
        MessageHandler(filters.ALL | filters.COMMAND, cancel_all),
    ],
    per_user=True,
)
