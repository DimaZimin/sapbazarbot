from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp

from loader import dp
from utils.misc import rate_limit


@rate_limit(1, 'help')
@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message):
    text = [
        'List of commands: ',
        '/start - shows main menu',
        '/unsubscribe - unsubscribe from job and blog subscription',
        '/help - shows this list of commands'
    ]
    await message.answer('\n'.join(text))
