import mysql.connector as sql

from data import config


class MySQLManager:

    def __init__(self):
        self.host = config.MYSQL_HOST
        self.user = config.MYSQL_USER
        self.password = config.MYSQL_PASS
        self.database = config.MYSQL_DB
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
        self.connection.close()
