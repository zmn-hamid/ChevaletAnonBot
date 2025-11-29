from typing import Callable

import psycopg2
from telegram import Message, ReplyParameters, Update
from telegram.constants import ParseMode as PM
from telegram.error import BadRequest, Forbidden, TimedOut
from telegram.ext import ContextTypes, ConversationHandler

from config import ERROR_CHAT_ID, GM_GROUP_ID
from modules.Global.database import DBHandler, db_base
from modules.Global.log import logger
from modules.Global.myhelpers import generate_chevaletid, get_trace
from modules.Global.user_init import init_user


def prep_function(func) -> Callable:
    """prepare user and handle forbidden error"""

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # only handle updates from private chats
        if (
            update is None
            or update.edited_message
            or update.effective_chat.type in ["channel", "group"]
            or update.effective_chat.id in [int(GM_GROUP_ID)]
            or (
                update.my_chat_member
                and update.my_chat_member.chat
                and (update.my_chat_member.chat.id in [int(GM_GROUP_ID)])
            )
        ):
            return ConversationHandler.END
        conn = None
        try:
            context.user_data.setdefault("media_msgs", [])
            context.user_data.setdefault("sent_medias", [])
            conn = db_base.get_connection()
            with conn.cursor() as cur:
                # get db
                dbh = DBHandler(cur, conn)

                # check connection
                if not context.user_data.get("no db check"):
                    try:
                        dbh.user_count()
                    except (psycopg2.OperationalError, psycopg2.InterfaceError):
                        logger.info("Lost connection to PostgreSQL, reconnecting...")
                        try:
                            cur.close()
                        except:
                            pass
                        try:
                            conn.close()
                        except:
                            pass
                        try:
                            db_base.connect_db()
                            context.user_data["no db check"] = True
                            return await wrapper(update, context)
                        except:
                            pass

                message: Message = update.effective_message
                userid = str(update.effective_user.id)
                bot = update.get_bot()

                # initialize user
                output = await init_user(userid, bot, dbh)
                if output is False:
                    await message.reply_text(
                        "مشکلی در ساخت لینک ناشناس بوجود اومد. دوباره تلاش کن و اگه موفق نشدی، قبل از استفاده از بات با پشتیبانی تماس بگیر"
                    )
                    context.user_data.clear()
                    return ConversationHandler.END
                elif not dbh.get_chevaletid_by_uid(userid):
                    if dbh.set_chevaletid(userid, generate_chevaletid()) is False:
                        await message.reply_text(
                            "مشکلی در ساخت اکانت شما بوجود اومد. دوباره تلاش کن و اگه موفق نشدی، قبل از استفاده از بات با پشتیبانی تماس بگیر"
                        )
                        context.user_data.clear()
                        return ConversationHandler.END

                if dbh.is_banned(userid):
                    # await message.reply_text(
                    #     "از بات بن شدی. اگه فک میکنی این یه اشتباهه با ادمین صحبت کن"
                    # )
                    context.user_data.clear()
                    return ConversationHandler.END

                context.user_data["no db check"] = False
                conn.commit()
                return await func(update, context, message, userid, bot, dbh)
        except BadRequest as e:
            if str(e).startswith("Query is too old"):
                logger.debug("old query ignored: %s" % e)
                return
            elif str(e) == "Message to be replied not found":
                logger.debug("Message to be replied not found")
                return
            raise e
        except (psycopg2.Error, psycopg2.DatabaseError) as e:
            try:
                await message.reply_text(
                    "مشکلی برای دیتابیس به وجود آمده. به پشتیبانی خبردادیم، لطفا صبر کنید و دوباره تلاش کنید"
                )
            except:
                pass
            try:
                await bot.send_message(
                    ERROR_CHAT_ID,
                    f"PostgreSQL ERROR: {e}\n<pre>{get_trace(e)}</pre>",
                    parse_mode=PM.HTML,
                )
            except:
                try:
                    await bot.send_message(ERROR_CHAT_ID, f"PostgreSQL ERROR2: {e}")
                except:
                    try:
                        await bot.send_message(
                            ERROR_CHAT_ID,
                            "PostgreSQL ERROR3: COULDN'T EVEN SEND THE ERROR",
                        )
                        logger.error(f"ERRORRR -> {get_trace(e, False)}")
                    except:
                        pass
        except TimedOut:
            return
        except Forbidden as e:
            # bot is blocked by the user
            logger.debug(str(e))
            return ConversationHandler.END
        finally:
            if conn:
                try:
                    db_base.put_connection(conn)
                except:
                    pass

    return wrapper


def delete_notify_on_END(func) -> Callable:
    """deletes the notify user message that is sent before private messages"""

    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        # making a list so whatever added to it in the function
        # will be accessible from here (inside the wrapper)
        # reason: lists are linked to their instances by default
        wrapper_list = []
        context.user_data["wrapper_list"] = wrapper_list
        output = await func(update, context, *args, **kwargs)

        # main
        if output in ["del+0", "del+e"]:
            try:
                await wrapper_list[0].delete()
            except:
                pass

        # output
        if output == "del+0":
            return 0
        elif output == "del+e":
            return ConversationHandler.END
        else:
            return output

    return wrapper


def handle_target_send(message: Message, external_reply: Message):
    """decorator for handling sending message to target (in case errors happen)"""

    def tst(func) -> Callable:
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Forbidden as e:
                if str(e) == "Forbidden: bot is not a member of the channel chat":
                    # This part is unnecessary but better to be kept than nothing
                    await message.reply_html(
                        "چنلی که ازش ریپلای کردی بات رو به خودش اضافه نکرده. اول باید از ادمینش بخوای که اینکارو کنه."
                        "\n\nدوباره پیامتو بفرست.",
                        reply_parameters=ReplyParameters(message.message_id),
                    )
                    return "del+0"
                elif str(e) == "Forbidden: bot was blocked by the user":
                    await message.reply_html("مخاطبت بات رو بلاک کرده")
                    return "del+0"
                else:
                    raise
            except BadRequest as e:
                if str(e) == "Message to be replied not found":
                    if external_reply:
                        # This part is unnecessary but better to be kept than nothing
                        await message.reply_html(
                            "چنلی که ازش ریپلای کردی بات رو به خودش اضافه نکرده. اول باید از ادمینش بخوای که اینکارو کنه."
                            "\n\nدوباره پیامتو بفرست.",
                            reply_parameters=ReplyParameters(message.message_id),
                        )
                        return "del+0"
                    else:
                        # this was previously recognized as "deleted target message"
                        # but now after testing, it's probabely caused by blocking the bot
                        await message.reply_html(
                            "مخاطبت احتمالا بات رو بلاک کرده. ممکنم هست بخاطر کلیر هیستوری، پیام مدنظرت پاک شده باشه. میتونی لینکشو تست کنی تا ببینی میشه پیام فرستاد یا نه.\n\n"
                            "<blockquote>بخاطر ویژگیِ تلگرام، تا پیام معمولی نفرستم بهش نمیتونم مطمئن شم بات رو بلاک کرده یا نه</blockquote>",
                            reply_parameters=ReplyParameters(message.message_id),
                        )
                        return "del+e"
                elif str(e) == "MESSAGE_ID_INVALID":
                    return "del+e"
                elif str(e) == "Quote_text_invalid":
                    await message.reply_text(
                        "پیام اشتباهی رو ریپلای کردی. دوباره امتحان کن",
                        reply_parameters=ReplyParameters(message.message_id),
                    )
                    return "del+0"
                else:
                    raise

        return wrapper

    return tst
