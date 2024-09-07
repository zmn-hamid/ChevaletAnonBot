# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM
from telegram.warnings import PTBUserWarning

# project imports
from config import SELLER_ADMIN, MAX_CID_LENGTH, MIN_CID_LENGTH, ALLOWED_CID_CHARS
from modules.Global.database import dbh
from modules.Global.decorators import verify_user, handle_errors
from modules.Global.get_user import user_links_text, get_user_links
from modules.Global.cid_gen import generate_cid

# global imports
from mysql.connector.errors import IntegrityError
from warnings import filterwarnings


# ignore the per_message error
filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)


MARKUP_BUTTONS = {
    "default-set": [
        [
            InlineKeyboardButton(
                "اضافه کردن لینک جدید",
                callback_data=f"add-link",
            ),
        ],
        [
            InlineKeyboardButton(
                "شخصی سازی لینک",
                callback_data=f"ch-link",
            ),
            InlineKeyboardButton(
                "حذف کردن لینک",
                callback_data=f"rm-link",
            ),
        ],
    ],
    "undo": InlineKeyboardButton(
        "برگشت به منوی اصلی",
        callback_data=f"undo-main-menu",
    ),
    "what-is-id": InlineKeyboardButton(
        f"آیدی لینک چیه؟",
        callback_data=f"what-is-id|",
    ),
}


@handle_errors
@verify_user()
async def my_cids_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """returns users cids"""
    if update.callback_query:
        method = update.callback_query.edit_message_text
    else:
        method = message.reply_text
    await method(
        user_links_text(dbh.get_cids(userid), dbh.get_cid_limit(userid), bot.username),
        reply_markup=InlineKeyboardMarkup(MARKUP_BUTTONS["default-set"]),
        parse_mode=PM.HTML,
        disable_web_page_preview=False,
    )


@handle_errors
@verify_user()
async def add_link_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """adds a cid"""
    if clbk := update.callback_query:
        # check if user has reached limit
        cid_limit = dbh.get_cid_limit(userid)
        current_cid_count = len(dbh.get_cids(userid))
        if current_cid_count >= cid_limit:
            return await message.reply_text(
                f"به حد مجازت رسیدی. برای لینکهای بیشتر به ادمین پیام بده: @{SELLER_ADMIN}"
            )

        # add cid and return links
        output = dbh.add_cid(userid, generate_cid(), 0)
        if output == False:
            return await message.reply_text(
                "مشکلی در ساخت لینک ناشناس بوجود اومد. دوباره تلاش کن و اگه موفق نشدی، قبل از استفاده از بات با پشتیبانی تماس بگیر"
            )
        try:
            await clbk.edit_message_text(
                user_links_text(dbh.get_cids(userid), cid_limit, bot.username),
                reply_markup=InlineKeyboardMarkup(MARKUP_BUTTONS["default-set"]),
                parse_mode=PM.HTML,
                disable_web_page_preview=False,
            )
        except:
            pass
        await clbk.answer("added a new link")


