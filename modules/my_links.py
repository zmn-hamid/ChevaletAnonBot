# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM
from telegram.warnings import PTBUserWarning

# project imports
from config import SELLER_ADMIN, MAX_CID_LENGTH, MIN_CID_LENGTH, ALLOWED_CID_CHARS
from modules.Global.database import dbh
from modules.Global.decorators import prep_function
from modules.Global.get_user import user_links_text, get_user_links
from modules.Global.cid_gen import generate_cid
from modules.Global.fetch_texts import fetch_text
from modules.Global.reply_markups import MYLINKS_MARKUP

# global imports
from mysql.connector.errors import IntegrityError
from warnings import filterwarnings


# ignore the per_message error
filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)


@prep_function
async def my_links_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """# returns users cids"""
    if update.callback_query:
        method = update.callback_query.edit_message_text
    else:
        method = message.reply_text
    await method(
        user_links_text(dbh.get_cids(userid), dbh.get_cid_limit(userid), bot.username),
        reply_markup=InlineKeyboardMarkup(MYLINKS_MARKUP["default-set"]),
        parse_mode=PM.HTML,
        disable_web_page_preview=True,
    )
    return ConversationHandler.END


@prep_function
async def add_link_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """# adds a cid"""
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
        try:
            await clbk.edit_message_text(
                user_links_text(dbh.get_cids(userid), cid_limit, bot.username),
                reply_markup=InlineKeyboardMarkup(MYLINKS_MARKUP["default-set"]),
                parse_mode=PM.HTML,
                disable_web_page_preview=True,
            )
        except:
            pass
        await clbk.answer("added a new link")


@prep_function
async def remove_link_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """# removes a cid"""
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
                    + [[MYLINKS_MARKUP["back-to-menu"]]]
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
                                f"✅ آره مطمئنم",
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
                disable_web_page_preview=True,
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
                        + [[MYLINKS_MARKUP["back-to-menu"]]]
                    ),
                    parse_mode=PM.HTML,
                    disable_web_page_preview=True,
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
                        + [[MYLINKS_MARKUP["back-to-menu"]]]
                    ),
                    parse_mode=PM.HTML,
                )


@prep_function
async def change_link_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """# change cid selection"""
    if (clbk := update.callback_query) and (data := clbk.data):
        data_split = data.split("|")
        cids = dbh.get_cids(userid)
        if len(data_split) == 1:
            # ask to choose
            await clbk.edit_message_text(
                get_user_links(cids, bot.username) + "\n\nانتخاب کن",
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
                    + [
                        [MYLINKS_MARKUP["what-is-customize"]],
                        [MYLINKS_MARKUP["back-to-menu"]],
                    ]
                ),
                parse_mode=PM.HTML,
                disable_web_page_preview=True,
            )
            return ConversationHandler.END

        elif len(data_split) == 2:
            # ask for sending the new id
            chosen_cid = data_split[1]
            msg = await clbk.edit_message_text(
                get_user_links(cids, bot.username, flag_cid=chosen_cid)
                + "\n\n\n"
                + fetch_text("mylinks") % (MIN_CID_LENGTH, MAX_CID_LENGTH),
                reply_markup=InlineKeyboardMarkup(
                    [[MYLINKS_MARKUP["what-is-cid"]], [MYLINKS_MARKUP["back-to-menu"]]]
                ),
                parse_mode=PM.HTML,
                disable_web_page_preview=True,
            )
            context.user_data["chosen_cid"] = chosen_cid
            context.user_data["links_mid"] = msg.message_id
            return 0


@prep_function
async def update_cid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """# changes the cid"""
    new_cid = message.text
    chosen_cid = context.user_data.get("chosen_cid")
    links_mid = context.user_data.get("links_mid")

    # check unallowed length
    if not MIN_CID_LENGTH <= len(new_cid) <= MAX_CID_LENGTH:
        await message.reply_text(
            f"خطا: تعداد حروف مجاز {MIN_CID_LENGTH} تا {MAX_CID_LENGTH} حرفه"
        )
        return 0

    # check for unallowed characters
    for char in new_cid:
        if char not in ALLOWED_CID_CHARS:
            await message.reply_text(
                "فقط حروف کوچیک و بزرگ انگلیسی، اعداد، آندرلاین و خط تیره مجازه. "
                "دوباره امتحان کن",
                reply_parameters=ReplyParameters(message.message_id),
            )
            return 0

    # check if new cid is repetitive
    dbh.cur.execute(f"SELECT cid FROM {dbh.cids_table}")
    all_the_cids = [item[0] for item in dbh.cur.fetchall()]
    if new_cid in all_the_cids:
        await message.reply_text(
            "این آیدی برداشته شده. آیدی دیگه ای بفرس",
            reply_parameters=ReplyParameters(message.message_id),
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
                    + [[MYLINKS_MARKUP["back-to-menu"]]]
                ),
                parse_mode=PM.HTML,
                disable_web_page_preview=True,
            )
        except:
            pass
        await message.reply_text("با موفقیت تغییر یافت")

        return ConversationHandler.END
    except IntegrityError:
        await message.reply_text(
            "ظاهرا یکی زودتر این آیدی رو برداشت. دوباره امتحان کن",
            reply_parameters=ReplyParameters(message.message_id),
        )
        return 0


@prep_function
async def what_is_cid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """# explanation for cid"""
    await message.reply_html(fetch_text("cid_explanation"))


@prep_function
async def others_while_sending(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> int:
    """# if other messages sent"""
    context.user_data.clear()
    await message.reply_text(
        "در حال تغییر آیدی بودی پس کنسلش کردم. دوباره بفرست",
        reply_parameters=ReplyParameters(message.message_id),
    )
    return ConversationHandler.END


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
    return ConversationHandler.END


_mylinks_clbk = CallbackQueryHandler(my_links_cmd, r"mylinks-menu")
_what_is_cid = CallbackQueryHandler(what_is_cid, r"what-is-cid")
mylinks_handler = ConversationHandler(
    entry_points=[
        # change cid handler
        CallbackQueryHandler(change_link_clbk, r"^ch-link"),
        # other handlers
        CallbackQueryHandler(add_link_clbk, r"add-link"),
        CallbackQueryHandler(remove_link_clbk, r"^rm-link"),
        CommandHandler("my_links", my_links_cmd),
        _mylinks_clbk,
        _what_is_cid,
    ],
    states={
        0: [
            MessageHandler(filters.TEXT & (~filters.COMMAND), update_cid),
        ]
    },
    fallbacks=[
        _what_is_cid,
        _mylinks_clbk,
        CommandHandler("cancel", cancel_cmd),
        MessageHandler(filters.ALL, others_while_sending),
    ],
    per_user=True,
)
