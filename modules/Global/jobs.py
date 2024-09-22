# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.log import logger
from modules.Global.database import dbh

# global imports
import os


async def log_bot_started(context: CallbackContext) -> None:
    """updates the bot's command menu"""
    if context.application.bot._initialized:
        logger.info(f"started @{context.application.bot.username}...")
    else:
        context.application.job_queue.run_once(log_bot_started, 0.5)


async def renew_connection(context: CallbackContext) -> None:
    """updates the bot's command menu"""
    dbh.cur.close()
    dbh.connect_db()
    logger.debug("renewed sql connection")


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


async def send_mass_msg(context: CallbackContext) -> None:
    """sends mass msg"""
    msg: Message = context.job.data.get("message")
    failed_to_send = []

    # notify
    await msg.reply_text("starting to send mass msg...")

    # send to users
    dbh.cur.execute(f"SELECT uid FROM {dbh.users_table}")
    for item in dbh.cur.fetchall():
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
                    [f"{item['uid']} | {item.get('reason')}" for item in failed_to_send]
                )
            )
        await msg.reply_document(open(logfile, "rb"))
        os.remove(logfile)
