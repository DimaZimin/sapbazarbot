import logging
from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from keyboards.inline.keyboard import start_keys

from loader import dp

# This is the text message that bot sends after /start command has been activated.
START_TEXT = "You can subscribe to new SAP job openings via SAP Bazar BOT. " \
             "Sign up to receive new job alerts straight to this chat. " \
             "You can select all the categories you are interested in by pressing 'Subscribe'"


@dp.message_handler(CommandStart())
async def start(message: types.Message):
    """
    /start command
    """
    logging.info(f'USER MESSAGE: {message.text}\tUSER ID: {message.chat.id} BEGINS SUBSCRIPTION')
    await message.answer(text=f"Hello, {message.from_user.full_name}!\n" + START_TEXT,
                         reply_markup=start_keys())
