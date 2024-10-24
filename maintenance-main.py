"""main file"""

# telegram imports
from telegram import *
from telegram.ext import *
from telegram.error import TimedOut

# project imports
from config import BOT_TOKEN
from modules.Global.jobs import log_bot_started


async def bot_under_maintainance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """# to handle maintainance"""
    try:
        if update.message and str(update.effective_chat.type) not in [
            "channel",
            "group",
        ]:
            await update.message.reply_html("بات در حال آپدیت شدنه. لطفا یکم صبر کن🫶")
    except:
        pass


application = ApplicationBuilder().token(BOT_TOKEN).build()
job_queue = application.job_queue

# adding handlers
application.add_handler(
    MessageHandler(filters.ALL | filters.COMMAND, bot_under_maintainance)
)


# starting the bot
job_queue.run_once(log_bot_started, 2)
try:
    application.run_polling(timeout=5)
except TimedOut:
    print("connection timed out. closing the bot...")
