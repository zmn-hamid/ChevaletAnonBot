"""main file"""

# telegram & flask imports
from telegram import *
from telegram.ext import *

from contextlib import asynccontextmanager
from http import HTTPStatus
from fastapi import FastAPI, Request, Response

# project imports
from config import BOT_TOKEN
from modules.Global.log import logger
from modules.start import start_cmd_handler
from modules.my_links import my_cids_handler, rm_cid_handler, add_cid_handler
from modules.admin import admin_handler
from modules.myuid import myuid_handler
from modules.settings import (
    settings_handler,
    settings_name_handler,
    unblock_all_handler,
    unblock_me_handler,
    notify_src_handler,
    notify_src_enable_handler,
    notify_src_disable_handler,
)
from modules.privacy import privacy_handler
from modules.help import help_handler, more_links_help_handler
from modules.other_msgs import other_messages_handler, other_cancels_handler
from modules.app_handlers import error_handler, job_set_commands



# build the application
ptb = ApplicationBuilder().token(BOT_TOKEN).build()
job_queue = ptb.job_queue
bot = Bot(BOT_TOKEN)


# adding handlers
for handler in [
    # start help
    start_cmd_handler,
    help_handler,
    more_links_help_handler,
    # mylinks
    my_cids_handler,
    rm_cid_handler,
    add_cid_handler,
    # settings
    settings_handler,
    settings_name_handler,
    unblock_all_handler,
    unblock_me_handler,
    notify_src_handler,
    notify_src_enable_handler,
    notify_src_disable_handler,
    # privacy
    privacy_handler,
    # admin
    admin_handler,
    # myuid
    myuid_handler,
    # other messages
    other_cancels_handler,
    other_messages_handler,
]:
    ptb.add_handler(handler)

# adding error handler
ptb.add_error_handler(error_handler)

# updating the bot's command menu
job_queue.run_once(job_set_commands, 3)

@asynccontextmanager
async def lifespan(_: FastAPI):
    await bot.setWebhook('http://radioatur.com') # replace <your-webhook-url>
    async with ptb:
        await ptb.start()
        yield
        await ptb.stop()

# Initialize FastAPI app (similar to Flask)
app = FastAPI(lifespan=lifespan)

@app.post("/")
async def process_update(request: Request):
    req = await request.json()
    update = Update.de_json(req, bot)
    await ptb.process_update(update)
    return Response(status_code=HTTPStatus.OK)


# WSGI application callable
def application(environ, start_response):
    return process_update(environ, start_response)


# # starting the bot
# logger.info("starting the bot...")
# application.run_polling()