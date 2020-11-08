from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from loader import db


class JobCategory(BoundFilter):
    async def check(self, call: types.CallbackQuery) -> bool:
        categories = [category['category_name'] for category in await db.fetch_value('category_name', 'Categories')]
        return call.data[2:] in categories


class JobLocation(BoundFilter):
    async def check(self, call: types.CallbackQuery) -> bool:
        locations = [location['location_name'] for location in await db.fetch_value('location_name', 'Locations')]
        return call.data[2:] in locations


class IsCategory(BoundFilter):
    async def check(self, call: types.CallbackQuery) -> bool:
        categories = [category['category_name'] for category in await db.fetch_value('category_name', 'Categories')]
        return call.data[1:] in categories


class IsLocation(BoundFilter):
    async def check(self, call: types.CallbackQuery) -> bool:
        locations = [location['location_name'] for location in await db.fetch_value('location_name', 'Locations')]
        return call.data[1:] in locations


class SubscriptionCategories(BoundFilter):
    async def check(self, call: types.CallbackQuery) -> bool:
        categories = [category['category_name'] for category in
                      await db.fetch_value('category_name', 'Categories')] + ['next']
        return call.data in categories


class SubscriptionLocations(BoundFilter):
    async def check(self, call: types.CallbackQuery) -> bool:
        locations = [location['location_name'] for location in
                     await db.fetch_value('location_name', 'Locations')]
        return call.data in locations