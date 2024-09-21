# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from config import ADMINS
from modules.Global.database import dbh
from modules.Global.get_user import get_link_username
from modules.Global.decorators import prep_function
from modules.Global.fetch_texts import fetch_text
from modules.Global.exceptions import WrongSyntaxErr
from modules.other_msgs import other_messages_template

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
            failed_to_send = []

            # send to users
            dbh.cur.execute(f"SELECT uid FROM {dbh.users_table}")
            for item in dbh.cur.fetchall():
                uid = item[0]
                try:
                    await message.reply_to_message.copy(uid)
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
                await message.reply_document(open(logfile, "rb"))
                os.remove(logfile)

        # number of users
        elif arg1 == "user-count":
            dbh.cur.execute(f"SELECT COUNT(*) FROM {dbh.users_table}")
            await message.reply_text(f"{dbh.cur.fetchone()[0]} users")

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
                    f'UPDATE {dbh.users_table} SET cid_limit=%s WHERE uid="{uid}"',
                    (limit,),
                )
                dbh.db.commit()
            return await message.reply_text("done.")

        # user hyperlink option
        elif arg1 == "link":
            return await message.reply_html(
                await get_link_username(text[1], bot),
            )

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
