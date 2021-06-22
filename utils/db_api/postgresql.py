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
        is_mentor BOOLEAN,
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
        paid BOOLEAN NOT NULL,
        username VARCHAR(255),
        email VARCHAR(255)
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
        user_id INT NOT NULL,
        post_id VARCHAR (255) UNIQUE,
        user_mail VARCHAR (255), 
        external_user_id VARCHAR (255)
        );
        """
        await self.pool.execute(sql)

    async def create_table_answers(self):
        sql = """
        CREATE TABLE IF NOT EXISTS answers (
        user_id INT NOT NULL,
        question_id VARCHAR(255) NOT NULL REFERENCES questions (post_id),
        post_id VARCHAR(255),
        user_mail VARCHAR(255)
        );
        """
        await self.pool.execute(sql)

    async def create_table_consultations(self):
        sql = """
        CREATE TABLE IF NOT EXISTS consultation_requests (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        budget INT,
        content TEXT,
        image_url VARCHAR(1023),
        category VARCHAR(255),
        contact VARCHAR(255),
        closed BOOLEAN NOT NULL DEFAULT FALSE
        );
        """
        await self.pool.execute(sql)

    async def create_table_assistants(self):
        sql = """
        CREATE TABLE IF NOT EXISTS assistants (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        name VARCHAR(255),
        contact TEXT,
        request INT REFERENCES consultation_requests(id) ON DELETE CASCADE
        )
        """
        await self.pool.execute(sql)

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
            sql = """
            UPDATE Users SET name = $2, email = $3, job_subscription = $4, blog_subscription = $5
            WHERE user_id = $1;
            """
            await self.pool.execute(sql, user_id, name, email, job_subscription, blog_subscription)

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
        return await self.pool.execute(sql, user_id, post_id, str(user_email), external_user_id)

    async def create_answer(self, user_id, user_mail, question_id, post_id):
        sql = """
        INSERT INTO answers (user_id, user_mail, question_id, post_id)
        VALUES($1, $2, $3, $4)
        """
        return await self.pool.execute(sql, user_id, str(user_mail), question_id, post_id)

    async def get_user_mail_by_answer_id(self, answer_id):
        sql = f"""
        SELECT user_mail FROM answers WHERE post_id = '{answer_id}'
        """
        return await self.pool.fetch(sql)

    async def get_user_by_answer_id(self, answer_id):
        sql = f"""
            SELECT user_id FROM answers WHERE post_id = $1
            """
        return await self.pool.fetchval(sql, str(answer_id))

    async def get_question_id_by_answer_id(self, answer_id):
        sql = f"""
        SELECT question_id FROM answers WHERE post_id = '{answer_id}'
        """
        return await self.pool.fetch(sql)

    async def get_all_questions_by_user(self, user_id):
        sql = f"""
        SELECT post_id FROM questions WHERE user_id = {user_id}
        """
        return await self.pool.fetch(sql)

    async def get_user_question_mail(self, user_id):
        sql = f"""
        SELECT user_mail FROM questions WHERE user_id = {user_id}
        """
        return await self.pool.fetch(sql)

    async def get_mail_by_user_id(self, user_id):
        sql = f"""
        SELECT email FROM users WHERE user_id = {user_id} 
        """
        return await self.pool.fetchval(sql)

    async def select_user_by_post_id(self, post_id):
        sql = f"""
        SELECT user_id FROM questions WHERE post_id = $1
        """
        return await self.pool.fetchval(sql, post_id)

    async def select_category_users(self, category):
        sql = f"""
        SELECT user_id FROM subscriptions WHERE category = $1
        """
        return await self.pool.fetch(sql, category)

    async def select_external_user_id(self, email):
        sql = f"""
        SELECT external_user_id FROM questions WHERE user_mail = $1
        """
        return await self.pool.fetchval(sql, email)

    async def is_mentor(self, user_id):
        sql = """
        SELECT is_mentor FROM users WHERE user_id = $1
        """
        value = await self.pool.fetchval(sql, user_id)
        return True if value else False

    async def select_mentors_for_category(self, category):
        sql = """
        SELECT s.user_id FROM subscriptions s LEFT JOIN users u ON s.user_id = u.user_id 
        WHERE s.category = $1 AND u.is_mentor = true
        """
        return await self.pool.fetch(sql, category)

    async def select_all_mentors(self):
        sql = """
        SELECT user_id FROM users WHERE is_mentor = true
        """
        return await self.pool.fetch(sql)

    async def create_consultation_record(self, user_id, budget, content, image_url, category, contact):
        sql = """
        INSERT INTO consultation_requests(user_id, budget, content, image_url, category, contact) 
        VALUES ($1, $2, $3, $4, $5, $6) RETURNING id;
        """
        return await self.pool.fetchrow(sql, user_id, budget, content, image_url, category, contact)

    async def assign_assistance(self, assistant_id, name, contact, request_id):
        sql = """
        INSERT INTO assistants(user_id, name, contact, request)
        VALUES ($1, $2, $3, $4) RETURNING id;
        """
        return await self.pool.fetchrow(sql, assistant_id, name, contact, request_id)

    async def get_consultation_record(self, record_id):
        sql = """
        SELECT * FROM consultation_requests WHERE id = $1;
        """
        return await self.pool.fetchrow(sql, record_id)

    async def get_assistant(self, assistance_id):
        sql = """
        SELECT * FROM assistants WHERE id = $1;
        """
        return await self.pool.fetchrow(sql, assistance_id)

    async def select_assistants_for_request(self, request_id):
        sql = """
        SELECT * FROM assistants WHERE request = $1;
        """
        return await self.pool.fetch(sql, request_id)

    async def select_assigned_tasks(self, user_id):
        sql = """
        SELECT * FROM assistants WHERE user_id = $1;
        """
        return await self.pool.fetch(sql, user_id)

    async def get_requests_for_client(self, user_id):
        sql = """
        SELECT * from consultation_requests WHERE user_id = $1 AND closed = false;
        """
        return await self.pool.fetch(sql, user_id)

    async def get_assigned_requests(self, user_id):
        sql = """
        SELECT * from assistants WHERE user_id = $1
        """
        return await self.pool.fetch(sql, user_id)

    async def mark_request_as_paid(self, request_id):
        sql = """
        UPDATE consultation_requests SET paid = TRUE WHERE id = $1 RETURNING id, paid;
        """
        return await self.pool.fetch(sql, request_id)

    async def close_request(self, request_id):
        sql = """
        UPDATE consultation_requests SET closed = TRUE WHERE id = $1;
        """
        return await self.pool.execute(sql, request_id)

    async def mark_request_as_resolved_by_client(self, request_id):
        sql = """
        UPDATE consultation_requests SET resolved_client = TRUE WHERE id = $1;
        """
        return await self.pool.execute(sql, request_id)

    async def mark_request_as_resolved_by_consultant(self, request_id):
        sql = """
        UPDATE consultation_requests SET resolved_consultant = TRUE WHERE id = $1 RETURNING user_id, resolved_client;
        """
        return await self.pool.fetchrow(sql, request_id)

    async def create_or_update_consultant(self, user_id, name, last_name, exp):
        sql = """
        INSERT INTO consultants (user_id, name, last_name, about) VALUES ($1, $2, $3, $4)
        """
        try:
            return await self.pool.execute(sql, user_id, name, last_name, exp)
        except UniqueViolationError:
            sql = """
            UPDATE consultants SET name = $2, last_name = $3, about = $4 WHERE user_id = $1;
            """
            return await self.pool.execute(sql, user_id, name, last_name, exp)

    async def get_consultant_experience(self, user_id):
        sql = """
        SELECT about FROM consultants WHERE user_id = $1;
        """
        return await self.pool.fetchval(sql, user_id)

    async def remove_assistance_record(self, request, user_id):
        sql = """
        DELETE FROM assistants WHERE request = $1 AND user_id = $2;
        """
        return await self.pool.execute(sql, request, user_id)

    async def delete_consultation_record(self, request):
        sql = """
        DELETE FROM consultation_requests WHERE id = $1;
        """
        return await self.pool.execute(sql, request)
