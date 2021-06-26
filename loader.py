import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from data import config
from utils.db_api.postgresql import Database
from utils.db_api.sapbazarsql import SAPBazarSQL
from utils.parsers.api_questions import QuestionsAPI
import os

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = RedisStorage2(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB_FSM)
dp = Dispatcher(bot, storage=storage)


json_db = os.path.join(os.getcwd(), 'ad_id.json')
loop = asyncio.get_event_loop()
db = Database(loop)
mysql_db = SAPBazarSQL()
questions_api = QuestionsAPI()
json_answers = os.getcwd() + "/answers.json"
