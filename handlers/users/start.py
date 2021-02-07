import logging

from aiogram.dispatcher.filters import CommandStart
from aiogram import types
from aiogram.utils.exceptions import MessageIdentifierNotSpecified

from keyboards.inline.keyboard import start_keys
from loader import dp, bot

# This is the text message that bot sends after /start command has been activated.
from utils.misc import rate_limit

START_TEXT = "Welcome to SAPGURU. SAPGURU is sap support bot.\n- To subscribe to latest SAP Blogs, articles and answering of questions push the button 'Subscribe'\n- Need help of sap experts push the button 'Raise a ticket'"


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
    await message.answer(text=f"Hello, {message.from_user.full_name}!\n" + START_TEXT,
                         reply_markup=start_keys(message.chat.id))
