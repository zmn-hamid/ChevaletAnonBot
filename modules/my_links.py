# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM
from telegram.warnings import PTBUserWarning

# project imports
from config import SELLER_ADMIN, MAX_CID_LENGTH, MIN_CID_LENGTH, ALLOWED_CID_CHARS
from modules.Global.database import DBHandler
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


async def my_links_template(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    if update.callback_query:
        await update.callback_query.answer()
        method = update.callback_query.edit_message_text
    else:
        method = message.reply_text
    user_cids = dbh.get_cids(userid)
    await method(
        user_links_text(user_cids, dbh.get_cid_limit(userid), bot.username)
        + (
            "<blockquote>راستی یادت نره به کانالمون سر بزنی:\n@chevalet_studio</blockquote>"
            if len(user_cids) > 2
            else ""
        ),
        reply_markup=InlineKeyboardMarkup(MYLINKS_MARKUP["default-set"]),
        parse_mode=PM.HTML,
        disable_web_page_preview=True,
    )


@prep_function
async def my_links_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# returns users cids"""
    await my_links_template(update, context, message, userid, bot, dbh)
    return ConversationHandler.END


@prep_function
async def add_link_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# adds a cid"""
    await update.callback_query.answer()
    if clbk := update.callback_query:
        # check if user has reached limit
        cid_limit = dbh.get_cid_limit(userid)
        current_cid_count = len(dbh.get_cids(userid))
        if current_cid_count >= cid_limit:
            await message.reply_text(
                f"به حد مجازت رسیدی. برای لینکهای بیشتر به ادمین پیام بده: @{SELLER_ADMIN}"
            )
            return ConversationHandler.END

        # add cid and return links
        dbh.add_cid(userid, generate_cid(), 0)
        await my_links_template(update, context, message, userid, bot, dbh)
        await clbk.answer("added a new link")


@prep_function
async def remove_link_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# removes a cid"""
    await update.callback_query.answer()
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
                disable_web_page_preview=True,
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
                dbh.rm_cid(userid, chosen_cid)
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
                    disable_web_page_preview=True,
                )


@prep_function
async def change_link_clbk(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> int:
    """# change cid selection"""
    await update.callback_query.answer()
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
    dbh: DBHandler,
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
    all_the_cids = [item[0] for item in dbh.get_all_cids()]
    if new_cid in all_the_cids:
        await message.reply_text(
            "این آیدی برداشته شده. آیدی دیگه ای بفرس",
            reply_parameters=ReplyParameters(message.message_id),
        )
        return 0

    # update
    try:
        dbh.set_cid(new_cid, chosen_cid)
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
    dbh: DBHandler,
) -> int:
    """# explanation for cid"""
    await update.callback_query.answer()
    await message.reply_html(fetch_text("cid_explanation"))


@prep_function
async def others_while_sending(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
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
    dbh: DBHandler,
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
