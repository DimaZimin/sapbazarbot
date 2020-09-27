from aiogram import Dispatcher
from .filters import IsCategory
from .filters import IsLocation
from .filters import SubscriptionCategories


def setup(dp: Dispatcher):
    dp.filters_factory.bind(IsCategory)
    dp.filters_factory.bind(IsLocation)
    dp.filters_factory.bind(SubscriptionCategories)
    pass
