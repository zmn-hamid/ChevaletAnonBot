# telegram imports
from telegram import *
from telegram.ext import *

# project imports
from modules.Global.decorators import verify_user, handle_errors
from modules.Global.database import dbh

# end conversation
END = ConversationHandler.END


@handle_errors
@verify_user()
async def myuid_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message: Message,
    userid: str,
    bot: Bot,
) -> None:
    """returns user id | is gonna be used for education"""
    if userid =='84581926':
        dbh.cur.execute('select uid, name from users')
        for user in dbh.cur.fetchall():
            uid, name = user
            if '?' in name:
                try:
                    nn = (await bot.get_chat(uid)).full_name
                    dbh.cur.execute(f'update users set name=%s where uid="{uid}"', (nn, ))
                    dbh.db.commit()
                except:
                    pass
        print('done')


tf_handler = CommandHandler("fix", myuid_cmd)