@handle_errors
@verify_user()
async def remove_link_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """removes a cid"""
    if (clbk := update.callback_query) and (data := clbk.data):
        data_split = data.split("|")
        cids = dbh.get_cids(userid)
        if len(data_split) == 1:
            # ask to choose
            await clbk.edit_message_text(
                get_user_links(cids, bot.username),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"حذف لینک {idx+1}",
                                callback_data=f"rm-link|{cid}",
                            )
                        ]
                        for idx, cid in enumerate(cids)
                    ]
                    + [[MARKUP_BUTTONS["undo"]]]
                ),
                parse_mode=PM.HTML,
            )

        elif len(data_split) == 2:
            # ask for approval
            _, chosen_cid = data_split
            await clbk.edit_message_text(
                get_user_links(cids, bot.username, flag_cid=chosen_cid)
                + "\n\nمطمئنی از حذفش؟ قابل برگشت نیست",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"آره مطمئنم",
                                callback_data=f"rm-link|{chosen_cid}|yes",
                            ),
                            InlineKeyboardButton(
                                f"نههه پاک نکن",
                                callback_data=f"rm-link|{chosen_cid}|no",
                            ),
                        ]
                    ]
                ),
                parse_mode=PM.HTML,
                disable_web_page_preview=False,
            )

        elif len(data_split) == 3:
            # handle approval
            _, chosen_cid, sure = data_split
            if sure == "yes":
                # delete
                dbh.cur.execute(
                    f"DELETE FROM {dbh.cids_table} WHERE "
                    f'cid="{chosen_cid}" and uid="{userid}"'
                )
                dbh.db.commit()
                if len(dbh.get_cids(userid)) < 1:  # < in case set to -1
                    # create new cid
                    dbh.add_cid(userid, generate_cid(), 0)
                    await clbk.answer(
                        "با موفقیت حذف شد ولی چون فقط یک لینک داشتی، "
                        "بجاش یکی دیگه تولید شد",
                        show_alert=True,
                    )
                else:
                    await clbk.answer("با موفقیت حذف شد.")
                cids = dbh.get_cids(userid)
                await clbk.edit_message_text(
                    get_user_links(cids, bot.username),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"حذف لینک {idx+1}",
                                    callback_data=f"rm-link|{cid}",
                                )
                            ]
                            for idx, cid in enumerate(cids)
                        ]
                        + [[MARKUP_BUTTONS["undo"]]]
                    ),
                    parse_mode=PM.HTML,
                    disable_web_page_preview=False,
                )
            else:
                # don't delete
                await clbk.answer("کنسل شد")
                await clbk.edit_message_text(
                    get_user_links(cids, bot.username),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    f"حذف لینک {idx+1}",
                                    callback_data=f"rm-link|{cid}",
                                )
                            ]
                            for idx, cid in enumerate(cids)
                        ]
                        + [[MARKUP_BUTTONS["undo"]]]
                    ),
                    parse_mode=PM.HTML,
                )


@handle_errors
@verify_user()
async def change_link_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """changes a cid"""
    if (clbk := update.callback_query) and (data := clbk.data):
        data_split = data.split("|")
        cids = dbh.get_cids(userid)
        if len(data_split) == 1:
            # ask to choose
            await clbk.edit_message_text(
                get_user_links(cids, bot.username),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"شخصی سازی لینک {idx+1}",
                                callback_data=f"ch-link|{cid}",
                            )
                        ]
                        for idx, cid in enumerate(cids)
                    ]
                    + [[MARKUP_BUTTONS["undo"]]]
                ),
                parse_mode=PM.HTML,
                disable_web_page_preview=False,
            )
            return ConversationHandler.END

        elif len(data_split) == 2:
            # ask for sending the new id
            chosen_cid = data_split[1]
            msg = await clbk.edit_message_text(
                get_user_links(cids, bot.username, flag_cid=chosen_cid),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"شخصی سازی لینک {idx+1}",
                                callback_data=f"ch-link|{cid}",
                            )
                        ]
                        for idx, cid in enumerate(cids)
                    ]
                    + [[MARKUP_BUTTONS["undo"]]]
                ),
                parse_mode=PM.HTML,
                disable_web_page_preview=False,
            )
            await message.reply_text(
                "آیدی جدیدِ لینکت رو توی پیام بعد بفرس برام.\n"
                "فقط <i>حروف کوچیک و بزرگ انگلیسی، اعداد، آندرلاین و خط تیره</i> مجازه.\n"
                f"تعداد حروف مجاز: {MIN_CID_LENGTH} تا {MAX_CID_LENGTH}\n"
                "کنسل کردن: /cancel",
                reply_markup=InlineKeyboardMarkup([[MARKUP_BUTTONS["what-is-id"]]]),
                parse_mode=PM.HTML,
            )
            context.user_data["chosen_cid"] = chosen_cid
            context.user_data["links_mid"] = msg.message_id
            return 0


