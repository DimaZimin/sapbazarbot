import mysql.connector as mysql

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
        self.connection = mysql.connect(host=self.host,
                                        user=self.user,
                                        password=self.password,
                                        database=self.database)
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.commit()
        self.connection.close()


class MySQLDatabase:
    def __init__(self, host, user, password, database):
        self.host = host,
        self.user = user,
        self.password = password,
        self.database = database

    def __enter__(self):
        self._conn = mysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        self._cursor = self._conn.cursor()
        return self._cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def connection(self):
        return self._conn

    @property
    def cursor(self):
        return self._cursor

    def commit(self):
        self.connection.commit()

    def close(self, commit=True):
        if commit:
            self.commit()
        self.connection.close()

    def execute(self, sql, params=None):
        self.cursor.execute(sql, params or ())

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def query(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.fetchall()

    def select_all_users(self):
        q = """
        SELECT name, email, categories FROM user
        """
        return self.query(q)

    def select_category_users(self, category):
        q = """
        SELECT name, email, categories FROM user WHERE categories LIKE %s;
        """
        return self.query(q, ("%" + category + "%",))

    def select_all_projects(self):
        q = """
        SELECT id, projectid, slug, category FROM projects
        """
        return self.query(q)

    def insert(self, table, **kwargs):
        sql = f"""
                INSERT INTO {table}({', '.join(kwargs.keys())}) 
                VALUES ({', '.join(['%s' for key in kwargs])})"""
        val = tuple(kwargs.values())

        self.execute(sql, params=val)
        self.commit()
        print('1 row inserted')
