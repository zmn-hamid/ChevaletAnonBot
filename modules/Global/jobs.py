# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.log import logger
from modules.Global.database import DBHandler, db_base
from mysql.connector.errors import Error as mysql_Error
from mysql.connector.cursor import MySQLCursor

# global imports
import os


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
        await msg.edit_text("فرستادم بهش")
    except:
        pass


async def delete_message(context: CallbackContext) -> None:
    """deletes the warning message"""
    try:
        await context.job.data.get("message").delete()
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
