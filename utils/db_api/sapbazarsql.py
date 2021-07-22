from mysql.connector import IntegrityError

from utils.db_api import sqlmanager


class SAPBazarSQL:

    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.db_manager = sqlmanager.MySQLManager(self.host, self.user, self.password, self.database)

    def __fetchone(self, sql):
        with self.db_manager as db:
            db.execute(sql)
            result = db.fetchone()
        try:
            return result[0]
        except TypeError or IndexError:
            return None

    def __fetchall(self, sql):
        with self.db_manager as db:
            db.execute(sql)
            result = db.fetchall()
        try:
            return result
        except TypeError or IndexError:
            return None

    def __execute(self, sql, val):
        with self.db_manager as db:
            db.execute(sql, val)

    def select_raw(self, sql):
        return self.__fetchall(sql)

    def insert(self, table, **kwargs):
        sql = f"""
                INSERT INTO {table}({', '.join(kwargs.keys())}) 
                VALUES ({', '.join(['%s' for key in kwargs])})"""
        val = tuple(kwargs.values())
        print('1 row inserted')
        return self.__execute(sql, val)

    def insert_category(self, category):
        self.insert('categories', name=category, var_name=category, title=category)

    def get_city_id(self, location):
        sql = f"SELECT id FROM cities WHERE name = '{location}'"
        return self.__fetchone(sql)

    def get_category_id(self, category):
        sql = f"SELECT id FROM categories WHERE name = '{category}'"
        return self.__fetchone(sql)

    def insert_job(self, company, title, description, category, location):
        sql = f"""INSERT INTO jobs(type_id, employer_id, category_id, title, description, 
                                   created_on, expires, is_active, views_count, city_id, apply_online, company) 
                  VALUES (1, 144,(SELECT id FROM categories WHERE name = %s), %s, %s, 
                          NOW(), NOW() + INTERVAL 30 DAY, 1, 0, (SELECT id FROM cities WHERE name = %s), 
                          1, %s);"""
        val = (category, title, description, location, company)
        try:
            return self.__execute(sql, val)
        except IntegrityError:
            sql = f"""INSERT INTO jobs(type_id, employer_id, category_id, title, description, 
                                       created_on, expires, is_active, views_count, city_id, apply_online, company) 
                              VALUES (1, 144,(SELECT id FROM categories WHERE name = %s), %s,
                                     '{description}', NOW(), NOW() + INTERVAL 30 DAY, 1, 0, 1, 1, %s);"""
            val = (category, title, description, company)
            return self.__execute(sql, val)

    def get_column_where(self, table, column, where, condition):
        sql = f"""
        SELECT {column} FROM {table} WHERE {where} = {condition}
        """
        return self.__fetchall(sql)

    def delete_row_where(self, table, where, condition):
        sql = f"""
        DELETE FROM {table}  WHERE %s = %s
        """
        val = (where, condition)
        return self.__execute(sql, val)
