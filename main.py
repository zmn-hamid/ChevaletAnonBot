import asyncio
import os
from datetime import time

import pytz
from telegram.ext import ApplicationBuilder

from config import BOT_TOKEN, GM_TIME, GN_TIME, SEND_GM_GN
from modules.admin import admin_handler
from modules.ai_chat import ai_input_message_handler
from modules.Global.error_handler import error_handler
from modules.Global.jobs import (
    ai_responser,
    check_connection,
    health_check_app,
    log_bot_started,
    send_gm_gn,
    set_commands,
)
from modules.Global.log import logger
from modules.help import help_handler, more_links_clbk_handler
from modules.my_links import mylinks_handler
from modules.myuid import myuid_handler
from modules.other_msgs import no_callback_handler, other_messages_handler
from modules.privacy import privacy_handler
from modules.settings import settings_handler
from modules.start import delete_message_handler, media_group_handler, start_cmd_handler
from modules.warn_bug import warn_bug_handler

appbuilder = ApplicationBuilder().token(BOT_TOKEN)
if proxy := os.environ.get("PROXY"):
    logger.debug("Set proxy: %s" % proxy)
    appbuilder.proxy(proxy)
application = appbuilder.build()
job_queue = application.job_queue

# adding handlers
for handler in [
    # no callback handler
    no_callback_handler,
    # start help
    start_cmd_handler,
    media_group_handler,
    delete_message_handler,
    help_handler,
    more_links_clbk_handler,
    # mylinks
    mylinks_handler,
    # settings
    settings_handler,
    # privacy
    privacy_handler,
    # admin
    admin_handler,
    # myuid
    myuid_handler,
    # warn bugs
    warn_bug_handler,
    # ai message queue handler
    ai_input_message_handler,
    # other messages
    other_messages_handler,
]:
    application.add_handler(handler)

# adding error handler
application.add_error_handler(error_handler)


# check if db connection is lost every 1 hour
job_queue.run_repeating(
    check_connection,
    3600,
    5,
    job_kwargs={"misfire_grace_time": 10},
)

# run the ai responser (checks queue and answers via ai)
job_queue.run_once(
    ai_responser,
    3,
    job_kwargs={"misfire_grace_time": 10},
)

# run the ai responser (checks queue and answers via ai)
job_queue.run_once(
    set_commands,
    3,
    job_kwargs={"misfire_grace_time": 10},
)


# say gm gn
if SEND_GM_GN:
    job_queue.run_daily(
        callback=send_gm_gn,
        time=time(*GM_TIME, tzinfo=pytz.timezone("Asia/Tehran")),
        data={"is_morning": True},
        job_kwargs={"misfire_grace_time": 10},
    )
    job_queue.run_daily(
        callback=send_gm_gn,
        time=time(*GN_TIME, tzinfo=pytz.timezone("Asia/Tehran")),
        data={"is_morning": False},
        job_kwargs={"misfire_grace_time": 10},
    )


async def run_ptb():
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # log and set the commands
    logger.info(f"starting @{application.bot.username}...")
    await application.bot.set_my_commands(
        [
            ("help", "🆘 کمک!"),
            ("my_links", "🔗 لینک های من"),
            ("settings", "⚙️ تنظیمات و قابلیت ها"),
            ("cancel", "❌ کنسل کردن هرکاری که داری انجام میدی"),
        ]
    )
    logger.info("successfully set the commands")

    # Run until the application is stopped
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    finally:
        if application.updater.running:
            await application.updater.stop()
        await application.stop()
        await application.shutdown()
        logger.info("shutting down the bot")


async def main():
    bot_task = asyncio.create_task(run_ptb())
    health_task = asyncio.create_task(health_check_app())

    try:
        await asyncio.gather(bot_task, health_task)
    except Exception:
        health_task.cancel()
        await asyncio.gather(health_task, return_exceptions=True)
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.critical("closing the bot because of ctrl+c")
    except Exception as e:
        logger.critical(f"closing the bot because: {e} | {e.__class__.__name__}")
