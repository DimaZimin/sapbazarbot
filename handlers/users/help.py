from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp

from loader import dp
from utils.misc import rate_limit


@rate_limit(1, 'help')
@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message):
    text = [
        'What can SAPBazarBot do?',
        "By pressing the 'Subscribe' button and proceeding with the bot's instructions, "
        "you can subscribe to the SAP job alert. ",
        'Once a job opening that satisfies your criteria is created, the bot will notify you by a message. '
        'Using this bot, you can post a job opening and find an SAP '
        'specialist through our web service available at sapbazar.com \n'
        "To do that, press the 'Post a job' button and submit all necessary information about your job opening. "
        'List of commands: ',
        '/start - shows main menu',
        '/unsubscribe - unsubscribe from blog subscription',
        '/help - shows this list of commands'
    ]
    await message.answer('\n'.join(text))
