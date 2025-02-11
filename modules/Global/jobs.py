# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import (
    DELETION_TEXT,
    HEALTH_PORT,
    DELETION_TIMEOUT,
    DELETION_TIMEOUT_EXTENDED,
    GM_GROUP_ID,
    GM_GROUP_TOPIC_ID,
)
from config import DELETION_TEXT, HEALTH_PORT
from modules.Global.log import logger
from modules.Global.database import DBHandler, db_base
from mysql.connector.errors import Error as mysql_Error

# global imports
import os
import socket
import asyncio


async def log_bot_started(context: CallbackContext) -> None:
    """updates the bot's command menu"""
    if context.application.bot._initialized:
        logger.info(f"started @{context.application.bot.username}...")
    else:
        context.application.job_queue.run_once(log_bot_started, 0.5)


async def set_commands(context: CallbackContext) -> None:
    """updates the bot's command menu"""
    await context.application.bot.set_my_commands(
        [
            ("help", "🆘 کمک!"),
            ("my_links", "🔗 لینک های من"),
            ("settings", "⚙️ تنظیمات و قابلیت ها"),
            ("cancel", "❌ کنسل کردن هرکاری که داری انجام میدی"),
        ]
    )
    logger.info("successfully set the commands")


async def delete_warning(context: CallbackContext) -> None:
    """deletes the warning message"""
    try:
        msg: Message = context.job.data.get("warning_message")
        await msg.edit_text(
            msg.text_html.removesuffix(DELETION_TEXT % DELETION_TIMEOUT).removesuffix(
                DELETION_TEXT % DELETION_TIMEOUT_EXTENDED
            ),
            parse_mode=PM.HTML,
        )
    except:
        pass


async def delete_message(context: CallbackContext) -> None:
    """deletes the messages | used for cancel"""
    try:
        msg: Message = context.job.data.get("message")
        delete_reply = False
        try:
            txtsplt = msg.reply_to_message.text.split(" ")
            assert len(txtsplt) == 2 and txtsplt[0] == "/start"
            delete_reply = True
        except:
            pass
        await msg.delete()
        if delete_reply:
            try:
                await msg.reply_to_message.delete()
            except:
                pass
    except:
        pass


async def check_connection(context: CallbackContext) -> None:
    """check connection to db and reconnect if needed"""
    try:
        with db_base.connection_pool.get_connection() as conn:
            with conn.cursor() as cur:
                dbh = DBHandler(cur, conn)
                try:
                    dbh.user_count()
                except mysql_Error as e:
                    if e.errno in [2013, 2055]:  # Lost connection error
                        logger.info("Lost connection to MySQL, reconnecting...")
                        try:
                            db_base.connection_pool._remove_connections()
                        except:
                            pass
                        try:
                            cur.close()
                        except:
                            pass
                        try:
                            db_base.connect_db()
                        except:
                            pass
    except Exception as e:
        logger.error(f"error while checking connection: {e}")


async def send_mass_msg(context: CallbackContext) -> None:
    """sends mass msg"""
    try:
        with db_base.connection_pool.get_connection() as conn:
            with conn.cursor() as cur:
                dbh = DBHandler(cur, conn)
                msg: Message = context.job.data.get("message")
                failed_to_send = []

                # notify
                await msg.reply_text("starting to send mass msg...")

                # send to users
                for item in dbh.get_all_uids():
                    uid = item[0]
                    try:
                        await msg.reply_to_message.copy(uid)
                    except Exception as e:
                        failed_to_send.append({"uid": uid, "reason": str(e)})

                # send log
                if failed_to_send:
                    logfile = "mass-msg-failurs.txt"
                    with open(logfile, "w") as f:
                        f.write(
                            "\n".join(
                                [
                                    f"{item['uid']} | {item.get('reason')}"
                                    for item in failed_to_send
                                ]
                            )
                        )
                    await msg.reply_document(open(logfile, "rb"))
                    os.remove(logfile)

                # notify
                await msg.reply_text("sent the message to everyone.")
    except Exception as e:
        logger.warning("send_mass_msg faild: " + str(e))


async def send_gm_gn(context: CallbackContext) -> None:
    try:
        bot: Bot = context.application.bot
        await bot.send_message(
            GM_GROUP_ID,
            "صبح بخیر" if context.job.data.get("is_morning") else "شب بخیر",
            message_thread_id=GM_GROUP_TOPIC_ID,
            parse_mode=PM.HTML,
        )
    except Exception as e:
        logger.warning("send_gm_gn faild: " + str(e))


async def health_check_app():
    try:

        def _port_is_open(_host, _port):
            _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = _sock.connect_ex((_host, _port))
            _sock.close()
            return result == 0

        host, port = "localhost", HEALTH_PORT

        if not _port_is_open(host, port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((host, port))
            sock.listen(1)

            logger.info(f"socket on port {port} is open now...")

            try:
                while True:
                    await asyncio.sleep(1)
            finally:
                try:
                    sock.close()
                except:
                    pass
        else:
            logger.warning(f"Port {port} is not available")
    except asyncio.CancelledError:
        logger.warning("health check app was stopped")
    except Exception as e:
        logger.error(f"error running health | {e.__class__.__name__} | {e}")
    finally:
        try:
            sock.close()
        except:
            pass
