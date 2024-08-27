# telegram imports
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode as PM

# project imports
from modules.Global.database import dbh
from modules.Global.get_user import href_user
from modules.Global.decorators import verify_user, handle_errors
from modules.Global.fetch_texts import fetch_text
from modules.Global.exceptions import WrongSyntaxErr
from config import ADMINS


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
        return await message.reply_text("lol")
    await message.reply_text("<i>*admin detected*</i>", parse_mode=PM.HTML)

    # check what's the request
    text = message.text.split()[1:]
    try:
        arg1 = text[0]
        # help text
        if arg1 == "help":
            await message.reply_text(fetch_text("admin"), parse_mode=PM.HTML)
        
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
        
        # link option
        elif arg1 == "link":
            uid = text[1]
            try:
                c = await bot.get_chat(uid)
                uname_part = f" | @{c.username}"
            except:
                uname_part = None
            return await message.reply_text(
                f'{href_user(uid)}{uname_part if uname_part else ""}',
                parse_mode=PM.HTML,
            )
        
        else:
            raise WrongSyntaxErr
    except (IndexError, WrongSyntaxErr):
        return await message.reply_text(
            "wrong syntax. use <code>/admin help</code>", parse_mode=PM.HTML
        )
    except Exception as e:
        try:
            await message.reply_text(f"error: {e.__class__} | {e}")
        except:
            pass


admin_handler = CommandHandler("admin", admin_cmd)
