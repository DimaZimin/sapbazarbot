import asyncpg
from asyncpg.exceptions import UniqueViolationError
import asyncio
from data import config


# noinspection SqlNoDataSourceInspection
class Database:

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.pool: asyncpg.pool.Pool = loop.run_until_complete(
            asyncpg.create_pool(
                database='sap_bazar',
                user=config.PGUSER,
                password=config.PGPASSWORD,
                host=config.ip
            )
        )

    async def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
        user_id INT NOT NULL,
        name VARCHAR(255),
        email VARCHAR(255) UNIQUE,
        job_subscription BOOLEAN NOT NULL,
        blog_subscription BOOLEAN NOT NULL,
        location VARCHAR(255),
        PRIMARY KEY(user_id)
        );
        """

        await self.pool.execute(sql)

    async def create_table_categories(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Categories (
        id SERIAL PRIMARY KEY,
        category_name VARCHAR(255) UNIQUE
        );
        """
        await self.pool.execute(sql)

    async def create_table_locations(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Locations (
        id SERIAL PRIMARY KEY,
        location_name VARCHAR(255) UNIQUE
        );
        """
        await self.pool.execute(sql)

    async def create_table_subscriptions(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Subscriptions (
        user_id INT NOT NULL REFERENCES Users (user_id),
        category VARCHAR(255),
        UNIQUE (user_id, category)
        );
        """
        await self.pool.execute(sql)

    async def create_table_job_posting_orders(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Job_posting_orders (
        id SERIAL PRIMARY KEY,
        user_id	INT NOT NULL REFERENCES Users (user_id),
        company VARCHAR(255),
        job_name VARCHAR(255),	
        job_description VARCHAR(2555),	
        job_category VARCHAR(255),
        job_location VARCHAR(255),
        paid BOOLEAN NOT NULL
        );
        """
        await self.pool.execute(sql)

    async def create_table_settings(self):
        sql = """
        CREATE TABLE IF NOT EXISTS settings (
        payable BOOLEAN NOT NULL,
        posting_fees INT NOT NULL
        );
        """
        await self.pool.execute(sql)

    async def create_table_questions(self):
        sql = """
        CREATE TABLE IF NOT EXISTS questions (
        user_id INT NOT NULL REFERENCES Users (user_id),
        post_id VARCHAR (255),
        user_mail VARCHAR (255), 
        external_user_id VARCHAR (255)
        );
        """
        await self.pool.execute(sql)

    async def create_table_answers(self):
        pass

    async def payable_post(self, payable='True'):
        sql = f"""
        UPDATE settings 
        SET payable = {payable}
        """
        await self.pool.execute(sql)

    async def drop_all(self):
        sql = """
        DO $$ DECLARE
        r RECORD;
        BEGIN
        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
        EXECUTE 'DROP TABLE ' || quote_ident(r.tablename) || ' CASCADE';
        END LOOP;
        END $$;
        """
        await self.pool.execute(sql)

    async def add_user(self, user_id: int, name: str = None, email: str = None, job_subscription: bool = False,
                       blog_subscription: bool = False):
        sql = "INSERT INTO Users (user_id, name, email, job_subscription, blog_subscription) " \
              "VALUES($1, $2, $3, $4, $5)"
        try:
            await self.pool.execute(sql, user_id, name, email, job_subscription, blog_subscription)
        except UniqueViolationError:
            pass

    async def select_user(self, location, category):
        sql = f"""
        SELECT subscriptions.user_id, location, category 
        FROM Users LEFT JOIN Subscriptions ON users.user_id = subscriptions.user_id
        WHERE users.location = '{location}' 
        AND subscriptions.category = '{category}'
        """
        return await self.pool.fetch(sql)

    async def update_user(self, user_id, **kwargs):
        sql = "UPDATE Users SET " + \
                  ", ".join([f"{value[0]}='{str(value[1])}'" for value in zip(kwargs.keys(), kwargs.values())]) \
                  + f' WHERE user_id={user_id}'
        return await self.pool.execute(sql)

    async def get_value(self, table: str, column: str, where_col: str, value):
        sql = f"""
        SELECT {column}
        FROM {table}
        WHERE {where_col} = '{value}'
        """
        return await self.pool.fetch(sql)

    async def get_category_id(self, category_name: str):
        return await self.get_value(column='id',
                                    table='categories',
                                    where_col='category_name',
                                    value=category_name)

    async def fetch_all(self, table):
        sql = f"""
        SELECT *
        FROM {table}
        """
        return await self.pool.fetch(sql)

    async def add_location(self, location_name: str):
        sql = """
        INSERT INTO Locations 
        (location_name)
        VALUES ($1)
        """
        try:
            return await self.pool.execute(sql, location_name)
        except UniqueViolationError:
            return 'Record exists'

    async def fetch_value(self, col, table):
        sql = f"""
        SELECT {col}
        FROM {table}
        """
        return await self.pool.fetch(sql)

    async def add_category(self, category_name: str):
        sql = """
        INSERT INTO Categories
        (category_name)
        VALUES ($1)
        """
        try:
            return await self.pool.execute(sql, category_name)
        except UniqueViolationError:
            return 'Record exists'

    async def add_user_category(self, user_id, category):
        sql = """
        INSERT INTO subscriptions(user_id, category)
        VALUES ($1, $2);
        """
        try:
            return await self.pool.execute(sql, user_id, category)
        except UniqueViolationError:
            pass

    async def add_values(self, table_name: str, **kwargs):
        rows = ', '.join(kwargs.keys())
        values = ', '.join(kwargs.values())
        sql = f"""
        INSERT INTO {table_name}({rows})
        VALUES ({values});
        """
        try:
            return await self.pool.execute(sql)
        except UniqueViolationError:
            pass

    async def delete_data(self, table):
        sql = f"""
        DELETE FROM {table}
        """
        return await self.pool.execute(sql)

    async def delete_user_subscription(self, user_id):
        sql = f"""
        DELETE FROM subscriptions
        WHERE user_id = {user_id}
        """
        return await self.pool.execute(sql)

    async def get_blog_subscription_users(self, category):
        sql = f"""
        SELECT subscriptions.user_id, subscriptions.category, users.blog_subscription
        FROM users LEFT JOIN subscriptions ON users.user_id = subscriptions.user_id
        WHERE users.blog_subscription = true AND subscriptions.category = '{category}'
        ORDER by users.user_id
        """
        return await self.pool.fetch(sql)

    async def get_category_subscribers(self, category):
        sql = f"""
        SELECT user_id FROM subscriptions WHERE category = '{category}'
        """
        return await self.pool.fetch(sql)

    async def remove_category(self, category):
        sql = f"""
        DELETE FROM Categories
        WHERE category_name = '{category}'
        """
        return await self.pool.execute(sql)

    async def remove_location(self, location):
        sql = f"""
        DELETE FROM Locations
        WHERE location_name = '{location}'
        """
        return await self.pool.execute(sql)

    async def total_users(self):
        sql = f"""
        SELECT COUNT(user_id) FROM Users
        """
        return await self.pool.fetch(sql)

    async def subscribed_users(self):
        sql = f"""
        SELECT COUNT(user_id)
        FROM Users
        WHERE job_subscription = True
        """
        return await self.pool.fetch(sql)

    async def submit_order(self, user_id, company, job_name, job_description,
                           job_category, job_location, paid, username, email):
        sql = """
        INSERT INTO job_posting_orders (user_id, company, job_name, job_description, 
                                        job_category, job_location, paid, username, email)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        return await self.pool.execute(sql, user_id, company, job_name, job_description,
                                       job_category, job_location, paid, username, email)

    async def set_posting_fees(self, fees: int):
        sql = f"""
        UPDATE settings SET posting_fees = {fees} 
        """
        return await self.pool.execute(sql)

    async def get_username(self, job_title):
        sql = f"""
        SELECT username FROM job_posting_orders WHERE job_name LIKE '{job_title}%'
        """
        return await self.pool.fetch(sql)

    async def create_question(self, user_id, post_id, user_email, external_user_id):
        sql = f"""
        INSERT INTO questions (user_id, post_id, user_mail, external_user_id) 
        VALUES($1, $2, $3, $4)
        """
        return await self.pool.execute(sql, user_id, post_id, user_email, external_user_id)
