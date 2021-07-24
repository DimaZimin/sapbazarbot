import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
PAYMENTS_PROVIDER_TOKEN = str(os.getenv("PAYMENTS_PROVIDER_TOKEN"))

admins = [
    os.getenv("ADMIN_ID"),
    os.getenv("ADMIN_ID2"),
]

ip = os.getenv("ip")

aiogram_redis = {
    'host': ip,
}

redis = {
    'address': (ip, 6379),
    'encoding': 'utf8'
}
PRODUCTION = int(os.getenv('PRODUCTION', 0))
PGHOST = 'db' if PRODUCTION else str(os.getenv('PGHOST'))
PGUSER = str(os.getenv("PGUSER"))
PGPASSWORD = str(os.getenv("PGPASSWORD"))
DATABASE = str(os.getenv("DATABASE"))
POSTGRES_URI = f"postgresql://{PGUSER}:{PGPASSWORD}@{ip}/{DATABASE}"

MYSQL_HOST = str(os.getenv('MYSQL_HOST'))
MYSQL_DB = str(os.getenv('MYSQL_DB'))
MYSQL_USER = str(os.getenv('MYSQL_USER'))
MYSQL_PASS = str(os.getenv('MYSQL_PASS'))
DB_PROJ_DATABASE = str(os.getenv('DB_PROJ_DATABASE'))
DB_PROJ_USERNAME = str(os.getenv('DB_PROJ_USERNAME'))
DB_PROJ_PASSWORD = str(os.getenv('DB_PROJ_PASSWORD'))


REDIS_HOST = str(os.getenv("REDIS_HOST", default="localhost"))
REDIS_PORT = int(os.getenv("REDIS_PORT", default=6379))
REDIS_DB_FSM = int(os.getenv("REDIS_DB_FSM", default=0))
REDIS_DB_JOBSTORE = int(os.getenv("REDIS_DB_JOBSTORE", default=1))
REDIS_DB_JOIN_LIST = int(os.getenv("REDIS_DB_JOIN_LIST", default=2))


EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
PORT = os.getenv('PORT')