from utils.db_api import sqlmanager


class SAPBazarSQL:

    @staticmethod
    def __fetchone(sql):
        with sqlmanager.MySQLManager() as db:
            db.execute(sql)
            result = db.fetchone()
        try:
            return result[0]
        except TypeError and IndexError:
            return None

    @staticmethod
    def __fetchall(sql):
        with sqlmanager.MySQLManager() as db:
            db.execute(sql)
            result = db.fetchall()
        try:
            return result
        except TypeError and IndexError:
            return None

    @staticmethod
    def __execute(sql):
        with sqlmanager.MySQLManager() as db:
            db.execute(sql)

    def select_raw(self, sql):
        return self.__fetchall(sql)

    def insert(self, table, **kwargs):
        sql = f"""
                INSERT INTO {table}({', '.join(kwargs.keys())}) 
                VALUES ({', '.join([f"'{key}'" for key in kwargs.values()])})"""
        return self.__execute(sql)

    def insert_category(self, category):
        self.insert('categories', name=category, var_name=category, title=category)

    def get_city_id(self, location):
        sql = f"SELECT id FROM cities WHERE name = '{location}'"
        return self.__fetchone(sql)

    def get_category_id(self, category):
        sql = f"SELECT id FROM categories WHERE name = '{category}'"
        return self.__fetchone(sql)

    def insert_job(self, company, title, description, category):
        sql = f"""INSERT INTO jobs(type_id, employer_id, category_id, title, description, 
                                   created_on, expires, is_active, views_count, city_id, apply_online, company) 
                  VALUES (1, 144,(SELECT id FROM categories WHERE name = '{category}'), '{title}','{description}', 
                          NOW(), NOW() + INTERVAL 30 DAY, 1, 0, 1, 1,'{company}');"""
        return self.__execute(sql)

    def get_column_where(self, table, column, where, condition):
        sql = f"""
        SELECT {column} FROM {table} WHERE {where} = '{condition}' 
        """
        return self.__fetchall(sql)

    def delete_row_where(self, table, where, condition):
        sql = f"""
        DELETE FROM {table} WHERE {where} = {condition}
        """
        return self.__execute(sql)
