import logging

from aiogram.dispatcher.filters import CommandStart
from aiogram import types
from aiogram.utils.exceptions import MessageIdentifierNotSpecified

from keyboards.inline.keyboard import start_keys
from loader import dp, bot, db

# This is the text message that bot sends after /start command has been activated.
from utils.misc import rate_limit

START_TEXT = "SAPGuru is a service providing instant one-on-one help for sap consultants and developers by telegram " \
             "in order to replicate for users the experience of having a sap mentor for sap consulting, " \
             "sap programming. Create a request for sap mentors for getting help with any sap problem or " \
             "Subscribe as SAP Mentor to get paid while making an impact"


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
                         reply_markup=await start_keys(message.chat.id))
