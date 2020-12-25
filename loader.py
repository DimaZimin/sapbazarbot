import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from data import config
from utils.db_api.postgresql import Database
from utils.db_api.sapbazarsql import SAPBazarSQL
from utils.parsers.api_questions import QuestionsAPI

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

json_db = '/Users/dima/PycharmProjects/sapbazar/ad_id.json'
database_file = '/Users/dima/PycharmProjects/sapbazar/sapdb.db'
loop = asyncio.get_event_loop()
db = Database(loop)
mysql_db = SAPBazarSQL()
questions_api = QuestionsAPI()
