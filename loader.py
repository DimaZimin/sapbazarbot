import asyncio
from aiogram import Bot, Dispatcher, types
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
mysql_db = SAPBazarSQL(config.MYSQL_HOST, config.MYSQL_USER, config.MYSQL_PASS, config.MYSQL_DB)
projects_db = SAPBazarSQL(config.MYSQL_HOST, config.DB_PROJ_USERNAME, config.DB_PROJ_PASSWORD, config.DB_PROJ_DATABASE)
questions_api = QuestionsAPI()
json_answers = os.path.join(os.getcwd(), "/answers.json")
