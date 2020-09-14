from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from utils.db_api.db_manager import SQLContextManager
from data import config

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


json_db = '/Users/dima/PycharmProjects/sapbazar/ad_id.json'
database_file = '/Users/dima/PycharmProjects/sapbazar/sapdb.db'
db_manager = SQLContextManager(database_file)