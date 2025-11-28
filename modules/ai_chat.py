from telegram import *
from telegram.constants import ParseMode as PM
from telegram.constants import ReactionEmoji
from telegram.ext import *

from config import BOT_ID, GM_GROUP_ID
from modules.Global.ai_queue import ai_queue_manager


async def ai_input_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """handles the messages replied to the bot and queues them for ai to answer"""
    message: Message = update.message
    ai_queue_manager.add_to_queue(message)
    await message.set_reaction(ReactionEmoji.THINKING_FACE)


class FilterReplyToBot(filters.MessageFilter):
    def filter(self, message: Message) -> bool:
        return message.reply_to_message.from_user.id == int(BOT_ID)


ai_input_message_handler = MessageHandler(
    filters.TEXT & filters.Chat(int(GM_GROUP_ID)) & FilterReplyToBot(),
    ai_input_message,
)
