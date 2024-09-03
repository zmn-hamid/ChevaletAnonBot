# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import ADMINS
from modules.Global.database import dbh
from modules.Global.get_user import href_user
from modules.Global.decorators import verify_user, handle_errors
from modules.Global.fetch_texts import fetch_text
from modules.Global.exceptions import WrongSyntaxErr
from modules.other_msgs import other_messages_template

# global imports
from mysql.connector.errors import IntegrityError
import os


@handle_errors
@verify_user()
async def admin_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None | Message:
    """for admins to handle the bot"""
    # check if it's admin
    if userid not in ADMINS:
        return await other_messages_template(message)
    await message.reply_text("<i>*admin detected*</i>", parse_mode=PM.HTML)

    # check what's the request
    text = message.text.split()[1:]
    try:
        arg1 = text[0]

        # help text
        if arg1 == "help":
            await message.reply_text(fetch_text("admin"), parse_mode=PM.HTML)

        # send mass message to users
        elif arg1 == "send-mass-msg":
            if not (len(text) > 1 and text[1] == "YES"):
                return await message.reply_text(
                    "send <code>/admin send-mass-msg YES</code> if you're sure",
                    parse_mode=PM.HTML,
                )
            sent_to = []

            # send to users
            dbh.cur.execute(f"SELECT uid FROM {dbh.users_table}")
            for item in dbh.cur.fetchall():
                uid = item[0]
                try:
                    await message.reply_to_message.copy(uid)
                    sent_to.append({"uid": uid, "sent": True})
                except Exception as e:
                    sent_to.append({"uid": uid, "sent": False, "reason": str(e)})

            # send log
            logfile = "log-mass-msg.txt"
            with open(logfile, "w") as f:
                f.writelines(
                    [
                        f"{uid} | {'success' if item['sent'] else f'fail | {item.get('reason')}'}"
                        for item in sent_to
                    ]
                )
            await message.reply_document(open(logfile, "rb"))
            os.remove(logfile)

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
                dbh.cur.execute(
                    f"UPDATE {dbh.users_table} SET cid_limit={limit} "
                    f'WHERE uid="{uid}"'
                )
                dbh.db.commit()
            return await message.reply_text("done.")

        # user hyperlink option
        elif arg1 == "link":
            uid = text[1]
            try:
                uname_part = f" | @{(await bot.get_chat(uid)).username}"
            except:
                uname_part = ""
            return await message.reply_text(
                f"{href_user(uid)}{uname_part}",
                parse_mode=PM.HTML,
            )

        else:
            raise WrongSyntaxErr
    except (IndexError, ValueError, WrongSyntaxErr):
        return await message.reply_text(
            "wrong syntax. use <code>/admin help</code>", parse_mode=PM.HTML
        )
    except IntegrityError:
        return await message.reply_text(
            "wrong value (uid or whatever). use <code>/admin help</code>",
            parse_mode=PM.HTML,
        )
    except Exception as e:
        try:
            return await message.reply_text(f"error: {e.__class__} | {e}")
        except:
            pass


admin_handler = CommandHandler("admin", admin_cmd)
