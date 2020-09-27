from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from loader import db, loop


class IsCategory(BoundFilter):
    async def check(self, call: types.CallbackQuery) -> bool:
        categories = [category['category_name'] for category in await db.fetch_value('category_name', 'Categories')]
        return call.data in categories

