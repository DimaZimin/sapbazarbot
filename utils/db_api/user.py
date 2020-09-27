import asyncio

from sqlalchemy import Column, Integer, BigInteger, String, Boolean, sql
from asyncpg import UniqueViolationError
from utils.db_api.dborm import TimedBaseModel, db
from data import config

class User(TimedBaseModel):

    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    name = Column(String(255))
    email = Column(String(255))
    job_subscription = Column(Boolean)
    blog_subscription = Column(Boolean)
    location = Column(String(255))

    query: sql.Select


async def add_user(user_id: int,
                   name: str,
                   email: str = None,
                   job_subscription: bool = None,
                   blog_subscription: bool = None,
                   location: str = None):
    try:
        user = User(user_id=user_id,
                    name=name,
                    email=email,
                    job_subscription=job_subscription,
                    blog_subscription=blog_subscription,
                    location=location
                    )
        await user.create()
    except UniqueViolationError:
        pass


async def select_all_users():
    users = await User.query.gino.all()
    return users

async def select_user(user_id: int):
    user = await User.query.where(User.user_id == user_id).gino.first()
    return user



async def test():
    await db.set_bind(config.POSTGRES_URI)
    await select_user(111)


loop = asyncio.get_event_loop()
loop.run_until_complete(test())