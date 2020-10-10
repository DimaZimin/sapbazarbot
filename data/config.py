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

PGUSER = str(os.getenv("PGUSER"))
PGPASSWORD = str(os.getenv("PGPASSWORD"))
DATABASE = str(os.getenv("DATABASE"))
POSTGRES_URI = f"postgresql://{PGUSER}:{PGPASSWORD}@{ip}/{DATABASE}"

MYSQL_HOST = str(os.getenv('MYSQL_HOST'))
MYSQL_DB = str(os.getenv('MYSQL_DB'))
MYSQL_USER = str(os.getenv('MYSQL_USER'))
MYSQL_PASS = str(os.getenv('MYSQL_PASS'))
