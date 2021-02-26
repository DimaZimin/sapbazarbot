import logging

from aiogram.dispatcher.filters import CommandStart
from aiogram import types
from aiogram.utils.exceptions import MessageIdentifierNotSpecified

from keyboards.inline.keyboard import start_keys
from loader import dp, bot, db

# This is the text message that bot sends after /start command has been activated.
from utils.misc import rate_limit

START_TEXT = "You can subscribe to new SAP job openings via SAP Bazar BOT. " \
             "Sign up to receive new job alerts straight to this chat. " \
             "You can select all the categories you are interested in by pressing 'Subscribe'"


@rate_limit(5, 'start')
@dp.message_handler(CommandStart())
async def start(message: types.Message):
    """
    /start command
    """
    try:
        await bot.edit_message_reply_markup()
    except MessageIdentifierNotSpecified:
        pass
    logging.info(f'USER MESSAGE: {message.text}\tUSER ID: {message.chat.id} BEGINS SUBSCRIPTION')
    name = message.from_user.full_name
    user_id = message.from_user.id
    await db.add_user(user_id, name)
    await message.answer(text=f"Hello, {name}!\n" + START_TEXT,
                         reply_markup=start_keys(message.chat.id))
