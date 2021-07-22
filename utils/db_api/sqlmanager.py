import mysql.connector as sql

from data import config


class MySQLManager:

    def __init__(self,
                 host=config.MYSQL_HOST,
                 user=config.MYSQL_USER,
                 password=config.MYSQL_PASS,
                 database=config.MYSQL_DB):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None

    def __enter__(self):
        self.connection = sql.connect(host=self.host,
                                      user=self.user,
                                      password=self.password,
                                      database=self.database)
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.commit()
        self.connection.close()