@handle_errors
@verify_user()
async def update_cid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """changes the cid"""
    new_cid = message.text
    chosen_cid = context.user_data.get("chosen_cid")
    links_mid = context.user_data.get("links_mid")

    # check unallowed length
    if not MIN_CID_LENGTH < len(new_cid) < MAX_CID_LENGTH:
        await message.reply_text(f'خطا: تعداد حروف مجاز {MIN_CID_LENGTH} تا {MAX_CID_LENGTH} حرفه')
        return 0

    # check for unallowed characters
    for char in new_cid:
        if char not in ALLOWED_CID_CHARS:
            await message.reply_text(
                "فقط حروف کوچیک و بزرگ انگلیسی، اعداد، آندرلاین و خط تیره مجازه. "
                "دوباره امتحان کن یا کنسل کن: /cancel",
                reply_to_message_id=message.message_id,
            )
            return 0

    # check if new cid is repetitive
    dbh.cur.execute(f"SELECT cid FROM {dbh.cids_table}")
    all_the_cids = [item[0] for item in dbh.cur.fetchall()]
    if new_cid in all_the_cids:
        await message.reply_text(
            "این آیدی برداشته شده. آیدی دیگه ای بفرس یا کنسل کن: /cancel",
            reply_to_message_id=message.message_id,
        )
        return 0

    # update
    try:
        dbh.cur.execute(
            f"UPDATE {dbh.cids_table} SET cid=%s WHERE cid='{chosen_cid}'", (new_cid,)
        )
        dbh.db.commit()
        cids = dbh.get_cids(userid)
        try:
            await bot.edit_message_text(
                message_id=links_mid,
                chat_id=userid,
                text=get_user_links(dbh.get_cids(userid), bot.username),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"شخصی سازی لینک {idx+1}",
                                callback_data=f"ch-link|{cid}",
                            )
                        ]
                        for idx, cid in enumerate(cids)
                    ]
                    + [[MARKUP_BUTTONS["undo"]]]
                ),
                parse_mode=PM.HTML,
                disable_web_page_preview=False,
            )
        except:
            pass
        await message.reply_text("با موفقیت تغییر یافت")

        return ConversationHandler.END
    except IntegrityError:
        await message.reply_text(
            "ظاهرا یکی زودتر این آیدی رو برداشت. "
            "دوباره امتحان کن یا کنسل کن: /cancel"
        )
        return 0


@handle_errors
@verify_user()
async def others_while_sending(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    context.user_data.clear()
    await message.reply_text("در حال تغییر آیدی بودی، اگه پشیمون شدی بزن رو /cancel")
    return 0


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
    cids = dbh.get_cids(userid)
    try:
        await bot.edit_message_text(
            message_id=context.user_data["links_mid"],
            chat_id=userid,
            text=get_user_links(cids, bot.username),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"شخصی سازی لینک {idx+1}",
                            callback_data=f"ch-link|{cid}",
                        )
                    ]
                    for idx, cid in enumerate(cids)
                ]
                + [[MARKUP_BUTTONS["undo"]]]
            ),
            parse_mode=PM.HTML,
        )
    except:
        pass
    context.user_data.clear()
    await message.reply_text("کنسل شد.")
    return ConversationHandler.END


my_cids_handler = CommandHandler("my_links", my_cids_cmd)
my_cids_callback_handler = CallbackQueryHandler(my_cids_cmd, r"undo-main-menu")
add_cid_handler = CallbackQueryHandler(add_link_clbk, r"add-link")
rm_cid_handler = CallbackQueryHandler(remove_link_clbk, r"^rm-link")
change_cid_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(change_link_clbk, r"^ch-link"),
    ],
    states={
        0: [
            MessageHandler(filters.TEXT & (~filters.COMMAND), update_cid),
            MessageHandler(
                filters.ALL & (~filters.Regex("/cancel")), others_while_sending
            ),
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
    ],
    per_user=True,
)
