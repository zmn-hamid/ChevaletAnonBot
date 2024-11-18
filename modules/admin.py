# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import ADMINS
from modules.Global.database import DBHandler
from modules.Global.get_user import get_link_username
from modules.Global.decorators import prep_function
from modules.Global.fetch_texts import fetch_text
from modules.Global.exceptions import WrongSyntaxErr
from modules.Global.jobs import send_mass_msg
from modules.Global.handler_templates import other_messages_template

# global imports
import os
from mysql.connector.errors import IntegrityError


@prep_function
async def admin_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
    dbh: DBHandler,
) -> None:
    """# admin messages handler"""
    # check if it's admin
    if userid not in ADMINS:
        return await other_messages_template(message)

    # check what's the request
    text = message.text.split()[1:]
    try:
        arg1 = text[0]

        # help text
        if arg1 == "help":
            await message.reply_html(fetch_text("admin"))

        # send mass message to users
        elif arg1 == "send-mass-msg":
            if not (len(text) > 1 and text[1] == "YES"):
                return await message.reply_html(
                    "send <code>/admin send-mass-msg YES</code> if you're sure",
                )
            await message.reply_text("queued for 7 seconds later...")
            context.application.job_queue.run_once(
                send_mass_msg, 7, {"message": message}
            )

        # send msg to specific user | used for reports mostly
        elif arg1 == "send-msg":
            target_uid = text[1]
            if not (len(text) > 2 and text[2] == "YES"):
                return await message.reply_html(
                    f"send <code>/admin send-msg {target_uid} YES</code> if you're sure",
                )
            try:
                await message.reply_to_message.copy(target_uid)
                await message.reply_html(
                    f"sent to {await get_link_username(target_uid, bot)}"
                )
            except Exception as e:
                await message.reply_text(f"failed to send: {e}")

        # number of users
        elif arg1 == "user-count":
            await message.reply_text(f"{dbh.user_count()} users")

        # user status -> banned cid limit stats
        elif arg1 == "stats":
            try:
                stats = dbh.user_status(text[1])
            except IndexError:
                return await message.reply_text("user has not started the bot yet?")
            return await message.reply_text(
                f"is_banned={stats[0]}\ncid_limit={stats[1]}"
            )

        # ban and unban option
        elif arg1 in ["ban", "unban"]:
            dbh.ban_action(text[1], True if arg1 == "ban" else False)
            return await message.reply_text("done.")

        # get/change cid limit for a user
        elif arg1 == "cid":
            if text[1] == "get":
                return await message.reply_text(f"limit: {dbh.get_cid_limit(text[2])}")
            elif text[1] == "set":
                uid = text[2]
                limit = int(text[3])
                dbh.set_cid_limit(uid, limit)
            return await message.reply_text("done.")

        # user hyperlink option
        elif arg1 == "link":
            return await message.reply_html(
                await get_link_username(text[1], bot),
            )

        # report id handling
        elif arg1 == "report":
            report_id = text[2]
            if text[1] == "add":
                await message.reply_text(
                    f"added {report_id}\ncounter: {dbh.add_report_id(report_id)}"
                )
            elif text[1] == "del":
                delete_count = dbh.del_report_id(report_id)
                if delete_count == 0:
                    await message.reply_text("this report didn't exist")
                else:
                    await message.reply_text(
                        f"deleted {delete_count} instance(s) of report: {report_id}"
                    )
            elif text[1] == "get":
                await message.reply_text(dbh.get_report_id(report_id))

        else:
            raise WrongSyntaxErr
    except (IndexError, ValueError, WrongSyntaxErr):
        return await message.reply_html("wrong syntax. use <code>/admin help</code>")
    except IntegrityError:
        return await message.reply_html(
            "wrong value (uid or whatever). use <code>/admin help</code>"
        )
    except Exception as e:
        try:
            return await message.reply_text(f"error: {e.__class__} | {e}")
        except:
            pass


admin_handler = CommandHandler("admin", admin_cmd)
